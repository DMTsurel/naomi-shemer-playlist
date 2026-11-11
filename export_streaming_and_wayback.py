#!/usr/bin/env python3
"""
Layers 5 & 6 – Lightweight Non-Audio/Video Backups:
1. `naomi_shemer_streaming_import.csv`:
   Standard CSV (`title,artist,album,year,role,youtube_url,youtube_id,isrc_hint`)
   ready for one-click import into Spotify, Apple Music, YouTube Music, Tidal, or Deezer
   via Soundiiz / TuneMyMusic.
2. `naomi_shemer_youtube_stream.m3u8`:
   Standard Extended M3U8 playlist (`#EXTM3U` + `#EXTINF`) with YouTube URLs and
   song/performer titles, playable directly by VLC, IINA (macOS), or mpv without
   downloading a single byte of MP3/MP4 to disk.
3. `wayback_backup_urls.txt`:
   Complete list of all 670 YouTube URLs + direct National Library of Israel (NLI),
   Shironet, and Zemereshet archive URLs, formatted for batch submission to the
   Internet Archive Wayback Machine (`web.archive.org`) or ArchiveBox.
4. `wayback_archive_playlist.py`:
   Helper script to check Wayback Machine availability via the CDX / Availability API
   (`https://archive.org/wayback/available?url=...`) and optionally submit unarchived
   rare channel URLs to `https://web.archive.org/save/...`.
"""

import csv
import json
import re
from pathlib import Path

BASE_DIR = Path("/Users/dmtsurel/.gemini/antigravity/scratch/naomi-shemer-playlist")
if not BASE_DIR.exists():
    BASE_DIR = Path(__file__).resolve().parent

JSON_PATH = BASE_DIR / "naomi_shemer_youtube_playlist.json"
STREAMING_CSV_PATH = BASE_DIR / "naomi_shemer_streaming_import.csv"
M3U8_PATH = BASE_DIR / "naomi_shemer_youtube_stream.m3u8"
WAYBACK_URLS_PATH = BASE_DIR / "wayback_backup_urls.txt"


def parse_duration_seconds(dur_str: str) -> int:
    if not dur_str:
        return -1
    parts = [p for p in str(dur_str).strip().split(":") if p.isdigit()]
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return -1


def clean_artist(item: dict, sel: dict) -> str:
    perf = sel.get("matched_performer") or item.get("matched_performer") or ""
    if not perf:
        cat_perfs = item.get("catalog_performers") or item.get("performers") or []
        if cat_perfs:
            perf = cat_perfs[0]
    if not perf:
        ch = sel.get("channel", "")
        perf = re.sub(r"\s*-\s*Topic$", "", ch).strip()
    if not perf or perf.lower() in ("various artists", "release"):
        perf = "נעמי שמר"
    return perf


def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    playlist = data.get("playlist", [])
    matched = [item for item in playlist if item.get("selected_video")]

    # 1. Generate naomi_shemer_streaming_import.csv
    with open(STREAMING_CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "playlist_order",
                "title",
                "artist",
                "album",
                "year",
                "composer_lyricist_role",
                "duration",
                "youtube_url",
                "youtube_id",
                "backup_youtube_urls",
            ],
        )
        writer.writeheader()
        for idx, item in enumerate(matched, 1):
            sel = item["selected_video"]
            vid = sel["video_id"]
            yr = item.get("year", "")
            yr_clean = yr if (yr and str(yr) != "2099") else ""
            alb = item.get("album_group") or sel.get("matched_album") or ""
            artist = clean_artist(item, sel)
            alts = [
                f"https://www.youtube.com/watch?v={a['video_id']}"
                for a in item.get("alternative_videos", [])[:5]
                if a.get("video_id") and a.get("video_id") != vid
            ]
            writer.writerow({
                "playlist_order": idx,
                "title": item.get("title", ""),
                "artist": artist,
                "album": alb,
                "year": yr_clean,
                "composer_lyricist_role": item.get("role_label_heb", "מילים ולחן: נעמי שמר"),
                "duration": sel.get("duration", ""),
                "youtube_url": f"https://www.youtube.com/watch?v={vid}",
                "youtube_id": vid,
                "backup_youtube_urls": " | ".join(alts),
            })

    # 2. Generate naomi_shemer_youtube_stream.m3u8
    m3u_lines = [
        "#EXTM3U",
        "#PLAYLIST:שירי נעמי שמר – האוסף המקיף (670 ביצועים ביוטיוב)",
    ]
    for idx, item in enumerate(matched, 1):
        sel = item["selected_video"]
        vid = sel["video_id"]
        sec = parse_duration_seconds(sel.get("duration", ""))
        artist = clean_artist(item, sel)
        title = item.get("title", "")
        yr = item.get("year", "")
        yr_str = f" ({yr})" if (yr and str(yr) != "2099") else ""
        m3u_lines.append(f"#EXTINF:{sec},{artist} - {title}{yr_str}")
        m3u_lines.append(f"https://www.youtube.com/watch?v={vid}")
    M3U8_PATH.write_text("\n".join(m3u_lines) + "\n", encoding="utf-8")

    # 3. Generate wayback_backup_urls.txt (all primary YouTube URLs + rare backup URLs + NLI/Shironet direct URLs)
    urls = ["https://www.youtube.com/playlist?list=PLFHErlX6i22g"]
    seen = set(urls)
    for item in playlist:
        sel = item.get("selected_video") or {}
        vid = sel.get("video_id")
        if vid:
            u = f"https://www.youtube.com/watch?v={vid}"
            if u not in seen:
                seen.add(u)
                urls.append(u)
        for lk in item.get("archive_links", []):
            lu = lk.get("url", "")
            if lu and ("nli.org.il/he/items/" in lu or "shironet.mako.co.il/artist?type=lyrics" in lu):
                if lu not in seen:
                    seen.add(lu)
                    urls.append(lu)

    WAYBACK_URLS_PATH.write_text("\n".join(urls) + "\n", encoding="utf-8")
    print(
        f"Generated:\n"
        f"  1. {STREAMING_CSV_PATH.name} ({len(matched)} tracks)\n"
        f"  2. {M3U8_PATH.name} ({len(matched)} stream entries)\n"
        f"  3. {WAYBACK_URLS_PATH.name} ({len(urls)} archival URLs)"
    )


if __name__ == "__main__":
    main()
