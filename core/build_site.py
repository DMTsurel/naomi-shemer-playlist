"""Shared static site, playlist export, and YouTube sync script generator."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any

from core.artists import (
    clean_artist_name,
    clean_display_album,
    normalize_performers_list,
)
from core.config import (
    ASSETS_DIR,
    REPO_ROOT,
    ComposerConfig,
    list_enabled_slugs,
    load_composer,
    load_registry,
)
from core.hebrew import get_decade, parse_duration_seconds

GENERIC_ARCHIVE_ROLE_LABELS: dict[str, str] = {
    "words_and_music": "מילים ולחן",
    "music_only": "לחן בלבד",
    "words_only": "מילים בלבד",
    "translation": "תרגום",
    "performance_only": "ביצוע בלבד",
}


def _is_non_song_clip(entry: dict[str, Any], tv_album_group: str) -> bool:
    if entry.get("album_group") == tv_album_group:
        return True
    sv = entry.get("selected_video") or {}
    txt = f"{sv.get('matched_performer', '')} {sv.get('video_title', '')}"
    return any(w in txt for w in ("ראיון", "פרודיה", "סקיצה נדירה", "חזרה,"))


def validate_and_normalize_playlist(data: dict[str, Any], cfg: ComposerConfig) -> bool:
    """Normalize tiers, recompute version indices, dual_role, chrono indices, and stats."""
    playlist = data.get("playlist", [])
    tier_norm = {
        "1_naomi_album": ("1_album_naomi", f"1. אלבום של {cfg.name_he}"),
        "5_cover_version": ("5_cover", "5. ביצוע מחודש / קאבר"),
        "6_no_youtube": ("6_not_found", "6. לא נמצא סרטון תואם"),
    }
    canonical_tier_labels = {
        "5_cover": "5. ביצוע מחודש / קאבר",
    }
    valid_matched_tiers = {
        "1_album_naomi",
        "1_album_creator",
        "2_album_original",
        "3_naomi_performance",
        "3_creator_performance",
        "4_original_performance",
        "5_cover",
    }
    creator_perf_tiers = set(cfg.creator_performance_tiers)
    tv_grp = cfg.tv_album_group

    changed = False
    matched_entries: list[dict[str, Any]] = []
    unmatched_entries: list[dict[str, Any]] = []
    seen_primary_vids: dict[str, int] = {}
    by_title: dict[str, list[dict[str, Any]]] = {}

    for item in playlist:
        if str(item.get("year", "")) == "2099":
            item["year"] = ""
            changed = True
        ag_val = str(item.get("album_group", "") or "").strip()
        if ag_val.startswith(f"ביצוע {cfg.name_he} (אחרי האלבום:") or ag_val == f"סינגל / ביצוע בודד (ביצוע {cfg.name_he})":
            item["album_group"] = "סינגל / ביצוע בודד"
            changed = True
        if "catalog_performers" in item:
            norm_cp = normalize_performers_list(item.get("catalog_performers", []))
            if norm_cp != item.get("catalog_performers", []):
                item["catalog_performers"] = norm_cp
                changed = True
        t = item.get("tier", "")
        if t in tier_norm:
            item["tier"], item["tier_label"] = tier_norm[t]
            changed = True
        if item.get("tier") in canonical_tier_labels and item.get("tier_label") != canonical_tier_labels[item["tier"]]:
            item["tier_label"] = canonical_tier_labels[item["tier"]]
            changed = True
        sel = item.get("selected_video")
        if sel and sel.get("video_id"):
            st = sel.get("tier", "")
            if st in tier_norm:
                sel["tier"], sel["tier_label"] = tier_norm[st]
                changed = True
            if sel.get("tier") in canonical_tier_labels and sel.get("tier_label") != canonical_tier_labels[sel["tier"]]:
                sel["tier_label"] = canonical_tier_labels[sel["tier"]]
                changed = True
            matched_entries.append(item)
            by_title.setdefault(item["title"], []).append(item)
        else:
            if item.get("tier") != "6_not_found":
                item["tier"] = "6_not_found"
                item["tier_label"] = "6. לא נמצא סרטון תואם"
                changed = True
            unmatched_entries.append(item)

    for _title, group in by_title.items():
        total_v = len(group)
        orig_idx = 0
        if total_v > 1:
            explicit_orig = [idx_g for idx_g, x in enumerate(group) if x.get("is_true_original")]
            if explicit_orig:
                orig_idx = explicit_orig[0]
            else:
                candidates = [
                    (
                        int(str(x.get("year", "")).strip()) if str(x.get("year", "")).strip().isdigit() else 9999,
                        0 if x.get("tier") != "5_cover" else 1,
                        idx_g,
                    )
                    for idx_g, x in enumerate(group)
                    if not _is_non_song_clip(x, tv_grp)
                ]
                if candidates:
                    orig_idx = min(candidates)[2]

        for idx_in_group, it in enumerate(group):
            if it.get("ver_idx") != idx_in_group + 1:
                it["ver_idx"] = idx_in_group + 1
                changed = True
            if it.get("ver_total") != total_v:
                it["ver_total"] = total_v
                changed = True
            if total_v == 1:
                if "dual_role" in it:
                    del it["dual_role"]
                    changed = True
            else:
                if idx_in_group == orig_idx:
                    new_role = "original_performance"
                elif it.get("tier") in creator_perf_tiers:
                    new_role = "naomi_performance" if "naomi" in str(it.get("tier", "")) else "creator_performance"
                else:
                    new_role = "additional_performance"
                if it.get("dual_role") != new_role:
                    it["dual_role"] = new_role
                    changed = True

    ordered = matched_entries + unmatched_entries
    for i, it in enumerate(ordered, 1):
        if it.get("index") != i:
            it["index"] = i
            changed = True

    def _chrono_sort_key(it: dict[str, Any]):
        yr_s = str(it.get("year", "") or "").strip()
        yr_num = int(yr_s) if (yr_s.isdigit() and int(yr_s) < 2099) else 9999
        prev_c = it.get("chrono_index")
        prev_c_num = int(prev_c) if isinstance(prev_c, int) else 999999
        return (yr_num, prev_c_num, it["index"])

    for c_idx, it in enumerate(sorted(matched_entries, key=_chrono_sort_key), 1):
        if it.get("chrono_index") != c_idx:
            it["chrono_index"] = c_idx
            changed = True

    errors = []
    for it in matched_entries:
        vid = it["selected_video"]["video_id"]
        if vid in seen_primary_vids:
            errors.append(f"Duplicate primary video_id {vid} at #{it['index']} and #{seen_primary_vids[vid]}")
        seen_primary_vids[vid] = it["index"]
        if it.get("tier") not in valid_matched_tiers:
            errors.append(f"Invalid tier '{it.get('tier')}' at #{it['index']} ({it['title']})")
        for a in it.get("alternative_videos", []):
            if a.get("video_id") == vid:
                errors.append(f"Self-referencing backup video_id {vid} at #{it['index']}")

    if errors:
        print(f"⚠️ אזהרות שלמות נתונים ({cfg.slug}):")
        for e in errors:
            print("  -", e)
    else:
        print(f"✔ בדיקת שלמות נתונים עברה בהצלחה ({cfg.slug}: {len(matched_entries)} סרטונים ייחודיים, 0 שגיאות).")

    data["playlist"] = ordered
    stats = data.setdefault("stats", {})
    matched_songs_cnt = len(by_title)
    total_songs_cnt = len({it["title"] for it in ordered})
    by_tier_map: dict[str, int] = {}
    tier_breakdown_map: dict[str, int] = {}
    for it in ordered:
        tl = it.get("tier_label", "")
        tk = it.get("tier", "")
        if tl:
            by_tier_map[tl] = by_tier_map.get(tl, 0) + 1
        if tk:
            tier_breakdown_map[tk] = tier_breakdown_map.get(tk, 0) + 1

    if (
        stats.get("matched_videos") != len(matched_entries)
        or stats.get("matched_songs") != matched_songs_cnt
        or stats.get("unmatched_songs") != len(unmatched_entries)
        or stats.get("total_songs") != total_songs_cnt
        or stats.get("total_playlist_entries") != len(ordered)
        or stats.get("by_tier") != by_tier_map
        or stats.get("tier_breakdown") != tier_breakdown_map
    ):
        changed = True
    stats["total_songs"] = total_songs_cnt
    stats["total_catalog_songs"] = total_songs_cnt
    stats["matched_songs"] = matched_songs_cnt
    stats["unmatched_songs"] = len(unmatched_entries)
    stats["total_playlist_videos"] = len(matched_entries)
    stats["total_videos"] = len(matched_entries)
    stats["matched_videos"] = len(matched_entries)
    stats["total_playlist_entries"] = len(ordered)
    stats["by_tier"] = by_tier_map
    stats["tier_breakdown"] = tier_breakdown_map
    return changed


def sync_all_secondary_exports(data: dict[str, Any], cfg: ComposerConfig) -> list[Path]:
    """Generate and sync secondary export artifacts (CSV, MD, M3U8, streaming CSV, Wayback URLs)."""
    playlist = data["playlist"]
    matched = [x for x in playlist if x.get("selected_video")]
    csv_path = cfg.playlist_csv
    md_path = cfg.playlist_md
    stream_csv_path = cfg.streaming_import_csv
    m3u8_path = cfg.stream_m3u8
    wayback_path = cfg.wayback_txt

    fieldnames = [
        "index", "chrono_index", "canonical_layer", "canonical_score", "title",
        "year", "role_category", "role_label_heb", "co_creators_heb", "lyricist", "composer",
        "translator", "tier", "tier_label", "matched_performer", "matched_album",
        "album_group", "album_track_number", "video_id", "video_url",
        "video_title", "channel", "duration", "views", "opening_line", "nli_url",
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for item in playlist:
            sel = item.get("selected_video") or {}
            nli_url = next(
                (
                    lk.get("url", "")
                    for lk in item.get("archive_links", [])
                    if str(lk.get("source", "")) == "nli" and lk.get("url")
                ),
                next(
                    (
                        lk.get("url", "")
                        for lk in item.get("archive_links", [])
                        if str(lk.get("source", "")).startswith("nli") and lk.get("url")
                    ),
                    "",
                ),
            )
            yr_raw = item.get("year", "")
            yr_csv = yr_raw if (yr_raw and str(yr_raw) != "2099") else ""
            w.writerow({
                "index": item.get("index", ""),
                "chrono_index": item.get("chrono_index", ""),
                "canonical_layer": item.get("canonical_layer", ""),
                "canonical_score": item.get("canonical_score", ""),
                "title": item.get("title", ""),
                "year": yr_csv,
                "role_category": item.get("role_category", ""),
                "role_label_heb": item.get("role_label_heb", ""),
                "co_creators_heb": item.get("co_creators_heb", ""),
                "lyricist": item.get("lyricist", ""),
                "composer": item.get("composer", ""),
                "translator": item.get("translator", ""),
                "tier": item.get("tier", ""),
                "tier_label": item.get("tier_label", ""),
                "matched_performer": sel.get("matched_performer") or item.get("matched_performer", ""),
                "matched_album": sel.get("matched_album", ""),
                "album_group": item.get("album_group", ""),
                "album_track_number": item.get("album_track_number", ""),
                "video_id": sel.get("video_id", ""),
                "video_url": f"https://www.youtube.com/watch?v={sel['video_id']}" if sel.get("video_id") else "",
                "video_title": sel.get("video_title", ""),
                "channel": sel.get("channel", ""),
                "duration": sel.get("duration", ""),
                "views": sel.get("views", ""),
                "opening_line": item.get("opening_line", ""),
                "nli_url": nli_url,
            })

    md_lines = [
        f"# פלייליסט {cfg.playlist_title_he} ביוטיוב ({len(matched)} ביצועים)",
        "",
        "| # | שנה | שם השיר | תפקיד | סיווג | מבצע / ערוץ | קישור ליוטיוב | אורך |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, item in enumerate(matched, 1):
        sel = item["selected_video"]
        vid = sel["video_id"]
        yr = item.get("year") if item.get("year") and str(item.get("year")) != "2099" else "—"
        perf = sel.get("matched_performer") or sel.get("channel", "")
        vtitle = sel.get("video_title", "").replace("|", "·")
        md_lines.append(
            f"| {i} | {yr} | **{item['title']}** | {item.get('role_label_heb', '')} | "
            f"{item.get('tier_label', '')} | {perf} | [{vtitle}](https://www.youtube.com/watch?v={vid}) | {sel.get('duration', '')} |"
        )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    with open(stream_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "playlist_order", "title", "artist", "album", "year",
                "composer_lyricist_role", "duration", "youtube_url",
                "youtube_id", "backup_youtube_urls",
            ],
        )
        writer.writeheader()
        for idx, item in enumerate(matched, 1):
            sel = item["selected_video"]
            vid = sel["video_id"]
            yr = item.get("year", "")
            yr_clean = yr if (yr and str(yr) != "2099") else ""
            alb = clean_display_album(item, sel, include_track=False)
            artist = clean_artist_name(item, sel, fallback_artist=cfg.name_he)
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
                "composer_lyricist_role": item.get("role_label_heb", cfg.default_role_label_heb),
                "duration": sel.get("duration", ""),
                "youtube_url": f"https://www.youtube.com/watch?v={vid}",
                "youtube_id": vid,
                "backup_youtube_urls": " | ".join(alts),
            })

    m3u_lines = [
        "#EXTM3U",
        f"#PLAYLIST:{cfg.playlist_title_he} – האוסף המקיף ({len(matched)} ביצועים ביוטיוב)",
    ]
    for item in matched:
        sel = item["selected_video"]
        vid = sel["video_id"]
        sec = parse_duration_seconds(sel.get("duration", ""))
        artist = clean_artist_name(item, sel, fallback_artist=cfg.name_he)
        title = item.get("title", "")
        yr = item.get("year", "")
        yr_str = f" ({yr})" if (yr and str(yr) != "2099") else ""
        m3u_lines.append(f"#EXTINF:{sec},{artist} - {title}{yr_str}")
        m3u_lines.append(f"https://www.youtube.com/watch?v={vid}")
    m3u8_path.write_text("\n".join(m3u_lines) + "\n", encoding="utf-8")

    urls: list[str] = []
    if cfg.youtube_playlist_id:
        urls.append(f"https://www.youtube.com/playlist?list={cfg.youtube_playlist_id}")
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
    wayback_path.write_text("\n".join(urls) + "\n", encoding="utf-8")

    return [csv_path, md_path, stream_csv_path, m3u8_path, wayback_path]


def generate_browser_scripts(matched_entries: list[dict[str, Any]], cfg: ComposerConfig) -> list[Path]:
    """Generate browser console scripts for creating and syncing the YouTube playlist."""
    total_videos = len(matched_entries)
    video_ids = [item["selected_video"]["video_id"] for item in matched_entries]
    fn_suffix = cfg.js_function_suffix
    desc_literal = json.dumps(cfg.playlist_description_he, ensure_ascii=False)
    title_literal = json.dumps(cfg.playlist_title_he, ensure_ascii=False)

    create_js = f"""// ============================================================================
