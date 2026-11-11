#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
העלאת הפלייליסט "שירי נעמי שמר - האוסף המקיף" (449 שירים) לחשבון יוטיוב.

הסקריפט תומך בשתי שיטות לבחירתך:
  שיטה 1 (מומלצת ומהירה - ללא מגבלת מכסה של 200 שירים ליום וללא צורך בפרויקט Google Cloud):
    שימוש ב-create_playlist_in_browser.js בקונסול של לשונית https://www.youtube.com פתוחה,
    או העברת קובץ cookies.txt לסקריפט זה (--cookies cookies.txt).

  שיטה 2 (רשמית דרך YouTube Data API v3 + OAuth 2.0):
    הנח קובץ client_secret.json בתיקייה זו והרץ:
      python3 upload_youtube_playlist.py --oauth
    הסקריפט שומר התקדמות ב-raw_cache/youtube_upload_progress.json כך שאם מכסת ה-API היומית
    של גוגל (כ-200 שירים ביום) מתמלאת, הרצה חוזרת תמשיך אוטומטית מהשיר שבו עצרה!
"""

import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "raw_cache")
PLAYLIST_JSON_PATH = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.json")
PROGRESS_PATH = os.path.join(CACHE_DIR, "youtube_upload_progress.json")
CLIENT_SECRET_PATH = os.path.join(BASE_DIR, "client_secret.json")
TOKEN_PATH = os.path.join(CACHE_DIR, "youtube_oauth_token.json")


def load_video_ids() -> List[Dict[str, str]]:
    with open(PLAYLIST_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for entry in data["playlist"]:
        sel = entry.get("selected_video")
        if sel and sel.get("video_id"):
            items.append({
                "video_id": sel["video_id"],
                "title": entry["title"],
                "tier_label": entry["tier_label"],
            })
    return items


def upload_via_cookies(cookies_file: str) -> None:
    """יוצר את הפלייליסט ומוסיף את כל 449 השירים תוך שניות באמצעות Innertube API ו-cookies.txt."""
    items = load_video_ids()
    video_ids = [x["video_id"] for x in items]

    cj = http.cookiejar.MozillaCookieJar(cookies_file)
    cj.load(ignore_discard=True, ignore_expires=True)
    session = requests.Session()
    session.cookies = cj

    sapisid = None
    for c in cj:
        if c.name in ("SAPISID", "__Secure-3PAPISID") and "youtube.com" in c.domain:
            sapisid = c.value
            break
    if not sapisid:
        print("שגיאה: לא נמצאה עוגיית SAPISID בקובץ ה-cookies.")
        sys.exit(1)

    origin = "https://www.youtube.com"
    r_home = session.get(origin, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    m_ctx = re.search(r'"INNERTUBE_CONTEXT":(\{.*?\}),"INNERTUBE_', r_home.text)
    if not m_ctx:
        print("שגיאה: לא ניתן לחלץ INNERTUBE_CONTEXT מדף הבית של יוטיוב.")
        sys.exit(1)
    context = json.loads(m_ctx.group(1))

    def yt_post(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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

    title = f"שירי נעמי שמר - האוסף המקיף ({len(video_ids)} שירים)"
    desc = (
        "אוסף מקיף של שירי נעמי שמר (אלבומיה של נעמי שמר, ביצועים מקוריים מתוך אלבומים, "
        "הקלטות ארכיון וקאברים נבחרים). נוצר מתוך איחוד 9 מאגרים."
    )
    print(f"יוצר פלייליסט חדש: {title}...")
    res = yt_post("/youtubei/v1/playlist/create", {
        "title": title,
        "description": desc,
        "privacyStatus": "UNLISTED",
    })
    playlist_id = res.get("playlistId")
    if not playlist_id:
        print("שגיאה ביצירת הפלייליסט:", res)
        sys.exit(1)

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


def upload_via_oauth() -> None:
    """יוצר את הפלייליסט ומוסיף שירים באמצעות YouTube Data API v3 הרשמי (עם שמירת התקדמות)."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError:
        print("מתקין ספריות Google API נדרשות...")
        os.system(f"{sys.executable} -m pip install --user google-api-python-client google-auth-oauthlib google-auth-httplib2")
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

    if not os.path.exists(CLIENT_SECRET_PATH):
        print(f"שגיאה: לא נמצא הקובץ {CLIENT_SECRET_PATH}")
        print("כדי להשתמש ב-OAuth רשמי, הורד קובץ OAuth Desktop client_secret.json מ-Google Cloud Console")
        print("או השתמש בקובץ create_playlist_in_browser.js שיוצר את כל 449 השירים תוך 10 שניות ללא צורך ב-API Key!")
        sys.exit(1)

    scopes = ["https://www.googleapis.com/auth/youtube"]
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, scopes)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    youtube = build("youtube", "v3", credentials=creds)
    items = load_video_ids()

    progress: Dict[str, Any] = {"playlist_id": None, "added_video_ids": []}
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            progress = json.load(f)

    playlist_id = progress.get("playlist_id")
    if not playlist_id:
        title = f"שירי נעמי שמר - האוסף המקיף ({len(items)} שירים)"
        desc = (
            "אוסף מקיף של שירי נעמי שמר (אלבומיה של נעמי שמר, ביצועים מקוריים מתוך אלבומים, "
            "הקלטות ארכיון וקאברים נבחרים). נוצר מתוך איחוד 9 מאגרים."
        )
        req = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": desc},
                "status": {"privacyStatus": "unlisted"},
            },
        )
        res = req.execute()
        playlist_id = res["id"]
        progress["playlist_id"] = playlist_id
        with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
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
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
            print(f"[{idx}/{len(items)}] נוסף השיר: {item['title']} ({vid})")
            time.sleep(0.3)
        except HttpError as e:
            if e.resp.status == 403 and "quotaExceeded" in str(e):
                print("\n[!] הגעת למכסת ה-API היומית של YouTube Data API v3.")
                print(f"נוספו עד כה {len(added_set)}/{len(items)} שירים.")
                print(f"קישור לפלייליסט: https://www.youtube.com/playlist?list={playlist_id}")
                print("הרץ את הסקריפט שוב מחר והוא ימשיך אוטומטית מהשיר הבא!")
                sys.exit(0)
            else:
                print(f"  [!] שגיאה בהוספת {item['title']} ({vid}): {e}")

    print(f"\nהסתיימה העלאת כל {len(added_set)} השירים!")
    print(f"קישור לפלייליסט: https://www.youtube.com/playlist?list={playlist_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="העלאת פלייליסט שירי נעמי שמר ליוטיוב")
    parser.add_argument("--cookies", help="נתיב לקובץ cookies.txt בפורמט Netscape/Mozilla")
    parser.add_argument("--oauth", action="store_true", help="שימוש ב-OAuth 2.0 רשמי (client_secret.json)")
    args = parser.parse_args()

    if args.cookies:
        upload_via_cookies(args.cookies)
    elif args.oauth:
        upload_via_oauth()
    else:
        print("בחר שיטת העלאה:")
        print("  1. המהירה ביותר (10 שניות לכל 449 השירים ללא צורך בהגדרות API):")
        print("     פתח את הקובץ naomi_shemer_playlist_player.html או create_playlist_in_browser.js")
        print("  2. באמצעות קובץ cookies.txt:")
        print("     python3 upload_youtube_playlist.py --cookies cookies.txt")
        print("  3. באמצעות Google OAuth (client_secret.json):")
        print("     python3 upload_youtube_playlist.py --oauth")


if __name__ == "__main__":
    main()
