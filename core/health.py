"""Shared YouTube playability monitor (InnerTube) and oEmbed auto-healer."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from core.backup import backup_composer_metadata
from core.build_site import build_composer
from core.config import load_composer, load_overrides

_DESKTOP_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
_CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _fetch_yt_config(playlist_id: str | None = None, sample_video_id: str | None = None) -> tuple[str, str]:
    """Fetch InnerTube API key and client version from a public YouTube page."""
    if playlist_id:
        target_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    elif sample_video_id:
        target_url = f"https://www.youtube.com/watch?v={sample_video_id}"
    else:
        target_url = "https://www.youtube.com/"
    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": _DESKTOP_UA, "Accept-Language": "en-US,en;q=0.9"},
    )
    html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
    api_key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html).group(1)
    cver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html).group(1)
    return api_key, cver


def _format_mmss(sec_val: Any) -> str:
    try:
        secs = int(sec_val)
        if secs <= 0:
            return ""
        if secs >= 3600:
            return f"{secs // 3600}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"
        return f"{secs // 60}:{secs % 60:02d}"
    except Exception:
        return ""


def _check_video_player(vid: str, api_key: str, cver: str) -> dict[str, Any]:
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

        if not countries:
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
    except Exception as exc:
        return {
            "video_id": vid,
            "health": "FETCH_ERROR",
            "status": "ERROR",
            "reason": str(exc),
            "countries_count": 0,
            "title": "",
            "channel": "",
            "duration": "",
        }


def _fetch_live_playlist_ids(
    playlist_id: str,
    api_key: str,
    cver: str,
    show_unavailable: bool,
) -> list[str]:
    ctx = {"client": {"clientName": "WEB", "clientVersion": cver, "hl": "en", "gl": "IL"}}

    def _post(body: dict[str, Any]) -> dict[str, Any]:
        req_b = dict(body)
        req_b["context"] = ctx
        req = urllib.request.Request(
            f"https://www.youtube.com/youtubei/v1/browse?key={api_key}&prettyPrint=false",
            data=json.dumps(req_b).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        return json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))

    items: list[str] = []
    tokens: list[str] = []
    seen_tokens: set[str] = set()

    def _walk(node: Any) -> None:
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

    req_body: dict[str, Any] = {"browseId": "VL" + playlist_id}
    if show_unavailable:
        req_body["params"] = "wgYCCAA="
    _walk(_post(req_body))
    while tokens:
        _walk(_post({"continuation": tokens.pop(0)}))
    return items


def check_composer_health(
    slug: str,
    json_report: Path | None = None,
    skip_live_playlist: bool = False,
    auto_fix: bool = False,
    standalone: bool = False,
) -> tuple[dict[str, Any], int]:
    """Run InnerTube player & live-playlist checks for a composer and return `(report, exit_code)`."""
    cfg = load_composer(slug)
    ov = load_overrides(slug)
    bad_ids = set((ov.get("bad_video_ids") or {}).keys())

    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    matched = [x for x in data["playlist"] if x.get("selected_video")]
    sample_vid = matched[0]["selected_video"]["video_id"] if matched else None
    api_key, cver = _fetch_yt_config(cfg.youtube_playlist_id or None, sample_vid)

    print(f"🔎 [{cfg.slug}] בודק תקינות של {len(matched)} סרטוני הפלייליסט מול YouTube (client {cver})...")
    results_by_vid: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=20) as ex:
        fut_map = {
            ex.submit(_check_video_player, it["selected_video"]["video_id"], api_key, cver): it
            for it in matched
        }
        for fut in as_completed(fut_map):
            res = fut.result()
            results_by_vid[res["video_id"]] = res

    unavailable: list[dict[str, Any]] = []
    signin_gated: list[dict[str, Any]] = []
    geo_restricted: list[dict[str, Any]] = []
    auto_fixed: list[dict[str, Any]] = []
    dead_vids_to_purge: set[str] = set()

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
                avid = alt.get("video_id", "")
                if not avid or avid in bad_ids:
                    continue
                chk = _check_video_player(avid, api_key, cver)
                if chk["health"] in ("OK_WORLDWIDE", "GEO_RESTRICTED_IL_ONLY"):
                    entry_summary["recommended_backups"].append({
                        "video_id": avid,
                        "title": chk["title"] or alt.get("video_title", ""),
                        "channel": chk["channel"] or alt.get("channel", ""),
                        "duration": chk["duration"] or alt.get("duration", ""),
                        "health": chk["health"],
                    })
            if auto_fix and entry_summary["recommended_backups"]:
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
                    a
                    for a in it.get("alternative_videos", [])
                    if a.get("video_id") and a.get("video_id") not in (chosen["video_id"], vid)
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
                    a for a in it["alternative_videos"] if a.get("video_id") not in dead_vids_to_purge
                ]
        cfg.playlist_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        if cfg.catalog_json.exists():
            cat_data = json.loads(cfg.catalog_json.read_text(encoding="utf-8"))
            rep_map = {fx["old_video_id"]: fx["new_video_id"] for fx in auto_fixed}
            for s in cat_data.get("songs", []):
                if "youtube_ids" in s:
                    updated_ids = [
                        rep_map.get(v, v)
                        for v in s["youtube_ids"]
                        if v not in dead_vids_to_purge or v in rep_map
                    ]
                    s["youtube_ids"] = list(dict.fromkeys(updated_ids))
            cfg.catalog_json.write_text(json.dumps(cat_data, ensure_ascii=False, indent=2), encoding="utf-8")

        build_composer(slug, standalone=standalone, rebuild_hub=True)
        print(f"🛠️ הוחלפו אוטומטית {len(auto_fixed)} סרטונים לא-זמינים ועודכנו כל קובצי הפרויקט!")
        for fx in auto_fixed:
            print(f"  ✔ #{fx['index']} {fx['title']} ({fx['performer']}): {fx['old_video_id']} -> {fx['new_video_id']} ({fx['new_title']})")

    live_summary: dict[str, Any] = {}
    if not skip_live_playlist and cfg.youtube_playlist_id:
        vis_ids = _fetch_live_playlist_ids(cfg.youtube_playlist_id, api_key, cver, show_unavailable=False)
        all_ids = _fetch_live_playlist_ids(cfg.youtube_playlist_id, api_key, cver, show_unavailable=True)
        vis_set = set(vis_ids)
        hidden_in_live = [
            {"position": pos, "video_id": v}
            for pos, v in enumerate(all_ids, 1)
            if v not in vis_set
        ]
        live_summary = {
            "playlist_id": cfg.youtube_playlist_id,
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
            f"  📺 פלייליסט חי ביוטיוב ({cfg.youtube_playlist_id}): "
            f"{live_summary['visible_count']} גלויים מתוך {live_summary['total_with_hidden_count']} סה\"כ "
            f"(מוסתרים כרגע: {len(live_summary['hidden_items'])})"
        )

    report = {
        "slug": cfg.slug,
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
    if json_report:
        json_report.parent.mkdir(parents=True, exist_ok=True)
        json_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return report, (1 if unavailable else 0)


def check_oembed_health(vid: str) -> dict[str, Any]:
    """Check whether a YouTube video is public and embeddable via YouTube oEmbed."""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    req = urllib.request.Request(
        oembed_url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            d = json.loads(resp.read().decode("utf-8", errors="replace"))
            return {
                "video_id": vid,
                "status": "OK",
                "reason": "",
                "title": d.get("title", ""),
                "channel": d.get("author_name", ""),
                "duration": "",
                "views": "",
            }
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 401, 403, 404):
            reason_map = {
                400: "Invalid video ID (400)",
                401: "Private or embedding disabled (401)",
                403: "Forbidden / Private video (403)",
                404: "Video deleted or not found (404)",
            }
            return {
                "video_id": vid,
                "status": f"HTTP_{exc.code}",
                "reason": reason_map.get(exc.code, str(exc)),
            }
        return {"video_id": vid, "status": "TRANSIENT_ERROR", "reason": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"video_id": vid, "status": "TRANSIENT_ERROR", "reason": str(exc)}


check_video_health = check_oembed_health


def search_youtube_candidates(query: str, max_results: int = 8) -> list[str]:
    """Search YouTube HTML results and extract unique 11-character video IDs."""
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _CHROME_UA,
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return []

    vids: list[str] = []
    for m in re.finditer(r'"videoId":"([a-zA-Z0-9_-]{11})"', html):
        v = m.group(1)
        if v not in vids:
            vids.append(v)
            if len(vids) >= max_results:
                break
    return vids


def _candidate_matches_song_title(song_title: str, cand_title: str) -> bool:
    return song_title in cand_title or any(w in cand_title for w in song_title.split() if len(w) >= 3)


def heal_composer_playlist(
    slug: str,
    dry_run: bool = False,
    standalone: bool = False,
    run_backup: bool = True,
) -> dict[str, Any]:
    """Check playlist + backup links via oEmbed, heal broken items, and rebuild composer artifacts."""
    cfg = load_composer(slug)
    ov = load_overrides(slug)
    bad_ids = set((ov.get("bad_video_ids") or {}).keys())

    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    playlist = data.get("playlist", [])
    matched_items = [item for item in playlist if item.get("selected_video")]

    used_vids = {
        item["selected_video"]["video_id"]
        for item in matched_items
        if item.get("selected_video", {}).get("video_id")
    }

    print(f"[{cfg.slug}] Checking health of {len(matched_items)} primary playlist videos via oEmbed...")
    health_map: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=20) as ex:
        fut_map = {
            ex.submit(check_oembed_health, item["selected_video"]["video_id"]): item
            for item in matched_items
        }
        for fut in as_completed(fut_map):
            res = fut.result()
            health_map[res["video_id"]] = res

    alt_vids = {
        a.get("video_id")
        for item in matched_items
        for a in item.get("alternative_videos", [])
        if a.get("video_id") and a.get("video_id") not in health_map
    }
    if alt_vids:
        print(f"[{cfg.slug}] Checking health of {len(alt_vids)} unique alternative backup videos via oEmbed...")
        with ThreadPoolExecutor(max_workers=20) as ex:
            fut_map = {ex.submit(check_oembed_health, avid): avid for avid in alt_vids}
            for fut in as_completed(fut_map):
                res = fut.result()
                health_map[res["video_id"]] = res

    pruned_alts_count = 0
    for item in matched_items:
        orig_alts = item.get("alternative_videos", [])
        if not orig_alts:
            continue
        healthy_alts = [
            a
            for a in orig_alts
            if health_map.get(a.get("video_id"), {}).get("status") in ("OK", "TRANSIENT_ERROR")
            and a.get("video_id") not in bad_ids
        ]
        if len(healthy_alts) != len(orig_alts):
            pruned_alts_count += len(orig_alts) - len(healthy_alts)
            if not dry_run:
                item["alternative_videos"] = healthy_alts

    broken_items = [
        (item, health_map.get(item["selected_video"]["video_id"], {}))
        for item in matched_items
        if health_map.get(item["selected_video"]["video_id"], {}).get("status") not in ("OK", "TRANSIENT_ERROR")
    ]

    print(
        f"[{cfg.slug}] Health check complete: {len(matched_items) - len(broken_items)}/{len(matched_items)} primary OK, "
        f"{len(broken_items)} broken/unavailable, {pruned_alts_count} dead backup links pruned."
    )

    healed_records: list[dict[str, Any]] = []
    unhealed_records: list[dict[str, Any]] = []
    forbidden = used_vids | bad_ids

    for item, broken_info in broken_items:
        old_sel = item["selected_video"]
        old_vid = old_sel["video_id"]
        old_vtitle = old_sel.get("video_title", "")
        song_title = item.get("title", "")

        candidate_vids: list[str] = []
        alt_meta_map: dict[str, dict[str, Any]] = {}
        for a in item.get("alternative_videos", []):
            avid = a.get("video_id")
            if avid and avid not in forbidden and avid not in candidate_vids:
                candidate_vids.append(avid)
                alt_meta_map[avid] = a

        perf_hint = old_sel.get("matched_performer") or item.get("matched_performer") or ""
        search_queries = [q for q in (old_vtitle, f"{song_title} {perf_hint} {cfg.name_he}".strip()) if q]
        for q in search_queries:
            for svid in search_youtube_candidates(q, max_results=6):
                if svid not in forbidden and svid != old_vid and svid not in candidate_vids:
                    candidate_vids.append(svid)

        replacement = None
        for cand_vid in candidate_vids:
            ch = check_oembed_health(cand_vid)
            if ch.get("status") == "OK" and _candidate_matches_song_title(song_title, ch.get("title", "")):
                if cand_vid in alt_meta_map and alt_meta_map[cand_vid].get("duration"):
                    ch["duration"] = alt_meta_map[cand_vid]["duration"]
                replacement = ch
                break

        if replacement:
            new_vid = replacement["video_id"]
            forbidden.discard(old_vid)
            forbidden.add(new_vid)
            healed_records.append({
                "index": item.get("index"),
                "song_title": song_title,
                "old_vid": old_vid,
                "old_title": old_vtitle,
                "old_status": broken_info.get("status"),
                "old_reason": broken_info.get("reason", ""),
                "new_vid": new_vid,
                "new_title": replacement.get("title", ""),
                "new_channel": replacement.get("channel", ""),
                "new_duration": replacement.get("duration", ""),
            })
            if not dry_run:
                item["selected_video"] = {
                    **old_sel,
                    "video_id": new_vid,
                    "url": f"https://www.youtube.com/watch?v={new_vid}",
                    "video_title": replacement.get("title", ""),
                    "channel": replacement.get("channel", ""),
                    "duration": replacement.get("duration") or old_sel.get("duration", ""),
                    "views": replacement.get("views", ""),
                    "healed_from": old_vid,
                    "healed_at": time.strftime("%Y-%m-%d"),
                }
                item["alternative_videos"] = [
                    a for a in item.get("alternative_videos", []) if a.get("video_id") not in (old_vid, new_vid)
                ]
        else:
            unhealed_records.append({
                "index": item.get("index"),
                "song_title": song_title,
                "old_vid": old_vid,
                "old_title": old_vtitle,
                "old_status": broken_info.get("status"),
                "old_reason": broken_info.get("reason", ""),
            })

    report_lines = [
        f"# דו\"ח תקינות וריפוי אוטומטי של {cfg.playlist_title_he}",
        "",
        f"- **תאריך בדיקה:** `{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}`",
        f"- **סה\"כ סרטונים שנבדקו:** `{len(matched_items)}`",
        f"- **סרטונים תקינים ופעילים:** `{len(matched_items) - len(broken_items)} / {len(matched_items)}`",
        f"- **סרטונים שהוחלפו אוטומטית במקור גיבוי (Auto-Healed):** `{len(healed_records)}`",
        f"- **סרטונים הדורשים בדיקה ידנית:** `{len(unhealed_records)}`",
        "",
    ]
    if healed_records:
        report_lines.extend([
            "## סרטונים שהוחלפו אוטומטית במקור גיבוי תקין",
            "",
            "| # | שיר | סרטון שהוסר (סיבה) | סרטון גיבוי חדש שנבחר | ערוץ | אורך |",
            "|---|---|---|---|---|---|",
        ])
        for r in healed_records:
            report_lines.append(
                f"| {r['index']} | **{r['song_title']}** | `{r['old_vid']}` ({r['old_status']}) | "
                f"[{r['new_title']}](https://www.youtube.com/watch?v={r['new_vid']}) | {r['new_channel']} | {r['new_duration']} |"
            )
        report_lines.append("")

    if unhealed_records:
        report_lines.extend([
            "## סרטונים לא זמינים ללא חלופה אוטומטית",
            "",
            "| # | שיר | סרטון | סטטוס |",
            "|---|---|---|---|",
        ])
        for r in unhealed_records:
            report_lines.append(
                f"| {r['index']} | **{r['song_title']}** | `{r['old_vid']}` ({r['old_title']}) | {r['old_status']} ({r['old_reason']}) |"
            )
        report_lines.append("")

    if not healed_records and not unhealed_records:
        report_lines.append(
            f"✅ **כל {len(matched_items)} הסרטונים בפלייליסט תקינים, זמינים וניתנים להטמעה ולניגון!**\n"
        )

    cfg.health_report_md.write_text("\n".join(report_lines), encoding="utf-8")

    changed = (len(healed_records) > 0 or pruned_alts_count > 0) and not dry_run
    if changed:
        cfg.playlist_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        if run_backup:
            backup_composer_metadata(slug)
        build_composer(slug, standalone=standalone, rebuild_hub=True)
        print(
            f"[{cfg.slug}] Auto-healed {len(healed_records)} videos, pruned {pruned_alts_count} dead backup links, "
            "and regenerated all playlist files."
        )
    else:
        print(f"[{cfg.slug}] All videos healthy — no file changes needed.")

    return {
        "slug": cfg.slug,
        "checked": len(matched_items),
        "broken": len(broken_items),
        "pruned_alts": pruned_alts_count,
        "healed": healed_records,
        "unhealed": unhealed_records,
        "changed": changed,
        "report_md": str(cfg.health_report_md),
    }
