#!/usr/bin/env python3
"""
Layer 4 & Layer 1 Data Preparation:
1. Enriches `alternative_videos` in `naomi_shemer_youtube_playlist.json` so that:
   - Existing `alternative_videos` are cleaned and deduplicated.
   - Other recordings of the same song in the playlist are added as fallback alternatives
     (if not already present), giving every multi-version song automatic failover backups.
2. Fetches full YouTube metadata (`title`, `author`, `channelId`, `lengthSeconds`,
   `shortDescription`, `keywords`, `publishDate`, `viewCount`, `isUnlisted`) for all
   670 primary playlist videos and saves a complete text/JSON archive to
   `youtube_full_metadata_backup.json` (zero audio/video disk footprint).
"""

import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path("/Users/dmtsurel/.gemini/antigravity/scratch/naomi-shemer-playlist")
JSON_PATH = BASE_DIR / "naomi_shemer_youtube_playlist.json"
METADATA_BACKUP_PATH = BASE_DIR / "youtube_full_metadata_backup.json"


def enrich_alternative_videos(data: dict) -> int:
    playlist = data.get("playlist", [])
    by_title = {}
    for idx, item in enumerate(playlist):
        sel = item.get("selected_video") or {}
        vid = sel.get("video_id")
        if not vid:
            continue
        by_title.setdefault(item.get("title", ""), []).append((idx, item))

    enriched_count = 0
    for item in playlist:
        sel = item.get("selected_video") or {}
        primary_vid = sel.get("video_id")
        if not primary_vid:
            continue

        alts = item.get("alternative_videos") or []
        seen_vids = {primary_vid}
        cleaned_alts = []

        for a in alts:
            avid = a.get("video_id")
            if avid and avid not in seen_vids:
                seen_vids.add(avid)
                cleaned_alts.append({
                    "video_id": avid,
                    "url": a.get("url") or f"https://www.youtube.com/watch?v={avid}",
                    "video_title": a.get("video_title", ""),
                    "channel": a.get("channel", ""),
                    "duration": a.get("duration", ""),
                    "views": a.get("views", ""),
                    "source": a.get("source", "direct_alternative"),
                })

        # Add sibling performances of the same song as secondary fallback alternatives
        siblings = by_title.get(item.get("title", ""), [])
        for _, sib in siblings:
            sib_sel = sib.get("selected_video") or {}
            sib_vid = sib_sel.get("video_id")
            if sib_vid and sib_vid not in seen_vids:
                seen_vids.add(sib_vid)
                cleaned_alts.append({
                    "video_id": sib_vid,
                    "url": f"https://www.youtube.com/watch?v={sib_vid}",
                    "video_title": sib_sel.get("video_title", ""),
                    "channel": sib_sel.get("channel", ""),
                    "duration": sib_sel.get("duration", ""),
                    "views": sib_sel.get("views", ""),
                    "source": "same_song_performance",
                })

        if cleaned_alts != alts:
            enriched_count += 1
        item["alternative_videos"] = cleaned_alts

    return enriched_count


def fetch_video_metadata(vid: str) -> dict:
    url = f"https://www.youtube.com/watch?v={vid}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return {"video_id": vid, "status": "fetch_error", "error": str(e)}

    m = re.search(r"var ytInitialPlayerResponse\s*=\s*(\{.*?\});", html)
    if not m:
        m = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.*?\});", html)
    if not m:
        return {"video_id": vid, "status": "parse_error"}

    try:
        pr = json.loads(m.group(1))
    except Exception as e:
        return {"video_id": vid, "status": "json_error", "error": str(e)}

    playability = pr.get("playabilityStatus", {})
    status = playability.get("status", "UNKNOWN")
    vd = pr.get("videoDetails", {})
    micro = (
        pr.get("microformat", {})
        .get("playerMicroformatRenderer", {})
    )

    return {
        "video_id": vid,
        "url": url,
        "playability_status": status,
        "title": vd.get("title", ""),
        "author": vd.get("author", ""),
        "channel_id": vd.get("channelId", ""),
        "length_seconds": int(vd.get("lengthSeconds", 0) or 0),
        "view_count": vd.get("viewCount", ""),
        "publish_date": micro.get("publishDate", "") or micro.get("uploadDate", ""),
        "category": micro.get("category", ""),
        "is_unlisted": bool(micro.get("isUnlisted", False)),
        "keywords": vd.get("keywords", []),
        "short_description": vd.get("shortDescription", ""),
    }


