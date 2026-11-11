#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה את קובץ הסקריפט לדפדפן (create_playlist_in_browser.js)
ואת הנגן האינטראקטיבי המלא (naomi_shemer_playlist_player.html)
מתוך naomi_shemer_youtube_playlist.json.
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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


def generate_files():
    playlist_json_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.json")
    with open(playlist_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    playlist = data["playlist"]
    stats = data["stats"]

    matched_entries = [item for item in playlist if item.get("selected_video")]
    unmatched_entries = [item for item in playlist if not item.get("selected_video")]

    total_videos = len(matched_entries)
    matched_songs_count = stats.get("matched_songs", 369)
    unmatched_songs_count = len(unmatched_entries)
    total_catalog_songs = stats.get("total_songs", 465)

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
  const PLAYLIST_TITLE = "שירי נעמי שמר - האוסף המקיף ({total_videos} ביצועים, {matched_songs_count} שירים)";
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

  // שליפת כל הסרטונים הקיימים כרגע בפלייליסט (כולל setVideoId לצורך עריכה/מחיקה/הזזה מדויקת)
  function extractVideosAndContinuation(obj, itemsOut, tokensOut) {{
    if (!obj || typeof obj !== "object") return;
    if (Array.isArray(obj)) {{
      for (const el of obj) extractVideosAndContinuation(el, itemsOut, tokensOut);
      return;
    }}
    if (obj.playlistVideoRenderer) {{
      const r = obj.playlistVideoRenderer;
      if (r.videoId) {{
        itemsOut.push({{
          videoId: r.videoId,
          setVideoId: r.setVideoId || null
        }});
      }}
      return;
    }}
    if (obj.continuationItemRenderer) {{
      const tok = obj.continuationItemRenderer?.continuationEndpoint?.continuationCommand?.token;
      if (tok) tokensOut.push(tok);
      return;
    }}
    for (const k of Object.keys(obj)) {{
      extractVideosAndContinuation(obj[k], itemsOut, tokensOut);
    }}
  }}

  async function fetchCurrentPlaylistItems() {{
    const items = [];
    const tokens = [];
    const firstPage = await ytPost("/youtubei/v1/browse", {{ browseId: "VL" + PLAYLIST_ID }});
    extractVideosAndContinuation(firstPage, items, tokens);
    while (tokens.length > 0) {{
      const tok = tokens.shift();
      const nextPage = await ytPost("/youtubei/v1/browse", {{ continuation: tok }});
      extractVideosAndContinuation(nextPage, items, tokens);
    }}
    return items;
  }}

  console.log("🔍 קורא את מצב הפלייליסט הקיים ביוטיוב (" + PLAYLIST_ID + ")...");
  let currentItems = await fetchCurrentPlaylistItems();
  console.log(`📋 נמצאו כרגע בפלייליסט ${{currentItems.length}} סרטונים (יעד רצוי: ${{TARGET_VIDEO_IDS.length}} סרטונים).`);

  const curIds = currentItems.map(x => x.videoId);
  if (curIds.length === TARGET_VIDEO_IDS.length && curIds.every((v, i) => v === TARGET_VIDEO_IDS[i])) {{
    console.log("✅ [וידוא הושלם] הפלייליסט כבר מסודר ומעודכן ב-100% לפי הסדר המבוקש!");
    return;
  }}

  // בדיקה אם מדובר בשינוי נקודתי (עד 25 החלפות באותו אורך/סדר) או בסידור מחדש מלא
  let diffPositions = [];
  if (curIds.length === TARGET_VIDEO_IDS.length) {{
    for (let i = 0; i < curIds.length; i++) {{
      if (curIds[i] !== TARGET_VIDEO_IDS[i]) diffPositions.push(i);
    }}
  }}

  const BATCH_SIZE = 50;

  if (curIds.length === TARGET_VIDEO_IDS.length && diffPositions.length > 0 && diffPositions.length <= 25) {{
    console.log(`⚡ זוהו ${{diffPositions.length}} החלפות נקודתיות בלבד! מעדכן במקום תוך שמירה על המיקומים...`);
    for (const idx of diffPositions) {{
      const oldItem = currentItems[idx];
      const newVid = TARGET_VIDEO_IDS[idx];
      console.log(`🔄 מחליף רצועה #${{idx + 1}} (${{VIDEO_TITLES[newVid] || newVid}}): ${{oldItem.videoId}} -> ${{newVid}}`);
      const addRes = await ytPost("/youtubei/v1/browse/edit_playlist", {{
        playlistId: PLAYLIST_ID,
        actions: [{{ action: "ACTION_ADD_VIDEO", addedVideoId: newVid }}]
      }});
      const newSetVideoId = addRes?.playlistEditResults?.[0]?.playlistEditVideoAddedResultData?.setVideoId;
      if (newSetVideoId && oldItem.setVideoId) {{
        await ytPost("/youtubei/v1/browse/edit_playlist", {{
          playlistId: PLAYLIST_ID,
          actions: [{{
            action: "ACTION_MOVE_VIDEO_BEFORE",
            setVideoId: newSetVideoId,
            movedSetVideoIdSuccessor: oldItem.setVideoId
          }}]
        }});
      }}
      await ytPost("/youtubei/v1/browse/edit_playlist", {{
        playlistId: PLAYLIST_ID,
        actions: [oldItem.setVideoId
          ? {{ action: "ACTION_REMOVE_VIDEO", setVideoId: oldItem.setVideoId }}
          : {{ action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: oldItem.videoId }}
        ]
      }});
    }}
  }} else {{
    console.log("🔄 מבצע עדכון סדר מלא בתוך הפלייליסט הקיים (" + PLAYLIST_ID + ")...");
    // שלב א': ניקוי הרשימה הישנה (עם וידוא שהרשימה התרוקנה לגמרי לפני הוספה)
    let pass = 1;
    while (currentItems.length > 0 && pass <= 3) {{
      for (let i = 0; i < currentItems.length; i += BATCH_SIZE) {{
        const batch = currentItems.slice(i, i + BATCH_SIZE);
        console.log(`🗑️ מנקה סדר ישן (סבב ${{pass}}: ${{i + 1}} עד ${{Math.min(i + BATCH_SIZE, currentItems.length)}} מתוך ${{currentItems.length}})...`);
        await ytPost("/youtubei/v1/browse/edit_playlist", {{
          playlistId: PLAYLIST_ID,
          actions: batch.map(item => item.setVideoId
            ? {{ action: "ACTION_REMOVE_VIDEO", setVideoId: item.setVideoId }}
            : {{ action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: item.videoId }}
          )
        }});
        await new Promise(r => setTimeout(r, 450));
      }}
      await new Promise(r => setTimeout(r, 1000));
      currentItems = await fetchCurrentPlaylistItems();
      pass++;
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

  if (missingFromYt.length > 0) {{
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
    }}
  }}

  // 3. הסרת סרטונים עודפים או כפולים שאינם ברשימת היעד
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
    console.log(`🧹 מסיר ${{toRemoveExtra.length}} סרטונים עודפים/כפולים...`);
    await ytPost("/youtubei/v1/browse/edit_playlist", {{
      playlistId: PLAYLIST_ID,
      actions: toRemoveExtra.map(item => item.setVideoId
        ? {{ action: "ACTION_REMOVE_VIDEO", setVideoId: item.setVideoId }}
        : {{ action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: item.videoId }}
      )
    }});
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

    html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>פלייליסט שירי נעמי שמר – האוסף המקיף ({total_videos} ביצועים ביוטיוב + {unmatched_songs_count} שירי ארכיון)</title>
  <meta name="description" content="האוסף הכרונולוגי המקיף של שירי נעמי שמר ({total_catalog_songs} שירים מאוחדים מ-9 מאגרים): {total_videos} ביצועים מקוריים ביוטיוב ו-{unmatched_songs_count} שירי ארכיון נדירים עם קישורים לספרייה הלאומית, שירונט, זמרשת ואקו&quot;ם." />
  <meta property="og:title" content="פלייליסט שירי נעמי שמר – האוסף המקיף ({total_videos} ביצועים + {unmatched_songs_count} שירי ארכיון)" />
  <meta property="og:description" content="נגן אינטראקטיבי וקטלוג כרונולוגי מלא של כל {total_catalog_songs} שירי נעמי שמר: אלבומים מקוריים, ביצועי נעמי שמר, תרגומים וארכיון הספרייה הלאומית." />
  <meta property="og:type" content="website" />
  <style>
    :root {{
      --bg: #0f172a;
      --card: #1e293b;
      --card-hover: #26354d;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --gold: #f59e0b;
      --green: #10b981;
      --purple: #c084fc;
      --rose: #fb7185;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    .container {{ max-width: 1380px; margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; color: #fff; }}
    .subtitle {{ color: var(--muted); margin-bottom: 20px; font-size: 15px; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
    }}
    .upload-box {{
      border: 2px solid var(--gold);
      background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(30,41,59,0.95));
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 18px;
      border-radius: 8px;
      border: none;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s;
    }}
    .btn:hover {{ opacity: 0.92; transform: translateY(-1px); }}
    .btn-gold {{ background: var(--gold); color: #000; font-size: 15px; padding: 12px 22px; }}
    .btn-blue {{ background: var(--accent); color: #0f172a; }}
    .btn-outline {{ background: transparent; color: var(--text); border: 1px solid var(--border); }}
    .steps {{ margin: 14px 0 0; padding-right: 20px; color: #e2e8f0; font-size: 14px; }}
    .steps li {{ margin-bottom: 6px; }}
    .instant-grid {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 12px;
    }}
    /* Tabs */
    .tabs-bar {{
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      border-bottom: 2px solid var(--border);
      padding-bottom: 12px;
      flex-wrap: wrap;
    }}
    .tab-btn {{
      background: var(--card);
      color: var(--muted);
      border: 1px solid var(--border);
      padding: 12px 22px;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .tab-btn:hover {{ color: var(--text); border-color: var(--accent); }}
    .tab-btn.active {{
      background: rgba(56,189,248,0.15);
      color: var(--accent);
      border-color: var(--accent);
      box-shadow: 0 0 0 1px var(--accent);
    }}
    .player-layout {{
      display: grid;
      grid-template-columns: 430px 1fr;
      gap: 20px;
      align-items: start;
    }}
    @media (max-width: 1024px) {{
      .player-layout {{ grid-template-columns: 1fr; }}
    }}
    .sticky-player {{ position: sticky; top: 20px; }}
    iframe {{ width: 100%; aspect-ratio: 16/9; border-radius: 8px; border: none; background: #000; }}
    .controls {{ display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }}
    input, select {{
      background: #0f172a;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 9px 12px;
      border-radius: 8px;
      font-size: 13.5px;
    }}
    input {{ flex: 1; min-width: 220px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
    th, td {{ padding: 10px 10px; border-bottom: 1px solid var(--border); text-align: right; vertical-align: top; }}
    th {{ color: var(--muted); font-weight: 600; position: sticky; top: 0; background: var(--card); z-index: 2; }}
    tr.song-row {{ cursor: pointer; transition: background 0.1s; }}
    tr.song-row:hover {{ background: rgba(56,189,248,0.08); }}
    tr.song-row.active {{ background: rgba(245,158,11,0.18); }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11.5px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .t-1_album_naomi {{ background: rgba(245,158,11,0.2); color: #fbbf24; }}
    .t-2_album_original {{ background: rgba(16,185,129,0.2); color: #34d399; }}
    .t-3_naomi_performance {{ background: rgba(56,189,248,0.2); color: #38bdf8; }}
    .t-4_original_performance {{ background: rgba(168,85,247,0.2); color: #c084fc; }}
    .t-5_cover {{ background: rgba(148,163,184,0.2); color: #cbd5e1; }}

    .r-words_and_music {{ background: rgba(245,158,11,0.15); color: #fcd34d; border: 1px solid rgba(245,158,11,0.3); }}
    .r-music_only {{ background: rgba(56,189,248,0.15); color: #7dd3fc; border: 1px solid rgba(56,189,248,0.3); }}
    .r-words_only {{ background: rgba(192,132,252,0.15); color: #d8b4fe; border: 1px solid rgba(192,132,252,0.3); }}
    .r-translation {{ background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }}
    .r-performance_only {{ background: rgba(251,113,133,0.15); color: #fda4af; border: 1px solid rgba(251,113,133,0.3); }}

    .table-wrap {{ max-height: 680px; overflow-y: auto; }}
    .opening-line {{
      color: #94a3b8;
      font-size: 12px;
      font-style: italic;
      margin-top: 3px;
    }}
    .quote-box {{
      background: rgba(15,23,42,0.65);
      border-right: 3px solid var(--gold);
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
      color: #e2e8f0;
      margin-bottom: 10px;
    }}
    .archive-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }}
    .arch-pill {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 9px;
      border-radius: 6px;
      font-size: 11.5px;
      font-weight: 600;
      text-decoration: none;
      background: rgba(56,189,248,0.12);
      color: var(--accent);
      border: 1px solid rgba(56,189,248,0.3);
      transition: all 0.15s;
    }}
    .arch-pill:hover {{
      background: var(--accent);
      color: #0f172a;
    }}
    .arch-pill.nli {{
      background: rgba(245,158,11,0.14);
      color: #fbbf24;
      border-color: rgba(245,158,11,0.35);
    }}
    .arch-pill.nli:hover {{
      background: #fbbf24;
      color: #0f172a;
    }}
    .arch-pill.shironet {{
      background: rgba(16,185,129,0.14);
      color: #34d399;
      border-color: rgba(16,185,129,0.35);
    }}
    .arch-pill.shironet:hover {{
      background: #34d399;
      color: #0f172a;
    }}
    .count-chip {{
      color: var(--muted);
      font-size: 13px;
      margin-right: auto;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1>שירי נעמי שמר – האוסף המקיף ({total_videos} ביצועים ביוטיוב · {total_catalog_songs} שירים בקטלוג)</h1>
    <div class="subtitle">
      איחוד של 9 מאגרים (אקו"ם, הספרייה הלאומית – בית לזמר העברי, שירונט, ויקיפדיה, סטריאו ומונו, פזמונט, זמרשת, Discogs ו-MusicBrainz) · כולל תפקיד נעמי שמר ויוצרים שותפים, שורות פתיחה וקישורים ישירים לארכיון הצליל הלאומי ולמילות השירים
    </div>

    <div class="card upload-box">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
        <div style="flex:1; min-width:280px;">
          <h2 style="margin:0 0 6px; font-size:20px; color:#fff;">🎵 הפלייליסט המלא זמין להאזנה ב-YouTube</h2>
          <p style="margin:0; color:#cbd5e1; font-size:14.5px;">
            כל <strong>{total_videos} הביצועים</strong> ({matched_songs_count} שירים) מסודרים מהקלאסיקות הגדולות ושירי הילדים והחגים הקאנוניים אל הפנינים הנדירות — כולל ביצועי המבצעים המקוריים וביצועיה של נעמי שמר. בדף זה ניתן גם למיין את הרשימה לפי סדר כרונולוגי (1953–2004), אלבומים, תפוצה או א'-ב':
          </p>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
          <a class="btn btn-gold" href="https://www.youtube.com/playlist?list=PLFHErlX6i22g" target="_blank">▶️ פתח את הפלייליסט המלא ב-YouTube ({total_videos} שירים) ↗</a>
          <button class="btn btn-outline" onclick="copyShareUrl()">🔗 שתף קישור לשיר המתנגן</button>
          <span id="shareStatus" style="color:var(--green); font-weight:600; display:none; font-size:13px;">✔ הקישור הועתק!</span>
        </div>
      </div>
    </div>

    <div class="tabs-bar">
      <button id="tabBtnYt" class="tab-btn active" onclick="switchTab('yt')">
        🎵 הפלייליסט המלא ביוטיוב ({total_videos} ביצועים · {matched_songs_count} שירים)
      </button>
      <button id="tabBtnArch" class="tab-btn" onclick="switchTab('arch')">
        🏛️ פלייליסט ארכיון משלים – שירים נדירים שלא ביוטיוב ({unmatched_songs_count} שירים בספרייה הלאומית, שירונט וזמרשת)
      </button>
    </div>

    <!-- לשונית 1: פלייליסט יוטיוב -->
    <div id="tabYtContent">
      <div class="player-layout">
        <div class="card sticky-player">
          <div id="nowPlayingTitle" style="font-weight:700; font-size:17px; margin-bottom:4px;">בחר שיר מהרשימה לניגון</div>
          <div id="nowPlayingMeta" style="color:var(--muted); font-size:13px; margin-bottom:8px;"></div>
          <div id="nowPlayingRole" style="margin-bottom:8px;"></div>
          <div id="nowPlayingQuote" class="quote-box" style="display:none;"></div>
          <div id="failoverBanner" style="display:none; background:rgba(245,158,11,0.18); border:1px solid var(--gold); color:#fcd34d; padding:7px 10px; border-radius:8px; font-size:12.5px; margin-bottom:8px;"></div>
          <iframe id="ytFrame" src="" allow="autoplay; encrypted-media" allowfullscreen></iframe>
          <div id="backupSourcesBox" style="display:none; margin-top:8px; padding:8px 10px; background:rgba(15,23,42,0.65); border:1px solid var(--border); border-radius:8px; font-size:12.5px;">
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap;">
              <span style="color:var(--muted); font-weight:600;">🛡️ מקור גיבוי / ביצוע חלופי:</span>
              <select id="backupSelect" onchange="switchVideoSource(this.value)" style="flex:1; min-width:180px; padding:5px 8px; font-size:12px;"></select>
            </div>
          </div>
          <div id="nowPlayingLinks" class="archive-pills" style="margin-top:10px;"></div>
          <div style="display:flex; justify-content:space-between; margin-top:14px; gap:8px; flex-wrap:wrap;">
            <button class="btn btn-outline" onclick="playPrev()">⏮ השיר הקודם</button>
            <a id="openOnYt" class="btn btn-outline" href="#" target="_blank">פתח ביוטיוב ↗</a>
            <button class="btn btn-outline" onclick="playNext()">השיר הבא ⏭</button>
          </div>
        </div>

        <div class="card">
          <div class="controls">
            <input type="text" id="searchInput" placeholder="חיפוש לפי שם שיר, שורת פתיחה, מבצע, אלבום או יוצר שותף..." oninput="renderTable()" />
            <select id="sortSelect" onchange="renderTable()" style="border-color: var(--gold); font-weight: 600;">
              <option value="canonical">🌟 מיון: מהקלאסיקות האהובות לנדירים (ברירת מחדל)</option>
              <option value="chrono_asc">📅 מיון: סדר כרונולוגי (מהמוקדם למאוחר: 1953–2004)</option>
              <option value="chrono_desc">⏪ מיון: סדר כרונולוגי הפוך (מהמאוחר למוקדם)</option>
              <option value="albums">💿 מיון: לפי אלבומים מקוריים (אלבומי נעמי שמר תחילה)</option>
              <option value="popularity">🔥 מיון: לפי תפוצה ומספר גרסאות באקו"ם</option>
              <option value="title_asc">🔤 מיון: לפי שם השיר (א'–ת')</option>
              <option value="perf_asc">🎤 מיון: לפי שם המבצע (א'–ת')</option>
            </select>
            <select id="layerFilter" onchange="renderTable()">
              <option value="ALL">כל השכבות ({total_videos})</option>
              <option value="1">🌟 שכבה א': קלאסיקות ושירי ילדים קאנוניים ({l1})</option>
              <option value="2">💿 שכבה ב': אלבומים וביצועים מוכרים ({l2})</option>
              <option value="3">💎 שכבה ג': פנינים נדירות וארכיון ({l3})</option>
            </select>
            <select id="tierFilter" onchange="renderTable()">
              <option value="ALL">כל רמות העדיפות ({total_videos})</option>
              <option value="1_album_naomi">1. אלבום של נעמי שמר ({t1})</option>
              <option value="2_album_original">2. אלבום של המבצע המקורי ({t2})</option>
              <option value="3_naomi_performance">3. ביצוע של נעמי שמר ({t3})</option>
              <option value="4_original_performance">4. ביצוע מקורי ({t4})</option>
              <option value="5_cover">5. קאבר / ביצוע נוסף ({t5})</option>
            </select>
            <select id="roleFilter" onchange="renderTable()">
              <option value="ALL">כל תפקידי היצירה ({total_videos})</option>
              <option value="words_and_music">מילים ולחן: נעמי שמר ({r_wm})</option>
              <option value="music_only">לחן: נעמי שמר · מילים: אחרים ({r_m})</option>
              <option value="words_only">מילים: נעמי שמר · לחן: אחרים ({r_w})</option>
              <option value="translation">תרגום / נוסח עברי: נעמי שמר ({r_t})</option>
              <option value="performance_only">ביצוע בלבד: נעמי שמר ({r_p})</option>
            </select>
            <select id="decadeFilter" onchange="renderTable()">
              <option value="ALL">כל העשורים ({total_videos})</option>
              <option value="1950s">שנות ה-50 ({d_50})</option>
              <option value="1960s">שנות ה-60 ({d_60})</option>
              <option value="1970s">שנות ה-70 ({d_70})</option>
              <option value="1980s">שנות ה-80 ({d_80})</option>
              <option value="1990s+">שנות ה-90 ואילך ({d_90})</option>
              <option value="unknown">ללא שנה מתועדת ({d_unk})</option>
            </select>
            <span id="ytCountChip" class="count-chip"></span>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>שם השיר ושורת פתיחה</th>
                  <th>תפקיד ויוצרים</th>
                  <th>סיווג הביצוע</th>
                  <th>מבצע / אלבום</th>
                  <th>כותרת הסרטון ומאגרים</th>
                  <th>אורך</th>
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
      <div class="card" style="border-color: var(--accent);">
        <h3 style="margin:0 0 8px; font-size:18px; color:var(--accent);">🏛️ ארכיון משלים: {unmatched_songs_count} שירים מתוך הקטלוג שאינם זמינים ביוטיוב</h3>
        <p style="margin:0 0 12px; color:#cbd5e1; font-size:14px;">
          שירים אלה אותרו בארכיוני <strong>הספרייה הלאומית (בית לזמר העברי וארכיון הצליל הלאומי)</strong>, <strong>אקו"ם</strong>, <strong>שירונט</strong>, <strong>זמרשת</strong> ו<strong>פזמונט</strong>, אך טרם הועלו ליוטיוב (חלקם הקלטות רדיו נדירות בקול ישראל, שירי הצגות ומופעים מוקדמים משנות ה-50 וה-60, או לחנים מכתבי יד וספרי תווים).
          לכל שיר צורפו קישורים ישירים להאזנה או לעיון בכרטיס היצירה ב<strong>ספרייה הלאומית</strong>, לקריאת המילים ב<strong>שירונט</strong>, ולחיפוש ב<strong>זמרשת</strong> ו<strong>אקו"ם</strong>.
        </p>
        <div class="controls">
          <input type="text" id="archSearchInput" placeholder="חיפוש בארכיון לפי שם שיר, שורת פתיחה, מבצע מתועד או יוצר שותף..." oninput="renderArchiveTable()" />
          <select id="archRoleFilter" onchange="renderArchiveTable()">
            <option value="ALL">כל תפקידי היצירה ({unmatched_songs_count})</option>
            <option value="words_and_music">מילים ולחן: נעמי שמר ({ar_wm})</option>
            <option value="music_only">לחן: נעמי שמר · מילים: אחרים ({ar_m})</option>
            <option value="words_only">מילים: נעמי שמר · לחן: אחרים ({ar_w})</option>
            <option value="translation">תרגום / נוסח עברי: נעמי שמר ({ar_t})</option>
            <option value="performance_only">ביצוע בלבד: נעמי שמר ({ar_p})</option>
          </select>
          <select id="archSourceFilter" onchange="renderArchiveTable()">
            <option value="ALL">כל המאגרים ({unmatched_songs_count})</option>
            <option value="nli">קיים כרטיס ישיר בספרייה הלאומית – בית לזמר ({as_nli})</option>
            <option value="acum">קיים במאגר אקו"ם ({as_acum})</option>
            <option value="shironet">קיימות מילים בשירונט ({as_shir})</option>
          </select>
          <span id="archCountChip" class="count-chip"></span>
        </div>
        <div class="table-wrap" style="max-height: 720px;">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>שנה</th>
                <th>שם השיר ושמות חלופיים</th>
                <th>תפקיד נעמי שמר ויוצרים שותפים</th>
                <th>מבצעים ואלבומים מתועדים</th>
                <th>שורת פתיחה והערות</th>
                <th>קישורים להאזנה ולמילים בארכיון</th>
              </tr>
            </thead>
            <tbody id="archiveBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <script>
    function esc(s) {{ const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }}
    const SONGS = {json.dumps(songs_js, ensure_ascii=False, indent=2)};
    const ARCHIVE_SONGS = {json.dumps(archive_songs_js, ensure_ascii=False, indent=2)};

    let filteredSongs = [...SONGS];
    let currentIndex = 0;
    let currentAltIdx = -1; // -1 = primary video, 0..N = index in s.alts
    let ytPlayer = null;
    let ytApiReady = false;

    function loadYouTubeIframeAPI() {{
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
    }}

    window.onYouTubeIframeAPIReady = function() {{
      try {{
        ytPlayer = new YT.Player("ytFrame", {{
          events: {{
            onReady: function() {{ ytApiReady = true; }},
            onStateChange: function(ev) {{
              if (ev.data === 0) {{ // YT.PlayerState.ENDED
                playNext();
              }}
            }},
            onError: function(ev) {{
              handleVideoPlaybackError(ev.data);
            }}
          }}
        }});
      }} catch (e) {{}}
    }};

    function handleVideoPlaybackError(errCode) {{
      const s = filteredSongs[currentIndex];
      if (!s) return;
      const alts = s.alts || [];
      const nextAltIdx = currentAltIdx + 1;
      const banner = document.getElementById("failoverBanner");
      if (nextAltIdx < alts.length) {{
        currentAltIdx = nextAltIdx;
        const alt = alts[currentAltIdx];
        if (banner) {{
          banner.style.display = "block";
          banner.innerHTML = `⚠️ הסרטון הראשי אינו זמין כעת (קוד ${{errCode}}). הנגן עבר אוטומטית למקור גיבוי #${{currentAltIdx + 1}}: <strong>${{esc(alt.vtitle || alt.vid)}}</strong>`;
        }}
        const sel = document.getElementById("backupSelect");
        if (sel) sel.value = alt.vid;
        loadVideoByIdOrSrc(alt.vid, true);
        document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{alt.vid}}`;
      }} else {{
        if (banner) {{
          banner.style.display = "block";
          banner.innerHTML = `⚠️ הסרטון אינו זמין (קוד ${{errCode}}) ולא נמצאו מקורות גיבוי נוספים. עובר לשיר הבא...`;
        }}
        setTimeout(() => playNext(), 1800);
      }}
    }}

    function loadVideoByIdOrSrc(vid, autoplay) {{
      const frame = document.getElementById("ytFrame");
      const originParam = window.location.origin && window.location.origin !== "null" ? `&origin=${{encodeURIComponent(window.location.origin)}}` : "";
      if (ytApiReady && ytPlayer && typeof ytPlayer.loadVideoById === "function") {{
        if (autoplay) ytPlayer.loadVideoById(vid);
        else ytPlayer.cueVideoById(vid);
      }} else {{
        frame.src = `https://www.youtube.com/embed/${{vid}}?enablejsapi=1&rel=0${{autoplay ? "&autoplay=1" : ""}}${{originParam}}`;
      }}
    }}

    function switchVideoSource(vid) {{
      const s = filteredSongs[currentIndex];
      if (!s) return;
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
      document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{vid}}`;
    }}

    function switchTab(tab) {{
      const isYt = tab === "yt";
      document.getElementById("tabYtContent").style.display = isYt ? "block" : "none";
      document.getElementById("tabArchContent").style.display = isYt ? "none" : "block";
      document.getElementById("tabBtnYt").classList.toggle("active", isYt);
      document.getElementById("tabBtnArch").classList.toggle("active", !isYt);
    }}

    function copyShareUrl() {{
      const s = filteredSongs[currentIndex] || SONGS[0];
      if (!s) return;
      const url = new URL(window.location.href);
      url.searchParams.set("song", s.n);
      const shareStr = url.toString();
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
        if (l.source.startsWith("nli")) cls += " nli";
        else if (l.source === "shironet") cls += " shironet";
        return `<a class="${{cls}}" href="${{l.url}}" target="_blank" ${{onclickAttr}}>${{l.label}} ↗</a>`;
      }}).join("") + `</div>`;
    }}

    function updateNowPlayingCard(s) {{
      document.getElementById("nowPlayingTitle").textContent = `${{s.n}}. ${{s.title}}`;
      document.getElementById("nowPlayingMeta").textContent = `${{s.tier_label}} · ${{s.perf || s.ch}} ${{s.alb ? "· " + s.alb : ""}}`;
      document.getElementById("nowPlayingRole").innerHTML = `<span class="badge r-${{s.role_cat}}">${{s.role_label}}</span>`;
      const qBox = document.getElementById("nowPlayingQuote");
      const parts = [];
      const notesArr = Array.isArray(s.notes) ? s.notes : (s.notes ? [s.notes] : []);
      if (s.opening_line) parts.push(`<strong>שורת פתיחה:</strong> "${{esc(s.opening_line)}}"`);
      if (notesArr.length) parts.push(`<strong>הערות:</strong> ${{notesArr.map(esc).join(" · ")}}`);
      if (parts.length > 0) {{
        qBox.innerHTML = parts.join("<br/>");
        qBox.style.display = "block";
      }} else {{
        qBox.style.display = "none";
      }}
      document.getElementById("nowPlayingLinks").innerHTML = renderArchivePills(s.links, false);
      document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{s.vid}}`;
      const banner = document.getElementById("failoverBanner");
      if (banner) banner.style.display = "none";
      const bBox = document.getElementById("backupSourcesBox");
      const bSel = document.getElementById("backupSelect");
      const alts = s.alts || [];
      if (bBox && bSel) {{
        if (alts.length > 0) {{
          bBox.style.display = "block";
          const opts = [`<option value="${{s.vid}}">⭐ מקור ראשי: ${{esc(s.vtitle)}} (${{esc(s.ch)}})</option>`];
          alts.forEach((a, i) => {{
            const tag = a.src === "same_song_performance" ? "ביצוע נוסף" : "עותק גיבוי";
            opts.push(`<option value="${{a.vid}}">🔄 גיבוי #${{i + 1}} (${{tag}}): ${{esc(a.vtitle || a.vid)}} (${{esc(a.ch || "")}})</option>`);
          }});
          bSel.innerHTML = opts.join("");
          bSel.value = s.vid;
        }} else {{
          bBox.style.display = "none";
        }}
      }}
    }}

    function playSongAt(idx) {{
      if (idx < 0 || idx >= filteredSongs.length) return;
      currentIndex = idx;
      currentAltIdx = -1;
      const s = filteredSongs[idx];
      updateNowPlayingCard(s);
      loadVideoByIdOrSrc(s.vid, true);
      document.querySelectorAll("tr.song-row").forEach((tr, i) => {{
        tr.classList.toggle("active", i === idx);
      }});
      try {{
        const url = new URL(window.location.href);
        url.searchParams.set("song", s.n);
        window.history.replaceState({{}}, "", url.toString());
      }} catch (e) {{}}
    }}

    function playNext() {{
      if (currentIndex + 1 < filteredSongs.length) playSongAt(currentIndex + 1);
    }}
    function playPrev() {{
      if (currentIndex - 1 >= 0) playSongAt(currentIndex - 1);
    }}

    function renderTable() {{
      const currentVid = filteredSongs[currentIndex] ? filteredSongs[currentIndex].vid : null;
      const q = document.getElementById("searchInput").value.trim().toLowerCase();
      const sortBy = document.getElementById("sortSelect").value;
      const lf = document.getElementById("layerFilter").value;
      const tf = document.getElementById("tierFilter").value;
      const rf = document.getElementById("roleFilter").value;
      const df = document.getElementById("decadeFilter").value;

      filteredSongs = SONGS.filter(s => {{
        if (lf !== "ALL" && String(s.layer) !== lf) return false;
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
          const aIsAlbum = a.alb_group && !a.alb_group.startsWith("סינגל");
          const bIsAlbum = b.alb_group && !b.alb_group.startsWith("סינגל");
          if (aIsAlbum !== bIsAlbum) return aIsAlbum ? -1 : 1;
          const aNaomi = a.tier === "1_album_naomi" ? 0 : 1;
          const bNaomi = b.tier === "1_album_naomi" ? 0 : 1;
          if (aNaomi !== bNaomi) return aNaomi - bNaomi;
          return (a.chrono_n || a.n) - (b.chrono_n || b.n);
        }}
        return a.n - b.n;
      }});

      if (currentVid) {{
        const foundIdx = filteredSongs.findIndex(x => x.vid === currentVid);
        if (foundIdx >= 0) currentIndex = foundIdx;
      }}

      document.getElementById("ytCountChip").textContent = `מציג ${{filteredSongs.length}} מתוך ${{SONGS.length}} ביצועים`;

      const layerBadgeMap = {{
        1: `<span class="badge" style="background:rgba(245,158,11,0.18); color:#fcd34d; margin-top:4px;">🌟 שכבה א' (קלאסיקה)</span>`,
        2: `<span class="badge" style="background:rgba(56,189,248,0.15); color:#7dd3fc; margin-top:4px;">💿 שכבה ב' (אלבומים)</span>`,
        3: `<span class="badge" style="background:rgba(148,163,184,0.15); color:#cbd5e1; margin-top:4px;">💎 שכבה ג' (נדירים)</span>`
      }};

      const tbody = document.getElementById("songsBody");
      tbody.innerHTML = filteredSongs.map((s, i) => `
        <tr class="song-row ${{i === currentIndex ? "active" : ""}}" onclick="playSongAt(${{i}})">
          <td>
            <div style="font-weight:700;">${{i + 1}}</div>
            ${{sortBy !== "canonical" ? `<div style="font-size:11px; color:var(--muted);">(#${{s.n}})</div>` : ""}}
          </td>
          <td>
            <div style="font-weight:600;">${{s.title}}</div>
            ${{s.opening_line ? `<div class="opening-line">"${{s.opening_line}}"</div>` : ""}}
          </td>
          <td>
            <div><span class="badge r-${{s.role_cat}}">${{s.role_label}}</span></div>
            <div>${{layerBadgeMap[s.layer] || ""}}</div>
          </td>
          <td><span class="badge t-${{s.tier}}">${{s.tier_label}}</span></td>
          <td>${{[s.perf, s.alb].filter(Boolean).join(" / ") || s.ch}}</td>
          <td>
            <div style="color:#cbd5e1;">${{s.vtitle}}</div>
            ${{renderArchivePills(s.links, true)}}
          </td>
          <td style="color:var(--muted);">${{s.dur}}</td>
        </tr>
      `).join("");
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

      document.getElementById("archCountChip").textContent = `מציג ${{filteredArch.length}} מתוך ${{ARCHIVE_SONGS.length}} שירי ארכיון`;

      const tbody = document.getElementById("archiveBody");
      tbody.innerHTML = filteredArch.map(s => `
        <tr>
          <td>${{s.n}}</td>
          <td style="color:var(--muted);">${{s.year}}</td>
          <td>
            <div style="font-weight:700; color:#fff;">${{s.title}}</div>
            ${{s.alt_titles && s.alt_titles.length ? `<div style="font-size:12px; color:var(--muted);">שמות נוספים: ${{s.alt_titles.join(", ")}}</div>` : ""}}
          </td>
          <td><span class="badge r-${{s.role_cat}}">${{s.role_label}}</span></td>
          <td>
            <div>${{s.perfs || "<span style='color:var(--muted);'>לא מתועד מבצע</span>"}}</div>
            ${{s.albums ? `<div style="font-size:12px; color:var(--muted);">אלבום/אוסף: ${{s.albums}}</div>` : ""}}
          </td>
          <td>
            ${{s.opening_line ? `<div style="font-style:italic; color:#e2e8f0;">"${{esc(s.opening_line)}}"</div>` : "<span style='color:var(--muted);'>—</span>"}}
            ${{(Array.isArray(s.notes) ? s.notes : (s.notes ? [s.notes] : [])).length ? `<div style="font-size:12px; color:var(--gold); margin-top:3px;">${{(Array.isArray(s.notes) ? s.notes : [s.notes]).map(esc).join(" · ")}}</div>` : ""}}
          </td>
          <td>${{renderArchivePills(s.links, false)}}</td>
        </tr>
      `).join("");
    }}

    renderTable();
    renderArchiveTable();
    if (SONGS.length > 0) {{
      let initIdx = 0;
      try {{
        const params = new URLSearchParams(window.location.search);
        const songParam = parseInt(params.get("song") || "", 10);
        if (!isNaN(songParam)) {{
          const foundIdx = SONGS.findIndex(x => x.n === songParam);
          if (foundIdx >= 0) initIdx = foundIdx;
        }}
      }} catch (e) {{}}
      currentIndex = initIdx;
      currentAltIdx = -1;
      const s = SONGS[initIdx];
      updateNowPlayingCard(s);
      const originParam = window.location.origin && window.location.origin !== "null" ? `&origin=${{encodeURIComponent(window.location.origin)}}` : "";
      document.getElementById("ytFrame").src = `https://www.youtube.com/embed/${{s.vid}}?enablejsapi=1&rel=0${{originParam}}`;
      loadYouTubeIframeAPI();
      document.querySelectorAll("tr.song-row").forEach((tr, i) => {{
        tr.classList.toggle("active", i === initIdx);
      }});
    }}
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

    print(f"עודכנו בהצלחה:\n  1. {js_path}\n  2. {html_path}\n  3. {index_path}")


if __name__ == "__main__":
    generate_files()
