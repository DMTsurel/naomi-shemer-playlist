"""Generic composer-agnostic YouTube playlist uploader (cookies/InnerTube and OAuth v3)."""

from __future__ import annotations

import hashlib
import http.cookiejar
import json
from pathlib import Path
import re
import sys
import time
from typing import Any
import requests

from core.config import REPO_ROOT, load_composer


def load_composer_video_ids(slug: str, composer_dir: Path | None = None) -> list[dict[str, str]]:
    """Load ordered matched YouTube video IDs and titles from `<slug>/playlist.json`."""
    cfg = load_composer(slug, composer_dir=composer_dir)
    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    items: list[dict[str, str]] = []
    for entry in data.get("playlist", []):
        sel = entry.get("selected_video")
        if sel and sel.get("video_id"):
            items.append({
                "video_id": sel["video_id"],
                "title": entry["title"],
                "tier_label": entry.get("tier_label", ""),
            })
    return items


def _default_playlist_description(name_he: str, desc_override: str) -> str:
    if desc_override:
        return desc_override
    return f"אוסף מקיף וכרונולוגי של שירי {name_he} — אלבומים מקוריים, ביצועים היסטוריים וקאברים נבחרים."


def upload_composer_via_cookies(
    slug: str,
    cookies_file: str | Path,
    *,
    privacy: str = "UNLISTED",
    composer_dir: Path | None = None,
) -> str:
    """Create and populate a YouTube playlist using InnerTube SAPISIDHASH and Netscape cookies.txt."""
    cfg = load_composer(slug, composer_dir=composer_dir)
    items = load_composer_video_ids(slug, composer_dir=composer_dir)
    video_ids = [x["video_id"] for x in items]

    cj = http.cookiejar.MozillaCookieJar(str(cookies_file))
    cj.load(ignore_discard=True, ignore_expires=True)
    session = requests.Session()
    session.cookies = cj

    sapisid = None
    for c in cj:
        if c.name in ("SAPISID", "__Secure-3PAPISID") and "youtube.com" in c.domain:
            sapisid = c.value
            break
    if not sapisid:
        raise RuntimeError("שגיאה: לא נמצאה עוגיית SAPISID בקובץ ה-cookies.")

    origin = "https://www.youtube.com"
    r_home = session.get(origin, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    m_ctx = re.search(r'"INNERTUBE_CONTEXT":(\{.*?\}),"INNERTUBE_', r_home.text)
    if not m_ctx:
        raise RuntimeError("שגיאה: לא ניתן לחלץ INNERTUBE_CONTEXT מדף הבית של יוטיוב.")
    context = json.loads(m_ctx.group(1))

    def yt_post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        ts = int(time.time())
        sha1_hex = hashlib.sha1(f"{ts} {sapisid} {origin}".encode("utf-8")).hexdigest()
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
            "Authorization": f"SAPISIDHASH {ts}_{sha1_hex}",
            "X-Origin": origin,
            "X-Goog-AuthUser": "0",
        }
        body = {"context": context, **payload}
        resp = session.post(f"{origin}{endpoint}?prettyPrint=false", headers=headers, json=body, timeout=20)
        resp.raise_for_status()
        return resp.json()

    title = f"{cfg.playlist_title_he} - האוסף המקיף ({len(video_ids)} שירים)"
    desc = _default_playlist_description(cfg.name_he, cfg.playlist_description_he)
    print(f"יוצר פלייליסט חדש: {title}...")
    res = yt_post("/youtubei/v1/playlist/create", {
        "title": title,
        "description": desc,
        "privacyStatus": privacy.upper(),
    })
    playlist_id = res.get("playlistId")
    if not playlist_id:
        raise RuntimeError(f"שגיאה ביצירת הפלייליסט: {res}")

    print(f"הפלייליסט נוצר! מזהה: {playlist_id}")
    batch_size = 50
    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i : i + batch_size]
        print(f"  -> מוסיף שירים {i + 1} עד {min(i + batch_size, len(video_ids))} מתוך {len(video_ids)}...")
        yt_post("/youtubei/v1/browse/edit_playlist", {
            "playlistId": playlist_id,
            "actions": [{"action": "ACTION_ADD_VIDEO", "addedVideoId": vid} for vid in batch],
        })
        time.sleep(0.5)

    print(f"\nהפלייליסט המלא זמין בכתובת:\nhttps://www.youtube.com/playlist?list={playlist_id}")
    return str(playlist_id)