// יצירת פלייליסט "{cfg.playlist_title_he} - האוסף המקיף" ({total_videos} ביצועים) בחשבון היוטיוב שלך
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com בדפדפן וודא שאתה מחובר לחשבון היוטיוב שלך.
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console של הדפדפן.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// תוך כ-10 שניות הפלייליסט ייווצר וייפתח אוטומטית!
// ============================================================================
(async function create{fn_suffix}Playlist() {{
  const VIDEO_IDS = {json.dumps(video_ids, ensure_ascii=False)};
  const PLAYLIST_TITLE = {title_literal};
  const PLAYLIST_DESC = {desc_literal};

  if (!window.ytcfg || typeof window.ytcfg.get !== "function") {{
    alert("שגיאה: יש להריץ את הסקריפט מתוך לשונית פתוחה של https://www.youtube.com");
    return;
  }}

  function getCookie(name) {{
    const m = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([.$?*|{{}}()\\[\\]\\\\/+^])/g, "\\\\$1") + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : null;
  }}

  const sapisid = getCookie("SAPISID") || getCookie("__Secure-3PAPISID");
  if (!sapisid) {{
    alert("שגיאה: לא נמצא חיבור לחשבון יוטיוב. אנא התחבר לחשבון היוטיוב שלך ב-https://www.youtube.com ונסה שוב.");
    return;
  }}

  async function makeSapisidHash(origin) {{
    const ts = Math.floor(Date.now() / 1000);
    const input = ts + " " + sapisid + " " + origin;
    const buf = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(input));
    const hex = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    return "SAPISIDHASH " + ts + "_" + hex;
  }}

  async function ytPost(endpoint, bodyObj) {{
    const origin = window.location.origin;
    const auth = await makeSapisidHash(origin);
    const headers = {{
      "Content-Type": "application/json",
      "Authorization": auth,
      "X-Origin": origin,
      "X-Goog-AuthUser": String(window.ytcfg.get("SESSION_INDEX") ?? "0"),
    }};
    const visitor = window.ytcfg.get("VISITOR_DATA");
    if (visitor) headers["X-Goog-Visitor-Id"] = visitor;

    const resp = await fetch(origin + endpoint + "?prettyPrint=false", {{
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({{
        context: window.ytcfg.get("INNERTUBE_CONTEXT"),
        ...bodyObj
      }})
    }});
    if (!resp.ok) {{
      const txt = await resp.text();
      throw new Error("HTTP " + resp.status + ": " + txt.slice(0, 300));
    }}
    return resp.json();
  }}

  console.log("🚀 יוצר פלייליסט חדש ביוטיוב:", PLAYLIST_TITLE);
  const createRes = await ytPost("/youtubei/v1/playlist/create", {{
    title: PLAYLIST_TITLE,
    description: PLAYLIST_DESC,
    privacyStatus: "UNLISTED"
  }});

  const playlistId = createRes.playlistId;
  if (!playlistId) {{
    console.error("תגובת שרת:", createRes);
    throw new Error("לא התקבל playlistId מיוטיוב.");
  }}
  console.log("✅ הפלייליסט נוצר בהצלחה! מזהה:", playlistId);

  const BATCH_SIZE = 50;
  for (let i = 0; i < VIDEO_IDS.length; i += BATCH_SIZE) {{
    const batch = VIDEO_IDS.slice(i, i + BATCH_SIZE);
    console.log(`⏳ מוסיף שירים ${{i + 1}} עד ${{Math.min(i + BATCH_SIZE, VIDEO_IDS.length)}} מתוך ${{VIDEO_IDS.length}}...`);
    await ytPost("/youtubei/v1/browse/edit_playlist", {{
      playlistId: playlistId,
      actions: batch.map(vid => ({{
        action: "ACTION_ADD_VIDEO",
        addedVideoId: vid
      }}))
    }});
    await new Promise(r => setTimeout(r, 600));
  }}

  const url = "https://www.youtube.com/playlist?list=" + playlistId;
  console.log("🎉 סיימנו! כל " + VIDEO_IDS.length + " השירים נוספו לפלייליסט:");
  console.log(url);
  window.open(url, "_blank");
}})();
"""
    out_paths = [cfg.create_js]
    cfg.create_js.write_text(create_js, encoding="utf-8")

    if cfg.youtube_playlist_id:
        pl_id = cfg.youtube_playlist_id
        vid_to_title = {
            item["selected_video"]["video_id"]: f"{item['title']} ({item.get('year', '')})"
            for item in matched_entries
        }
        update_js = f"""// ============================================================================