def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    enriched = enrich_alternative_videos(data)
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    playlist = data.get("playlist", [])
    songs_with_alts = sum(1 for item in playlist if item.get("alternative_videos"))
    total_alts = sum(len(item.get("alternative_videos", [])) for item in playlist)
    print(f"Enriched {enriched} entries. {songs_with_alts}/{len(playlist)} entries now have backup videos ({total_alts} total backup links).")

    # Collect all unique primary video IDs
    vids = []
    seen = set()
    for item in playlist:
        vid = (item.get("selected_video") or {}).get("video_id")
        if vid and vid not in seen:
            seen.add(vid)
            vids.append(vid)

    # Load existing backup if present to avoid re-fetching already archived videos
    existing_archive = {}
    if METADATA_BACKUP_PATH.exists():
        try:
            old = json.loads(METADATA_BACKUP_PATH.read_text(encoding="utf-8"))
            for k, v in old.get("videos", {}).items():
                if v.get("playability_status") == "OK" and v.get("title"):
                    existing_archive[k] = v
        except Exception:
            pass

    to_fetch = [v for v in vids if v not in existing_archive]
    print(f"Fetching full metadata for {len(to_fetch)} videos ({len(existing_archive)} cached)...")

    results = dict(existing_archive)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=20) as ex:
        fut_map = {ex.submit(fetch_video_metadata, vid): vid for vid in to_fetch}
        done_count = 0
        for fut in as_completed(fut_map):
            vid = fut_map[fut]
            res = fut.result()
            results[vid] = res
            done_count += 1
            if done_count % 100 == 0 or done_count == len(to_fetch):
                print(f"  [{done_count}/{len(to_fetch)}] fetched ({time.time() - t0:.1f}s)")

    # Build comprehensive metadata backup indexed by video_id and linked to song catalog metadata
    ordered_videos = {}
    ok_count = 0
    for idx, item in enumerate(playlist, 1):
        sel = item.get("selected_video") or {}
        vid = sel.get("video_id")
        if not vid:
            continue
        meta = results.get(vid, {})
        if meta.get("playability_status") == "OK":
            ok_count += 1
        ordered_videos[vid] = {
            "playlist_position": idx,
            "song_number": item.get("number"),
            "song_title": item.get("title", ""),
            "year": item.get("year", ""),
            "role": item.get("role", ""),
            "lyricist": item.get("lyricist", ""),
            "composer": item.get("composer", ""),
            "matched_performer": item.get("matched_performer", ""),
            "catalog_performers": item.get("performers", []),
            "alternative_video_ids": [
                a.get("video_id") for a in item.get("alternative_videos", []) if a.get("video_id")
            ],
            "youtube_metadata": meta,
        }

    archive_payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_playlist_entries": len(playlist),
        "total_unique_videos": len(ordered_videos),
        "healthy_videos_count": ok_count,
        "songs_with_backup_alternatives": songs_with_alts,
        "total_backup_links": total_alts,
        "videos": ordered_videos,
    }
    METADATA_BACKUP_PATH.write_text(
        json.dumps(archive_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    size_kb = METADATA_BACKUP_PATH.stat().st_size / 1024
    print(f"Saved {METADATA_BACKUP_PATH.name} ({size_kb:.1f} KB, {ok_count}/{len(ordered_videos)} OK).")


if __name__ == "__main__":
    main()
