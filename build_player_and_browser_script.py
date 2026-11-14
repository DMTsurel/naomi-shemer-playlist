#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה את קובץ הסקריפט לדפדפן (create_playlist_in_browser.js)
ואת הנגן האינטראקטיבי המלא (naomi_shemer_playlist_player.html)
מתוך naomi_shemer_youtube_playlist.json.
"""

import csv
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _parse_duration_seconds(dur_str: str) -> int:
    if not dur_str:
        return -1
    parts = [p for p in str(dur_str).strip().split(":") if p.isdigit()]
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return -1


def _clean_artist_name(item: dict, sel: dict) -> str:
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


def sync_all_secondary_exports(data: dict) -> list:
    """מייצר ומסנכרן את כל קובצי הפלט המשניים (CSV, MD, M3U8, Streaming CSV, Wayback URLs)."""
    playlist = data["playlist"]
    matched = [x for x in playlist if x.get("selected_video")]
    csv_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.csv")
    md_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.md")
    stream_csv_path = os.path.join(BASE_DIR, "naomi_shemer_streaming_import.csv")
    m3u8_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_stream.m3u8")
    wayback_path = os.path.join(BASE_DIR, "wayback_backup_urls.txt")

    # 1. naomi_shemer_youtube_playlist.csv
    fieldnames = [
        "index", "chrono_index", "canonical_layer", "canonical_score", "title",
        "year", "role_category", "role_label_heb", "lyricist", "composer",
        "translator", "tier", "tier_label", "matched_performer", "matched_album",
        "album_group", "album_track_number", "video_id", "video_url",
        "video_title", "channel", "duration", "views", "opening_line", "notes"
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for item in playlist:
            sel = item.get("selected_video") or {}
            notes_val = item.get("notes", [])
            if isinstance(notes_val, list):
                notes_str = " | ".join(str(x) for x in notes_val)
            else:
                notes_str = str(notes_val or "")
            w.writerow({
                "index": item.get("index", ""),
                "chrono_index": item.get("chrono_index", ""),
                "canonical_layer": item.get("canonical_layer", ""),
                "canonical_score": item.get("canonical_score", ""),
                "title": item.get("title", ""),
                "year": item.get("year", ""),
                "role_category": item.get("role_category", ""),
                "role_label_heb": item.get("role_label_heb", ""),
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
                "notes": notes_str,
            })

    # 2. naomi_shemer_youtube_playlist.md
    md_lines = [
        f"# פלייליסט שירי נעמי שמר ביוטיוב ({len(matched)} ביצועים)",
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
            f"| {i} | {yr} | **{item['title']}** | {item.get('role_label_heb','')} | "
            f"{item.get('tier_label','')} | {perf} | [{vtitle}](https://www.youtube.com/watch?v={vid}) | {sel.get('duration','')} |"
        )
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    # 3. naomi_shemer_streaming_import.csv
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
            alb = item.get("album_group") or sel.get("matched_album") or ""
            artist = _clean_artist_name(item, sel)
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

    # 4. naomi_shemer_youtube_stream.m3u8
    m3u_lines = [
        "#EXTM3U",
        f"#PLAYLIST:שירי נעמי שמר – האוסף המקיף ({len(matched)} ביצועים ביוטיוב)",
    ]
    for item in matched:
        sel = item["selected_video"]
        vid = sel["video_id"]
        sec = _parse_duration_seconds(sel.get("duration", ""))
        artist = _clean_artist_name(item, sel)
        title = item.get("title", "")
        yr = item.get("year", "")
        yr_str = f" ({yr})" if (yr and str(yr) != "2099") else ""
        m3u_lines.append(f"#EXTINF:{sec},{artist} - {title}{yr_str}")
        m3u_lines.append(f"https://www.youtube.com/watch?v={vid}")
    with open(m3u8_path, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    # 5. wayback_backup_urls.txt
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
    with open(wayback_path, "w", encoding="utf-8") as f:
        f.write("\n".join(urls) + "\n")

    return [csv_path, md_path, stream_csv_path, m3u8_path, wayback_path]


def get_decade(year_str: str) -> str:
    if not year_str:
        return "unknown"
    m = re.match(r"^(\d{4})$", str(year_str).strip())
    if not m:
        return "unknown"
    yr = int(m.group(1))
    if yr >= 2099:
        return "unknown"
    if yr < 1960:
        return "1950s"
    if yr < 1970:
        return "1960s"
    if yr < 1980:
        return "1970s"
    if yr < 1990:
        return "1980s"
    return "1990s+"


def validate_and_normalize_playlist(data: dict) -> bool:
    """מנרמל ערכי tier, מחשב מחדש אינדקסים, dual_role וסטטיסטיקות, ומוודא שלמות נתונים."""
    playlist = data.get("playlist", [])
    tier_norm = {
        "1_naomi_album": ("1_album_naomi", "1. אלבום של נעמי שמר"),
        "5_cover_version": ("5_cover", "5. קאבר / ביצוע נוסף"),
        "6_no_youtube": ("6_not_found", "6. לא נמצא סרטון תואם"),
    }
    valid_matched_tiers = {
        "1_album_naomi",
        "2_album_original",
        "3_naomi_performance",
        "4_original_performance",
        "5_cover",
    }

    changed = False
    matched_entries = []
    unmatched_entries = []
    seen_primary_vids = {}
    by_title = {}

    for item in playlist:
        t = item.get("tier", "")
        if t in tier_norm:
            item["tier"], item["tier_label"] = tier_norm[t]
            changed = True
        sel = item.get("selected_video")
        if sel and sel.get("video_id"):
            st = sel.get("tier", "")
            if st in tier_norm:
                sel["tier"], sel["tier_label"] = tier_norm[st]
                changed = True
            matched_entries.append(item)
            by_title.setdefault(item["title"], []).append(item)
        else:
            if item.get("tier") != "6_not_found":
                item["tier"] = "6_not_found"
                item["tier_label"] = "6. לא נמצא סרטון תואם"
                changed = True
            unmatched_entries.append(item)

    # Recompute dual_role and version numbering per song
    for title, group in by_title.items():
        total_v = len(group)
        for idx_in_group, it in enumerate(group):
            it["ver_idx"] = idx_in_group + 1
            it["ver_total"] = total_v
            if total_v == 1:
                if "dual_role" in it:
                    del it["dual_role"]
                    changed = True
            else:
                if idx_in_group == 0:
                    new_role = "original_performance"
                elif it.get("tier") in ("1_album_naomi", "3_naomi_performance"):
                    new_role = "naomi_performance"
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

    # Integrity validation checks
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
        print("⚠️ אזהרות שלמות נתונים:")
        for e in errors:
            print("  -", e)
    else:
        print(f"✔ בדיקת שלמות נתונים עברה בהצלחה ({len(matched_entries)} סרטונים ייחודיים, 0 שגיאות).")

    data["playlist"] = ordered
    stats = data.setdefault("stats", {})
    matched_songs_cnt = len(by_title)
    total_songs_cnt = len({it["title"] for it in ordered})
    if stats.get("matched_videos") != len(matched_entries) or stats.get("matched_songs") != matched_songs_cnt:
        changed = True
    stats["total_songs"] = total_songs_cnt
    stats["total_catalog_songs"] = total_songs_cnt
    stats["matched_songs"] = matched_songs_cnt
    stats["unmatched_songs"] = len(unmatched_entries)
    stats["total_playlist_videos"] = len(matched_entries)
    stats["total_videos"] = len(matched_entries)
    stats["matched_videos"] = len(matched_entries)
    stats["total_playlist_entries"] = len(ordered)
    return changed


def generate_files():
    playlist_json_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.json")
    with open(playlist_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if validate_and_normalize_playlist(data):
        with open(playlist_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    playlist = data["playlist"]

    matched_entries = [item for item in playlist if item.get("selected_video")]
    unmatched_entries = [item for item in playlist if not item.get("selected_video")]

    total_videos = len(matched_entries)
    matched_songs_count = len({item["title"] for item in matched_entries})
    unmatched_songs_count = len(unmatched_entries)
    total_catalog_songs = len({item["title"] for item in playlist})

    video_ids = [item["selected_video"]["video_id"] for item in matched_entries]

    # 1. יצירת create_playlist_in_browser.js
    js_script = f"""// ============================================================================