// עדכון הפלייליסט הקיים ביוטיוב ({pl_id}) + וידוא אוטומטי של הסדר הסופי!
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com/playlist?list={pl_id} בדפדפן (מחובר לחשבון שלך).
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// הסקריפט יעדכן את הפלייליסט הקיים ({pl_id}), ובסיום יקרא מחדש את כל הרצועות
// משרתי יוטיוב כדי לוודא ב-100% שהסידור הסופי תואם לרשימת היעד (ויתקן אוטומטית כל סטייה).
// ============================================================================
(async function updateExisting{fn_suffix}Playlist() {{
  const PLAYLIST_ID = "{pl_id}";
  const PLAYLIST_TITLE = {title_literal};
  const TARGET_VIDEO_IDS = {json.dumps(video_ids, ensure_ascii=False)};
  const VIDEO_TITLES = {json.dumps(vid_to_title, ensure_ascii=False)};

  if (!window.ytcfg || typeof window.ytcfg.get !== "function") {{
    alert("שגיאה: יש להריץ את הסקריפט מתוך לשונית פתוחה של https://www.youtube.com");
    return;
  }}

  function getCookie(name) {{
    const m = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([.$?*|{{}}()\\[\\]\\\\/+^])/g, "\\\\$1") + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : null;
  }}

  const sapisid = getCookie("SAPISID") || getCookie("__Secure-3PAPISID");
  if (!sapisid) {{
    alert("שגיאה: לא נמצא חיבור לחשבון יוטיוב. אנא התחבר לחשבון היוטיוב שלך ונסה שוב.");
    return;
  }}

  async function makeSapisidHash(origin) {{
    const ts = Math.floor(Date.now() / 1000);
    const input = ts + " " + sapisid + " " + origin;
    const buf = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(input));
    const hex = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    return "SAPISIDHASH " + ts + "_" + hex;
  }}

  async function ytPost(endpoint, bodyObj) {{
    const origin = window.location.origin;
    const auth = await makeSapisidHash(origin);
    const headers = {{
      "Content-Type": "application/json",
      "Authorization": auth,
      "X-Origin": origin,
      "X-Goog-AuthUser": String(window.ytcfg.get("SESSION_INDEX") ?? "0"),
    }};
    const visitor = window.ytcfg.get("VISITOR_DATA");
    if (visitor) headers["X-Goog-Visitor-Id"] = visitor;

    const resp = await fetch(origin + endpoint + "?prettyPrint=false", {{
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({{
        context: window.ytcfg.get("INNERTUBE_CONTEXT"),
        ...bodyObj
      }})
    }});
    if (!resp.ok) {{
      const txt = await resp.text();
      throw new Error("HTTP " + resp.status + ": " + txt.slice(0, 300));
    }}
    return resp.json();
  }}

  // שליפת כל הסרטונים הקיימים כרגע בפלייליסט (כולל סרטונים מוסתרים/לא זמינים עם params: "wgYCCAA=")
  function findSetVideoId(node, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 22) return null;
    if (typeof node.setVideoId === "string" && node.setVideoId) return node.setVideoId;
    if (Array.isArray(node)) {{
      for (const el of node) {{
        const found = findSetVideoId(el, depth + 1);
        if (found) return found;
      }}
      return null;
    }}
    for (const k of Object.keys(node)) {{
      const found = findSetVideoId(node[k], depth + 1);
      if (found) return found;
    }}
    return null;
  }}

  function findWatchVideoId(node, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 10) return null;
    if (node.watchEndpoint && typeof node.watchEndpoint.videoId === "string" && node.watchEndpoint.videoId) {{
      return node.watchEndpoint.videoId;
    }}
    if (Array.isArray(node)) {{
      for (const el of node) {{
        const found = findWatchVideoId(el, depth + 1);
        if (found) return found;
      }}
      return null;
    }}
    for (const k of Object.keys(node)) {{
      if (k === "menuButton") continue;
      const found = findWatchVideoId(node[k], depth + 1);
      if (found) return found;
    }}
    return null;
  }}

  function nodeBelongsToPlaylist(node, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 14) return false;
    if (node.playlistId === PLAYLIST_ID) return true;
    if (Array.isArray(node)) return node.some(el => nodeBelongsToPlaylist(el, depth + 1));
    for (const k of Object.keys(node)) {{
      if (nodeBelongsToPlaylist(node[k], depth + 1)) return true;
    }}
    return false;
  }}

  function findContinuationTokens(node, tokensOut, seenTokens, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 16) return;
    if (node.continuationCommand && typeof node.continuationCommand.token === "string") {{
      const tok = node.continuationCommand.token;
      if (tok && tok.startsWith("4qmF") && !seenTokens.has(tok)) {{
        seenTokens.add(tok);
        tokensOut.push(tok);
      }}
    }}
    if (node.nextContinuationData && typeof node.nextContinuationData.continuation === "string") {{
      const tok = node.nextContinuationData.continuation;
      if (tok && !seenTokens.has(tok)) {{
        seenTokens.add(tok);
        tokensOut.push(tok);
      }}
    }}
    if (Array.isArray(node)) {{
      for (const el of node) findContinuationTokens(el, tokensOut, seenTokens, depth + 1);
      return;
    }}
    for (const k of Object.keys(node)) {{
      findContinuationTokens(node[k], tokensOut, seenTokens, depth + 1);
    }}
  }}

  function extractVideosAndContinuation(obj, itemsOut, tokensOut, seenTokens) {{
    if (!obj || typeof obj !== "object") return;
    if (Array.isArray(obj)) {{
      for (const el of obj) extractVideosAndContinuation(el, itemsOut, tokensOut, seenTokens);
      return;
    }}
    // דילוג על מדפי המלצות ("Recommended videos") שיוטיוב מציג לבעל הפלייליסט ואינם שייכים לפלייליסט!
    if (obj.reelShelfRenderer || obj.shelfRenderer || obj.horizontalCardListRenderer) {{
      return;
    }}
    if (obj.playlistVideoRenderer) {{
      const r = obj.playlistVideoRenderer;
      const svid = r.setVideoId || findSetVideoId(r) || null;
      if ((r.videoId || svid) && (svid || nodeBelongsToPlaylist(r))) {{
        itemsOut.push({{
          videoId: r.videoId || null,
          setVideoId: svid
        }});
      }}
      return;
    }}
    if (obj.lockupViewModel) {{
      const lv = obj.lockupViewModel;
      const vid = lv.contentId || findWatchVideoId(lv);
      const svid = findSetVideoId(lv);
      const isVidType = lv.contentType === "LOCKUP_CONTENT_TYPE_VIDEO" || !lv.contentType;
      if (((vid && isVidType) || svid) && (svid || nodeBelongsToPlaylist(lv))) {{
        itemsOut.push({{
          videoId: vid || null,
          setVideoId: svid
        }});
      }}
      return;
    }}
    if (obj.continuationItemRenderer || obj.continuationItemViewModel) {{
      findContinuationTokens(obj, tokensOut, seenTokens);
      return;
    }}
    if (obj.continuations && Array.isArray(obj.continuations)) {{
      findContinuationTokens(obj.continuations, tokensOut, seenTokens);
    }}
    for (const k of Object.keys(obj)) {{
      extractVideosAndContinuation(obj[k], itemsOut, tokensOut, seenTokens);
    }}
  }}

  function getFirstSectionRoot(browseData) {{
    const secContents = browseData?.contents?.twoColumnBrowseResultsRenderer?.tabs?.[0]?.tabRenderer?.content?.sectionListRenderer?.contents;
    if (Array.isArray(secContents) && secContents.length > 0) {{
      // תמיד קוראים אך ורק את contents[0] (רשימת הפלייליסט עצמה), ולא את contents[1] (סרטונים מומלצים להוספה)!
      return secContents[0];
    }}
    return browseData;
  }}

  // includeUnavailable=true שולח params: "wgYCCAA=" ("Show unavailable videos") כך שגם סרטונים מוסתרים מזוהים ונמחקים!
  async function fetchCurrentPlaylistItems(includeUnavailable = true) {{
    const items = [];
    const tokens = [];
    const seenTokens = new Set();
    const reqBody = {{ browseId: "VL" + PLAYLIST_ID }};
    if (includeUnavailable) reqBody.params = "wgYCCAA=";
    const firstPage = await ytPost("/youtubei/v1/browse", reqBody);
    extractVideosAndContinuation(getFirstSectionRoot(firstPage), items, tokens, seenTokens);
    while (tokens.length > 0) {{
      const tok = tokens.shift();
      const nextPage = await ytPost("/youtubei/v1/browse", {{ continuation: tok }});
      extractVideosAndContinuation(nextPage, items, tokens, seenTokens);
    }}
    return items;
  }}

  function buildRemoveActions(items) {{
    const actions = [];
    const seenVid = new Set();
    for (const item of items) {{
      if (item.setVideoId) {{
        actions.push({{ action: "ACTION_REMOVE_VIDEO", setVideoId: item.setVideoId }});
      }} else if (item.videoId && !seenVid.has(item.videoId)) {{
        seenVid.add(item.videoId);
        actions.push({{ action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: item.videoId }});
      }}
    }}
    return actions;
  }}

  async function safeDeleteBatch(batch) {{
    if (!batch || batch.length === 0) return;
    try {{
      await ytPost("/youtubei/v1/browse/edit_playlist", {{
        playlistId: PLAYLIST_ID,
        actions: batch
      }});
    }} catch (err) {{
      console.warn(`⚠️ מחיקת אצווה נתקלה בשגיאה (${{err.message.slice(0, 80)}}), מנסה פריט-פריט...`);
      for (const act of batch) {{
        try {{
          await ytPost("/youtubei/v1/browse/edit_playlist", {{
            playlistId: PLAYLIST_ID,
            actions: [act]
          }});
        }} catch (innerErr) {{
          console.warn("  ⏭️ דילוג על פריט שאינו בפלייליסט:", act, innerErr.message.slice(0, 60));
        }}
        await new Promise(r => setTimeout(r, 120));
      }}
    }}
  }}

  // עדכון שם הפלייליסט ל-"{cfg.playlist_title_he}"
  try {{
    await ytPost("/youtubei/v1/browse/edit_playlist", {{
      playlistId: PLAYLIST_ID,
      actions: [{{ action: "ACTION_SET_PLAYLIST_NAME", playlistName: PLAYLIST_TITLE }}]
    }});
    console.log(`🏷️ שם הפלייליסט עודכן ל: "${{PLAYLIST_TITLE}}"`);
  }} catch (e) {{
    console.warn("⚠️ לא הצלחתי לעדכן את שם הפלייליסט אוטומטית:", e.message);
  }}

  console.log("🔍 קורא את מצב הפלייליסט הקיים ביוטיוב (" + PLAYLIST_ID + ")...");
  let currentItems = await fetchCurrentPlaylistItems();
  console.log(`📋 נמצאו כרגע בפלייליסט ${{currentItems.length}} סרטונים (יעד רצוי: ${{TARGET_VIDEO_IDS.length}} סרטונים).`);

  // הגנה: אם הקריאה מיוטיוב החזירה 0 סרטונים בזמן שעל הדף עצמו יש סרטונים — עצור מיד לפני הוספה כפולה!
  if (currentItems.length === 0 && window.ytInitialData) {{
    const pageItems = [];
    const dummyTokens = [];
    extractVideosAndContinuation(getFirstSectionRoot(window.ytInitialData), pageItems, dummyTokens, new Set());
    if (pageItems.length > 0) {{
      console.error(`❌ עצירת חירום: בדף מופיעים ${{pageItems.length}} סרטונים אך קריאת ה-API החזירה 0. לא מוסיף כדי למנוע כפילויות!`);
      return;
    }}
  }}

  const curIds = currentItems.map(x => x.videoId);
  if (curIds.length === TARGET_VIDEO_IDS.length && curIds.every((v, i) => v === TARGET_VIDEO_IDS[i])) {{
    console.log("✅ [וידוא הושלם] הפלייליסט כבר מסודר ומעודכן ב-100% לפי הסדר המבוקש!");
    return;
  }}

  // חישוב תת-הסדרה המשותפת הארוכה ביותר (LCS) לצורך עדכון כירורגי מהיר ללא מחיקת כל הפלייליסט
  function computeLcsSet(a, b) {{
    const n = a.length, m = b.length;
    const dp = Array.from({{ length: n + 1 }}, () => new Int16Array(m + 1));
    for (let i = n - 1; i >= 0; i--) {{
      for (let j = m - 1; j >= 0; j--) {{
        dp[i][j] = a[i] === b[j] ? 1 + dp[i + 1][j + 1] : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }}
    }}
    const keepInA = new Set();
    let i = 0, j = 0;
    while (i < n && j < m) {{
      if (a[i] === b[j]) {{
        keepInA.add(a[i]);
        i++; j++;
      }} else if (dp[i + 1][j] >= dp[i][j + 1]) {{
        i++;
      }} else {{
        j++;
      }}
    }}
    return keepInA;
  }}

  const BATCH_SIZE = 50;
  const targetSetInit = new Set(TARGET_VIDEO_IDS);
  const seenInCur = new Set();
  const toDeleteItems = [];
  for (const it of currentItems) {{
    if (!targetSetInit.has(it.videoId) || seenInCur.has(it.videoId)) {{
      toDeleteItems.push(it);
    }} else {{
      seenInCur.add(it.videoId);
    }}
  }}
  const toAddVids = TARGET_VIDEO_IDS.filter(v => !seenInCur.has(v));
  const survivingCurIds = currentItems.filter(it => !toDeleteItems.includes(it)).map(it => it.videoId);
  const commonTargetIds = TARGET_VIDEO_IDS.filter(v => seenInCur.has(v));
  const lcsKeep = computeLcsSet(survivingCurIds, commonTargetIds);
  const estMoves = (commonTargetIds.length - lcsKeep.size) + toAddVids.length;
  const totalSurgicalOps = toDeleteItems.length + toAddVids.length + estMoves;

  const hasAllSetIds = currentItems.every(it => Boolean(it.setVideoId));
  if (currentItems.length > 0 && totalSurgicalOps <= 120 && (estMoves === 0 || hasAllSetIds)) {{
    console.log(`⚡ מבצע עדכון כירורגי מהיר (${{toDeleteItems.length}} מחיקות, ${{toAddVids.length}} הוספות, ${{estMoves}} הזזות מיקום)...`);
    if (toDeleteItems.length > 0) {{
      const delActions = buildRemoveActions(toDeleteItems);
      for (let i = 0; i < delActions.length; i += BATCH_SIZE) {{
        const batch = delActions.slice(i, i + BATCH_SIZE);
        await safeDeleteBatch(batch);
        await new Promise(r => setTimeout(r, 400));
      }}
    }}
    if (toAddVids.length > 0) {{
      for (let i = 0; i < toAddVids.length; i += BATCH_SIZE) {{
        const batch = toAddVids.slice(i, i + BATCH_SIZE);
        await ytPost("/youtubei/v1/browse/edit_playlist", {{
          playlistId: PLAYLIST_ID,
          actions: batch.map(vid => ({{ action: "ACTION_ADD_VIDEO", addedVideoId: vid }}))
        }});
        await new Promise(r => setTimeout(r, 500));
      }}
    }}
    if (estMoves > 0) {{
      await new Promise(r => setTimeout(r, 900));
      currentItems = await fetchCurrentPlaylistItems();
      const curMap = new Map(currentItems.map(it => [it.videoId, it.setVideoId]));
      const presentTarget = TARGET_VIDEO_IDS.filter(v => curMap.has(v));
      const lcsNow = computeLcsSet(currentItems.map(it => it.videoId), presentTarget);
      // עוברים מהסוף להתחלה ומזיזים רק רצועות שאינן ב-LCS אל לפני הרצועה העוקבת שלהן
      for (let k = presentTarget.length - 2; k >= 0; k--) {{
        const vid = presentTarget[k];
        if (!lcsNow.has(vid)) {{
          const nextVid = presentTarget[k + 1];
          const setVid = curMap.get(vid);
          const succSetVid = curMap.get(nextVid);
          if (setVid && succSetVid) {{
            await ytPost("/youtubei/v1/browse/edit_playlist", {{
              playlistId: PLAYLIST_ID,
              actions: [{{
                action: "ACTION_MOVE_VIDEO_BEFORE",
                setVideoId: setVid,
                movedSetVideoIdSuccessor: succSetVid
              }}]
            }});
            lcsNow.add(vid);
          }}
        }}
      }}
    }}
  }} else {{
    console.log("🔄 מבצע עדכון סדר מלא בתוך הפלייליסט הקיים (" + PLAYLIST_ID + ")...");
    // שלב א': ניקוי הרשימה הישנה (עם וידוא שהרשימה התרוקנה לגמרי לפני הוספה)
    let pass = 1;
    while (currentItems.length > 0 && pass <= 10) {{
      const delActions = buildRemoveActions(currentItems);
      if (delActions.length === 0) break;
      for (let i = 0; i < delActions.length; i += BATCH_SIZE) {{
        const batch = delActions.slice(i, i + BATCH_SIZE);
        console.log(`🗑️ מנקה סדר ישן (סבב ${{pass}}: ${{i + 1}} עד ${{Math.min(i + BATCH_SIZE, delActions.length)}} מתוך ${{delActions.length}})...`);
        await safeDeleteBatch(batch);
        await new Promise(r => setTimeout(r, 450));
      }}
      await new Promise(r => setTimeout(r, 1200));
      currentItems = await fetchCurrentPlaylistItems();
      pass++;
    }}

    if (currentItems.length > 0) {{
      console.error(`❌ עצירה לפני הוספה: נותרו עדיין ${{currentItems.length}} סרטונים בפלייליסט לאחר ניקוי. רענן את העמוד והרץ שוב כדי להשלים ללא כפילויות.`);
      return;
    }}

    // שלב ב': הוספת כל הסרטונים לפי הסדר החדש
    for (let i = 0; i < TARGET_VIDEO_IDS.length; i += BATCH_SIZE) {{
      const batch = TARGET_VIDEO_IDS.slice(i, i + BATCH_SIZE);
      console.log(`⏳ מוסיף בסדר החדש ${{i + 1}} עד ${{Math.min(i + BATCH_SIZE, TARGET_VIDEO_IDS.length)}} מתוך ${{TARGET_VIDEO_IDS.length}}...`);
      await ytPost("/youtubei/v1/browse/edit_playlist", {{
        playlistId: PLAYLIST_ID,
        actions: batch.map(vid => ({{
          action: "ACTION_ADD_VIDEO",
          addedVideoId: vid
        }}))
      }});
      await new Promise(r => setTimeout(r, 550));
    }}
  }}

  // ============================================================================
  // שלב ג': וידוא סופי של הסידור בשרתי יוטיוב ותיקון אוטומטי של כל אי-התאמה
  // ============================================================================
  console.log("🔎 מבצע וידוא סופי של סדר השירים ובדיקת סרטונים מוסתרים מול שרתי יוטיוב...");
  await new Promise(r => setTimeout(r, 1500));
  let finalItems = await fetchCurrentPlaylistItems(true);
  let finalIds = finalItems.map(x => x.videoId);
  let visibleItems = await fetchCurrentPlaylistItems(false);
  const visibleSet = new Set(visibleItems.map(x => x.videoId));
  const hiddenNow = [];
  finalIds.forEach((vid, idx) => {{
    if (!visibleSet.has(vid)) {{
      hiddenNow.push({{ position: idx + 1, videoId: vid, title: VIDEO_TITLES[vid] || vid }});
    }}
  }});
  if (hiddenNow.length === 0) {{
    console.log("🟢 בדיקת זמינות: 0 סרטונים מוסתרים/לא-זמינים בפלייליסט באזור הגלישה שלך!");
  }} else {{
    console.warn(`⚠️ שים לב: יוטיוב מסתיר כעת באזור הגלישה שלך ${{hiddenNow.length}} סרטונים (חסימה אזורית או הסרה):`);
    console.table(hiddenNow);
  }}

  // 1. בדיקת התאמה מלאה של הרשימה והסדר
  if (finalIds.length === TARGET_VIDEO_IDS.length && finalIds.every((v, i) => v === TARGET_VIDEO_IDS[i])) {{
    console.log(`✅ [וידוא הושלם בהצלחה - 100% התאמה!] כל ${{finalIds.length}} השירים נמצאים בפלייליסט ${{PLAYLIST_ID}} בדיוק בסדר המבוקש!`);
    console.log("🔄 מרענן את העמוד בעוד 2 שניות כדי להציג את הרשימה המעודכנת...");
    setTimeout(() => location.reload(), 2000);
    return;
  }}

  console.warn(`⚠️ נמצא פער בבדיקה הראשונית: בפלייליסט יש ${{finalIds.length}} שירים לעומת ${{TARGET_VIDEO_IDS.length}} ברשימת היעד. מנתח ומתקן...`);

  // 2. איתור סרטונים שיוטיוב לא הצליח להוסיף (למשל סרטון שהפך לפרטי/נמחק)
  const finalSet = new Set(finalIds);
  const targetSet = new Set(TARGET_VIDEO_IDS);
  const missingFromYt = [];
  TARGET_VIDEO_IDS.forEach((vid, idx) => {{
    if (!finalSet.has(vid)) {{
      missingFromYt.push({{ index: idx + 1, videoId: vid, title: VIDEO_TITLES[vid] || vid }});
    }}
  }});

  if (missingFromYt.length > 0 && missingFromYt.length <= 40) {{
    console.log(`🔧 מנסה להוסיף שוב ${{missingFromYt.length}} סרטונים שחסרים בפלייליסט...`);
    for (const m of missingFromYt) {{
      try {{
        await ytPost("/youtubei/v1/browse/edit_playlist", {{
          playlistId: PLAYLIST_ID,
          actions: [{{ action: "ACTION_ADD_VIDEO", addedVideoId: m.videoId }}]
        }});
        console.log(`  ➕ נוסף בהצלחה: #${{m.index}} ${{m.title}} (${{m.videoId}})`);
      }} catch (err) {{
        console.error(`  ❌ יוטיוב דחה את הסרטון #${{m.index}} ${{m.title}} (${{m.videoId}}):`, err.message);
      }}
      await new Promise(r => setTimeout(r, 250));
    }}
  }} else if (missingFromYt.length > 40) {{
    console.warn(`⚠️ חסרים ${{missingFromYt.length}} סרטונים — מדלג על הוספה פרטנית כדי למנוע חסימת קצב מיוטיוב.`);
  }}

  // 3. הסרת סרטונים עודפים או כפולים שאינם ברשימת היעד (באצוות של 50)
  const seenCounts = {{}};
  const targetCounts = {{}};
  TARGET_VIDEO_IDS.forEach(v => {{ targetCounts[v] = (targetCounts[v] || 0) + 1; }});
  const toRemoveExtra = [];
  for (const item of finalItems) {{
    seenCounts[item.videoId] = (seenCounts[item.videoId] || 0) + 1;
    if (!targetSet.has(item.videoId) || seenCounts[item.videoId] > (targetCounts[item.videoId] || 0)) {{
      toRemoveExtra.push(item);
    }}
  }}
  if (toRemoveExtra.length > 0) {{
    const extraActions = buildRemoveActions(toRemoveExtra);
    console.log(`🧹 מסיר ${{extraActions.length}} סרטונים עודפים/כפולים...`);
    for (let i = 0; i < extraActions.length; i += BATCH_SIZE) {{
      const batch = extraActions.slice(i, i + BATCH_SIZE);
      await safeDeleteBatch(batch);
      await new Promise(r => setTimeout(r, 450));
    }}
  }}

  // 4. בדיקה חוזרת של הסדר היחסי ותיקון מיקומים במידת הצורך
  await new Promise(r => setTimeout(r, 1200));
  finalItems = await fetchCurrentPlaylistItems();
  finalIds = finalItems.map(x => x.videoId);
  const availableTargets = TARGET_VIDEO_IDS.filter(v => finalIds.includes(v));

  let orderMismatches = [];
  for (let i = 0; i < Math.min(finalIds.length, availableTargets.length); i++) {{
    if (finalIds[i] !== availableTargets[i]) {{
      orderMismatches.push({{
        position: i + 1,
        expected: availableTargets[i],
        expectedTitle: VIDEO_TITLES[availableTargets[i]] || availableTargets[i],
        actual: finalIds[i],
        actualTitle: VIDEO_TITLES[finalIds[i]] || finalIds[i]
      }});
    }}
  }}

  if (orderMismatches.length === 0 && finalIds.length === TARGET_VIDEO_IDS.length) {{
    console.log(`✅ [וידוא הושלם בהצלחה לאחר תיקון!] כל ${{finalIds.length}} השירים נמצאים בפלייליסט בדיוק בסדר המבוקש!`);
    setTimeout(() => location.reload(), 2000);
  }} else if (orderMismatches.length === 0) {{
    console.log(`✅ [וידוא סדר הושלם] הסדר של כל ${{finalIds.length}} הסרטונים הזמינים תואם ב-100% לסדר המבוקש!`);
    const stillMissing = TARGET_VIDEO_IDS.filter(v => !finalIds.includes(v)).map(v => ({{ videoId: v, title: VIDEO_TITLES[v] || v }}));
    if (stillMissing.length > 0) {{
      console.warn("⚠️ סרטונים שיוטיוב לא איפשר להוסיף (כנראה הוסרו/נחסמו ביוטיוב):", stillMissing);
      console.table(stillMissing);
    }}
    setTimeout(() => location.reload(), 3000);
  }} else {{
    console.warn(`⚠️ נמצאו ${{orderMismatches.length}} אי-התאמות מיקום (מתוך ${{finalIds.length}} שירים):`);
    console.table(orderMismatches.slice(0, 20));
  }}
}})();
"""
        cfg.update_js.write_text(update_js, encoding="utf-8")
        out_paths.append(cfg.update_js)

    return out_paths


def _build_songs_and_archive_payloads(
    matched_entries: list[dict[str, Any]],
    unmatched_entries: list[dict[str, Any]],
    cfg: ComposerConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, int]]]:
    """Build client-side song & archive JSON arrays plus aggregated facet counts."""
    songs_js: list[dict[str, Any]] = []
    tier_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    decade_counts: dict[str, int] = {}
    in_extras_section = False
    seen_primary_titles: set[str] = set()
    prev_primary_lyr = 1
    tv_grp = cfg.tv_album_group
    tail_vids = cfg.tail_video_ids
    tail_kws = cfg.tail_performer_keywords

    for idx_item, item in enumerate(matched_entries):
        sel = item["selected_video"]
        yr = item.get("year", "")
        yr_display = yr if (yr and str(yr) != "2099") else ""
        dual_role = item.get("dual_role", "")
        if dual_role == "original_performance":
            role_suffix = " [ביצוע מקורי]"
        elif dual_role in ("naomi_performance", "creator_performance"):
            role_suffix = f" [{cfg.creator_performance_tag_he}]"
        elif dual_role == "additional_performance":
            perf_lbl = sel.get("matched_performer", "").strip()
            role_suffix = f" [ביצוע: {perf_lbl}]" if perf_lbl else " [ביצוע נוסף]"
        else:
            role_suffix = ""

        display_title = f"{item['title']}{role_suffix}" + (f" ({yr_display})" if yr_display else "")
        tier = item["tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        rcat = item.get("role_category", "words_and_music")
        role_counts[rcat] = role_counts.get(rcat, 0) + 1

        dec = get_decade(yr_display)
        decade_counts[dec] = decade_counts.get(dec, 0) + 1

        lyr = int(item.get("canonical_layer", 2))
        lyr_label = item.get("canonical_layer_label", "")

        ag = item.get("album_group", "")
        trk = item.get("album_track_number", "")
        alb_str = clean_display_album(item, sel, include_track=True)

        perf_raw_blk = sel.get("matched_performer", "")
        is_tv_blk = ag == tv_grp
        is_tail_blk = (not is_tv_blk) and (
            sel["video_id"] in tail_vids or any(kw in perf_raw_blk for kw in tail_kws)
        )
        if not in_extras_section:
            if (
                is_tv_blk
                or is_tail_blk
                or lyr < prev_primary_lyr
                or (
                    item["title"] in seen_primary_titles
                    and (idx_item == 0 or matched_entries[idx_item - 1]["title"] != item["title"])
                )
            ):
                in_extras_section = True
            else:
                seen_primary_titles.add(item["title"])
                prev_primary_lyr = lyr

        if is_tv_blk:
            blk_id = "tv"
        elif is_tail_blk:
            blk_id = "tail"
        elif not in_extras_section:
            blk_id = f"p{lyr}"
        else:
            blk_id = f"e{lyr}"

        alts_list = []
        seen_alt_vids = {sel["video_id"]}
        for a in item.get("alternative_videos", []):
            avid = a.get("video_id", "")
            if avid and avid not in seen_alt_vids:
                seen_alt_vids.add(avid)
                alts_list.append({
                    "vid": avid,
                    "vtitle": a.get("video_title", ""),
                    "ch": a.get("channel", ""),
                    "dur": a.get("duration", ""),
                    "src": a.get("source", "direct_alternative"),
                })
                if len(alts_list) >= 6:
                    break

        songs_js.append({
            "n": item["index"],
            "chrono_n": item.get("chrono_index", item["index"]),
            "canon_score": item.get("canonical_score", 0),
            "acum_v": item.get("acum_versions_count", 0),
            "layer": lyr,
            "layer_label": lyr_label,
            "blk": blk_id,
            "ch_lbl": item.get("layer2_chapter", "") if blk_id == "p2" else "",
            "title": display_title,
            "raw_title": item["title"],
            "alt_titles": item.get("alt_titles", []),
            "ver_idx": item.get("ver_idx", 1),
            "ver_total": item.get("ver_total", 1),
            "year": yr_display,
            "decade": dec,
            "vid": sel["video_id"],
            "vtitle": sel["video_title"],
            "ch": sel["channel"],
            "dur": sel.get("duration", ""),
            "tier": tier,
            "tier_label": item["tier_label"],
            "perf": sel.get("matched_performer") or (", ".join(item.get("catalog_performers", [])[:2])),
            "alb": alb_str,
            "alb_group": ag,
            "alb_trk": int(trk) if str(trk).isdigit() else 999,
            "role_cat": rcat,
            "role_label": item.get("role_label_heb", cfg.default_role_label_heb),
            "co_creators": item.get("co_creators_heb", ""),
            "opening_line": item.get("opening_line", ""),
            "links": item.get("archive_links", []),
            "alts": alts_list,
        })

    archive_songs_js: list[dict[str, Any]] = []
    arch_role_counts: dict[str, int] = {}
    arch_src_counts: dict[str, int] = {}
    as_audio = 0
    for item in unmatched_entries:
        yr = item.get("year", "")
        yr_display = yr if (yr and str(yr) != "2099") else "ללא שנה"
        rcat = item.get("role_category", "words_and_music")
        arch_role_counts[rcat] = arch_role_counts.get(rcat, 0) + 1
        links_list = item.get("archive_links", [])
        has_audio = any(lk.get("source") in ("nli_audio", "zemereshet_audio") for lk in links_list)
        if has_audio:
            as_audio += 1
        seen_src_groups = set()
        for lk in links_list:
            src_key = str(lk.get("source", ""))
            if src_key.startswith("nli"):
                seen_src_groups.add("nli")
            elif src_key.startswith("zemereshet"):
                seen_src_groups.add("zemereshet")
            elif src_key:
                seen_src_groups.add(src_key)
        for sg in seen_src_groups:
            arch_src_counts[sg] = arch_src_counts.get(sg, 0) + 1
        archive_songs_js.append({
            "n": item["index"],
            "title": item["title"],
            "alt_titles": item.get("alt_titles", []),
            "year": yr_display,
            "role_cat": rcat,
            "role_label": item.get("role_label_heb", cfg.default_role_label_heb),
            "co_creators": item.get("co_creators_heb", ""),
            "perfs": ", ".join(item.get("catalog_performers", [])[:5]),
            "albums": ", ".join(item.get("catalog_albums", [])[:3]),
            "opening_line": item.get("opening_line", ""),
            "sources": item.get("sources", []),
            "has_audio": has_audio,
            "links": links_list,
        })

    counts = {
        "tier": tier_counts,
        "role": role_counts,
        "decade": decade_counts,
        "arch_role": arch_role_counts,
        "arch_src": arch_src_counts,
        "misc": {
            "as_audio": as_audio,
            "unique_songs": sum(1 for item in songs_js if item.get("ver_idx") == 1),
        },
    }
    return songs_js, archive_songs_js, counts


def _render_player_html(
    cfg: ComposerConfig,
    playlist_data_obj: dict[str, Any],
    counts: dict[str, dict[str, int]],
    total_videos: int,
    unmatched_songs_count: int,
    total_catalog_songs: int,
    standalone: bool = False,
) -> str:
    """Render composer player HTML (thin asset-linked by default, or self-contained when standalone=True)."""
    songs_js = playlist_data_obj["songs"]
    first_vid = songs_js[0]["vid"] if songs_js else ""
    tier_counts = counts["tier"]
    role_counts = counts["role"]
    decade_counts = counts["decade"]
    arch_role_counts = counts["arch_role"]
    arch_src_counts = counts["arch_src"]
    as_audio = counts["misc"]["as_audio"]
    unique_songs_count = counts["misc"]["unique_songs"]

    tier_options_html = "\n              ".join(
        f'<option value="{html.escape(key)}">{html.escape(label)} ({tier_counts.get(key, 0)})</option>'
        for key, label in cfg.tier_filter_options
    )
    role_options_html = "\n              ".join(
        f'<option value="{html.escape(key)}">{html.escape(label)} ({role_counts.get(key, 0)})</option>'
        for key, label in cfg.role_filter_options
    )
    arch_role_options_html = "\n            ".join(
        f'<option value="{html.escape(key)}">{html.escape(GENERIC_ARCHIVE_ROLE_LABELS.get(key, label))} ({arch_role_counts.get(key, 0)})</option>'
        for key, label in cfg.role_filter_options
    )

    yt_playlist_btn_html = (
        f'\n        <a class="btn btn-outline" href="https://www.youtube.com/playlist?list={html.escape(cfg.youtube_playlist_id)}" target="_blank" rel="noopener">פתח ב-YouTube ↗</a>'
        if cfg.youtube_playlist_id
        else ""
    )

    meta_desc = cfg.meta_description_template.format(
        total_catalog_songs=total_catalog_songs,
        total_videos=total_videos,
        unmatched_songs=unmatched_songs_count,
    ) or f"{cfg.playlist_title_he} ({total_videos} ביצועים ביוטיוב + {unmatched_songs_count} שירי ארכיון)"
    og_desc = cfg.og_description_template.format(
        total_catalog_songs=total_catalog_songs,
        total_videos=total_videos,
        unmatched_songs=unmatched_songs_count,
    ) or meta_desc

    if standalone:
        css_text = (ASSETS_DIR / "player.css").read_text(encoding="utf-8")
        js_text = (ASSETS_DIR / "player.js").read_text(encoding="utf-8")
        safe_data_json = json.dumps(playlist_data_obj, ensure_ascii=False, indent=2).replace("</script>", "<\\/script>")
        safe_js_text = js_text.replace("</script>", "<\\/script>")
        style_block = f"<style>\n{css_text}  </style>"
        script_block = f"<script>\n    window.PLAYLIST_DATA = {safe_data_json};\n{safe_js_text}  </script>"
    else:
        style_block = '<link rel="stylesheet" href="../assets/player.css" />'
        script_block = '<script src="./playlist_data.js"></script>\n  <script src="../assets/player.js"></script>'

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(cfg.playlist_title_he)} – האוסף המקיף ({total_videos} ביצועים ביוטיוב + {unmatched_songs_count} שירי ארכיון)</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230b1120' stroke='%23f59e0b' stroke-width='3'/%3E%3Ctext x='32' y='45' font-size='36' text-anchor='middle' fill='%23fbbf24'%3E%E2%99%AB%3C/text%3E%3C/svg%3E" />
  <meta name="description" content="{html.escape(meta_desc)}" />
  <meta property="og:title" content="{html.escape(cfg.playlist_title_he)} – האוסף המקיף ({total_videos} ביצועים + {unmatched_songs_count} שירי ארכיון)" />
  <meta property="og:description" content="{html.escape(og_desc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{html.escape(cfg.public_url)}" />
  <meta property="og:image" content="https://i.ytimg.com/vi/{html.escape(first_vid)}/hqdefault.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{html.escape(cfg.playlist_title_he)} – האוסף המקיף ({total_videos} ביצועים + {unmatched_songs_count} שירי ארכיון)" />
  <meta name="twitter:image" content="https://i.ytimg.com/vi/{html.escape(first_vid)}/hqdefault.jpg" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@600;700;800&family=Heebo:wght@400;500;600;700&display=swap" rel="stylesheet">
  {style_block}
</head>
<body>
  <div class="container">
    <!-- כותרת עליונה אלגנטית ומאוחדת -->
    <header class="top-header">
      <div>
        <a href="../" style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-secondary); text-decoration:none; margin-bottom:4px; transition:color 0.15s;" onmouseover="this.style.color='var(--gold)'" onmouseout="this.style.color='var(--text-secondary)'">← כל אוספי המלחינים</a>
        <h1 class="brand-title">
          {html.escape(cfg.playlist_title_he)}
          <span class="brand-count">{total_videos} ביצועים · {total_catalog_songs} שירים בקטלוג</span>
        </h1>
        <p class="subtitle">
          {html.escape(cfg.subtitle_he)}
        </p>
      </div>
      <div class="header-actions">
        <button id="playPlaylistBtn" class="btn btn-gold btn-hero-play" onclick="startPlaylistPlayback()">▶ נגן פלייליסט</button>{yt_playlist_btn_html}
      </div>
    </header>

    <!-- סרגל לשוניות ברור למעבר בין הפלייליסט המרכזי לארכיון המשלים -->
    <div id="topStatusRow" class="nav-bar" style="margin-bottom: 12px;">
      <div class="tabs-bar" role="tablist" aria-label="תצוגת אוסף">
        <button id="tabBtnYt" class="tab-btn active" type="button" role="tab" aria-selected="true" aria-controls="tabYtContent" onclick="switchTab('yt')">
          🎵 הפלייליסט המרכזי <span class="tab-count">({total_videos})</span>
        </button>
        <button id="tabBtnArch" class="tab-btn" type="button" role="tab" aria-selected="false" aria-controls="tabArchContent" onclick="switchTab('arch')">
          🏛️ ארכיון נדירים — ללא יוטיוב <span class="tab-count">({unmatched_songs_count})</span>
        </button>
      </div>
      <span id="ytCountChip" class="count-chip"></span>
    </div>

    <!-- לשונית 1: פלייליסט יוטיוב -->
    <div id="tabYtContent">
      <div class="search-hero" role="search">
        <div class="search-wrap search-wrap-hero">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <circle cx="11" cy="11" r="7.5"></circle>
            <line x1="20" y1="20" x2="16.4" y2="16.4"></line>
          </svg>
          <input type="text" id="searchInput" role="searchbox" aria-label="חיפוש שיר, מבצע, אלבום או שורת פתיחה" placeholder="חיפוש שיר, מבצע, אלבום או שורת פתיחה..." oninput="onSearchInput('yt')" />
          <span id="searchKbd" class="search-kbd" title="קיצור מקלדת לחיפוש">/</span>
          <button id="searchClearBtn" class="search-clear" type="button" onclick="clearSearch('yt')" title="נקה חיפוש (Esc)" aria-label="נקה חיפוש">✕</button>
        </div>
      </div>
      <div class="player-layout">
        <!-- כרטיס הנגן הדביק -->
        <div class="card sticky-player">
          <div id="failoverBanner" style="display:none; background:rgba(245,158,11,0.18); border:1px solid var(--gold); color:#fcd34d; padding:7px 10px; border-radius:8px; font-size:12.5px; margin-bottom:8px;"></div>
          <div id="ytFrameWrap" class="yt-frame-wrap">
            <div id="ytFrame"></div>
          </div>

          <div class="transport-bar">
            <button class="btn btn-outline btn-icon" type="button" onclick="playPrev()" title="השיר הקודם (P)">⏮</button>
            <button id="mainPlayPauseBtn" class="btn btn-outline btn-icon" type="button" onclick="togglePlayPause()" title="ניגון / השהיה (Space / K)">⏯</button>
            <button class="btn btn-outline btn-icon" type="button" onclick="playNext()" title="השיר הבא (N)">⏭</button>
            <button id="shuffleBtn" class="btn btn-outline btn-icon" type="button" onclick="toggleShuffle()" title="ניגון אקראי (S)">🔀</button>
            <button id="repeatBtn" class="btn btn-outline btn-icon" type="button" onclick="toggleRepeatOne()" aria-pressed="false" title="ניגון חוזר לשיר הנוכחי (R)">🔂</button>
            <button id="npShareBtn" class="btn btn-outline btn-icon" type="button" onclick="copyShareUrl()" title="שתף או העתק קישור ישיר לשיר זה">🔗</button>
            <a id="openOnYt" class="btn btn-outline btn-icon" href="#" target="_blank" rel="noopener" title="פתח ביוטיוב">↗ YT</a>
          </div>

          <div class="np-header">
            <div class="np-title-row">
              <div id="nowPlayingTitle">בחר שיר מהרשימה</div>
              <div class="np-title-actions">
                <button class="btn btn-outline btn-sm" type="button" onclick="scrollToActiveRow()" title="גלול לשיר המתנגן בטבלה">🎯</button>
                <button id="npFavBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleCurrentFavorite()" title="הוסף / הסר מהמועדפים (F)">♡</button>
              </div>
            </div>
            <div id="nowPlayingMeta"></div>
            <div id="nowPlayingRole" class="np-badges"></div>
            <div id="nowPlayingVersions" class="np-versions" style="display:none;"></div>
            <div id="nowPlayingQuote" class="quote-box" style="display:none;"></div>
            <div id="nowPlayingLinks" class="archive-pills" style="margin-bottom:6px;"></div>
          </div>

          <!-- פרטים משניים מוסתרים במגירה נקייה -->
          <details id="npDetails" class="np-details">
            <summary id="npDetailsSummary">⚙️ מקורות גיבוי וקיצורי מקלדת</summary>
            <div style="margin-top:8px; display:flex; flex-direction:column; gap:8px;">
              <div id="backupSourcesBox" style="display:none;">
                <label style="display:block; margin-bottom:4px; color:var(--text-secondary);">🛡️ החלף למקור גיבוי / ביצוע חלופי:</label>
                <select id="backupSelect" onchange="switchVideoSource(this.value)" style="width:100%; padding:6px 8px; font-size:12px;"></select>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                <button class="btn btn-outline btn-sm" onclick="scrollToActiveRow()">🎯 גלול לשיר המתנגן בטבלה</button>
                <span>קיצורים: <kbd>Space</kbd> השהיה · <kbd>N</kbd>/<kbd>P</kbd> מעבר · <kbd>S</kbd> אקראי · <kbd>R</kbd> חוזר · <kbd>F</kbd> מועדף · <kbd>/</kbd> חיפוש</span>
              </div>
            </div>
          </details>
        </div>

        <!-- כרטיס רשימת השירים -->
        <div class="card">
          <!-- שורת מיון וסינון מהיר -->
          <div class="toolbar">
            <select id="sortSelect" onchange="renderTable()">
              <option value="canonical">🌟 מיון: קלאסיקות תחילה</option>
              <option value="chrono_asc">📅 כרונולוגי (לפי שנת הקלטה)</option>
              <option value="chrono_desc">⏪ כרונולוגי הפוך</option>
              <option value="albums">💿 לפי אלבומים מקוריים</option>
              <option value="popularity">🔥 לפי תפוצה באקו"ם</option>
              <option value="title_asc">🔤 שם השיר (א'–ת')</option>
              <option value="perf_asc">🎤 שם המבצע (א'–ת')</option>
            </select>
            <select id="decadeFilter" onchange="renderTable()">
              <option value="ALL">כל העשורים ({total_videos})</option>
              <option value="1950s">שנות ה-50 ({decade_counts.get('1950s', 0)})</option>
              <option value="1960s">שנות ה-60 ({decade_counts.get('1960s', 0)})</option>
              <option value="1970s">שנות ה-70 ({decade_counts.get('1970s', 0)})</option>
              <option value="1980s">שנות ה-80 ({decade_counts.get('1980s', 0)})</option>
              <option value="1990s+">שנות ה-90+ ({decade_counts.get('1990s+', 0)})</option>
              <option value="unknown">ללא שנה ({decade_counts.get('unknown', 0)})</option>
            </select>
            <button id="onePerSongBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleOnePerSong()" aria-pressed="false" title="סנן לביצוע מוביל אחד לכל שיר (מדלג על גרסאות כפולות בלי למחוק אותן)">
              🎯 ביצוע אחד לכל שיר ({unique_songs_count})
            </button>
            <button id="favOnlyBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleFavOnly()" aria-pressed="false" title="הצג רק ביצועים שסימנת כמועדפים">
              ❤️ מועדפים (<span id="favCountSpan">0</span>)
            </button>
            <button id="advFilterBtn" class="btn btn-outline btn-sm" onclick="toggleAdvancedFilters()">
              ⚙️ סינון מתקדם <span id="activeFiltersBadge" style="display:none; background:var(--gold); color:#000; padding:0 6px; border-radius:999px; font-size:11px;"></span>
            </button>
          </div>

          <!-- מגירת סינון מתקדם (מוסתרת כברירת מחדל) -->
          <div id="advancedDrawer" class="advanced-drawer">
            <select id="tierFilter" onchange="renderTable()">
              <option value="ALL">כל סוגי הביצועים ({total_videos})</option>
              {tier_options_html}
            </select>
            <select id="roleFilter" onchange="renderTable()">
              <option value="ALL">כל תפקידי היצירה ({total_videos})</option>
              {role_options_html}
            </select>
            <button class="btn btn-outline btn-sm" onclick="resetAllFilters()" title="אפס את כל המסננים">↺ איפוס</button>
          </div>

          <!-- שורת תגיות מסננים פעילים -->
          <div id="activeFilterChips" class="active-chips-bar" style="display:none;"></div>

          <!-- ניווט מהיר בין בלוקים במיון קלאסיקות -->
          <div id="blockJumpBar" class="block-jump-bar" style="display:none;"></div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style="width:44px; text-align:center;">#</th>
                  <th>שיר</th>
                  <th>מבצע ואלבום</th>
                  <th style="width:84px; text-align:left;">אורך</th>
                </tr>
              </thead>
              <tbody id="songsBody"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- לשונית 2: ארכיון שירים נדירים שלא ביוטיוב -->
    <div id="tabArchContent" style="display:none;">
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
          <div>
            <h3 style="margin:0 0 4px; font-size:18px; color:#fff;">🏛️ ארכיון משלים: {unmatched_songs_count} שירים נדירים שאינם ביוטיוב</h3>
            <p style="margin:0; color:var(--muted); font-size:13.5px;">
              שירים שאותרו בספרייה הלאומית, אקו"ם, שירונט וזמרשת (הקלטות רדיו, שירי הצגות מוקדמים או כתבי יד) עם קישורים ישירים למילים ולהאזנה בארכיון.
            </p>
          </div>
          <span id="archCountChip" class="count-chip"></span>
        </div>
        <div class="search-hero" role="search">
          <div class="search-wrap search-wrap-hero">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="7.5"></circle>
              <line x1="20" y1="20" x2="16.4" y2="16.4"></line>
            </svg>
            <input type="text" id="archSearchInput" role="searchbox" aria-label="חיפוש בארכיון לפי שם שיר, שורת פתיחה או מבצע" placeholder="חיפוש בארכיון לפי שם שיר, שורת פתיחה או מבצע..." oninput="onSearchInput('arch')" />
            <span id="archSearchKbd" class="search-kbd" title="קיצור מקלדת לחיפוש">/</span>
            <button id="archSearchClearBtn" class="search-clear" type="button" onclick="clearSearch('arch')" title="נקה חיפוש (Esc)" aria-label="נקה חיפוש">✕</button>
          </div>
        </div>
        <div class="toolbar">
          <button id="archAudioOnlyBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleArchAudioOnly()" aria-pressed="false" title="סנן לשירים שקיימת עבורם הקלטת שמע פתוחה להאזנה חופשית באתר הספרייה הלאומית או בזמרשת">
            🎧 קיימת הקלטה להאזנה ({as_audio})
          </button>
          <select id="archRoleFilter" onchange="renderArchiveTable()">
            <option value="ALL">כל התפקידים ({unmatched_songs_count})</option>
            {arch_role_options_html}
          </select>
          <select id="archSourceFilter" onchange="renderArchiveTable()">
            <option value="ALL">כל המאגרים ({unmatched_songs_count})</option>
            <option value="nli">הספרייה הלאומית ({arch_src_counts.get('nli', 0)})</option>
            <option value="acum">אקו"ם ({arch_src_counts.get('acum', 0)})</option>
            <option value="shironet">שירונט ({arch_src_counts.get('shironet', 0)})</option>
            <option value="zemereshet">זמרשת ({arch_src_counts.get('zemereshet', 0)})</option>
          </select>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th style="width:44px;">#</th>
                <th>שיר ושנה</th>
                <th>מבצעים ותפקיד</th>
                <th>שורת פתיחה</th>
                <th>קישורים לארכיון</th>
              </tr>
            </thead>
            <tbody id="archiveBody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- פוטר שקט בתחתית העמוד למעבר לארכיון המשלים -->
    <footer style="margin-top: 24px; padding-top: 14px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; color: var(--muted); font-size: 13px;">
      <span>{html.escape(cfg.footer_label_he)} · {total_videos} ביצועים ביוטיוב</span>
      <button id="footerArchToggleBtn" class="btn btn-outline btn-sm arch-toggle-btn" onclick="switchTab(currentTab === 'yt' ? 'arch' : 'yt')">
        🏛️ מעבר לארכיון {unmatched_songs_count} שירים נדירים שאינם ביוטיוב
      </button>
    </footer>
  </div>

  <div id="miniPlayerBar" class="mini-player-bar" role="region" aria-label="נגן מוקטן">
    <div id="miniProgressWrap" class="mini-progress-wrap" onclick="seekFromMiniBar(event)" title="לחץ לדילוג לנקודה בשיר">
      <div id="miniProgressFill" class="mini-progress-fill"></div>
    </div>
    <div class="mini-player-inner">
      <div class="mini-song-info" onclick="scrollToTopPlayer()" title="חזרה לנגן הווידאו בראש העמוד">
        <img id="miniThumb" class="mini-thumb" src="" alt="" loading="lazy" />
        <div class="mini-text">
          <div id="miniTitle" class="mini-title">בחר שיר מהרשימה</div>
          <div class="mini-perf"><span id="miniTimeText" class="mini-time-text"></span><span id="miniPerf"></span></div>
        </div>
      </div>
      <div class="mini-controls">
        <button class="btn btn-outline btn-icon" type="button" onclick="playPrev()" title="השיר הקודם (P)">⏮</button>
        <button id="miniPlayBtn" class="btn btn-gold btn-icon" type="button" onclick="togglePlayPause()" title="ניגון / השהיה (Space / K)">▶</button>
        <button class="btn btn-outline btn-icon" type="button" onclick="playNext()" title="השיר הבא (N)">⏭</button>
        <button class="btn btn-outline btn-icon" type="button" onclick="scrollToActiveRow(true)" title="גלול לשיר המתנגן בטבלה">🎯</button>
        <button id="miniFavBtn" class="btn btn-outline btn-icon" type="button" onclick="toggleCurrentFavorite()" title="הוסף / הסר מהמועדפים (F)">♡</button>
        <button class="btn btn-outline btn-icon mini-hide-xs" type="button" onclick="copyShareUrl()" title="שתף או העתק קישור ישיר לשיר זה">🔗</button>
        <button class="btn btn-outline btn-sm" type="button" onclick="scrollToTopPlayer()" title="חזרה לנגן הווידאו">⬆ <span class="mini-back-lbl">לנגן</span></button>
      </div>
    </div>
  </div>
  <div id="shareToast" class="share-toast" role="status" aria-live="polite">✔ הקישור הישיר לשיר הועתק!</div>

  {script_block}
</body>
</html>
"""


