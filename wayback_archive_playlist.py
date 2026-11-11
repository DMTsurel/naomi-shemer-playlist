#!/usr/bin/env python3
"""
Layer 5 – Wayback Machine / Internet Archive URL Checker & Archiver (`wayback_archive_playlist.py`)
- Reads `naomi_shemer_youtube_playlist.json` and focuses on rare/archival non-Topic channels
  (or all URLs when `--all` is passed).
- Checks the Internet Archive Availability API (`https://archive.org/wayback/available?url=...`).
- If `--save` is passed, submits unarchived URLs to `https://web.archive.org/save/<url>`
  with polite rate-limiting.
"""

import argparse
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

BASE_DIR = Path("/Users/dmtsurel/.gemini/antigravity/scratch/naomi-shemer-playlist")
if not BASE_DIR.exists():
    BASE_DIR = Path(__file__).resolve().parent

JSON_PATH = BASE_DIR / "naomi_shemer_youtube_playlist.json"


def check_wayback(url: str) -> dict:
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    req = urllib.request.Request(api, headers={"User-Agent": "NaomiShemerArchiveBot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            closest = data.get("archived_snapshots", {}).get("closest", {})
            return {
                "url": url,
                "archived": bool(closest.get("available")),
                "snapshot_url": closest.get("url", ""),
                "timestamp": closest.get("timestamp", ""),
            }
    except Exception as e:
        return {"url": url, "archived": False, "error": str(e)}


def save_to_wayback(url: str) -> dict:
    save_url = f"https://web.archive.org/save/{url}"
    req = urllib.request.Request(save_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"url": url, "saved": resp.status in (200, 302), "status": resp.status}
    except Exception as e:
        return {"url": url, "saved": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Check all 670 videos (default: non-Topic rare channels)")
    parser.add_argument("--save", action="store_true", help="Submit unarchived URLs to web.archive.org/save/")
    parser.add_argument("--limit", type=int, default=50, help="Max URLs to check/save in one run")
    args = parser.parse_args()

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    matched = [item for item in data.get("playlist", []) if item.get("selected_video")]

    targets = []
    for item in matched:
        sel = item["selected_video"]
        ch = sel.get("channel", "")
        if not args.all and ch.endswith("- Topic"):
            continue
        targets.append(f"https://www.youtube.com/watch?v={sel['video_id']}")
        if len(targets) >= args.limit:
            break

    print(f"Checking Wayback Machine status for {len(targets)} URLs...")
    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        fut_map = {ex.submit(check_wayback, u): u for u in targets}
        for fut in as_completed(fut_map):
            results.append(fut.result())

    archived = [r for r in results if r.get("archived")]
    missing = [r for r in results if not r.get("archived")]
    print(f"Wayback check: {len(archived)}/{len(results)} already archived, {len(missing)} not yet archived.")

    if args.save and missing:
        print(f"Submitting {min(len(missing), 15)} URLs to web.archive.org/save/ (rate-limited)...")
        for r in missing[:15]:
            res = save_to_wayback(r["url"])
            print(f"  {r['url']} -> {res}")
            time.sleep(4)


if __name__ == "__main__":
    main()