// יצירת פלייליסט "שירי נעמי שמר - האוסף המקיף" ({total_videos} ביצועים) בחשבון היוטיוב שלך
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com בדפדפן וודא שאתה מחובר לחשבון היוטיוב שלך.
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console של הדפדפן.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// תוך כ-10 שניות הפלייליסט ייווצר וייפתח אוטומטית!
// ============================================================================
(async function createNaomiShemerPlaylist() {{
  const VIDEO_IDS = {json.dumps(video_ids, ensure_ascii=False)};
  const PLAYLIST_TITLE = "שירי נעמי שמר";
  const PLAYLIST_DESC = "אוסף מקיף של שירי נעמי שמר (אלבומיה של נעמי שמר, ביצועים מקוריים מתוך אלבומים, הקלטות ארכיון וקאברים נבחרים). נוצר מתוך איחוד 9 מאגרים (אקו\\"ם, הספרייה הלאומית, שירונט, ויקיפדיה, סטריאו ומונו, פזמונט, זמרשת, Discogs ו-MusicBrainz).";

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

    js_path = os.path.join(BASE_DIR, "create_playlist_in_browser.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_script)

    # 1b. יצירת update_existing_playlist_in_browser.js (עדכון הפלייליסט הקיים PLFHErlX6i22g + וידוא מלא מול שרתי יוטיוב)
    vid_to_title = {item["selected_video"]["video_id"]: f"{item['title']} ({item.get('year','')})" for item in matched_entries}
    update_js_script = f"""// ============================================================================
// עדכון הפלייליסט הקיים ביוטיוב (PLFHErlX6i22g) + וידוא אוטומטי של הסדר הסופי!
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com/playlist?list=PLFHErlX6i22g בדפדפן (מחובר לחשבון שלך).
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// הסקריפט יעדכן את הפלייליסט הקיים (PLFHErlX6i22g), ובסיום יקרא מחדש את כל הרצועות
// משרתי יוטיוב כדי לוודא ב-100% שהסידור הסופי תואם לרשימת היעד (ויתקן אוטומטית כל סטייה).
// ============================================================================
(async function updateExistingNaomiShemerPlaylist() {{
  const PLAYLIST_ID = "PLFHErlX6i22g";
  const PLAYLIST_TITLE = "שירי נעמי שמר";
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

  // שליפת כל הסרטונים הקיימים כרגע בפלייליסט (תומך הן ב-lockupViewModel החדש והן ב-playlistVideoRenderer הישן)
  function findSetVideoId(node, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 12) return null;
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

  function extractVideosAndContinuation(obj, itemsOut, tokensOut, seenTokens) {{
    if (!obj || typeof obj !== "object") return;
    if (Array.isArray(obj)) {{
      for (const el of obj) extractVideosAndContinuation(el, itemsOut, tokensOut, seenTokens);
      return;
    }}
    if (obj.playlistVideoRenderer) {{
      const r = obj.playlistVideoRenderer;
      const svid = r.setVideoId || findSetVideoId(r) || null;
      if (r.videoId || svid) {{
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
      if ((vid && (lv.contentType === "LOCKUP_CONTENT_TYPE_VIDEO" || !lv.contentType)) || svid) {{
        itemsOut.push({{
          videoId: vid || null,
          setVideoId: svid
        }});
      }}
      return;
    }}
    if (obj.continuationItemRenderer) {{
      const tok = obj.continuationItemRenderer?.continuationEndpoint?.continuationCommand?.token;
      if (tok && !seenTokens.has(tok)) {{
        seenTokens.add(tok);
        tokensOut.push(tok);
      }}
      return;
    }}
    if (obj.continuationItemViewModel) {{
      const civ = obj.continuationItemViewModel;
      const tok =
        civ?.continuationCommand?.innertubeCommand?.continuationCommand?.token ||
        civ?.continuationEndpoint?.continuationCommand?.token;
      if (tok && !seenTokens.has(tok)) {{
        seenTokens.add(tok);
        tokensOut.push(tok);
      }}
      return;
    }}
    for (const k of Object.keys(obj)) {{
      extractVideosAndContinuation(obj[k], itemsOut, tokensOut, seenTokens);
    }}
  }}

  async function fetchCurrentPlaylistItems() {{
    const items = [];
    const tokens = [];
    const seenTokens = new Set();
    const firstPage = await ytPost("/youtubei/v1/browse", {{ browseId: "VL" + PLAYLIST_ID }});
    extractVideosAndContinuation(firstPage, items, tokens, seenTokens);
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

  // עדכון שם הפלייליסט ל-"שירי נעמי שמר"
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
    extractVideosAndContinuation(window.ytInitialData, pageItems, dummyTokens, new Set());
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
        await ytPost("/youtubei/v1/browse/edit_playlist", {{
          playlistId: PLAYLIST_ID,
          actions: batch
        }});
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
        await ytPost("/youtubei/v1/browse/edit_playlist", {{
          playlistId: PLAYLIST_ID,
          actions: batch
        }});
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
  console.log("🔎 מבצע וידוא סופי של סדר השירים מול שרתי יוטיוב...");
  await new Promise(r => setTimeout(r, 1500));
  let finalItems = await fetchCurrentPlaylistItems();
  let finalIds = finalItems.map(x => x.videoId);

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
      await ytPost("/youtubei/v1/browse/edit_playlist", {{
        playlistId: PLAYLIST_ID,
        actions: batch
      }});
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
    update_js_path = os.path.join(BASE_DIR, "update_existing_playlist_in_browser.js")
    with open(update_js_path, "w", encoding="utf-8") as f:
        f.write(update_js_script)

    # 2. בניית נתוני SONGS ו-ARCHIVE_SONGS עבור ה-HTML
    def norm_notes(val) -> list:
        if not val:
            return []
        if isinstance(val, list):
            return [str(x).strip() for x in val if str(x).strip()]
        if isinstance(val, str):
            return [val.strip()] if val.strip() else []
        return []

    songs_js = []
    tier_counts = {}
    role_counts = {}
    decade_counts = {}
    layer_counts = {1: 0, 2: 0, 3: 0}

    for item in matched_entries:
        sel = item["selected_video"]
        yr = item.get("year", "")
        yr_display = yr if (yr and str(yr) != "2099") else ""
        dual_role = item.get("dual_role", "")
        if dual_role == "original_performance":
            role_suffix = " [ביצוע מקורי]"
        elif dual_role == "naomi_performance":
            role_suffix = " [ביצוע נעמי שמר]"
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
        layer_counts[lyr] = layer_counts.get(lyr, 0) + 1
        lyr_label = item.get("canonical_layer_label", "")

        ag = item.get("album_group", "")
        trk = item.get("album_track_number", "")
        alb_str = f"{ag} (#{trk})" if (ag and trk) else (ag or sel.get("matched_album", ""))

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
            "title": display_title,
            "raw_title": item["title"],
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
            "role_label": item.get("role_label_heb", "מילים ולחן: נעמי שמר"),
            "opening_line": item.get("opening_line", ""),
            "notes": norm_notes(item.get("notes", [])),
            "links": item.get("archive_links", []),
            "alts": alts_list,
        })

    archive_songs_js = []
    arch_role_counts = {}
    arch_src_counts = {}
    for item in unmatched_entries:
        yr = item.get("year", "")
        yr_display = yr if (yr and str(yr) != "2099") else "ללא שנה"
        rcat = item.get("role_category", "words_and_music")
        arch_role_counts[rcat] = arch_role_counts.get(rcat, 0) + 1
        for lk in item.get("archive_links", []):
            src_key = lk.get("source", "")
            if src_key:
                arch_src_counts[src_key] = arch_src_counts.get(src_key, 0) + 1
        archive_songs_js.append({
            "n": item["index"],
            "title": item["title"],
            "alt_titles": item.get("alt_titles", []),
            "year": yr_display,
            "role_cat": rcat,
            "role_label": item.get("role_label_heb", "מילים ולחן: נעמי שמר"),
            "perfs": ", ".join(item.get("catalog_performers", [])[:5]),
            "albums": ", ".join(item.get("catalog_albums", [])[:3]),
            "opening_line": item.get("opening_line", ""),
            "notes": norm_notes(item.get("notes", [])),
            "sources": item.get("sources", []),
            "links": item.get("archive_links", []),
        })

    ar_wm = arch_role_counts.get("words_and_music", 0)
    ar_m = arch_role_counts.get("music_only", 0)
    ar_w = arch_role_counts.get("words_only", 0)
    ar_t = arch_role_counts.get("translation", 0)
    ar_p = arch_role_counts.get("performance_only", 0)

    as_nli = arch_src_counts.get("nli", 0)
    as_acum = arch_src_counts.get("acum", 0)
    as_shir = arch_src_counts.get("shironet", 0)

    t1 = tier_counts.get("1_album_naomi", 0)
    t2 = tier_counts.get("2_album_original", 0)
    t3 = tier_counts.get("3_naomi_performance", 0)
    t4 = tier_counts.get("4_original_performance", 0)
    t5 = tier_counts.get("5_cover", 0)

    r_wm = role_counts.get("words_and_music", 0)
    r_m = role_counts.get("music_only", 0)
    r_w = role_counts.get("words_only", 0)
    r_t = role_counts.get("translation", 0)
    r_p = role_counts.get("performance_only", 0)

    d_50 = decade_counts.get("1950s", 0)
    d_60 = decade_counts.get("1960s", 0)
    d_70 = decade_counts.get("1970s", 0)
    d_80 = decade_counts.get("1980s", 0)
    d_90 = decade_counts.get("1990s+", 0)
    d_unk = decade_counts.get("unknown", 0)

    l1 = layer_counts.get(1, 0)
    l2 = layer_counts.get(2, 0)
    l3 = layer_counts.get(3, 0)
    unique_songs_count = sum(1 for item in songs_js if item.get("ver_idx") == 1)

    html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>שירי נעמי שמר – האוסף המקיף ({total_videos} ביצועים ביוטיוב + {unmatched_songs_count} שירי ארכיון)</title>
  <meta name="description" content="האוסף הכרונולוגי המקיף של שירי נעמי שמר ({total_catalog_songs} שירים מאוחדים מ-9 מאגרים): {total_videos} ביצועים מקוריים ביוטיוב ו-{unmatched_songs_count} שירי ארכיון נדירים עם קישורים לספרייה הלאומית, שירונט, זמרשת ואקו&quot;ם." />
  <meta property="og:title" content="שירי נעמי שמר – האוסף המקיף ({total_videos} ביצועים + {unmatched_songs_count} שירי ארכיון)" />
  <meta property="og:description" content="נגן אינטראקטיבי וקטלוג כרונולוגי מלא של כל {total_catalog_songs} שירי נעמי שמר: אלבומים מקוריים, ביצועי נעמי שמר, תרגומים וארכיון הספרייה הלאומית." />
  <meta property="og:type" content="website" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@600;700;800&family=Heebo:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b1120;
      --bg-grad: radial-gradient(1200px 600px at 85% -10%, rgba(245, 158, 11, 0.10), transparent 60%),
                 radial-gradient(1000px 500px at 10% 0%, rgba(56, 189, 248, 0.08), transparent 55%),
                 #0b1120;
      --card: rgba(22, 32, 51, 0.85);
      --card-solid: #162033;
      --card-hover: rgba(38, 53, 77, 0.55);
      --border: rgba(148, 163, 184, 0.14);
      --border-strong: rgba(148, 163, 184, 0.25);
      --text: #f8fafc;
      --text-secondary: #cbd5e1;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --gold: #f59e0b;
      --gold-soft: #fbbf24;
      --green: #10b981;
      --purple: #c084fc;
      --rose: #fb7185;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Heebo", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg-grad);
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 20px 24px 36px;
      min-height: 100vh;
    }}
    .container {{ max-width: 1420px; margin: 0 auto; }}

    /* Top Header */
    .top-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 18px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }}
    .brand-title {{
      font-family: "Frank Ruhl Libre", Georgia, serif;
      margin: 0 0 4px;
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.3px;
      color: #fff;
      display: flex;
      align-items: baseline;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .brand-count {{
      font-family: "Heebo", sans-serif;
      font-size: 14px;
      font-weight: 500;
      color: var(--gold-soft);
      background: rgba(245, 158, 11, 0.12);
      border: 1px solid rgba(245, 158, 11, 0.28);
      padding: 2px 10px;
      border-radius: 999px;
    }}
    .subtitle {{
      color: var(--muted);
      margin: 0;
      font-size: 14px;
      max-width: 780px;
    }}
    .header-actions {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}

    /* Cards */
    .card {{
      background: var(--card);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 12px 32px -8px rgba(0, 0, 0, 0.35);
    }}

    /* Buttons */
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      padding: 9px 15px;
      border-radius: 10px;
      border: 1px solid transparent;
      font-family: inherit;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease;
      white-space: nowrap;
    }}
    .btn:hover {{ transform: translateY(-1px); }}
    .btn-gold {{
      background: linear-gradient(135deg, #f59e0b, #fbbf24);
      color: #0f172a;
      font-weight: 700;
      box-shadow: 0 4px 14px rgba(245, 158, 11, 0.25);
    }}
    .btn-gold:hover {{ box-shadow: 0 6px 18px rgba(245, 158, 11, 0.35); }}
    .btn-outline {{
      background: rgba(15, 23, 42, 0.55);
      color: var(--text-secondary);
      border-color: var(--border-strong);
    }}
    .btn-outline:hover {{
      color: #fff;
      border-color: var(--accent);
      background: rgba(56, 189, 248, 0.10);
    }}
    .btn-outline.btn-active {{
      background: rgba(245, 158, 11, 0.2);
      color: var(--gold-soft);
      border-color: var(--gold);
    }}
    .btn-sm {{ padding: 6px 11px; font-size: 12.5px; border-radius: 8px; }}
    .btn-icon {{ padding: 8px 12px; font-size: 14px; }}
    .btn-hero-play {{
      padding: 11px 22px;
      font-size: 15px;
      border-radius: 12px;
      box-shadow: 0 6px 20px rgba(245, 158, 11, 0.32);
    }}
    .unmute-banner {{
      display: none;
      width: 100%;
      background: rgba(245, 158, 11, 0.16);
      border: 1px solid var(--gold);
      color: #fde68a;
      padding: 8px 12px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 10px;
      cursor: pointer;
      text-align: center;
      font-family: inherit;
    }}
    .unmute-banner:hover {{
      background: rgba(245, 158, 11, 0.28);
      color: #fff;
    }}

    /* Top Bar: Tabs + Search + Quick Filters */
    .nav-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .tabs-bar {{
      display: inline-flex;
      background: rgba(15, 23, 42, 0.75);
      padding: 4px;
      border-radius: 12px;
      border: 1px solid var(--border);
      gap: 4px;
    }}
    .tab-btn {{
      background: transparent;
      color: var(--muted);
      border: none;
      padding: 8px 16px;
      border-radius: 9px;
      font-family: inherit;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .tab-btn:hover {{ color: var(--text); }}
    .tab-btn.active {{
      background: var(--card-solid);
      color: var(--gold-soft);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }}

    /* Layout */
    .player-layout {{
      display: grid;
      grid-template-columns: 390px 1fr;
      gap: 20px;
      align-items: start;
    }}
    @media (max-width: 1080px) {{
      .player-layout {{ grid-template-columns: 1fr; }}
    }}
    .sticky-player {{ position: sticky; top: 16px; }}
    .yt-frame-wrap {{
      width: 100%;
      aspect-ratio: 16/9;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid var(--border);
      background: #000;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }}
    .yt-frame-wrap iframe, #ytFrame {{
      width: 100%;
      height: 100%;
      border: none;
      display: block;
    }}
    @media (max-width: 768px) {{
      .container {{ padding: 12px 10px 32px; }}
      .sticky-player {{
        position: sticky;
        top: 6px;
        z-index: 25;
        padding: 10px 12px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.65);
      }}
      .yt-frame-wrap {{ max-height: 185px; }}
      #nowPlayingTitle {{ font-size: 17px !important; }}
      #nowPlayingMeta {{ font-size: 12.5px !important; margin-bottom: 5px !important; }}
      .quote-box {{ display: none !important; }}
      .arch-toggle-btn {{ white-space: normal; text-align: center; }}
      th, td {{ padding: 8px 7px; font-size: 12.5px; }}
      .song-main-title {{ font-size: 13.5px; }}
    }}

    /* Now Playing Card */
    .np-header {{ margin-top: 12px; }}
    .np-title-row {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 4px;
    }}
    #nowPlayingTitle {{
      font-family: "Frank Ruhl Libre", Georgia, serif;
      font-weight: 700;
      font-size: 21px;
      color: #fff;
      line-height: 1.25;
    }}
    #nowPlayingMeta {{
      color: var(--text-secondary);
      font-size: 13.5px;
      font-weight: 500;
      margin-bottom: 8px;
    }}
    .np-badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      margin-bottom: 10px;
    }}
    .transport-bar {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 6px;
      margin-top: 12px;
    }}
    .np-details {{
      margin-top: 10px;
      border-top: 1px solid var(--border);
      padding-top: 8px;
      font-size: 12.5px;
      color: var(--muted);
    }}
    .np-details summary {{
      cursor: pointer;
      user-select: none;
      font-weight: 500;
      color: var(--muted);
      padding: 3px 0;
    }}
    .np-details summary:hover {{ color: var(--text-secondary); }}

    /* Filter Toolbar */
    .toolbar {{
      display: flex;
      gap: 10px;
      margin-bottom: 12px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .search-wrap {{
      position: relative;
      flex: 1;
      min-width: 240px;
    }}
    .search-wrap input {{
      width: 100%;
      padding-left: 34px;
    }}
    .search-kbd {{
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      pointer-events: none;
      font-size: 11px;
      color: var(--muted);
      border: 1px solid var(--border-strong);
      border-radius: 5px;
      padding: 0 5px;
      background: rgba(15, 23, 42, 0.7);
    }}
    .search-clear {{
      position: absolute;
      left: 8px;
      top: 50%;
      transform: translateY(-50%);
      background: rgba(148, 163, 184, 0.18);
      color: var(--text);
      border: none;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      font-size: 11px;
      line-height: 1;
      cursor: pointer;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 0;
    }}
    .search-clear:hover {{ background: rgba(245, 158, 11, 0.35); color: #fff; }}
    input, select {{
      background: rgba(11, 17, 32, 0.75);
      color: var(--text);
      border: 1px solid var(--border-strong);
      padding: 8px 12px;
      border-radius: 10px;
      font-family: inherit;
      font-size: 13.5px;
      transition: border-color 0.15s;
    }}
    input:focus, select:focus {{
      outline: none;
      border-color: var(--accent);
    }}
    .advanced-drawer {{
      display: none;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      padding: 10px 12px;
      margin-bottom: 12px;
      background: rgba(11, 17, 32, 0.55);
      border: 1px solid var(--border);
      border-radius: 12px;
    }}
    .advanced-drawer.open {{ display: flex; }}

    /* Clean 4-Column Song List Table */
    .table-wrap {{
      max-height: 700px;
      overflow-y: auto;
      border-radius: 10px;
    }}
    .table-wrap::-webkit-scrollbar {{ width: 7px; }}
    .table-wrap::-webkit-scrollbar-track {{ background: transparent; }}
    .table-wrap::-webkit-scrollbar-thumb {{ background: rgba(148, 163, 184, 0.22); border-radius: 999px; }}
    .table-wrap::-webkit-scrollbar-thumb:hover {{ background: rgba(148, 163, 184, 0.38); }}

    table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: right;
      vertical-align: middle;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
      font-size: 12px;
      letter-spacing: 0.2px;
      position: sticky;
      top: 0;
      background: var(--card-solid);
      z-index: 2;
    }}
    tr.song-row {{ cursor: pointer; transition: background 0.12s; }}
    tr.song-row:hover {{ background: var(--card-hover); }}
    tr.song-row.active {{
      background: rgba(245, 158, 11, 0.13);
    }}
    tr.song-row.active td:first-child {{
      border-right: 3px solid var(--gold);
    }}
    tr.song-row.multi-ver-row:not(.active) td:first-child {{
      border-right: 3px solid rgba(56, 189, 248, 0.38);
    }}
    tr.album-group-header td {{
      background: rgba(15, 23, 42, 0.92);
      color: var(--gold-soft);
      font-weight: 700;
      font-size: 13px;
      padding: 8px 14px;
      border-bottom: 1px solid rgba(245, 158, 11, 0.25);
      border-top: 1px solid rgba(245, 158, 11, 0.18);
    }}
    .album-group-count {{
      color: var(--muted);
      font-weight: 400;
      font-size: 12px;
      margin-right: 6px;
    }}

    .row-num {{
      font-weight: 600;
      color: var(--muted);
      font-variant-numeric: tabular-nums;
      width: 44px;
      text-align: center;
    }}
    tr.song-row.active .row-num {{ color: var(--gold-soft); font-weight: 700; }}
    .playing-ind {{
      display: none;
      color: var(--gold);
      font-size: 11px;
      margin-left: 2px;
    }}
    tr.song-row.active .playing-ind {{ display: inline; }}

    .song-main-title {{
      font-weight: 600;
      font-size: 14.5px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .song-year {{
      color: var(--muted);
      font-weight: 400;
      font-size: 12.5px;
    }}
    .opening-line {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
      display: -webkit-box;
      -webkit-line-clamp: 1;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .perf-primary {{
      font-weight: 500;
      color: var(--text-secondary);
      font-size: 13.5px;
    }}
    .perf-album {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 1px;
    }}
    .meta-col {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
      white-space: nowrap;
    }}
    .dur-text {{
      color: var(--muted);
      font-size: 12.5px;
      font-variant-numeric: tabular-nums;
    }}

    /* Subtle Badges */
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .ver-badge {{
      display: inline-block;
      padding: 1px 6px;
      border-radius: 6px;
      font-size: 10.5px;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.13);
      color: var(--accent);
      cursor: pointer;
      transition: all 0.14s;
    }}
    .ver-badge:hover {{
      background: var(--accent);
      color: #0f172a;
    }}
    .t-1_album_naomi {{ background: rgba(245, 158, 11, 0.16); color: #fbbf24; }}
    .t-2_album_original {{ background: rgba(16, 185, 129, 0.16); color: #34d399; }}
    .t-3_naomi_performance {{ background: rgba(56, 189, 248, 0.16); color: #38bdf8; }}
    .t-4_original_performance {{ background: rgba(168, 85, 247, 0.16); color: #c084fc; }}
    .t-5_cover {{ background: rgba(148, 163, 184, 0.14); color: #cbd5e1; }}

    .r-words_and_music {{ background: rgba(245, 158, 11, 0.12); color: #fcd34d; }}
    .r-music_only {{ background: rgba(56, 189, 248, 0.12); color: #7dd3fc; }}
    .r-words_only {{ background: rgba(192, 132, 252, 0.12); color: #d8b4fe; }}
    .r-translation {{ background: rgba(16, 185, 129, 0.12); color: #6ee7b7; }}
    .r-performance_only {{ background: rgba(251, 113, 133, 0.12); color: #fda4af; }}

    .quote-box {{
      background: rgba(11, 17, 32, 0.6);
      border-right: 3px solid var(--gold);
      padding: 7px 11px;
      border-radius: 6px;
      font-size: 12.5px;
      line-height: 1.55;
      color: var(--text-secondary);
      margin-bottom: 10px;
      max-height: 155px;
      overflow-y: auto;
    }}
    .quote-box::-webkit-scrollbar {{ width: 5px; }}
    .quote-box::-webkit-scrollbar-track {{ background: transparent; }}
    .quote-box::-webkit-scrollbar-thumb {{ background: rgba(148, 163, 184, 0.25); border-radius: 999px; }}
    .archive-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }}
    .arch-pill {{
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      text-decoration: none;
      background: rgba(56, 189, 248, 0.10);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.22);
      transition: all 0.15s;
    }}
    .arch-pill:hover {{ background: var(--accent); color: #0f172a; }}
    .arch-pill.nli {{
      background: rgba(245, 158, 11, 0.12);
      color: #fbbf24;
      border-color: rgba(245, 158, 11, 0.28);
    }}
    .arch-pill.nli:hover {{ background: #fbbf24; color: #0f172a; }}
    .arch-pill.shironet {{
      background: rgba(16, 185, 129, 0.12);
      color: #34d399;
      border-color: rgba(16, 185, 129, 0.28);
    }}
    .arch-pill.shironet:hover {{ background: #34d399; color: #0f172a; }}
    .count-chip {{
      color: var(--muted);
      font-size: 12.5px;
      margin-right: auto;
      white-space: nowrap;
    }}
    kbd {{
      background: #0f172a;
      border: 1px solid var(--border-strong);
      border-radius: 4px;
      padding: 1px 5px;
      font-size: 11px;
      color: #cbd5e1;
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- כותרת עליונה אלגנטית ומאוחדת -->
    <header class="top-header">
      <div>
        <h1 class="brand-title">
          שירי נעמי שמר
          <span class="brand-count">{total_videos} ביצועים · {total_catalog_songs} שירים בקטלוג</span>
        </h1>
        <p class="subtitle">
          האוסף המקיף מאוחד מ-9 מאגרים (אקו"ם, הספרייה הלאומית, שירונט, זמרשת ועוד) — מסודר מהקלאסיקות הגדולות אל הפנינים הנדירות.
        </p>
      </div>
      <div class="header-actions">
        <button id="playPlaylistBtn" class="btn btn-gold btn-hero-play" onclick="startPlaylistPlayback()">▶ נגן פלייליסט</button>
        <button class="btn btn-outline" onclick="copyShareUrl()">🔗 שתף שיר מתנגן</button>
        <span id="shareStatus" style="color:var(--green); font-weight:600; display:none; font-size:12.5px;">✔ הועתק!</span>
        <a class="btn btn-outline" href="https://www.youtube.com/playlist?list=PLFHErlX6i22g" target="_blank" rel="noopener">פתח ב-YouTube ↗</a>
      </div>
    </header>

    <!-- סרגל עליון למעבר מהיר לארכיון ומונה -->
    <div id="topStatusRow" class="nav-bar" style="margin-bottom: 10px;">
      <button id="topArchToggleBtn" class="btn btn-outline btn-sm arch-toggle-btn" onclick="switchTab('arch')">
        🏛️ הצג גם {unmatched_songs_count} שירים נדירים מהארכיון שאינם ביוטיוב
      </button>
      <button id="backToPlayerBtn" class="btn btn-outline btn-sm" style="display:none;" onclick="switchTab('yt')">← חזרה לנגן הפלייליסט ({total_videos} ביצועים)</button>
      <span id="ytCountChip" class="count-chip"></span>
    </div>

    <!-- לשונית 1: פלייליסט יוטיוב -->
    <div id="tabYtContent">
      <div class="player-layout">
        <!-- כרטיס הנגן הדביק -->
        <div class="card sticky-player">
          <button id="unmuteBanner" type="button" class="unmute-banner" onclick="startPlaylistPlayback()">🔇 מתנגן בהשתקה בגלל מגבלת דפדפן — לחץ כאן להפעלת שמע 🔊</button>
          <div id="failoverBanner" style="display:none; background:rgba(245,158,11,0.18); border:1px solid var(--gold); color:#fcd34d; padding:7px 10px; border-radius:8px; font-size:12.5px; margin-bottom:8px;"></div>
          <div id="ytFrameWrap" class="yt-frame-wrap">
            <div id="ytFrame"></div>
          </div>

          <div class="np-header">
            <div class="np-title-row">
              <div id="nowPlayingTitle">בחר שיר מהרשימה</div>
            </div>
            <div id="nowPlayingMeta"></div>
            <div id="nowPlayingRole" class="np-badges"></div>
            <div id="nowPlayingQuote" class="quote-box" style="display:none;"></div>
            <div id="nowPlayingLinks" class="archive-pills" style="margin-bottom:6px;"></div>
          </div>

          <div class="transport-bar">
            <button class="btn btn-outline btn-icon" onclick="playPrev()" title="השיר הקודם (P)">⏮</button>
            <button class="btn btn-outline btn-icon" onclick="togglePlayPause()" title="ניגון / השהיה (Space / K)">⏯</button>
            <button class="btn btn-outline btn-icon" onclick="playNext()" title="השיר הבא (N)">⏭</button>
            <button id="shuffleBtn" class="btn btn-outline btn-icon" onclick="toggleShuffle()" title="ניגון אקראי (S)">🔀</button>
            <a id="openOnYt" class="btn btn-outline btn-icon" href="#" target="_blank" rel="noopener" title="פתח ביוטיוב">↗ YT</a>
          </div>

          <!-- פרטים משניים מוסתרים במגירה נקייה -->
          <details id="npDetails" class="np-details">
            <summary id="npDetailsSummary">⚙️ מקורות גיבוי, גלילה וקיצורי מקלדת</summary>
            <div style="margin-top:8px; display:flex; flex-direction:column; gap:8px;">
              <div id="backupSourcesBox" style="display:none;">
                <label style="display:block; margin-bottom:4px; color:var(--text-secondary);">🛡️ החלף למקור גיבוי / ביצוע חלופי:</label>
                <select id="backupSelect" onchange="switchVideoSource(this.value)" style="width:100%; padding:6px 8px; font-size:12px;"></select>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                <button class="btn btn-outline btn-sm" onclick="scrollToActiveRow()">🎯 גלול לשיר המתנגן בטבלה</button>
                <span>קיצורים: <kbd>Space</kbd> השהיה · <kbd>N</kbd>/<kbd>P</kbd> מעבר · <kbd>S</kbd> אקראי · <kbd>/</kbd> חיפוש</span>
              </div>
            </div>
          </details>
        </div>

        <!-- כרטיס רשימת השירים -->
        <div class="card" style="padding: 16px;">
          <!-- שורת חיפוש ומיון נקייה -->
          <div class="toolbar">
            <div class="search-wrap">
              <input type="text" id="searchInput" placeholder="חיפוש שיר, שורת פתיחה, מבצע או אלבום..." oninput="onSearchInput('yt')" />
              <span id="searchKbd" class="search-kbd">/</span>
              <button id="searchClearBtn" class="search-clear" type="button" onclick="clearSearch('yt')" title="נקה חיפוש (Esc)">✕</button>
            </div>
            <select id="sortSelect" onchange="renderTable()">
              <option value="canonical">🌟 מיון: קלאסיקות תחילה</option>
              <option value="chrono_asc">📅 כרונולוגי (1953–2004)</option>
              <option value="chrono_desc">⏪ כרונולוגי הפוך</option>
              <option value="albums">💿 לפי אלבומים מקוריים</option>
              <option value="popularity">🔥 לפי תפוצה באקו"ם</option>
              <option value="title_asc">🔤 שם השיר (א'–ת')</option>
              <option value="perf_asc">🎤 שם המבצע (א'–ת')</option>
            </select>
            <select id="decadeFilter" onchange="renderTable()">
              <option value="ALL">כל העשורים ({total_videos})</option>
              <option value="1950s">שנות ה-50 ({d_50})</option>
              <option value="1960s">שנות ה-60 ({d_60})</option>
              <option value="1970s">שנות ה-70 ({d_70})</option>
              <option value="1980s">שנות ה-80 ({d_80})</option>
              <option value="1990s+">שנות ה-90+ ({d_90})</option>
              <option value="unknown">ללא שנה ({d_unk})</option>
            </select>
            <button id="onePerSongBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleOnePerSong()" aria-pressed="false" title="סנן לביצוע מוביל אחד לכל שיר (מדלג על גרסאות כפולות בלי למחוק אותן)">
              🎯 ביצוע אחד לכל שיר ({unique_songs_count})
            </button>
            <button id="advFilterBtn" class="btn btn-outline btn-sm" onclick="toggleAdvancedFilters()">
              ⚙️ סינון מתקדם <span id="activeFiltersBadge" style="display:none; background:var(--gold); color:#000; padding:0 6px; border-radius:999px; font-size:11px;"></span>
            </button>
          </div>

          <!-- מגירת סינון מתקדם (מוסתרת כברירת מחדל) -->
          <div id="advancedDrawer" class="advanced-drawer">
            <select id="tierFilter" onchange="renderTable()">
              <option value="ALL">כל סוגי הביצועים ({total_videos})</option>
              <option value="1_album_naomi">אלבום של נעמי שמר ({t1})</option>
              <option value="2_album_original">אלבום מבצע מקורי ({t2})</option>
              <option value="3_naomi_performance">ביצוע נעמי שמר ({t3})</option>
              <option value="4_original_performance">ביצוע מקורי ({t4})</option>
              <option value="5_cover">ביצוע נוסף / קאבר ({t5})</option>
            </select>
            <select id="roleFilter" onchange="renderTable()">
              <option value="ALL">כל תפקידי היצירה ({total_videos})</option>
              <option value="words_and_music">מילים ולחן: נעמי שמר ({r_wm})</option>
              <option value="music_only">לחן בלבד ({r_m})</option>
              <option value="words_only">מילים בלבד ({r_w})</option>
              <option value="translation">תרגום ({r_t})</option>
              <option value="performance_only">ביצוע בלבד ({r_p})</option>
            </select>
            <button class="btn btn-outline btn-sm" onclick="resetAllFilters()" title="אפס את כל המסננים">↺ איפוס</button>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style="width:44px; text-align:center;">#</th>
                  <th>שיר</th>
                  <th>מבצע ואלבום</th>
                  <th style="width:68px; text-align:left;">אורך</th>
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
        <div class="toolbar">
          <div class="search-wrap">
            <input type="text" id="archSearchInput" placeholder="חיפוש בארכיון לפי שם שיר, שורת פתיחה או מבצע..." oninput="onSearchInput('arch')" />
            <button id="archSearchClearBtn" class="search-clear" type="button" onclick="clearSearch('arch')" title="נקה חיפוש (Esc)">✕</button>
          </div>
          <select id="archRoleFilter" onchange="renderArchiveTable()">
            <option value="ALL">כל התפקידים ({unmatched_songs_count})</option>
            <option value="words_and_music">מילים ולחן ({ar_wm})</option>
            <option value="music_only">לחן בלבד ({ar_m})</option>
            <option value="words_only">מילים בלבד ({ar_w})</option>
            <option value="translation">תרגום ({ar_t})</option>
            <option value="performance_only">ביצוע בלבד ({ar_p})</option>
          </select>
          <select id="archSourceFilter" onchange="renderArchiveTable()">
            <option value="ALL">כל המאגרים ({unmatched_songs_count})</option>
            <option value="nli">הספרייה הלאומית ({as_nli})</option>
            <option value="acum">אקו"ם ({as_acum})</option>
            <option value="shironet">שירונט ({as_shir})</option>
          </select>
        </div>
        <div class="table-wrap" style="max-height: 720px;">
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
      <span>קטלוג שירי נעמי שמר · {total_videos} ביצועים ביוטיוב</span>
      <button id="footerArchToggleBtn" class="btn btn-outline btn-sm arch-toggle-btn" onclick="switchTab(currentTab === 'yt' ? 'arch' : 'yt')">
        🏛️ הצג גם {unmatched_songs_count} שירים נדירים מהארכיון שאינם ביוטיוב
      </button>
    </footer>
  </div>

  <script>
    function esc(s) {{
      if (s === null || s === undefined) return "";
      const d = document.createElement("div");
      d.textContent = String(s);
      return d.innerHTML;
    }}
    const SONGS = {json.dumps(songs_js, ensure_ascii=False, indent=2)};
    const ARCHIVE_SONGS = {json.dumps(archive_songs_js, ensure_ascii=False, indent=2)};

    let filteredSongs = [...SONGS];
    let currentIndex = 0;
    let currentAltIdx = -1; // -1 = primary video, 0..N = index in s.alts
    let playHistory = [];
    let ytPlayer = null;
    let ytApiReady = false;
    let ytApiFailed = false;
    let pendingVideoLoad = null;
    let shuffleEnabled = false;
    let onePerSongOnly = false;
    let currentTab = "yt";
    let userInteractedPlayback = false;

    function syncPlayButtonUI() {{
      const btn = document.getElementById("playPlaylistBtn");
      const unmuteEl = document.getElementById("unmuteBanner");
      if (!btn) return;
      if (!ytApiReady || !ytPlayer || typeof ytPlayer.getPlayerState !== "function") {{
        btn.textContent = "▶ נגן פלייליסט";
        if (unmuteEl) unmuteEl.style.display = "none";
        return;
      }}
      const st = ytPlayer.getPlayerState();
      const muted = typeof ytPlayer.isMuted === "function" && ytPlayer.isMuted();
      if (st === 1 && muted) {{
        btn.textContent = "🔊 הפעל שמע (מתנגן)";
        if (unmuteEl) unmuteEl.style.display = "block";
      }} else if (st === 1) {{
        btn.textContent = "⏸ השהה פלייליסט";
        if (unmuteEl) unmuteEl.style.display = "none";
      }} else if (st === 2) {{
        btn.textContent = "▶ המשך פלייליסט";
        if (unmuteEl) unmuteEl.style.display = "none";
      }} else {{
        btn.textContent = "▶ נגן פלייליסט";
        if (unmuteEl) unmuteEl.style.display = "none";
      }}
    }}

    function startPlaylistPlayback() {{
      if (currentTab !== "yt") switchTab("yt");
      if (!filteredSongs.length) return;
      userInteractedPlayback = true;
      if (ytApiReady && ytPlayer && typeof ytPlayer.getPlayerState === "function") {{
        const st = ytPlayer.getPlayerState();
        const muted = typeof ytPlayer.isMuted === "function" && ytPlayer.isMuted();
        if (muted) {{
          if (typeof ytPlayer.unMute === "function") ytPlayer.unMute();
          if (st !== 1) ytPlayer.playVideo();
          syncPlayButtonUI();
          return;
        }}
        if (st === 1) {{
          ytPlayer.pauseVideo();
        }} else {{
          if (typeof ytPlayer.unMute === "function") ytPlayer.unMute();
          ytPlayer.playVideo();
        }}
        syncPlayButtonUI();
        return;
      }}
      playSongAt(currentIndex >= 0 ? currentIndex : 0, true, true);
    }}

    function loadYouTubeIframeAPI() {{
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      tag.onerror = function() {{
        ytApiFailed = true;
        if (pendingVideoLoad) {{
          const req = pendingVideoLoad;
          pendingVideoLoad = null;
          loadVideoByIdOrSrc(req.vid, req.autoplay);
        }}
      }};
      document.head.appendChild(tag);
      setTimeout(() => {{
        if (!ytApiReady && !ytApiFailed) {{
          ytApiFailed = true;
          if (pendingVideoLoad) {{
            const req = pendingVideoLoad;
            pendingVideoLoad = null;
            loadVideoByIdOrSrc(req.vid, req.autoplay);
          }}
        }}
      }}, 6000);
    }}

    window.onYouTubeIframeAPIReady = function() {{
      try {{
        const initReq = pendingVideoLoad || {{ vid: (filteredSongs[currentIndex] || SONGS[0]).vid, autoplay: true, initialAuto: true }};
        pendingVideoLoad = null;
        ytPlayer = new YT.Player("ytFrame", {{
          width: "100%",
          height: "100%",
          videoId: initReq.vid,
          playerVars: {{
            rel: 0,
            enablejsapi: 1,
            playsinline: 1,
            autoplay: initReq.autoplay ? 1 : 0
          }},
          events: {{
            onReady: function() {{
              ytApiReady = true;
              const req = pendingVideoLoad || initReq;
              pendingVideoLoad = null;
              if (req && req.autoplay) {{
                if (req.initialAuto && !userInteractedPlayback) {{
                  try {{ ytPlayer.playVideo(); }} catch (e) {{}}
                  setTimeout(() => {{
                    if (userInteractedPlayback || !ytPlayer || typeof ytPlayer.getPlayerState !== "function") return;
                    const st = ytPlayer.getPlayerState();
                    if (st !== 1 && st !== 3) {{
                      try {{
                        ytPlayer.mute();
                        ytPlayer.playVideo();
                      }} catch (e) {{}}
                    }}
                    syncPlayButtonUI();
                  }}, 900);
                }} else {{
                  if (typeof ytPlayer.unMute === "function") ytPlayer.unMute();
                  ytPlayer.loadVideoById(req.vid);
                }}
              }} else if (req) {{
                ytPlayer.cueVideoById(req.vid);
              }}
              syncPlayButtonUI();
            }},
            onStateChange: function(ev) {{
              if (ev.data === 0) {{ // YT.PlayerState.ENDED
                playNext();
              }}
              syncPlayButtonUI();
            }},
            onError: function(ev) {{
              handleVideoPlaybackError(ev.data);
            }}
          }}
        }});
      }} catch (e) {{
        ytApiFailed = true;
        if (pendingVideoLoad) {{
          const req = pendingVideoLoad;
          pendingVideoLoad = null;
          loadVideoByIdOrSrc(req.vid, req.autoplay);
        }}
      }}
    }};

    function handleVideoPlaybackError(errCode) {{
      const s = filteredSongs[currentIndex];
      if (!s) return;
      const alts = s.alts || [];
      const nextAltIdx = currentAltIdx + 1;
      const banner = document.getElementById("failoverBanner");
      const npDet = document.getElementById("npDetails");
      if (nextAltIdx < alts.length) {{
        currentAltIdx = nextAltIdx;
        const alt = alts[currentAltIdx];
        if (banner) {{
          banner.style.display = "block";
          banner.innerHTML = `⚠️ הסרטון הראשי אינו זמין כעת (קוד ${{esc(errCode)}}). הנגן עבר אוטומטית למקור גיבוי #${{currentAltIdx + 1}}: <strong>${{esc(alt.vtitle || alt.vid)}}</strong>`;
        }}
        if (npDet) npDet.open = true;
        const sel = document.getElementById("backupSelect");
        if (sel) sel.value = alt.vid;
        loadVideoByIdOrSrc(alt.vid, true);
        document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{encodeURIComponent(alt.vid)}}`;
      }} else {{
        if (banner) {{
          banner.style.display = "block";
          banner.innerHTML = `⚠️ הסרטון אינו זמין (קוד ${{esc(errCode)}}) ולא נמצאו מקורות גיבוי נוספים. עובר לשיר הבא...`;
        }}
        setTimeout(() => playNext(), 1800);
      }}
    }}

    function loadVideoByIdOrSrc(vid, autoplay) {{
      if (ytApiReady && ytPlayer && typeof ytPlayer.loadVideoById === "function") {{
        if (autoplay) {{
          if (userInteractedPlayback && typeof ytPlayer.unMute === "function") {{
            try {{ ytPlayer.unMute(); }} catch (_) {{}}
          }}
          ytPlayer.loadVideoById(vid);
        }} else {{
          ytPlayer.cueVideoById(vid);
        }}
        if (typeof syncPlayButtonUI === "function") syncPlayButtonUI();
        return;
      }}
      if (!ytApiFailed) {{
        pendingVideoLoad = {{ vid, autoplay }};
        return;
      }}
      const wrap = document.getElementById("ytFrameWrap");
      const originParam = window.location.origin && window.location.origin !== "null" ? `&origin=${{encodeURIComponent(window.location.origin)}}` : "";
      const muteParam = autoplay && !userInteractedPlayback ? "&mute=1" : "";
      const srcUrl = `https://www.youtube.com/embed/${{encodeURIComponent(vid)}}?enablejsapi=1&rel=0${{autoplay ? "&autoplay=1" : ""}}${{muteParam}}${{originParam}}`;
      let frame = document.getElementById("ytFrame");
      if (!frame || frame.tagName.toLowerCase() !== "iframe") {{
        if (wrap) {{
          wrap.innerHTML = `<iframe id="ytFrame" src="${{srcUrl}}" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
        }}
      }} else {{
        frame.src = srcUrl;
      }}
    }}

    function switchVideoSource(vid) {{
      const s = filteredSongs[currentIndex];
      if (!s) return;
      userInteractedPlayback = true;
      const banner = document.getElementById("failoverBanner");
      if (vid === s.vid) {{
        currentAltIdx = -1;
        if (banner) banner.style.display = "none";
      }} else {{
        const alts = s.alts || [];
        currentAltIdx = alts.findIndex(a => a.vid === vid);
        const alt = alts[currentAltIdx];
        if (banner && alt) {{
          banner.style.display = "block";
          banner.innerHTML = `🛡️ מנגן מקור גיבוי #${{currentAltIdx + 1}}: <strong>${{esc(alt.vtitle || alt.vid)}}</strong> (${{esc(alt.ch || "")}})`;
        }}
      }}
      loadVideoByIdOrSrc(vid, true);
      document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{encodeURIComponent(vid)}}`;
    }}

    function switchTab(tab, skipSync = false) {{
      currentTab = tab === "arch" ? "arch" : "yt";
      const isYt = currentTab === "yt";
      document.getElementById("tabYtContent").style.display = isYt ? "block" : "none";
      document.getElementById("tabArchContent").style.display = isYt ? "none" : "block";
      const topArchBtn = document.getElementById("topArchToggleBtn");
      if (topArchBtn) topArchBtn.style.display = isYt ? "inline-flex" : "none";
      const backBtn = document.getElementById("backToPlayerBtn");
      if (backBtn) backBtn.style.display = isYt ? "none" : "inline-flex";
      const ytChip = document.getElementById("ytCountChip");
      if (ytChip) ytChip.style.display = isYt ? "" : "none";
      const footerBtn = document.getElementById("footerArchToggleBtn");
      if (footerBtn) {{
        footerBtn.textContent = isYt
          ? `🏛️ הצג גם ${{ARCHIVE_SONGS.length}} שירים נדירים מהארכיון שאינם ביוטיוב`
          : `🎵 חזרה לנגן הפלייליסט הראשי (${{SONGS.length}} ביצועים)`;
      }}
      if (!skipSync) {{
        syncUrlAndStorageState();
        window.scrollTo({{ top: 0, behavior: "smooth" }});
      }}
    }}

    function syncOnePerSongUI() {{
      const btn = document.getElementById("onePerSongBtn");
      if (!btn) return;
      btn.classList.toggle("btn-active", onePerSongOnly);
      btn.setAttribute("aria-pressed", onePerSongOnly ? "true" : "false");
    }}

    function toggleOnePerSong() {{
      onePerSongOnly = !onePerSongOnly;
      syncOnePerSongUI();
      renderTable();
    }}

    function toggleAdvancedFilters() {{
      const drw = document.getElementById("advancedDrawer");
      const btn = document.getElementById("advFilterBtn");
      if (!drw) return;
      const isOpen = drw.classList.toggle("open");
      if (btn) btn.classList.toggle("btn-active", isOpen);
    }}

    function updateSearchClearUI(which) {{
      if (which === "arch") {{
        const inp = document.getElementById("archSearchInput");
        const clr = document.getElementById("archSearchClearBtn");
        if (inp && clr) clr.style.display = inp.value.length > 0 ? "inline-flex" : "none";
      }} else {{
        const inp = document.getElementById("searchInput");
        const clr = document.getElementById("searchClearBtn");
        const kbd = document.getElementById("searchKbd");
        const hasVal = inp && inp.value.length > 0;
        if (clr) clr.style.display = hasVal ? "inline-flex" : "none";
        if (kbd) kbd.style.display = hasVal ? "none" : "inline";
      }}
    }}

    function onSearchInput(which) {{
      updateSearchClearUI(which);
      if (which === "arch") renderArchiveTable();
      else renderTable();
    }}

    function clearSearch(which) {{
      if (which === "arch") {{
        const inp = document.getElementById("archSearchInput");
        if (inp) {{ inp.value = ""; inp.focus(); }}
        updateSearchClearUI("arch");
        renderArchiveTable();
      }} else {{
        const inp = document.getElementById("searchInput");
        if (inp) {{ inp.value = ""; inp.focus(); }}
        updateSearchClearUI("yt");
        renderTable();
      }}
    }}

    function filterBySongTitle(ev, rawTitle) {{
      if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
      const inp = document.getElementById("searchInput");
      if (!inp) return;
      if (inp.value.trim() === rawTitle) {{
        inp.value = "";
      }} else {{
        inp.value = rawTitle;
      }}
      updateSearchClearUI("yt");
      renderTable();
    }}

    function resetAllFilters() {{
      document.getElementById("searchInput").value = "";
      updateSearchClearUI("yt");
      document.getElementById("sortSelect").value = "canonical";
      document.getElementById("decadeFilter").value = "ALL";
      document.getElementById("tierFilter").value = "ALL";
      document.getElementById("roleFilter").value = "ALL";
      onePerSongOnly = false;
      syncOnePerSongUI();
      renderTable();
    }}

    function syncUrlAndStorageState() {{
      try {{
        const url = new URL(window.location.href);
        const s = filteredSongs[currentIndex] || SONGS[0];
        if (s) url.searchParams.set("song", s.n);
        const q = document.getElementById("searchInput").value.trim();
        const sortBy = document.getElementById("sortSelect").value;
        const tf = document.getElementById("tierFilter").value;
        const rf = document.getElementById("roleFilter").value;
        const df = document.getElementById("decadeFilter").value;

        const setOrDel = (k, val, defVal) => {{
          if (val && val !== defVal) url.searchParams.set(k, val);
          else url.searchParams.delete(k);
        }};
        setOrDel("q", q, "");
        setOrDel("sort", sortBy, "canonical");
        setOrDel("tier", tf, "ALL");
        setOrDel("role", rf, "ALL");
        setOrDel("decade", df, "ALL");
        setOrDel("tab", currentTab, "yt");
        setOrDel("shuffle", shuffleEnabled ? "1" : "", "");
        setOrDel("oneper", onePerSongOnly ? "1" : "", "");

        window.history.replaceState({{}}, "", url.toString());
        if (window.localStorage) {{
          localStorage.setItem("naomi_playlist_state", JSON.stringify({{
            song: s ? s.n : 1,
            sort: sortBy,
            tier: tf,
            role: rf,
            decade: df,
            tab: currentTab,
            shuffle: shuffleEnabled,
            oneper: onePerSongOnly
          }}));
        }}
      }} catch (e) {{}}
    }}

    function copyShareUrl() {{
      syncUrlAndStorageState();
      const shareStr = window.location.href;
      const showOk = () => {{
        const st = document.getElementById("shareStatus");
        st.style.display = "inline";
        setTimeout(() => st.style.display = "none", 3500);
      }};
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(shareStr).then(showOk);
      }}
    }}

    function renderArchivePills(links, stopProp = false) {{
      if (!links || !links.length) return "";
      const onclickAttr = stopProp ? 'onclick="event.stopPropagation()"' : "";
      return `<div class="archive-pills">` + links.map(l => {{
        let cls = "arch-pill";
        const src = String(l.source || "");
        if (src.startsWith("nli")) cls += " nli";
        else if (src === "shironet") cls += " shironet";
        return `<a class="${{cls}}" href="${{esc(l.url)}}" target="_blank" rel="noopener noreferrer" ${{onclickAttr}}>${{esc(l.label)}} ↗</a>`;
      }}).join("") + `</div>`;
    }}

    function updateNowPlayingCard(s) {{
      document.getElementById("nowPlayingTitle").textContent = `${{s.n}}. ${{s.raw_title}}${{s.year ? " (" + s.year + ")" : ""}}`;
      document.getElementById("nowPlayingMeta").textContent = `${{s.perf || s.ch}}${{s.alb ? " · " + s.alb : ""}}`;
      const verBadgeHtml = s.ver_total > 1
        ? `<span class="ver-badge" onclick="filterBySongTitle(event, ${{JSON.stringify(s.raw_title).replace(/"/g, '&quot;')}})" title="לחץ להצגת כל ${{s.ver_total}} הביצועים של שיר זה">ביצוע ${{s.ver_idx}}/${{s.ver_total}}</span>`
        : "";
      const tierShort = s.tier_label.replace(/^[0-9]\.\s*/, "");
      document.getElementById("nowPlayingRole").innerHTML = `<span class="badge t-${{esc(s.tier)}}">${{esc(tierShort)}}</span><span class="badge r-${{esc(s.role_cat)}}">${{esc(s.role_label)}}</span>${{verBadgeHtml}}`;
      const qBox = document.getElementById("nowPlayingQuote");
      const parts = [];
      const notesArr = Array.isArray(s.notes) ? s.notes : (s.notes ? [s.notes] : []);
      const formatNoteHtml = (txt) => esc(txt).replace(/\s*~\s*/g, "<br/>");
      if (s.opening_line) parts.push(`"${{esc(s.opening_line)}}"`);
      if (notesArr.length) parts.push(`<span style="color:var(--muted); font-size:11.5px;">${{notesArr.map(formatNoteHtml).join(" · ")}}</span>`);
      if (parts.length > 0) {{
        qBox.innerHTML = parts.join("<br/>");
        qBox.style.display = "block";
      }} else {{
        qBox.style.display = "none";
      }}
      document.getElementById("nowPlayingLinks").innerHTML = renderArchivePills(s.links, false);
      document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{encodeURIComponent(s.vid)}}`;
      const banner = document.getElementById("failoverBanner");
      if (banner) banner.style.display = "none";
      const bBox = document.getElementById("backupSourcesBox");
      const bSel = document.getElementById("backupSelect");
      const npSum = document.getElementById("npDetailsSummary");
      const alts = s.alts || [];
      if (npSum) {{
        npSum.textContent = alts.length > 0
          ? `⚙️ מקורות גיבוי (${{alts.length}}), גלילה וקיצורי מקלדת`
          : `⚙️ גלילה וקיצורי מקלדת`;
      }}
      if (bBox && bSel) {{
        if (alts.length > 0) {{
          bBox.style.display = "block";
          const opts = [`<option value="${{esc(s.vid)}}">⭐ מקור ראשי: ${{esc(s.vtitle)}} (${{esc(s.ch)}})</option>`];
          alts.forEach((a, i) => {{
            const tag = a.src === "same_song_performance" ? "ביצוע נוסף" : "עותק גיבוי";
            opts.push(`<option value="${{esc(a.vid)}}">🔄 גיבוי #${{i + 1}} (${{tag}}): ${{esc(a.vtitle || a.vid)}} (${{esc(a.ch || "")}})</option>`);
          }});
          bSel.innerHTML = opts.join("");
          bSel.value = s.vid;
        }} else {{
          bBox.style.display = "none";
        }}
      }}
    }}

    function scrollToActiveRow(smooth = true) {{
      const activeRow = document.querySelector("tr.song-row.active");
      if (activeRow) {{
        activeRow.scrollIntoView({{ behavior: smooth ? "smooth" : "auto", block: "nearest" }});
      }}
    }}

    function playSongAt(idx, shouldScroll = true, skipHistory = false) {{
      if (idx < 0 || idx >= filteredSongs.length) return;
      userInteractedPlayback = true;
      if (!skipHistory && currentIndex !== idx && filteredSongs[currentIndex]) {{
        playHistory.push( filteredSongs[currentIndex].vid );
        if (playHistory.length > 100) playHistory.shift();
      }}
      currentIndex = idx;
      currentAltIdx = -1;
      const s = filteredSongs[idx];
      updateNowPlayingCard(s);
      loadVideoByIdOrSrc(s.vid, true);
      document.querySelectorAll("tr.song-row").forEach((tr, i) => {{
        tr.classList.toggle("active", i === idx);
      }});
      if (shouldScroll) scrollToActiveRow(true);
      syncUrlAndStorageState();
    }}

    function toggleShuffle() {{
      shuffleEnabled = !shuffleEnabled;
      const btn = document.getElementById("shuffleBtn");
      if (btn) btn.classList.toggle("btn-active", shuffleEnabled);
      syncUrlAndStorageState();
    }}

    function togglePlayPause() {{
      userInteractedPlayback = true;
      if (ytApiReady && ytPlayer && typeof ytPlayer.getPlayerState === "function") {{
        if (typeof ytPlayer.isMuted === "function" && ytPlayer.isMuted() && typeof ytPlayer.unMute === "function") {{
          try {{ ytPlayer.unMute(); }} catch (_) {{}}
          ytPlayer.playVideo();
          if (typeof syncPlayButtonUI === "function") syncPlayButtonUI();
          return;
        }}
        const st = ytPlayer.getPlayerState();
        if (st === 1) ytPlayer.pauseVideo();
        else ytPlayer.playVideo();
        if (typeof syncPlayButtonUI === "function") syncPlayButtonUI();
      }}
    }}

    function playNext() {{
      if (!filteredSongs.length) return;
      if (shuffleEnabled && filteredSongs.length > 1) {{
        let randIdx = currentIndex;
        while (randIdx === currentIndex) {{
          randIdx = Math.floor(Math.random() * filteredSongs.length);
        }}
        playSongAt(randIdx);
        return;
      }}
      playSongAt((currentIndex + 1) % filteredSongs.length);
    }}

    function playPrev() {{
      if (!filteredSongs.length) return;
      if (shuffleEnabled && playHistory.length > 0) {{
        const prevVid = playHistory.pop();
        const prevIdx = filteredSongs.findIndex(x => x.vid === prevVid);
        if (prevIdx >= 0) {{
          playSongAt(prevIdx, true, true);
          return;
        }}
      }}
      playSongAt((currentIndex - 1 + filteredSongs.length) % filteredSongs.length, true, true);
    }}

    function renderTable(skipSync = false) {{
      const currentVid = filteredSongs[currentIndex] ? filteredSongs[currentIndex].vid : null;
      const q = document.getElementById("searchInput").value.trim().toLowerCase();
      const sortBy = document.getElementById("sortSelect").value;
      const tf = document.getElementById("tierFilter").value;
      const rf = document.getElementById("roleFilter").value;
      const df = document.getElementById("decadeFilter").value;

      filteredSongs = SONGS.filter(s => {{
        if (onePerSongOnly && s.ver_idx !== 1) return false;
        if (tf !== "ALL" && s.tier !== tf) return false;
        if (rf !== "ALL" && s.role_cat !== rf) return false;
        if (df !== "ALL" && s.decade !== df) return false;
        if (!q) return true;
        return (
          s.title.toLowerCase().includes(q) ||
          s.vtitle.toLowerCase().includes(q) ||
          s.perf.toLowerCase().includes(q) ||
          s.alb.toLowerCase().includes(q) ||
          s.ch.toLowerCase().includes(q) ||
          s.role_label.toLowerCase().includes(q) ||
          (s.opening_line && s.opening_line.toLowerCase().includes(q))
        );
      }});

      filteredSongs.sort((a, b) => {{
        if (sortBy === "canonical") return a.n - b.n;
        if (sortBy === "chrono_asc") return (a.chrono_n || a.n) - (b.chrono_n || b.n);
        if (sortBy === "chrono_desc") return (b.chrono_n || b.n) - (a.chrono_n || a.n);
        if (sortBy === "popularity") return (b.canon_score - a.canon_score) || (a.n - b.n);
        if (sortBy === "title_asc") return a.raw_title.localeCompare(b.raw_title, "he") || (a.n - b.n);
        if (sortBy === "perf_asc") return (a.perf || a.ch).localeCompare(b.perf || b.ch, "he") || (a.n - b.n);
        if (sortBy === "albums") {{
          const aIsAlbum = a.alb_group && !a.alb_group.startsWith("סינגל") && !a.alb_group.startsWith("ביצוע ");
          const bIsAlbum = b.alb_group && !b.alb_group.startsWith("סינגל") && !b.alb_group.startsWith("ביצוע ");
          if (aIsAlbum !== bIsAlbum) return aIsAlbum ? -1 : 1;
          const aNaomi = a.tier === "1_album_naomi" ? 0 : 1;
          const bNaomi = b.tier === "1_album_naomi" ? 0 : 1;
          if (aNaomi !== bNaomi) return aNaomi - bNaomi;
          const grpCmp = (a.alb_group || "").localeCompare(b.alb_group || "", "he");
          if (grpCmp !== 0) return grpCmp;
          const trkCmp = (a.alb_trk || 999) - (b.alb_trk || 999);
          if (trkCmp !== 0) return trkCmp;
          return (a.chrono_n || a.n) - (b.chrono_n || b.n);
        }}
        return a.n - b.n;
      }});

      if (currentVid) {{
        const foundIdx = filteredSongs.findIndex(x => x.vid === currentVid);
        if (foundIdx >= 0) currentIndex = foundIdx;
        else if (filteredSongs.length > 0) currentIndex = 0;
      }}

      document.getElementById("ytCountChip").textContent = filteredSongs.length === SONGS.length
        ? `${{SONGS.length}} ביצועים`
        : (onePerSongOnly
            ? `מציג ${{filteredSongs.length}} מתוך ${{SONGS.length}} ביצועים (ביצוע אחד לשיר)`
            : `מציג ${{filteredSongs.length}} מתוך ${{SONGS.length}} ביצועים`);

      const activeAdvCount = [tf !== "ALL", rf !== "ALL"].filter(Boolean).length;
      const advBadge = document.getElementById("activeFiltersBadge");
      if (advBadge) {{
        if (activeAdvCount > 0) {{
          advBadge.textContent = activeAdvCount;
          advBadge.style.display = "inline-block";
        }} else {{
          advBadge.style.display = "none";
        }}
      }}

      const albumCounts = {{}};
      if (sortBy === "albums") {{
        filteredSongs.forEach(s => {{
          const g = s.alb_group || "ללא שיוך לאלבום";
          albumCounts[g] = (albumCounts[g] || 0) + 1;
        }});
      }}

      let lastAlbGroup = null;
      const tbody = document.getElementById("songsBody");
      const htmlRows = [];
      filteredSongs.forEach((s, i) => {{
        if (sortBy === "albums") {{
          const grp = s.alb_group || "ללא שיוך לאלבום";
          if (grp !== lastAlbGroup) {{
            lastAlbGroup = grp;
            htmlRows.push(`
              <tr class="album-group-header">
                <td colspan="4">💿 ${{esc(grp)}} <span class="album-group-count">(${{albumCounts[grp]}} רצועות)</span></td>
              </tr>
            `);
          }}
        }}
        const roleSub = s.role_cat !== "words_and_music" ? `<span class="badge r-${{esc(s.role_cat)}}">${{esc(s.role_label)}}</span>` : "";
        const titleAttrEsc = JSON.stringify(s.raw_title).replace(/"/g, "&quot;");
        const subNumHtml = sortBy === "albums" && s.alb_trk
          ? `<div style="font-size:10.5px; color:var(--gold-soft); opacity:0.85;">רצועה #${{s.alb_trk}}</div>`
          : (sortBy !== "canonical" ? `<div style="font-size:10.5px; opacity:0.65;">#${{s.n}}</div>` : "");
        htmlRows.push(`
        <tr class="song-row ${{i === currentIndex ? "active" : ""}} ${{s.ver_total > 1 ? "multi-ver-row" : ""}}" onclick="playSongAt(${{i}}, false)">
          <td class="row-num">
            <div><span class="playing-ind">▶</span>${{i + 1}}</div>
            ${{subNumHtml}}
          </td>
          <td>
            <div class="song-main-title">
              <span>${{esc(s.raw_title)}}</span>
              ${{s.year ? `<span class="song-year">(${{esc(s.year)}})</span>` : ""}}
              ${{s.ver_total > 1 ? `<span class="ver-badge" onclick="filterBySongTitle(event, ${{titleAttrEsc}})" title="לחץ לסינון כל ${{s.ver_total}} הביצועים של שיר זה">ביצוע ${{s.ver_idx}}/${{s.ver_total}}</span>` : ""}}
              ${{roleSub}}
            </div>
          </td>
          <td>
            <div class="perf-primary">${{esc(s.perf || s.ch)}}</div>
            ${{s.alb ? `<div class="perf-album">${{esc(s.alb)}}</div>` : ""}}
          </td>
          <td style="text-align:left;">
            <span class="dur-text">${{esc(s.dur)}}</span>
          </td>
        </tr>`);
      }});
      tbody.innerHTML = htmlRows.join("");

      if (!skipSync) syncUrlAndStorageState();
    }}

    function renderArchiveTable() {{
      const q = document.getElementById("archSearchInput").value.trim().toLowerCase();
      const rf = document.getElementById("archRoleFilter").value;
      const sf = document.getElementById("archSourceFilter").value;

      const filteredArch = ARCHIVE_SONGS.filter(s => {{
        if (rf !== "ALL" && s.role_cat !== rf) return false;
        if (sf !== "ALL") {{
          const hasSource = (s.links || []).some(l => l.source === sf);
          if (!hasSource) return false;
        }}
        if (!q) return true;
        return (
          s.title.toLowerCase().includes(q) ||
          (s.alt_titles && s.alt_titles.join(" ").toLowerCase().includes(q)) ||
          (s.perfs && s.perfs.toLowerCase().includes(q)) ||
          (s.albums && s.albums.toLowerCase().includes(q)) ||
          s.role_label.toLowerCase().includes(q) ||
          (s.opening_line && s.opening_line.toLowerCase().includes(q))
        );
      }});

      document.getElementById("archCountChip").textContent = `${{filteredArch.length}} מתוך ${{ARCHIVE_SONGS.length}} שירי ארכיון`;

      const tbody = document.getElementById("archiveBody");
      tbody.innerHTML = filteredArch.map((s, idx) => `
        <tr>
          <td class="row-num">${{idx + 1}}</td>
          <td>
            <div class="song-main-title">
              <span>${{esc(s.title)}}</span>
              ${{s.year && s.year !== "ללא שנה" ? `<span class="song-year">(${{esc(s.year)}})</span>` : ""}}
            </div>
            ${{s.alt_titles && s.alt_titles.length ? `<div class="perf-album">שמות נוספים: ${{esc(s.alt_titles.join(", "))}}</div>` : ""}}
          </td>
          <td>
            <div class="perf-primary">${{s.perfs ? esc(s.perfs) : "<span style='color:var(--muted);'>לא מתועד מבצע</span>"}}</div>
            <div style="margin-top:3px;"><span class="badge r-${{esc(s.role_cat)}}">${{esc(s.role_label)}}</span></div>
          </td>
          <td>
            ${{s.opening_line ? `<div class="opening-line" style="-webkit-line-clamp:2;">"${{esc(s.opening_line)}}"</div>` : "<span style='color:var(--muted);'>—</span>"}}
          </td>
          <td>${{renderArchivePills(s.links, false)}}</td>
        </tr>
      `).join("");
    }}

    document.addEventListener("keydown", function(ev) {{
      const tag = (ev.target && ev.target.tagName) ? ev.target.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "textarea" || tag === "select" || (ev.target && ev.target.isContentEditable)) {{
        if (ev.key === "Escape") {{
          if (ev.target.id === "searchInput" && ev.target.value) {{
            clearSearch("yt");
          }} else if (ev.target.id === "archSearchInput" && ev.target.value) {{
            clearSearch("arch");
          }} else {{
            ev.target.blur();
          }}
        }}
        return;
      }}
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      if (ev.key === "/" ) {{
        ev.preventDefault();
        const inp = currentTab === "arch" ? document.getElementById("archSearchInput") : document.getElementById("searchInput");
        if (inp) {{ inp.focus(); inp.select(); }}
      }} else if (ev.key === " " || ev.key === "k" || ev.key === "K") {{
        ev.preventDefault();
        togglePlayPause();
      }} else if (ev.key === "n" || ev.key === "N") {{
        ev.preventDefault();
        playNext();
      }} else if (ev.key === "p" || ev.key === "P") {{
        ev.preventDefault();
        playPrev();
      }} else if (ev.key === "s" || ev.key === "S") {{
        ev.preventDefault();
        toggleShuffle();
      }}
    }});

    (function initApp() {{
      let saved = {{}};
      try {{
        if (window.localStorage) {{
          saved = JSON.parse(localStorage.getItem("naomi_playlist_state") || "{{}}") || {{}};
        }}
      }} catch (e) {{}}

      const params = new URLSearchParams(window.location.search);
      const qParam = params.get("q");
      const sortParam = params.get("sort") || saved.sort;
      const tierParam = params.get("tier") || saved.tier;
      const roleParam = params.get("role") || saved.role;
      const decadeParam = params.get("decade") || saved.decade;
      const tabParam = params.get("tab") || saved.tab;
      const shufParam = params.get("shuffle");
      const onePerParam = params.get("oneper");

      if (qParam !== null) {{
        document.getElementById("searchInput").value = qParam;
        updateSearchClearUI("yt");
      }}
      if (sortParam) document.getElementById("sortSelect").value = sortParam;
      if (tierParam) document.getElementById("tierFilter").value = tierParam;
      if (roleParam) document.getElementById("roleFilter").value = roleParam;
      if (decadeParam) document.getElementById("decadeFilter").value = decadeParam;
      if ((tierParam && tierParam !== "ALL") || (roleParam && roleParam !== "ALL")) {{
        const drw = document.getElementById("advancedDrawer");
        const btn = document.getElementById("advFilterBtn");
        if (drw) drw.classList.add("open");
        if (btn) btn.classList.add("btn-active");
      }}
      if (shufParam === "1" || (shufParam === null && saved.shuffle)) {{
        shuffleEnabled = true;
        const btn = document.getElementById("shuffleBtn");
        if (btn) btn.classList.add("btn-active");
      }}
      if (onePerParam === "1" || (onePerParam === null && saved.oneper)) {{
        onePerSongOnly = true;
        syncOnePerSongUI();
      }}
      if (tabParam === "arch") switchTab("arch", true);

      renderTable(true);
      renderArchiveTable();

      if (SONGS.length > 0) {{
        let initSongNum = parseInt(params.get("song") || saved.song || "1", 10);
        let initIdx = filteredSongs.findIndex(x => x.n === initSongNum);
        if (initIdx < 0) initIdx = 0;
        currentIndex = initIdx;
        currentAltIdx = -1;
        const s = filteredSongs[initIdx] || SONGS[0];
        updateNowPlayingCard(s);
        pendingVideoLoad = {{ vid: s.vid, autoplay: true, initialAuto: true }};
        loadYouTubeIframeAPI();
        document.querySelectorAll("tr.song-row").forEach((tr, i) => {{
          tr.classList.toggle("active", i === initIdx);
        }});
        if (initIdx > 0) setTimeout(() => scrollToActiveRow(false), 150);
      }}
    }})();
  </script>
</body>
</html>
"""

    html_path = os.path.join(BASE_DIR, "naomi_shemer_playlist_player.html")
    index_path = os.path.join(BASE_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    secondary_paths = sync_all_secondary_exports(data)
    all_out = [js_path, update_js_path, html_path, index_path] + secondary_paths
    print("עודכנו בהצלחה כל קובצי הפרויקט:")
    for idx_p, p in enumerate(all_out, 1):
        print(f"  {idx_p}. {p}")


if __name__ == "__main__":
    generate_files()