def build_composer(slug: str, standalone: bool = False, rebuild_hub: bool = True) -> dict[str, Any]:
    """Normalize playlist, build thin HTML + playlist_data.js, browser scripts, exports, and optional Hub."""
    cfg = load_composer(slug)
    playlist_json_path = cfg.playlist_json
    data = json.loads(playlist_json_path.read_text(encoding="utf-8"))

    if validate_and_normalize_playlist(data, cfg):
        playlist_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    playlist = data["playlist"]
    matched_entries = [item for item in playlist if item.get("selected_video")]
    unmatched_entries = [item for item in playlist if not item.get("selected_video")]

    total_videos = len(matched_entries)
    unmatched_songs_count = len(unmatched_entries)
    total_catalog_songs = len({item["title"] for item in playlist})

    browser_paths = generate_browser_scripts(matched_entries, cfg)
    songs_js, archive_songs_js, counts = _build_songs_and_archive_payloads(matched_entries, unmatched_entries, cfg)

    config_payload: dict[str, Any] = {
        "slug": cfg.slug,
        "name_he": cfg.name_he,
        "collection_prefix_he": cfg.collection_prefix_he,
        "storage_prefix": cfg.storage_prefix,
        "is_performer": cfg.is_performer,
        "creator_album_tiers": cfg.creator_album_tiers,
    }
    if cfg.block_meta:
        config_payload["block_meta"] = cfg.block_meta
    if cfg.jump_groups:
        config_payload["jump_groups"] = cfg.jump_groups

    playlist_data_obj = {
        "config": config_payload,
        "songs": songs_js,
        "archiveSongs": archive_songs_js,
    }
    safe_pd_json = json.dumps(playlist_data_obj, ensure_ascii=False, indent=2).replace("</script>", "<\\/script>")
    cfg.playlist_data_js.write_text(f"window.PLAYLIST_DATA = {safe_pd_json};\n", encoding="utf-8")

    thin_html = _render_player_html(
        cfg,
        playlist_data_obj,
        counts,
        total_videos=total_videos,
        unmatched_songs_count=unmatched_songs_count,
        total_catalog_songs=total_catalog_songs,
        standalone=False,
    )
    cfg.index_html.write_text(thin_html, encoding="utf-8")

    generated_paths: list[Path] = [*browser_paths, cfg.playlist_data_js, cfg.index_html]
    legacy_path = cfg.legacy_player_html
    if legacy_path:
        legacy_html = (
            _render_player_html(
                cfg,
                playlist_data_obj,
                counts,
                total_videos=total_videos,
                unmatched_songs_count=unmatched_songs_count,
                total_catalog_songs=total_catalog_songs,
                standalone=True,
            )
            if standalone
            else thin_html
        )
        legacy_path.write_text(legacy_html, encoding="utf-8")
        generated_paths.append(legacy_path)

    secondary_paths = sync_all_secondary_exports(data, cfg)
    generated_paths.extend(secondary_paths)

    if rebuild_hub:
        generated_paths.append(build_hub())

    print(f"עודכנו בהצלחה כל קובצי המלחין ({cfg.slug}):")
    for idx_p, p in enumerate(generated_paths, 1):
        print(f"  {idx_p}. {p}")

    return {
        "slug": cfg.slug,
        "total_videos": total_videos,
        "unmatched_songs": unmatched_songs_count,
        "total_catalog_songs": total_catalog_songs,
        "paths": [str(p) for p in generated_paths],
    }