def _resolve_client_secret(cfg_dir: Path, client_secret: Path | None) -> Path:
    if client_secret is not None:
        return client_secret
    local_secret = cfg_dir / "client_secret.json"
    if local_secret.exists():
        return local_secret
    return REPO_ROOT / "client_secret.json"


def upload_composer_via_oauth(
    slug: str,
    *,
    client_secret: Path | None = None,
    privacy: str = "unlisted",
    composer_dir: Path | None = None,
) -> str:
    """Create and resume-upload a YouTube playlist using official YouTube Data API v3 + OAuth 2.0."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        raise RuntimeError(
            "חסרות ספריות Google API. התקן באמצעות: "
            "pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        ) from exc

    cfg = load_composer(slug, composer_dir=composer_dir)
    secret_path = _resolve_client_secret(cfg.dir, client_secret)
    if not secret_path.exists():
        raise FileNotFoundError(
            f"לא נמצא הקובץ {secret_path}. הורד client_secret.json מ-Google Cloud Console "
            f"או השתמש ב-{cfg.create_js.name} בקונסול של YouTube."
        )

    scopes = ["https://www.googleapis.com/auth/youtube"]
    token_path = cfg.oauth_token_json
    creds = Credentials.from_authorized_user_file(str(token_path), scopes) if token_path.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), scopes)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    youtube = build("youtube", "v3", credentials=creds)
    items = load_composer_video_ids(slug, composer_dir=composer_dir)

    progress_path = cfg.upload_progress_json
    progress: dict[str, Any] = {"playlist_id": None, "added_video_ids": []}
    if progress_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))

    playlist_id = progress.get("playlist_id")
    if not playlist_id:
        title = f"{cfg.playlist_title_he} - האוסף המקיף ({len(items)} שירים)"
        desc = _default_playlist_description(cfg.name_he, cfg.playlist_description_he)
        res = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": desc},
                "status": {"privacyStatus": privacy.lower()},
            },
        ).execute()
        playlist_id = res["id"]
        progress["playlist_id"] = playlist_id
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"נוצר פלייליסט חדש: https://www.youtube.com/playlist?list={playlist_id}")

    added_set = set(progress.get("added_video_ids", []))
    for idx, item in enumerate(items, 1):
        vid = item["video_id"]
        if vid in added_set:
            continue
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": vid},
                    }
                },
            ).execute()
            progress["added_video_ids"].append(vid)
            added_set.add(vid)
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[{idx}/{len(items)}] נוסף השיר: {item['title']} ({vid})")
            time.sleep(0.3)
        except HttpError as exc:
            if exc.resp.status == 403 and "quotaExceeded" in str(exc):
                print("\n[!] הגעת למכסת ה-API היומית של YouTube Data API v3.")
                print(f"נוספו עד כה {len(added_set)}/{len(items)} שירים.")
                print(f"קישור לפלייליסט: https://www.youtube.com/playlist?list={playlist_id}")
                print("הרץ את הסקריפט שוב מחר והוא ימשיך אוטומטית מהשיר הבא!")
                sys.exit(0)
            print(f"  [!] שגיאה בהוספת {item['title']} ({vid}): {exc}")

    print(f"\nהסתיימה העלאת כל {len(added_set)} השירים!")
    print(f"קישור לפלייליסט: https://www.youtube.com/playlist?list={playlist_id}")
    return str(playlist_id)
