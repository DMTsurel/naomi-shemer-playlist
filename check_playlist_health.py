#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת תקינות, החלפה אוטומטית מגיבויים וניטור שוטף של סרטוני היוטיוב בפלייליסט שירי נעמי שמר:
1. בודק את כל 660 הסרטונים הראשיים מול /youtubei/v1/player (ולא רק oEmbed).
2. מזהה סרטונים שהפכו ללא-זמינים (UNAVAILABLE), דורשים התחברות (SIGN_IN_REQUIRED),
   או מוגבלים אזורית לישראל בלבד (GEO_RESTRICTED), ובודק אוטומטית סרטוני גיבוי תקינים.
3. עם הדגל --auto-fix: מחליף אוטומטית כל סרטון שהוסר בסרטון הגיבוי התקין הראשון שלו,
   מסיר את המזהה המת מקובצי ה-JSON ומריץ מחדש את build_player_and_browser_script.py.
4. משווה מול הפלייליסט החי ביוטיוב (PLFHErlX6i22g) עם ובלי params="wgYCCAA=" כדי לאתר סרטונים מוסתרים.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYLIST_ID = "PLFHErlX6i22g"


def _fetch_yt_config() -> tuple:
    req = urllib.request.Request(
        f"https://www.youtube.com/playlist?list={PLAYLIST_ID}",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
    api_key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html).group(1)
    cver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html).group(1)
    return api_key, cver


def _format_mmss(sec_val) -> str:
    try:
        s = int(sec_val)
        if s <= 0:
            return ""
        if s >= 3600:
            return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"
        return f"{s // 60}:{s % 60:02d}"
    except Exception:
        return ""


def _check_video_player(vid: str, api_key: str, cver: str) -> dict:
    body = {
        "videoId": vid,
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": cver,
                "hl": "he",
                "gl": "IL",
            }
        },
    }
    req = urllib.request.Request(
        f"https://www.youtube.com/youtubei/v1/player?key={api_key}&prettyPrint=false",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
        ps = resp.get("playabilityStatus") or {}
        mf = (resp.get("microformat") or {}).get("playerMicroformatRenderer") or {}
        reason = ps.get("reason") or ""
        status = ps.get("status") or "UNKNOWN"
        countries = mf.get("availableCountries")
        title = (mf.get("title") or {}).get("simpleText") or ""
        channel = mf.get("ownerChannelName") or ""
        duration = _format_mmss(mf.get("lengthSeconds"))

        if countries is None or len(countries) == 0:
            if status == "LOGIN_REQUIRED" or "sign in" in reason.lower() or "להיכנס" in reason:
                health = "SIGN_IN_REQUIRED"
            else:
                health = "UNAVAILABLE"
        elif "IL" not in countries:
            health = "BLOCKED_IN_IL"
        elif "US" not in countries or len(countries) <= 5:
            health = "GEO_RESTRICTED_IL_ONLY"
        else:
            health = "OK_WORLDWIDE"

        return {
            "video_id": vid,
            "health": health,
            "status": status,
            "reason": reason,
            "countries_count": len(countries) if countries else 0,
            "title": title,
            "channel": channel,
            "duration": duration,
        }
    except Exception as e:
        return {
            "video_id": vid,
            "health": "FETCH_ERROR",
            "status": "ERROR",
            "reason": str(e),
            "countries_count": 0,
            "title": "",
            "channel": "",
            "duration": "",
        }


def _fetch_live_playlist_ids(api_key: str, cver: str, show_unavailable: bool) -> list:
    ctx = {"client": {"clientName": "WEB", "clientVersion": cver, "hl": "en", "gl": "IL"}}

    def _post(body: dict) -> dict:
        b = dict(body)
        b["context"] = ctx
        req = urllib.request.Request(
            f"https://www.youtube.com/youtubei/v1/browse?key={api_key}&prettyPrint=false",
            data=json.dumps(b).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        return json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))

    items, tokens, seen_tokens = [], [], set()

    def _walk(node):
        if isinstance(node, list):
            for el in node:
                _walk(el)
            return
        if not isinstance(node, dict):
            return
        if "lockupViewModel" in node:
            lv = node["lockupViewModel"]
            vid = lv.get("contentId")
            if vid and lv.get("contentType", "") in ("LOCKUP_CONTENT_TYPE_VIDEO", ""):
                items.append(vid)
            return
        if "playlistVideoRenderer" in node:
            vid = node["playlistVideoRenderer"].get("videoId")
            if vid:
                items.append(vid)
            return
        if "continuationCommand" in node and isinstance(node["continuationCommand"], dict):
            tok = node["continuationCommand"].get("token")
            if tok and tok.startswith("4qmF") and tok not in seen_tokens:
                seen_tokens.add(tok)
                tokens.append(tok)
        for v in node.values():
            _walk(v)

    req_body = {"browseId": "VL" + PLAYLIST_ID}
    if show_unavailable:
        req_body["params"] = "wgYCCAA="
    _walk(_post(req_body))
    while tokens:
        _walk(_post({"continuation": tokens.pop(0)}))
    return items


