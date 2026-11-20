"""Shared YouTube metadata archival and Internet Archive Wayback utilities."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from core.config import load_composer

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def enrich_alternative_videos(data: dict[str, Any]) -> int:
    """Deduplicate `alternative_videos` and populate same-song playlist fallbacks."""
    playlist = data.get("playlist", [])
    by_title: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for idx, item in enumerate(playlist):
        sel = item.get("selected_video") or {}
        vid = sel.get("video_id")
        if vid:
            by_title.setdefault(item.get("title", ""), []).append((idx, item))

    enriched_count = 0
    for item in playlist:
        sel = item.get("selected_video") or {}
        primary_vid = sel.get("video_id")
        if not primary_vid:
            continue

        alts = item.get("alternative_videos") or []
        seen_vids = {primary_vid}
        cleaned_alts: list[dict[str, Any]] = []

        for alt in alts:
            avid = alt.get("video_id")
            if avid and avid not in seen_vids:
                seen_vids.add(avid)
                cleaned_alts.append({
                    "video_id": avid,
                    "url": alt.get("url") or f"https://www.youtube.com/watch?v={avid}",
                    "video_title": alt.get("video_title", ""),
                    "channel": alt.get("channel", ""),
                    "duration": alt.get("duration", ""),
                    "views": alt.get("views", ""),
                    "source": alt.get("source", "direct_alternative"),
                })

        for _, sib in by_title.get(item.get("title", ""), []):
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


def _parse_player_response(vid: str, url: str, pr: dict[str, Any]) -> dict[str, Any]:
    playability = pr.get("playabilityStatus", {})
    status = playability.get("status", "UNKNOWN")
    vd = pr.get("videoDetails", {})
    micro = pr.get("microformat", {}).get("playerMicroformatRenderer", {})
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


def fetch_video_metadata(vid: str) -> dict[str, Any]:
    """Fetch structured YouTube metadata via InnerTube player, `/watch`, and oEmbed fallback."""
    url = f"https://www.youtube.com/watch?v={vid}"
    innertube_url = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
    payload = json.dumps({
        "videoId": vid,
        "context": {
            "client": {
                "hl": "he",
                "gl": "IL",
                "clientName": "WEB",
                "clientVersion": "2.20240726.00.00",
            }
        },
    }).encode("utf-8")
    req_api = urllib.request.Request(
        innertube_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": _BROWSER_UA},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req_api, timeout=12) as resp:
            pr = json.loads(resp.read().decode("utf-8", errors="replace"))
            parsed = _parse_player_response(vid, url, pr)
            if parsed.get("title"):
                return parsed
    except Exception:
        pass

    req_html = urllib.request.Request(
        url,
        headers={
            "User-Agent": _BROWSER_UA,
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(req_html, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        m = re.search(r"var ytInitialPlayerResponse\s*=\s*(\{.*?\});", html)
        if not m:
            m = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.*?\});", html)
        if m:
            pr = json.loads(m.group(1))
            parsed = _parse_player_response(vid, url, pr)
            if parsed.get("title"):
                return parsed
    except Exception:
        pass

    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    req_oe = urllib.request.Request(
        oembed_url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
    )
    try:
        with urllib.request.urlopen(req_oe, timeout=12) as resp:
            oe = json.loads(resp.read().decode("utf-8", errors="replace"))
            return {
                "video_id": vid,
                "url": url,
                "playability_status": "OK",
                "title": oe.get("title", ""),
                "author": oe.get("author_name", ""),
                "channel_id": "",
                "length_seconds": 0,
                "view_count": "",
                "publish_date": "",
                "category": "Music",
                "is_unlisted": False,
                "keywords": [],
                "short_description": "",
            }
    except Exception as exc:
        return {"video_id": vid, "status": "fetch_error", "error": str(exc)}


def backup_composer_metadata(slug: str) -> dict[str, Any]:
    """Enrich alternative videos and save full YouTube metadata backup JSON for a composer."""
    cfg = load_composer(slug)
    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    enriched = enrich_alternative_videos(data)
    if enriched:
        cfg.playlist_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    playlist = data.get("playlist", [])
    songs_with_alts = sum(1 for item in playlist if item.get("alternative_videos"))
    total_alts = sum(len(item.get("alternative_videos", [])) for item in playlist)
    print(
        f"[{cfg.slug}] Enriched {enriched} entries. "
        f"{songs_with_alts}/{len(playlist)} entries now have backup videos ({total_alts} total backup links)."
    )

    vids: list[str] = []
    seen: set[str] = set()
    for item in playlist:
        vid = (item.get("selected_video") or {}).get("video_id")
        if vid and vid not in seen:
            seen.add(vid)
            vids.append(vid)

    existing_archive: dict[str, dict[str, Any]] = {}
    if cfg.metadata_backup_json.exists():
        try:
            old = json.loads(cfg.metadata_backup_json.read_text(encoding="utf-8"))
            for k, v in old.get("videos", {}).items():
                ym = v.get("youtube_metadata") if isinstance(v, dict) and "youtube_metadata" in v else v
                if isinstance(ym, dict) and ym.get("playability_status") == "OK" and ym.get("title"):
                    existing_archive[k] = ym
        except Exception:
            pass

    to_fetch = [v for v in vids if v not in existing_archive]
    print(f"[{cfg.slug}] Fetching full metadata for {len(to_fetch)} videos ({len(existing_archive)} cached)...")

    results = dict(existing_archive)
    t0 = time.time()
    if to_fetch:
        with ThreadPoolExecutor(max_workers=6) as ex:
            fut_map = {ex.submit(fetch_video_metadata, vid): vid for vid in to_fetch}
            done_count = 0
            for fut in as_completed(fut_map):
                vid = fut_map[fut]
                results[vid] = fut.result()
                done_count += 1
                if done_count % 100 == 0 or done_count == len(to_fetch):
                    print(f"  [{done_count}/{len(to_fetch)}] fetched ({time.time() - t0:.1f}s)")

    ordered_videos: dict[str, dict[str, Any]] = {}
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
            "song_number": item.get("index", idx),
            "song_title": item.get("title", ""),
            "year": item.get("year", ""),
            "role": item.get("role_label_heb", ""),
            "lyricist": item.get("lyricist", ""),
            "composer": item.get("composer", ""),
            "matched_performer": sel.get("matched_performer") or item.get("matched_performer", ""),
            "catalog_performers": item.get("catalog_performers", []),
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
    cfg.metadata_backup_json.write_text(
        json.dumps(archive_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    size_kb = cfg.metadata_backup_json.stat().st_size / 1024
    print(f"[{cfg.slug}] Saved {cfg.metadata_backup_json.name} ({size_kb:.1f} KB, {ok_count}/{len(ordered_videos)} OK).")
    return {
        "slug": cfg.slug,
        "enriched": enriched,
        "total_unique_videos": len(ordered_videos),
        "healthy_videos_count": ok_count,
        "backup_path": str(cfg.metadata_backup_json),
    }


def check_wayback(url: str, user_agent: str = "PlaylistsArchiveBot/1.0") -> dict[str, Any]:
    """Query Internet Archive Availability API for an existing snapshot of `url`."""
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    req = urllib.request.Request(api, headers={"User-Agent": user_agent})
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
    except Exception as exc:
        return {"url": url, "archived": False, "error": str(exc)}


def save_to_wayback(url: str) -> dict[str, Any]:
    """Submit a URL to Internet Archive Save Page Now (`web.archive.org/save/`)."""
    save_url = f"https://web.archive.org/save/{url}"
    req = urllib.request.Request(save_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"url": url, "saved": resp.status in (200, 302), "status": resp.status}
    except Exception as exc:
        return {"url": url, "saved": False, "error": str(exc)}


def archive_composer_wayback(
    slug: str,
    check_all: bool = False,
    save: bool = False,
    limit: int = 50,
    save_limit: int = 15,
) -> dict[str, Any]:
    """Check and optionally archive YouTube watch URLs for a composer on Wayback Machine."""
    cfg = load_composer(slug)
    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    matched = [item for item in data.get("playlist", []) if item.get("selected_video")]

    targets: list[str] = []
    for item in matched:
        sel = item["selected_video"]
        ch = sel.get("channel", "")
        if not check_all and ch.endswith("- Topic"):
            continue
        targets.append(f"https://www.youtube.com/watch?v={sel['video_id']}")
        if len(targets) >= limit:
            break

    print(f"[{cfg.slug}] Checking Wayback Machine status for {len(targets)} URLs...")
    results: list[dict[str, Any]] = []
    if targets:
        with ThreadPoolExecutor(max_workers=8) as ex:
            fut_map = {ex.submit(check_wayback, u): u for u in targets}
            for fut in as_completed(fut_map):
                results.append(fut.result())

    archived = [r for r in results if r.get("archived")]
    missing = [r for r in results if not r.get("archived")]
    print(f"[{cfg.slug}] Wayback check: {len(archived)}/{len(results)} already archived, {len(missing)} not yet archived.")

    saved_results: list[dict[str, Any]] = []
    if save and missing:
        to_submit = missing[:save_limit]
        print(f"[{cfg.slug}] Submitting {len(to_submit)} URLs to web.archive.org/save/ (rate-limited)...")
        for r in to_submit:
            res = save_to_wayback(r["url"])
            saved_results.append(res)
            print(f"  {r['url']} -> {res}")
            time.sleep(4)

    return {
        "slug": cfg.slug,
        "checked": len(results),
        "archived": len(archived),
        "missing": len(missing),
        "saved": saved_results,
    }