def _read_composer_counts(cfg: ComposerConfig) -> tuple[int, int, int, int]:
    """Read matched_videos, matched_songs, unmatched_songs, total_songs for a composer."""
    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    stats = data.get("stats") or {}
    if all(k in stats for k in ("matched_videos", "matched_songs", "unmatched_songs", "total_songs")):
        return (
            int(stats["matched_videos"]),
            int(stats["matched_songs"]),
            int(stats["unmatched_songs"]),
            int(stats["total_songs"]),
        )
    playlist = data.get("playlist", [])
    matched = [x for x in playlist if x.get("selected_video")]
    unmatched = [x for x in playlist if not x.get("selected_video")]
    return (
        len(matched),
        len({x["title"] for x in matched}),
        len(unmatched),
        len({x["title"] for x in playlist}),
    )


def build_hub() -> Path:
    """Render root playlists/index.html dynamically from creators.json and composer configs."""
    reg = load_registry()
    base_url = reg.get("base_url", "https://dmtsurel.github.io/playlists").rstrip("/") + "/"
    repo_url = reg.get("repo_url", "https://github.com/DMTsurel/playlists")

    cards_html: list[str] = []
    for entry in reg.get("creators", []):
        if not entry.get("enabled", True):
            continue
        cfg = load_composer(entry["slug"])
        matched_videos, matched_songs, unmatched_songs, total_songs = _read_composer_counts(cfg)
        desc = cfg.hub_description_he.format(
            matched_videos=matched_videos,
            matched_songs=matched_songs,
            unmatched_songs=unmatched_songs,
            total_songs=total_songs,
        )
        yt_btn = (
            f'\n          <a class="btn btn-outline" href="https://www.youtube.com/playlist?list={html.escape(cfg.youtube_playlist_id)}" target="_blank" rel="noopener">פלייליסט ב-YouTube ↗</a>'
            if cfg.youtube_playlist_id
            else ""
        )
        cards_html.append(
            f"""      <article class="card">
        <span class="badge">{matched_videos} ביצועים · {total_songs} שירים בקטלוג</span>
        <h2>{html.escape(cfg.name_he)}</h2>
        <p>
          {html.escape(desc)}
        </p>
        <div class="actions">
          <a class="btn btn-gold" href="./{html.escape(cfg.slug)}/">▶ פתח את נגן {html.escape(cfg.name_he)}</a>{yt_btn}
        </div>
      </article>"""
        )

    if reg.get("show_coming_soon_card", True):
        cards_html.append(
            """      <article class="card card-placeholder">
        <span class="badge badge-muted">בפיתוח</span>
        <h2>מלחינים נוספים — בקרוב</h2>
        <p>
          התשתית בנויה להוספה נקייה של אוספים וקטלוגים דומים למלחינים ויוצרים ישראלים נוספים תחת כתובת זו.
        </p>
      </article>"""
        )

    cards_joined = "\n\n".join(cards_html)
    hub_html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(reg.get("site_title_he", "אוספי מלחינים ישראלים — נגן אינטראקטיבי וקטלוג"))}</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230b1220' stroke='%23f5b942' stroke-width='3'/%3E%3Ctext x='32' y='45' font-size='36' text-anchor='middle' fill='%23f5b942'%3E%E2%99%AB%3C/text%3E%3C/svg%3E" />
  <meta property="og:title" content="{html.escape(reg.get("site_title_he", "אוספי מלחינים ישראלים — נגן אינטראקטיבי וקטלוג"))}" />
  <meta property="og:description" content="פלייליסטים מקיפים ומקוטלגים ממאגרי אקו&quot;ם, הספרייה הלאומית, שירונט, זמרשת ועוד." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{html.escape(base_url)}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@600;700;800&family=Heebo:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg: #0b1220;
      --bg-grad: #0f172a;
      --surface: #162033;
      --surface-hover: #1d2a42;
      --border: rgba(255, 255, 255, 0.1);
      --gold: #f5b942;
      --gold-dim: rgba(245, 185, 66, 0.14);
      --text: #f1f5f9;
      --text-secondary: #94a3b8;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0;
      padding: 0;
      min-height: 100%;
      background: radial-gradient(circle at top center, #17253d 0%, var(--bg-grad) 45%, var(--bg) 100%);
      color: var(--text);
      font-family: "Heebo", system-ui, -apple-system, sans-serif;
      overflow-x: clip;
    }}
    .wrap {{
      max-width: 1040px;
      margin: 0 auto;
      padding: clamp(24px, 4vw, 52px) clamp(16px, 3vw, 28px) 48px;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header.hub-header {{
      margin-bottom: clamp(24px, 4vw, 40px);
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12.5px;
      font-weight: 600;
      color: var(--gold);
      background: var(--gold-dim);
      border: 1px solid rgba(245, 185, 66, 0.3);
      padding: 4px 12px;
      border-radius: 999px;
      margin-bottom: 12px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-family: "Frank Ruhl Libre", "Heebo", Georgia, serif;
      font-size: clamp(28px, 4.4vw, 42px);
      font-weight: 800;
      line-height: 1.15;
      color: #ffffff;
    }}
    .lead {{
      margin: 0;
      max-width: 68ch;
      color: var(--text-secondary);
      font-size: clamp(14.5px, 1.5vw, 16.5px);
      line-height: 1.6;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr));
      gap: 20px;
      flex: 1 0 auto;
      align-items: start;
    }}
    .card {{
      min-width: 0;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28);
      display: flex;
      flex-direction: column;
      gap: 14px;
      transition: transform 0.18s ease, border-color 0.18s ease;
    }}
    .card:hover {{
      transform: translateY(-2px);
      border-color: rgba(245, 185, 66, 0.35);
    }}
    .card-placeholder {{
      background: rgba(22, 32, 51, 0.45);
      border: 1px dashed rgba(148, 163, 184, 0.28);
      box-shadow: none;
    }}
    .card-placeholder:hover {{
      transform: none;
      border-color: rgba(148, 163, 184, 0.4);
    }}
    .badge {{
      align-self: flex-start;
      font-size: 12.5px;
      font-weight: 600;
      color: var(--gold);
      background: var(--gold-dim);
      border: 1px solid rgba(245, 185, 66, 0.28);
      border-radius: 999px;
      padding: 4px 11px;
    }}
    .badge-muted {{
      color: var(--text-secondary);
      background: rgba(148, 163, 184, 0.12);
      border-color: rgba(148, 163, 184, 0.22);
    }}
    .card h2 {{
      margin: 0;
      font-family: "Frank Ruhl Libre", "Heebo", Georgia, serif;
      font-size: clamp(22px, 2.5vw, 27px);
      font-weight: 700;
      color: #ffffff;
    }}
    .card p {{
      margin: 0;
      color: var(--text-secondary);
      font-size: 14.5px;
      line-height: 1.6;
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 6px;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 10px 16px;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 600;
      text-decoration: none;
      cursor: pointer;
      transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
    }}
    .btn-gold {{
      background: var(--gold);
      color: #0b1220;
      border: 1px solid var(--gold);
    }}
    .btn-gold:hover {{
      background: #f8c660;
    }}
    .btn-outline {{
      background: transparent;
      color: var(--text);
      border: 1px solid rgba(255, 255, 255, 0.18);
    }}
    .btn-outline:hover {{
      border-color: var(--gold);
      color: var(--gold);
    }}
    footer.hub-footer {{
      margin-top: 40px;
      padding-top: 18px;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      font-size: 13px;
      color: var(--text-secondary);
    }}
    footer.hub-footer a {{
      color: var(--gold);
      text-decoration: none;
    }}
    footer.hub-footer a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hub-header">
      <span class="eyebrow">{html.escape(reg.get("site_eyebrow_he", "♫ ארכיון ונגני מוזיקה עברית"))}</span>
      <h1>{html.escape(reg.get("site_heading_he", "אוספי מלחינים ישראלים"))}</h1>
      <p class="lead">
        {html.escape(reg.get("site_lead_he", ""))}
      </p>
    </header>

    <main class="grid">
{cards_joined}
    </main>

    <footer class="hub-footer">
      <span>DMTsurel Playlists · GitHub Pages</span>
      <a href="{html.escape(repo_url)}" target="_blank" rel="noopener">קוד המאגר והנתונים ב-GitHub ↗</a>
    </footer>
  </div>
</body>
</html>
"""
    hub_path = REPO_ROOT / "index.html"
    hub_path.write_text(hub_html, encoding="utf-8")
    return hub_path


def build_all(standalone: bool = False) -> list[dict[str, Any]]:
    """Rebuild every enabled composer in creators.json and regenerate the root Hub."""
    results = [build_composer(slug, standalone=standalone, rebuild_hub=False) for slug in list_enabled_slugs()]
    build_hub()
    return results