def main():
    parser = argparse.ArgumentParser(description="Check YouTube health of Naomi Shemer playlist videos.")
    parser.add_argument("--json-report", help="Optional path to write JSON health report.")
    parser.add_argument("--skip-live-playlist", action="store_true", help="Skip live PLFHErlX6i22g comparison.")
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically replace unavailable videos with their best healthy backup and rebuild exports.",
    )
    args = parser.parse_args()

    playlist_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.json")
    catalog_path = os.path.join(BASE_DIR, "naomi_shemer_catalog.json")
    with open(playlist_path, encoding="utf-8") as f:
        data = json.load(f)

    matched = [x for x in data["playlist"] if x.get("selected_video")]
    api_key, cver = _fetch_yt_config()

    print(f"🔎 בודק תקינות של {len(matched)} סרטוני הפלייליסט מול YouTube (client {cver})...")
    results_by_vid = {}
    with ThreadPoolExecutor(max_workers=20) as ex:
        fut_map = {
            ex.submit(_check_video_player, it["selected_video"]["video_id"], api_key, cver): it
            for it in matched
        }
        for fut in as_completed(fut_map):
            res = fut.result()
            results_by_vid[res["video_id"]] = res

    unavailable = []
    signin_gated = []
    geo_restricted = []
    auto_fixed = []
    dead_vids_to_purge = set()

    for it in matched:
        sel = it["selected_video"]
        vid = sel["video_id"]
        r = results_by_vid[vid]
        entry_summary = {
            "index": it["index"],
            "title": it["title"],
            "performer": sel.get("matched_performer", ""),
            "video_id": vid,
            "health": r["health"],
            "reason": r["reason"],
            "recommended_backups": [],
        }
        if r["health"] in ("UNAVAILABLE", "BLOCKED_IN_IL"):
            for alt in it.get("alternative_videos", [])[:6]:
                chk = _check_video_player(alt["video_id"], api_key, cver)
                if chk["health"] in ("OK_WORLDWIDE", "GEO_RESTRICTED_IL_ONLY"):
                    entry_summary["recommended_backups"].append({
                        "video_id": alt["video_id"],
                        "title": chk["title"] or alt.get("video_title", ""),
                        "channel": chk["channel"] or alt.get("channel", ""),
                        "duration": chk["duration"] or alt.get("duration", ""),
                        "health": chk["health"],
                    })
            if args.auto_fix and entry_summary["recommended_backups"]:
                # Prefer OK_WORLDWIDE if available
                worldwide_b = [b for b in entry_summary["recommended_backups"] if b["health"] == "OK_WORLDWIDE"]
                chosen = worldwide_b[0] if worldwide_b else entry_summary["recommended_backups"][0]
                dead_vids_to_purge.add(vid)
                sel["video_id"] = chosen["video_id"]
                sel["url"] = f"https://www.youtube.com/watch?v={chosen['video_id']}"
                sel["video_title"] = chosen["title"]
                sel["channel"] = chosen["channel"]
                if chosen.get("duration"):
                    sel["duration"] = chosen["duration"]
                it["alternative_videos"] = [
                    a for a in it.get("alternative_videos", [])
                    if a.get("video_id") and a.get("video_id") != chosen["video_id"] and a.get("video_id") != vid
                ]
                auto_fixed.append({
                    "index": it["index"],
                    "title": it["title"],
                    "performer": sel.get("matched_performer", ""),
                    "old_video_id": vid,
                    "new_video_id": chosen["video_id"],
                    "new_title": chosen["title"],
                    "new_channel": chosen["channel"],
                })
            else:
                unavailable.append(entry_summary)
        elif r["health"] == "SIGN_IN_REQUIRED":
            signin_gated.append(entry_summary)
        elif r["health"] == "GEO_RESTRICTED_IL_ONLY":
            geo_restricted.append(entry_summary)

    if auto_fixed:
        for it in data["playlist"]:
            if "alternative_videos" in it:
                it["alternative_videos"] = [
                    a for a in it["alternative_videos"]
                    if a.get("video_id") not in dead_vids_to_purge
                ]
        with open(playlist_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if os.path.exists(catalog_path):
            with open(catalog_path, encoding="utf-8") as f:
                cat_data = json.load(f)
            rep_map = {fx["old_video_id"]: fx["new_video_id"] for fx in auto_fixed}
            for s in cat_data.get("songs", []):
                if "youtube_ids" in s:
                    updated_ids = [rep_map.get(v, v) for v in s["youtube_ids"] if v not in dead_vids_to_purge or v in rep_map]
                    seen = set()
                    s["youtube_ids"] = [v for v in updated_ids if not (v in seen or seen.add(v))]
            with open(catalog_path, "w", encoding="utf-8") as f:
                json.dump(cat_data, f, ensure_ascii=False, indent=2)

        build_script = os.path.join(BASE_DIR, "build_player_and_browser_script.py")
        subprocess.run([sys.executable, build_script], check=True)
        print(f"🛠️ הוחלפו אוטומטית {len(auto_fixed)} סרטונים לא-זמינים ועודכנו כל קובצי הפרויקט!")
        for fx in auto_fixed:
            print(f"  ✔ #{fx['index']} {fx['title']} ({fx['performer']}): {fx['old_video_id']} -> {fx['new_video_id']} ({fx['new_title']})")

    live_summary = {}
    if not args.skip_live_playlist:
        vis_ids = _fetch_live_playlist_ids(api_key, cver, show_unavailable=False)
        all_ids = _fetch_live_playlist_ids(api_key, cver, show_unavailable=True)
        vis_set = set(vis_ids)
        hidden_in_live = [
            {"position": pos, "video_id": v}
            for pos, v in enumerate(all_ids, 1)
            if v not in vis_set
        ]
        live_summary = {
            "playlist_id": PLAYLIST_ID,
            "visible_count": len(vis_ids),
            "total_with_hidden_count": len(all_ids),
            "hidden_items": hidden_in_live,
            "matches_local_json_100pct": all_ids == [x["selected_video"]["video_id"] for x in matched],
        }

    ok_worldwide = len(matched) - len(unavailable) - len(signin_gated) - len(geo_restricted)
    print(f"  🟢 תקינים בכל העולם: {ok_worldwide}")
    print(f"  🇮🇱 זמינים בישראל בלבד (כאן | מוזיקה / ארכיון): {len(geo_restricted)}")
    print(f"  🔐 דורשים התחברות ליוטיוב: {len(signin_gated)}")
    print(f"  🔴 לא זמינים שנותרו ללא גיבוי אוטומטי: {len(unavailable)}")

    if live_summary:
        print(
            f"  📺 פלייליסט חי ביוטיוב ({PLAYLIST_ID}): "
            f"{live_summary['visible_count']} גלויים מתוך {live_summary['total_with_hidden_count']} סה\"כ "
            f"(מוסתרים כרגע: {len(live_summary['hidden_items'])})"
        )

    report = {
        "total_checked": len(matched),
        "ok_worldwide_count": ok_worldwide,
        "geo_restricted_il_only_count": len(geo_restricted),
        "sign_in_required_count": len(signin_gated),
        "auto_fixed_count": len(auto_fixed),
        "auto_fixed": auto_fixed,
        "unavailable_unfixed_count": len(unavailable),
        "unavailable": unavailable,
        "sign_in_required": signin_gated,
        "geo_restricted_il_only": geo_restricted,
        "live_youtube_playlist": live_summary,
    }
    if args.json_report:
        with open(args.json_report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    sys.exit(1 if unavailable else 0)


if __name__ == "__main__":
    main()
