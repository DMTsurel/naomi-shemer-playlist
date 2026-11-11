#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
איתור ותעדוף ביצועי יוטיוב לשירי נעמי שמר מתוך הקטלוג המאוחד.

סדר עדיפויות לבחירת הסרטון המובחר לכל שיר (ללא כפילויות בין שירים):
  1. album_naomi          - ביצוע מתוך אלבום רשמי של נעמי שמר עצמה
  2. album_original       - ביצוע מתוך אלבום רשמי של המבצע המקורי / אלבום שירי נעמי שמר
  3. naomi_performance    - ביצוע של נעמי שמר עצמה (הופעה / הקלטת רדיו / טלוויזיה)
  4. original_performance - ביצוע מקורי (של המבצע המקורי מתוך הקטלוג / ארכיון)
  5. cover                - קאבר / ביצוע מחודש
"""

import csv
import json
import os
import re
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set, Tuple
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "raw_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

CATALOG_PATH = os.path.join(BASE_DIR, "naomi_shemer_catalog.json")
YT_SEARCH_CACHE_PATH = os.path.join(CACHE_DIR, "youtube_search_cache.json")
YT_TOPIC_ALBUMS_CACHE_PATH = os.path.join(CACHE_DIR, "youtube_topic_albums.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
}

NIKUD_RE = re.compile(r"[\u0591-\u05C7]")

# פלייליסטים רשמיים של אלבומי נעמי שמר ואלבומי המבצעים המקוריים ביוטיוב (OLAK5uy_...)
OFFICIAL_NAOMI_ALBUM_PLAYLISTS = [
    ("OLAK5uy_l89Mqw7PCC2HIQIdvl6jBjLIsiw9i9-Ak", "אל בורות המים", "נעמי שמר", "1_album_naomi"),
    ("OLAK5uy_m7Hyhou0eslurREtMD2UyyavX05Oi7jFQ", "על הדבש ועל העוקץ", "נעמי שמר", "1_album_naomi"),
    ("OLAK5uy_nANx6hX5o4pQG4ZfsSCP-Wfaptxrgk7Lw", "נעמי שמר שרה נעמי שמר", "נעמי שמר", "1_album_naomi"),
    ("OLAK5uy_mkiALYmJvnQ-r3QBjHycmoElLK9T5sA4E", "כיצד שוברים חמסין", "נעמי שמר", "1_album_naomi"),
    ("OLAK5uy_lrb5MmUbeDU1kora45gvUIwBCWM7achw0", "נעמי שמר שרה לילדים", "נעמי שמר", "1_album_naomi"),
    ("OLAK5uy_nvxVqjp2ccpDiaRfiN633rdF5aBqjSXKU", "ט\"ו בשבט שלי", "נעמי שמר", "1_album_naomi"),
    ("OLAK5uy_l2Lpo0FLbV-UQJcvkzLQIKfV9J_AeMD6Q", "חמש חמש", "משתתפי המחזמר חמש חמש", "2_album_original"),
    ("OLAK5uy_mI4dspMQc4Gvf6zV0hR7jF7wl-ocPhjuc", "עשרת הצדיקים", "להקת השעות הקטנות", "2_album_original"),
    ("OLAK5uy_lDhDSRbd0rCvj3jPqA7P-aPFXyD8e2Kig", "שמש במדבר", "להקת הנח\"ל", "2_album_original"),
    ("OLAK5uy_mMLMzmKasK8X7uALL6rte-cTszwdh-CME", "בגלל מסמר", "להקת פיקוד צפון", "2_album_original"),
    ("OLAK5uy_kBX_NVjfqdVim_DhdxC7M0Vd8Ywf8nQdI", "המלך ואני", "משתתפי המחזמר המלך ואני", "2_album_original"),
    ("OLAK5uy_mbRFvEepYyLXJqYTMAwiBVo_Hr6kT5CXg", "שולי נתן שרה נעמי שמר", "שולי נתן", "2_album_original"),
    ("OLAK5uy_me4EHg5QPVBx7iSonp43eomGH4u1uBAkY", "שירי נעמי שמר (חבורת בימות)", "חבורת בימות", "2_album_original"),
    ("OLAK5uy_mP0E75hkT8REoqBO3MFZ3rdffUlKEGLsU", "יוסי בנאי שר ברסאנס", "יוסי בנאי", "2_album_original"),
    ("PLevkTfR01kC7I6Cb5HgviCmGAOkNXc5l5", "מסעות בנימין השלישי", "משתתפי המחזמר מסעות בנימין השלישי", "2_album_original"),
    ("OLAK5uy_ltpJe3wlmQEQh0zqoeGCEP9q_7XHH1bfc", "אלף נשיקות", "יהורם גאון", "2_album_original"),
    ("OLAK5uy_nJDeRbUjYS2d3iWzW65PakbRdEyIJ5ZCk", "חפצים אישיים", "משה בקר", "2_album_original"),
    ("PLevkTfR01kC5ZsCMLYKvVkRotT8EGMD7E", "אצלנו בפסנתר", "משתתפי אצלנו בפסנתר", "2_album_original"),
]

NAOMI_SOLO_ALBUM_KEYWORDS = [
    "אל בורות המים",
    "על הדבש ועל העוקץ",
    "נעמי שמר שרה נעמי שמר",
    "כיצד שוברים חמסין",
    "נעמי שמר שרה לילדים",
    "ט\"ו בשבט שלי",
]

REJECT_KEYWORDS = [
    "קריוקי",
    "karaoke",
    "פלייבק",
    "playback",
    "אינסטרומנטל",
    "instrumental",
    "נעימות מפורסמות",
    "favorite melodies",
    "שיעור גיטרה",
    "שיעור פסנתר",
    "ללמוד לנגן",
    "אקורדים",
    "טאבים",
    "tutorial",
    "רינגטון",
    "ringtone",
    "רמיקס",
    "remix",
    "תיקון הכללי",
    "פרודיה",
    "בשפת הסימנים",
    "שפת הסימנים",
    "טריילר",
    "הקדמה לשיר",
    "לעבור לדף המקורי",
    "rokdim",
    "שם הריקוד",
    "שיר חדש של נעמי שמר",
    "שיר היסודות",
    "המנון הטבלה המחזורית",
    "for string orchestra",
    "string orchestra",
    "arranged by idan zion",
    "ירוסלב יעקובוביץ",
    "jaroslav jakubovic",
    "בעקבות רחל המשוררת",
    "הרצאה",
    "סיור מודרך",
    "פודקאסט",
    "acapella",
    "vocals only",
    "נערך באמצעות ai",
    "פרשה בדקה",
    "למידע נוסף",
]

VERIFIED_NAOMI_ALBUMS = [
    "אל בורות המים",
    "על הדבש ועל העוקץ",
    "נעמי שמר שרה נעמי שמר",
    "כיצד שוברים חמסין",
    "נעמי שמר שרה לילדים",
    "פירות חמישה עשר",
    "המלך ואני",
    "חמש חמש",
    "מסעות בנימין השלישי",
    "שמש במדבר",
    "חפצים אישיים",
    "אחר קציר",
    "הטיול הקטן",
    "פגישה מחודשת עם שירי גילברט",
    "עשרת הצדיקים",
    "בגלל מסמר",
    "שר ברסאנס",
    "אין אהבות שמחות",
    "חבורת בית רוטשילד ואפי נצר",
]

SONGS_REQUIRING_EXPLICIT_SHEMER = {
    "עוד חוזר הניגון",
    "האומנם",
    "זמר נוגה",
    "מותי בא לי פתע",
    "מקי הסכינאי",
    "מה שיהיה יהיה",
    "פלאי פלאים",
    "בכל דור ודור",
    "עת דודים",
    "ציפורים נודדות",
    "הלילה השנים עשר",
    "קרנבל",
    "שם חם ויפת",
    "ילד של אמא",
    "לרקוד איתך",
    "איש מוזר",
    "המנון",
    "שנה טובה",
}

GENERIC_ALBUM_NAMES = {
    "המיטב",
    "האוסף",
    "תקליט ראשון",
    "מוזיקה",
    "מוסיקה",
    "ירושלים",
    "שירי הילדים הגדולים בכל הזמנים",
    "שירי החגים הגדולים בכל הזמנים",
    "פסטיבל הזמר",
}

TIER_LABELS_HEB = {
    "1_album_naomi": "1. אלבום של נעמי שמר",
    "2_album_original": "2. אלבום של המבצע המקורי / אוסף רשמי",
    "3_naomi_performance": "3. ביצוע של נעמי שמר",
    "4_original_performance": "4. ביצוע מקורי",
    "5_cover": "5. קאבר / ביצוע נוסף",
    "6_not_found": "6. לא נמצא סרטון תואם",
}

SPELLING_VARIANTS = [
    ("איילת", "אילת"),
    ("סתיו", "סתו"),
    ("דואר", "דאר"),
    ("חופש", "חפש"),
    ("ציפורים", "צפורים"),
    ("ציפור", "צפור"),
    ("פירות", "פרות"),
    ("סוכה", "סכה"),
    ("סוכת", "סכת"),
    ("הולדת", "הלדת"),
    ("שייטת", "שיטת"),
    ("חייל", "חיל"),
    ("טיילת", "טילת"),
    ("האומנם", "האמנם"),
    ("היאחזות", "האחזות"),
    ("איקליפטוס", "אקליפטוס"),
    ("כלייזמרים", "כליזמרים"),
    ("מטרייה", "מטריה"),
    ("רביעייה", "רביעיה"),
    ("שלישיית", "שלישית"),
    ("שלישייה", "שלישיה"),
    ("נייר", "ניר"),
    ("סיפרתי", "ספרתי"),
    ("כיתה", "כתה"),
    ("נידחת", "נדחת"),
    ("פרידה", "פרדה"),
    ("מוזיקה", "מוסיקה"),
    ("נועה", "נעה"),
    ("נוגה", "נגה"),
    ("ליבבתיני", "לבבתיני"),
    ("עקידת", "עקדת"),
    ("אל\"ף בי\"ת", "אלף בית"),
    ("דוב", "דב"),
    ("בבית חלומותי", "בית חלומותי"),
    ("יושיעני", "יושיענו"),
    ("ומיכאלי", "ומיכלי"),
    ("הצלילים", "הצללים"),
    ("שייקספיר", "שקספיר"),
    ("לאין", "לאן"),
    ("אוניית", "אניית"),
    ("אונית", "אניית"),
    ("הנדל הלנה", "נחמה הנדל"),
    ("הלנה הנדל", "נחמה הנדל"),
    ("אימי", "אמי"),
    ("בנייך", "בניך"),
]

ENGLISH_TO_HEB_ARTISTS = [
    ("lehakat hanachal", "להקת הנחל"),
    ("lehakat ha nachal", "להקת הנחל"),
    ("tsevet havay shel hanachal", "צוות הווי של הנחל"),
    ("tsevet havay pikud merkaz", "צוות הווי פיקוד מרכז"),
    ("tzevet havai", "צוות הווי"),
    ("lehakat pikud tsafon", "להקת פיקוד צפון"),
    ("lehakat pikud darom", "להקת פיקוד דרום"),
    ("lehakat pikud merkaz", "להקת פיקוד מרכז"),
    ("lehakat geisot hashirion", "להקת גייסות השריון"),
    ("armored corps choir", "מקהלת גברי השריון"),
    ("havurat bimot", "חבורת בימות"),
    ("batzal yarok", "בצל ירוק"),
    ("green onion", "בצל ירוק"),
    ("gesher hayarkon", "גשר הירקון"),
    ("the roosters", "התרנגולים"),
    ("the twins", "שלישיית התאומים"),
    ("ran & nama", "רן ונמה"),
    ("chava alberstein", "חוה אלברשטיין"),
    ("hava alberstein", "חוה אלברשטיין"),
    ("yaffa yarkoni", "יפה ירקוני"),
    ("yafa yarkoni", "יפה ירקוני"),
    ("yehoram gaon", "יהורם גאון"),
    ("arik einstein", "אריק איינשטיין"),
    ("arik lavie", "אריק לביא"),
    ("shoshik shani", "שושיק שני"),
    ("shula chen", "שולה חן"),
    ("yossi banai", "יוסי בנאי"),
    ("moshe beker", "משה בקר"),
    ("moshe becker", "משה בקר"),
    ("ruhama raz", "רוחמה רז"),
    ("rivka raz", "רבקה רז"),
    ("ofira gluska", "אופירה גלוסקא"),
    ("cilla dagan", "צילה דגן"),
    ("dudu zakai", "דודו זכאי"),
    ("ilanit", "אילנית"),
    ("hadudaim", "הדודאים"),
    ("the dudaim", "הדודאים"),
    ("haparvarim", "הפרברים"),
    ("the parvarim", "הפרברים"),
    ("nehama hendel", "נחמה הנדל"),
    ("nechama hendel", "נחמה הנדל"),
    ("shoshana damari", "שושנה דמארי"),
    ("gidi gov", "גידי גוב"),
    ("matti caspi", "מתי כספי"),
    ("nurit galron", "נורית גלרון"),
    ("hagashash hachiver", "הגשש החיוור"),
    ("hagevatron", "הגבעטרון"),
    ("netanela", "נתנאלה"),
    ("ariel horowitz", "אריאל הורוביץ"),
    ("rona kenan", "רונה קינן"),
    ("shlomo gronich", "שלמה גרוניך"),
    ("rivka michaeli", "רבקה מיכאלי"),
    ("tamar giladi", "תמר גלעדי"),
    ("tiki dayan", "תיקי דיין"),
    ("gitit shoval", "גיתית שובל"),
    ("hanan yovel", "חנן יובל"),
    ("michal tal", "מיכל טל"),
    ("ofra diron", "עפרה דירון"),
    ("michal peres", "מיכל פרס"),
    ("danny ben israel", "דני בן ישראל"),
    ('cast of "ani pashosh"', "צוות אני פשוש"),
    ("ani pashosh", "צוות אני פשוש"),
    ("neomi shener", "נעמי שמר"),
    ("neomi shemer", "נעמי שמר"),
    ("hakol over habibi", "הכל עובר חביבי"),
    ("riki gal", "ריקי גל"),
    ("uzi meiri", "עוזי מאירי"),
    ("tzila dagan", "צילה דגן"),
]


def norm_heb(text: str) -> str:
    """נרמול מחרוזת עברית להשוואה גמישה (ללא ניקוד, פיסוק והבדלי כתיב מלא/חסר נפוצים)."""
    if not text:
        return ""
    s = NIKUD_RE.sub("", text).lower()
    for eng_a, heb_a in ENGLISH_TO_HEB_ARTISTS:
        s = s.replace(eng_a, heb_a)
    for full_w, def_w in SPELLING_VARIANTS:
        s = s.replace(full_w, def_w)
    # הסרת גרשיים בתוך ראשי תיבות בעברית (למשל נח"ל -> נחל, ביה"ס -> ביהס)
    s = re.sub(r'(?<=[\u0590-\u05FF])["״׳\'\u2018\u2019\u201c\u201d]+(?=[\u0590-\u05FF])', "", s)
    s = re.sub(r"[\"״'׳`–—\-_,.:;!?()\[\]/\\|•·]", " ", s)
    s = re.sub(r"\bיי", "י", s)
    s = re.sub(r"\bוו", "ו", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


KNOWN_1WORD_GROUPS = {
    "גבעטרון": "הגבעטרון",
    "פרברים": "הפרברים",
    "דודאים": "הדודאים",
    "תרנגולים": "התרנגולים",
    "שלושרים": "השלושרים",
}


def expand_performer_variants(perf: str) -> List[str]:
    """מרחיב שם מבצע (כולל היפוך 'שם משפחה שם פרטי' מאקו\"ם ופיצול צמדים) לצורך התאמה ביוטיוב."""
    base = re.sub(r"\s*\([^)]*\)", "", perf).strip()
    if not base:
        return []
    variants: List[str] = [base]
    # פיצול לפי " ו" רק עבור שמות דו-מילתיים ומעלה (ולא לפני שמות פרטיים שמתחילים ב-ו' כגון ורדה)
    sub_parts = [base]
    if " ו" in base and len(base.split()) >= 4:
        sp = [
            p.strip()
            for p in re.split(r"\s+ו(?!(?:רדה|ישינסקי|יואלדי|ילנסקי|רד)\b)(?=[א-ת])", base)
            if p.strip()
        ]
        if len(sp) >= 2 and all(len(p.split()) >= 2 for p in sp):
            sub_parts.extend(sp)

    for part in sub_parts:
        if part not in variants:
            variants.append(part)
        words = part.split()
        if len(words) == 1:
            w = words[0]
            if w in KNOWN_1WORD_GROUPS and KNOWN_1WORD_GROUPS[w] not in variants:
                variants.append(KNOWN_1WORD_GROUPS[w])
            for k_no_h, k_with_h in KNOWN_1WORD_GROUPS.items():
                if w == k_with_h and k_no_h not in variants:
                    variants.append(k_no_h)
        if len(words) == 2 and all(any("\u0590" <= c <= "\u05FF" for c in w) for w in words):
            # אם לא מתחיל במילת להקה/צוות/שלישיית/רביעיית/חמישיית/תזמורת/מקהלת/אנסמבל/חבורת/אחיות/ילדי
            if words[0] not in (
                "להקת", "צוות", "שלישיית", "רביעיית", "חמישיית", "תזמורת",
                "מקהלת", "אנסמבל", "חבורת", "האחיות", "ילדי", "זמרי", "קבוצת",
            ):
                rev = f"{words[1]} {words[0]}"
                if rev not in variants:
                    variants.append(rev)
    return variants


def parse_duration_seconds(dur_str: str) -> Optional[int]:
    if not dur_str:
        return None
    parts = [p.strip() for p in dur_str.split(":") if p.strip().isdigit()]
    if not parts:
        return None
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return None


def find_lockups(obj: Any) -> List[Dict[str, Any]]:
    res: List[Dict[str, Any]] = []
    if isinstance(obj, dict):
        if "lockupViewModel" in obj:
            res.append(obj["lockupViewModel"])
        else:
            for v in obj.values():
                res.extend(find_lockups(v))
    elif isinstance(obj, list):
        for item in obj:
            res.extend(find_lockups(item))
    return res


def fetch_official_topic_albums() -> Dict[str, List[Dict[str, Any]]]:
    """שולף את כל הרצועות מתוך פלייליסטי האלבומים הרשמיים של נעמי שמר ביוטיוב."""
    if os.path.exists(YT_TOPIC_ALBUMS_CACHE_PATH):
        with open(YT_TOPIC_ALBUMS_CACHE_PATH, "r", encoding="utf-8") as f:
            raw_map = json.load(f)
        rekeyed: Dict[str, List[Dict[str, Any]]] = {}
        for k, tr_list in raw_map.items():
            for tr in tr_list:
                if tr.get("video_id") in ("_k2Z2BwGoSA", "ZLrYDMTotCU", "zj2SGGGbnsY"):
                    continue
                nk = norm_heb(tr.get("clean_track_title", k))
                rekeyed.setdefault(nk, []).append(tr)
        return rekeyed

    tracks_by_norm_title: Dict[str, List[Dict[str, Any]]] = {}
    for pid, alb_name, perf_name, tier in OFFICIAL_NAOMI_ALBUM_PLAYLISTS:
        try:
            lups = []
            for attempt in range(3):
                r = requests.get(
                    "https://www.youtube.com/playlist",
                    params={"list": pid},
                    headers=HEADERS,
                    timeout=15,
                )
                m = re.search(r"var ytInitialData = (\{.*?\});</script>", r.text)
                if m:
                    data = json.loads(m.group(1))
                    lups = find_lockups(data)
                if lups:
                    break
                time.sleep(1.0 * (attempt + 1))
            if not lups:
                continue
            for l in lups:
                vid = l.get("contentId", "")
                raw_t = (
                    l.get("metadata", {})
                    .get("lockupMetadataViewModel", {})
                    .get("title", {})
                    .get("content", "")
                )
                if not vid or not raw_t:
                    continue
                if raw_t.startswith("הקדמה - ") or vid in ("_R16De7K1x8", "3yaCDiIaEAY"):
                    continue
                # ניקוי קידומת אומן/מספור אלבום וסיומות מתוך שם הרצועה
                clean_t = re.sub(r"^\(\"?\.{0,3}\s*", "", raw_t).strip()
                clean_t = re.sub(r"^[a-z_]+\s+", "", clean_t).strip()
                clean_t = re.sub(
                    r"^(?:(?:נעמי שמר|עודד תאומי|חבורת בימות|מירי אלוני וחבורת בימות|יהורם גאון|יוסי בנאי|להקת פיקוד הצפון|שולי נתן|משה בקר|רבקה רז)\s*[-–:]\s*|(?:מסעות בנימין השלישי|אצלנו בפסנתר)\s*-\d+-\s*)",
                    "",
                    clean_t,
                ).strip()
                clean_t = re.sub(
                    r"\s*(?:\(מתוך האלבום.*|\(קליפ,.*|[-–]?\s*הביצוע המקורי.*|\(הביצוע המקורי\)|[-–]\s*(?:יהורם גאון|חבורת בימות).*)$",
                    "",
                    clean_t,
                ).strip()
                clean_t = clean_t.strip("\"' .")
                nt = norm_heb(clean_t)
                track_info = {
                    "video_id": vid,
                    "title": raw_t,
                    "clean_track_title": clean_t,
                    "channel": "נעמי שמר - Topic" if tier == "1_album_naomi" else "Release - Topic",
                    "duration": "",
                    "description": f"Provided to YouTube · {perf_name} · מתוך האלבום: {alb_name}",
                    "album_name": alb_name,
                    "performer_name": perf_name,
                    "forced_tier": tier,
                    "playlist_id": pid,
                }
                tracks_by_norm_title.setdefault(nt, []).append(track_info)
                # אם יש סוגריים כמו "אצלנו בחצר (אורחים לקיץ)", נשמור גם לפי שני החלקים
                m_paren = re.match(r"^(.+?)\s*\((.+?)\)\s*$", clean_t)
                if m_paren:
                    for part in (m_paren.group(1), m_paren.group(2)):
                        np = norm_heb(part)
                        if np:
                            tracks_by_norm_title.setdefault(np, []).append(track_info)
        except Exception as e:
            print(f"  [!] שגיאה בשליפת פלייליסט אלבום {pid}: {e}")

    with open(YT_TOPIC_ALBUMS_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(tracks_by_norm_title, f, ensure_ascii=False, indent=2)
    return tracks_by_norm_title


def youtube_search_raw(query: str) -> List[Dict[str, Any]]:
    """מבצע חיפוש ביוטיוב ומחזיר עד 20 תוצאות עם מטא-דאטה מלא."""
    for attempt in range(3):
        try:
            r = requests.get(
                "https://www.youtube.com/results",
                params={"search_query": query},
                headers=HEADERS,
                timeout=15,
            )
            if r.status_code != 200:
                time.sleep(1.5 * (attempt + 1))
                continue
            m = re.search(r"var ytInitialData = (\{.*?\});</script>", r.text)
            if not m:
                return []
            data = json.loads(m.group(1))
            contents = (
                data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
            )
            results: List[Dict[str, Any]] = []
            for sec in contents:
                for it in sec.get("itemSectionRenderer", {}).get("contents", []):
                    if "videoRenderer" not in it:
                        continue
                    v = it["videoRenderer"]
                    vid = v.get("videoId", "")
                    if not vid:
                        continue
                    title = "".join(run.get("text", "") for run in v.get("title", {}).get("runs", []))
                    channel = "".join(run.get("text", "") for run in v.get("ownerText", {}).get("runs", []))
                    dur = v.get("lengthText", {}).get("simpleText", "")
                    desc = ""
                    if v.get("detailedMetadataSnippets"):
                        desc = "".join(
                            run.get("text", "")
                            for run in v["detailedMetadataSnippets"][0].get("snippetText", {}).get("runs", [])
                        )
                    results.append({
                        "video_id": vid,
                        "title": title,
                        "channel": channel,
                        "duration": dur,
                        "description": desc,
                    })
            return results
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return []


def fetch_video_details_by_id(video_id: str) -> Optional[Dict[str, Any]]:
    """שולף כותרת וערוץ עבור מזהה יוטיוב קיים מהקטלוג."""
    try:
        r = requests.get(
            "https://www.youtube.com/watch",
            params={"v": video_id},
            headers=HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            return None
        m_title = re.search(r'"title":"([^"]+)"', r.text)
        m_author = re.search(r'"author":"([^"]+)"', r.text)
        m_len = re.search(r'"lengthSeconds":"(\d+)"', r.text)
        title = m_title.group(1) if m_title else ""
        channel = m_author.group(1) if m_author else ""
        dur_str = ""
        if m_len:
            sec = int(m_len.group(1))
            dur_str = f"{sec // 60}:{sec % 60:02d}"
        if not title:
            return None
        return {
            "video_id": video_id,
            "title": title,
            "channel": channel,
            "duration": dur_str,
            "description": "מזהה יוטיוב מתוך מאגרי נעמי שמר (אקו\"ם / סטריאו ומונו / פזמונט)",
            "from_catalog_id": True,
        }
    except Exception:
        return None


def build_song_target_phrases(song: Dict[str, Any]) -> List[str]:
    """בונה רשימת ביטויי יעד מנורמלים לזיהוי השיר בכותרת הסרטון."""
    phrases: List[str] = []
    raw_candidates = [song["title"]] + song.get("alt_titles", [])
    for rc in raw_candidates:
        if not rc:
            continue
        # הסרת סוגריים כגון "כנרת (שם הרי גולן)" -> גם המלא וגם כל חלק
        n_full = norm_heb(rc)
        if n_full and n_full not in phrases:
            phrases.append(n_full)
        m_p = re.match(r"^(.+?)\s*\((.+?)\)\s*$", rc)
        if m_p:
            for p in (m_p.group(1), m_p.group(2)):
                np = norm_heb(p)
                if np and len(np) >= 2 and np not in phrases:
                    phrases.append(np)
        # אם יש לוכסן או מקף בשם השיר
        if "/" in rc:
            for p in rc.split("/"):
                np = norm_heb(p)
                if np and len(np) >= 2 and np not in phrases:
                    phrases.append(np)

    if song.get("opening_line"):
        nol = norm_heb(song["opening_line"])
        if nol and len(nol.split()) >= 2:
            phrases.append(nol)
            # גם 4 המילים הראשונות של שורת הפתיחה
            words = nol.split()
            if len(words) >= 4:
                short_ol = " ".join(words[:4])
                if short_ol not in phrases:
                    phrases.append(short_ol)
    return phrases


def title_matches_song(
    vid_title: str,
    vid_channel: str,
    vid_desc: str,
    target_phrases: List[str],
    all_other_multiword_titles: Set[str],
) -> bool:
    """בודק האם כותרת הסרטון אכן מתאימה לשיר המבוקש (ולא לשיר אחר של נעמי שמר או של יוצר אחר)."""
    ntitle = norm_heb(vid_title)
    ndesc = norm_heb(vid_desc)
    if not ntitle:
        return False

    # הסרת שמות מבצעים/להקות שמכילים מילה זהה לשם שיר בן מילה אחת (כמו שלומי שבת, דולי מודעי, פיקוד צפון)
    ntitle_for_1word = ntitle
    for conf_perf in ("שלומי שבת", "דולי מודעי", "להקת פיקוד צפון", "להקת פיקוד הצפון", "פיקוד צפון", "פיקוד הצפון"):
        ntitle_for_1word = ntitle_for_1word.replace(conf_perf, " ")

    # אם זהו סרטון Topic (ללא שם מבצע בכותרת הסרטון), נדרוש שכותרת הסרטון (ללא סוגריים) תהיה זהה לאחד מביטויי היעד
    is_topic_channel = "- topic" in vid_channel.lower()
    clean_vid_title_no_parens = norm_heb(re.sub(r"\s*\([^)]*\)", "", vid_title))

    matched_phrase = None
    for tp in target_phrases:
        if not tp:
            continue
        if is_topic_channel and " - " not in vid_title and " – " not in vid_title:
            if clean_vid_title_no_parens == tp or ntitle == tp:
                matched_phrase = tp
                break
            continue
        check_t = ntitle_for_1word if len(tp.split()) == 1 else ntitle
        pattern = rf"(?:^|\s){re.escape(tp)}(?:\s|$)"
        if re.search(pattern, check_t):
            matched_phrase = tp
            break
        if "provided to youtube" in ndesc and re.search(pattern, ndesc):
            matched_phrase = tp
            break

    if not matched_phrase:
        return False

    # הגנה מפני התאמה שגויה בשמות שירים קצרים או נפוצים (כגון "אור", "שבת", "מחר", "אל הכפר", "אחותי", "יריד", "רביעייה")
    target_set = set(target_phrases)
    if len(matched_phrase.split()) <= 2:
        for other_t in all_other_multiword_titles:
            if other_t in target_set or (matched_phrase in other_t.split() and other_t == matched_phrase):
                continue
            if matched_phrase == "פרולוג" and other_t == "שקספיר איננו":
                continue
            # אם כותרת הסרטון מכילה שם של שיר מרובה-מילים אחר מהקטלוג
            if re.search(rf"(?:^|\s){re.escape(other_t)}(?:\s|$)", ntitle):
                return False
        # מניעת התאמת "אל הכפר" ל-"הדרך אל הכפר", "אחותי" ל-"אחותי הקטנה", "יריד" ל-"יריד המזרח", "רביעיה" ל-"אומרים ישנה ארץ"
        if (
            f"הדרך {matched_phrase}" in ntitle
            or f"{matched_phrase} הקטנה" in ntitle
            or (matched_phrase in ("יריד", "היריד") and "יריד המזרח" in ntitle)
        ):
            return False
    return True


def is_naomi_performer_in_video(
    vid_title: str,
    vid_channel: str,
    vid_desc: str,
    other_performers: List[str],
    song_performers: List[str],
) -> bool:
    """בודק האם נעמי שמר עצמה היא המבצעת של הסרטון (ולא רק מחברת/מלחינה/מתרגמת בקרדיט)."""
    ch_lower = vid_channel.lower()
    if "נעמי שמר - topic" in ch_lower or "naomi shemer - topic" in ch_lower:
        return True
    if "provided to youtube" in vid_desc.lower():
        # בתיאור Provided to YouTube המבצע מופיע מיד אחרי הנקודה האמצעית הראשונה (·) בלבד
        if re.search(r"^[^·]*·\s*(?:naomi shemer|נעמי שמר)\b", vid_desc, flags=re.I):
            return True
        return False

    combined_td = f"{vid_title} {vid_desc}"
    # סינון הרכבים/אירועים קהילתיים שנושאים את שמה של נעמי שמר אך אינם ביצוע שלה
    if any(
        x in combined_td
        for x in (
            "אנסמבל נעמי שמר",
            "בואו שיר",
            "קולולם",
            "חבורת הזמר",
            "בביצוע מקהלת",
            "להקת השעות הקטנות",
            "חבורת בימות",
            'להקת הנח"ל - ואלס',
        )
    ):
        return False
    if ('להקת הנח"ל' in vid_title or "the nahal band" in vid_title.lower()) and "נעמי שמר ולהקת" not in vid_title:
        return False

    # אם בכותרת כתוב "מאת נעמי שמר[,] שרה/שר/שרים <מישהו אחר שאינו נעמי שמר>"
    m_by_shemer_sung = re.search(r"מאת\s+נעמי שמר\s*,?\s*שר(?:ה|ים|ות)\s+([^\n|•·]+)", combined_td)
    if m_by_shemer_sung and "נעמי שמר" not in m_by_shemer_sung.group(1):
        return False

    # אם בתיאור מצוין במפורש "ביצוע: X" או "שירה: X" שלא כולל את נעמי שמר
    m_perf_credit = re.search(
        r"(?:ביצוע|בצוע|שירה)\s*:\s*((?:(?!(?:מילים|מלים|לחן|עיבוד|תרגום|מתוך)\b)[^\n|•·])+)",
        vid_desc,
    )
    if m_perf_credit:
        credited = m_perf_credit.group(1).strip()
        if "שמר" not in credited and "shemer" not in credited.lower():
            return False

    # דפוס מובהק 0: קרדיט ביצוע מפורש לנעמי שמר ("ביצוע: נעמי שמר" / "שירה: נעמי שמר" / "נעמי שמר בשירה האחרון" / דואט "גידי גוב ונעמי שמר")
    if (
        re.search(
            r"(?:ביצוע|בצוע|שירה|שרה|שרות|שרים)\s*:\s*(?:(?!(?:מילים|מלים|לחן|עיבוד|תרגום|מתוך|ביצוע|שירה)\b)[^\n|•·])*נעמי שמר",
            combined_td,
        )
        or re.search(r"(?:בביצוע|שרה)\s+נעמי שמר|(?:שרות|שרים)\s+נעמי שמר(?:\s*,|\s+ו)", combined_td)
        or re.search(r"(?<!מאת\s)נעמי שמר\s+(?:שרה\b(?!\s+[א-ת])|בשירה)", combined_td)
        or ("גידי גוב ונעמי שמר" in combined_td)
        or ("נעמי שמר והדודאים" in combined_td)
        or ("נעמי שמר ולהקת" in combined_td)
        or ("נעמי שמר וילדי" in combined_td)
        or ("בתכנית עם נעמי שמר" in combined_td)
        or ("אלון אולארציק" in combined_td and "נעמי שמר" in combined_td)
    ):
        return True

    # אם בכותרת כתוב שהקרדיט של נעמי שמר הוא מילים/לחן/תרגום/מאת/by, היא לא המבצעת
    if re.search(
        r"(?:מילים|מלים|לחן|תרגום|עברית|נוסח עברי|מאת|שירי|משירי|מחווה ל|ערב|by)\s*[:\-–]?\s*(?:נעמי שמר|naomi shemer)",
        vid_title,
        flags=re.I,
    ):
        return False
    if re.search(r"שר[הים]\s+(?:את\s+)?[^\s]+.*נעמי שמר", vid_title):
        return False

    # דואט או הרכב שמתחיל ב-"נעמי שמר ו<אמן נוסף> - <שם השיר>"
    if re.match(r"^\s*נעמי שמר\s+ו.+?\s+[-–]\s+", vid_title):
        return True

    # אם כותרת הסרטון מכילה מבצע מוכר אחר של השיר (שאינו נעמי שמר), אז נעמי שמר מצוינת כיוצרת ולא כמבצעת
    ntitle = norm_heb(vid_title)
    for op in other_performers:
        for v_op in expand_performer_variants(op):
            nop = norm_heb(v_op)
            if nop and nop not in ("נעמי שמר", "naomi shemer") and len(nop) >= 3:
                if re.search(rf"(?:^|\s){re.escape(nop)}(?:\s|$)", ntitle):
                    return False

    # האם נעמי שמר מתועדת כמבצעת של השיר הזה בקטלוג?
    naomi_in_catalog_perfs = any(
        "נעמי שמר" in p or "שמר נעמי" in p or "Naomi Shemer" in p for p in song_performers
    )
    if not naomi_in_catalog_perfs:
        return False

    # דפוס מובהק 1: כותרת שמתחילה ב-"נעמי שמר - " (בפורמט מבצע - שם שיר)
    if re.match(r"^\s*(?:נעמי שמר|naomi shemer)\s*[-–]", vid_title, flags=re.I):
        return True

    # אם בתיאור מצוין שהיא רק כתבה/הלחינה ("כתבה והלחינה: נעמי שמר") ללא קרדיט שירה
    if re.search(r"(?:כתבה והלחינה|מילים ולחן)\s*:\s*נעמי שמר", vid_desc) and "נעמי שמר שרה" not in vid_desc:
        return False

    # אם הכותרת מורכבת מ-3 חלקים או יותר המופרדים במקפים (כגון "שיר - נעמי שמר - זמר אחר" או "Naomi Shemer - Singer - Song")
    hyphen_parts = [p.strip() for p in re.split(r"\s+[-–|]\s+", vid_title) if p.strip()]
    if len(hyphen_parts) >= 3 and "רון בכר" not in vid_title:
        return False

    # דפוס 3: "<שם שיר> - נעמי שמר" רק בערוצי ארכיון מוכרים או כשנעמי שמר היא המבצעת היחידה של השיר
    TRUSTED_NAOMI_CHANNELS = (
        "כאן | מוזיקה",
        "אוצר הזמר העברי",
        "שיר עד",
        "רון בכר",
        "דוד אסף",
        "gila hassid",
        "noam .menashe",
        "נעמי שמר - יש לי חבר",
    )
    if re.search(r"[-–|]\s*(?:נעמי שמר|naomi shemer)\s*(?:[-–|(]|$)", vid_title, flags=re.I):
        if any(tc in ch_lower for tc in TRUSTED_NAOMI_CHANNELS):
            return True

    return False


def match_known_performer(vid_title: str, vid_channel: str, vid_desc: str, performers: List[str]) -> Tuple[Optional[str], int]:
    """בודק האם אחד המבצעים המוכרים של השיר מופיע בסרטון, ומחזיר את שם המבצע ומיקומו ברשימה."""
    # הסרת קרדיטים של מילים/לחן/עיבוד/תרגום מהכותרת כדי שמלחין שהוא גם המבצע (כמו שלמה גרוניך) לא יזוהה כמבצע בקאבר של אחרים
    title_without_composer_credits = re.sub(
        r"(?:מילים|מלים|לחן|עיבוד|תרגום|מאת)\s*:\s*[^,;|()\n]+",
        " ",
        vid_title,
    )
    combined_title_ch = norm_heb(f"{title_without_composer_credits} {vid_channel}")
    ndesc = norm_heb(vid_desc)
    for idx, perf in enumerate(performers):
        if perf.strip() in ("נעמי שמר", "Naomi Shemer", "שמר נעמי"):
            continue
        variants = expand_performer_variants(perf)
        display_perf = variants[-1] if len(variants) >= 2 and len(variants[0].split()) == 2 else (variants[0] if variants else perf)
        for v_perf in variants:
            nperf = norm_heb(v_perf)
            if not nperf or len(nperf) < 3:
                continue
            if re.search(rf"(?:^|\s)[ובכלהמ]?{re.escape(nperf)}(?:\s|$)", combined_title_ch):
                return display_perf, idx
            if (
                "provided to youtube" in ndesc
                or "בשיתוף" in vid_desc
                or re.search(r"(?:ביצוע|בצוע|שירה|שרה|שרים|שרות)\s*:", vid_desc)
            ) and re.search(rf"(?:^|\s)(?<!שרים\s)[ובכלהמ]?{re.escape(nperf)}(?:\s|$)", ndesc):
                return display_perf, idx
    return None, 999


def match_known_album(vid_title: str, vid_desc: str, song_albums: List[str], song_title: str) -> Optional[str]:
    """בודק האם הסרטון מתייחס לאחד האלבומים המשויכים לשיר (ללא אלבומים ששמם זהה לשם השיר או גנרי)."""
    nsong = norm_heb(song_title)
    ndesc = norm_heb(vid_desc)
    ntitle = norm_heb(vid_title)
    norm_generic = {norm_heb(g) for g in GENERIC_ALBUM_NAMES}

    # תחילה בדיקה מול רשימת האלבומים הרשמיים של נעמי שמר / מחזות זמר בתיאור או בכותרת
    for valb in VERIFIED_NAOMI_ALBUMS:
        nvalb = norm_heb(valb)
        if nvalb and nvalb != nsong:
            if re.search(rf"(?:^|\s){re.escape(nvalb)}(?:\s|$)", f"{ntitle} {ndesc}"):
                return valb

    # בדיקה מול אלבומי השיר מהקטלוג (רק בתיאור הסרטון, וללא אלבום ששמו זהה לשם השיר)
    for alb in song_albums:
        base_alb = re.sub(r"\s*\([^)]*\)", "", alb).strip()
        nalb = norm_heb(base_alb)
        if not nalb or len(nalb) < 4 or nalb == nsong or nalb in norm_generic:
            continue
        if re.search(rf"(?:^|\s){re.escape(nalb)}(?:\s|$)", ndesc):
            return base_alb
    return None


def has_conflicting_composer_credit(vid_title: str, vid_desc: str, song: Dict[str, Any]) -> bool:
    """בודק האם הסרטון מציין במפורש מלחין אחר שאינו נעמי שמר ואינו ברשימת מלחיני השיר."""
    combined = f"{vid_title}\n{vid_desc}"
    # אם הסרטון נותן קרדיט מפורש לנעמי שמר כמחברת המילים או כמתרגמת, לחן של מלחין אחר אינו סתירה
    if re.search(r"(?:מילים|מלים|תרגום|נוסח עברי|עברית)\s*:\s*[^\n|•·,;]*שמר", combined) or "למילותיה של נעמי שמר" in combined:
        return False
    matches = re.findall(r"(?:מילים ולחן|מלים ולחן|לחן|composer)\s*:\s*([^\n|•·,;]+)", combined, flags=re.I)
    if not matches:
        return False
    allowed_comp_norm = norm_heb(" ".join(song.get("composers", []) + song.get("authors", []) + ["נעמי שמר", "naomi shemer", "עממי", "נחלת הכלל"]))
    for m in matches:
        cm = norm_heb(m)
        if not cm:
            continue
        if "שמר" in cm or "shemer" in cm or "עממי" in cm:
            continue
        # בדיקה אם לפחות מילה משמעותית משם המלחין מופיעה ברשימת המלחינים המורשים של השיר
        words = [w for w in cm.split() if len(w) >= 3]
        if words and not any(w in allowed_comp_norm for w in words):
            return True
    return False


def classify_and_score_candidate(
    cand: Dict[str, Any],
    song: Dict[str, Any],
    target_phrases: List[str],
    all_other_multiword_titles: Set[str],
    rank_idx: int,
) -> Optional[Dict[str, Any]]:
    """מסווג מועמד יוטיוב לאחת מ-5 רמות העדיפות ומחשב ציון איכות."""
    vid_title = cand.get("title", "")
    vid_channel = cand.get("channel", "")
    vid_desc = cand.get("description", "")
    dur_str = cand.get("duration", "")

    # אם מדובר ברצועה שהגיעה ישירות מפלייליסט אלבום רשמי (OLAK5uy_...)
    if cand.get("forced_tier"):
        tier = cand["forced_tier"]
        base_score = 5000 if tier == "1_album_naomi" else 4000
        matched_perf = cand.get("performer_name", "נעמי שמר")
        if tier == "2_album_original":
            if cand.get("album_name") == "אצלנו בפסנתר":
                if song["title"] == "הכל פתוח":
                    tier = "1_album_naomi"
                    base_score = 4800
                    matched_perf = "נעמי שמר"
                elif song["title"] != "פרי חדש":
                    tier = "5_cover"
                    base_score = 950
            elif cand.get("album_name") == "שולי נתן שרה נעמי שמר" and song["title"] not in (
                "שיר ערש לצבעים", "זמר", "בקיץ", "קרן יער", "כפות רגליך לבנות", "בגני נטעתיך", "כי לא יהיה להם יום", "מתי"
            ):
                tier = "5_cover"
                base_score = 950
        return {
            "video_id": cand["video_id"],
            "url": f"https://www.youtube.com/watch?v={cand['video_id']}",
            "video_title": vid_title,
            "channel": vid_channel,
            "duration": dur_str,
            "description": vid_desc,
            "tier": tier,
            "tier_label": TIER_LABELS_HEB[tier],
            "matched_performer": matched_perf,
            "matched_album": cand.get("album_name", ""),
            "score": base_score,
        }

    # 1. פסילה קשיחה (Hard Reject) של פלייבקים, קריוקי, שיעורי נגינה, נעימות אינסטרומנטליות, שפת הסימנים וכו'
    combined_all_lower = f"{vid_title} {vid_channel} {vid_desc}".lower()
    song_title_lower = song["title"].lower()
    for rk in REJECT_KEYWORDS:
        if rk in combined_all_lower and rk not in song_title_lower:
            return None
    if re.search(r"(?:[-–|]\s*ריקוד\b|\bdance\b)", vid_title.lower()) and "ריקוד" not in song_title_lower:
        return None

    # 2. פסילה קשיחה אם הסרטון נותן קרדיט מפורש למלחין אחר שאינו קשור לשיר
    if has_conflicting_composer_credit(vid_title, vid_desc, song):
        return None

    # 3. בדיקת התאמת שם השיר
    if not cand.get("from_catalog_id"):
        if not title_matches_song(vid_title, vid_channel, vid_desc, target_phrases, all_other_multiword_titles):
            return None

    # 4. בדיקת משך הסרטון
    is_topic_or_provided = (
        "- topic" in vid_channel.lower()
        or "provided to youtube" in vid_desc.lower()
        or "auto-generated by youtube" in vid_desc.lower()
    )
    dur_sec = parse_duration_seconds(dur_str)
    if dur_sec is not None:
        min_dur = 25 if (is_topic_or_provided or "כאן | מוזיקה" in vid_channel) else 35
        if dur_sec < min_dur or dur_sec > 780:
            return None

    if cand.get("video_id") in ("0-81T23NXr8", "OvN5nJ9bn2Y", "60221_oJK1U"):
        # 0-81T23NXr8: קטע קצר וקטוע (46 שניות) של "שנה טובה"
        # OvN5nJ9bn2Y: שיר הילדים "שנה טובה" של לוין קיפניס ונחום נרדי ששויך בטעות בהפצה דיגיטלית לנעמי שמר
        # 60221_oJK1U: "כמו חצב - יהורם גאון" מזוהה בטעות כביצוע של נעמי שמר בגלל "בתכנית עם נעמי שמר" בתיאור
        return None

    penalty = 0
    if "מחרוזת" in vid_title and "מחרוזת" not in song["title"]:
        penalty -= 700
    if "גרסה מחודשת" in f"{vid_title} {vid_desc}":
        penalty -= 600
    if "מופע" in vid_title and "מופע" not in song["title"]:
        penalty -= 50

    performers = song.get("performers", [])
    albums = song.get("albums", [])
    naomi_sings = is_naomi_performer_in_video(vid_title, vid_channel, vid_desc, performers, performers)
    matched_perf, perf_idx = match_known_performer(vid_title, vid_channel, vid_desc, performers)
    matched_alb = match_known_album(vid_title, vid_desc, albums, song["title"])

    # בדיקת שיוך לנעמי שמר / לקטלוג כדי לסנן שירים של יוצרים אחרים עם שם זהה
    combined_all_norm = norm_heb(f"{vid_title} {vid_channel} {vid_desc}")
    mentions_shemer = (
        "נעמי שמר" in combined_all_norm
        or "נעמי ספיר" in combined_all_norm
        or "naomi shemer" in combined_all_norm
        or "האחיות שמר" in combined_all_norm
        or "חבורת בימות" in combined_all_norm
        or "ללי שמר" in combined_all_norm
    )

    # עבור שירים שבהם נעמי שמר היא מבצעת בלבד (לא מחברת/מלחינה/מתרגמת), חובה שהביצוע בסרטון יהיה של נעמי שמר עצמה
    if set(song.get("roles", [])) == {"performer"} and not naomi_sings:
        return None

    # עבור שירים שיש להם גרסאות מפורסמות בלחן של מלחין אחר או שמות גנריים נפוצים, חובה אזכור מפורש של נעמי שמר
    if song["title"] in SONGS_REQUIRING_EXPLICIT_SHEMER and not mentions_shemer:
        return None

    matches_opening = False
    if song.get("opening_line") and len(song["opening_line"].split()) >= 3:
        nol_short = " ".join(norm_heb(song["opening_line"]).split()[:3])
        if nol_short and nol_short in combined_all_norm:
            matches_opening = True

    verified_albums_norm = {norm_heb(va) for va in VERIFIED_NAOMI_ALBUMS}
    has_verified_album = bool(matched_alb and norm_heb(matched_alb) in verified_albums_norm)

    # חובה עוגן קשיח (אזכור נעמי שמר / מבצע מקורי מהקטלוג / אלבום מאומת של נעמי שמר / שורת פתיחה)
    if not cand.get("from_catalog_id"):
        if not (mentions_shemer or matched_perf or has_verified_album or matches_opening):
            return None

    is_archival_original = bool(
        re.search(
            r"(?:הביצוע המקורי|ביצוע מקורי(?!\s*:)|הביצוע הראשון(?!\s*:)|הקלטה מקורית|קול ישראל|בית לזמר העברי|זמריר מאת נעמי שמר|אוצרות ארכיון ישראלי - רון בכר)",
            f"{vid_title} {vid_desc}",
        )
    )

    combined_tcd = f"{vid_title} {vid_channel} {vid_desc}"
    combined_tcd_lower = combined_tcd.lower()
    is_late_cover_album = (
        any(
            cov_kw in combined_tcd
            for cov_kw in (
                "הלהקה - פסקול הסרט",
                "Participants of 'The Troup'",
                "25 שירי הילדים הכי יפים",
                "בלוז לנעמי",
                "שרים נעמי שמר",
                "נעמי שמר השירים היפים",
                "כולם שרים נעמי שמר",
                "רגעים נפלאים",
                "האחיות שמר 24",
                "גרסה מחודשת",
            )
        )
        or ("Gitit Shoval" in combined_tcd and song["title"] != "למה צחקה מיכל")
        or ("האירוסים" in combined_tcd and song["title"] != "פרדס חנה בשבת")
        or ("יוני נמרי" in combined_tcd or "yoni namari" in combined_tcd_lower)
        or (song["title"] == "בשדה תלתן" and ("דודו זכאי" in combined_tcd or "dudu zakai" in combined_tcd_lower))
        or (song["title"] == "שיר לגדעון" and ("פיקוד צפון" in combined_tcd or "פיקוד הצפון" in combined_tcd or "pikud tsafon" in combined_tcd_lower))
        or (song["title"] == "העיר באפור" and ("הדודאים" in combined_tcd or "dudaim" in combined_tcd_lower))
        or (song["title"] == "אחותי רוחמה" and "מור וקינמון" in combined_tcd)
    )

    is_official_album_channel = is_topic_or_provided or (
        matched_alb
        and any(
            ch_kw in vid_channel.lower()
            for ch_kw in ("הערוץ הרשמי", "official", "פונוקול", "ישראפון", "האלבומים הגדולים", "shir ivri")
        )
    )

    # קביעת רמת העדיפות (1 עד 5)
    if naomi_sings and (is_topic_or_provided or any(k in f"{vid_title} {vid_desc}" for k in NAOMI_SOLO_ALBUM_KEYWORDS)):
        tier = "1_album_naomi"
        base_score = 4800
        matched_perf = "נעמי שמר"
        if not matched_alb:
            for k in NAOMI_SOLO_ALBUM_KEYWORDS:
                if k in f"{vid_title} {vid_desc}":
                    matched_alb = k
                    break
    elif (
        is_official_album_channel
        and not is_late_cover_album
        and (
            perf_idx <= 3
            or "חבורת בימות" in f"{vid_title} {vid_desc}"
            or ("האחיות שמר" in f"{vid_title} {vid_desc}" and "האחיות שמר 24" not in f"{vid_title} {vid_desc}")
            or "בית רוטשילד" in f"{vid_title} {vid_desc}"
        )
    ):
        tier = "2_album_original"
        eff_idx = 0 if perf_idx >= 999 else perf_idx
        base_score = (3900 if is_topic_or_provided else 3780) - min(eff_idx * 80, 400)
    elif naomi_sings:
        tier = "3_naomi_performance"
        base_score = 2800
        matched_perf = "נעמי שמר"
    elif not is_late_cover_album and (matched_perf or (is_archival_original and mentions_shemer) or cand.get("from_catalog_id")):
        tier = "4_original_performance"
        eff_idx = 0 if perf_idx >= 999 else perf_idx
        base_score = 1800 - min(eff_idx * 80, 400)
        if is_archival_original:
            base_score += 80
        if any(
            ch_kw in vid_channel.lower()
            for ch_kw in ("הערוץ הרשמי", "official", "כאן | מוזיקה", "ישראפון", "פונוקול", "שיר עד", "אוצר הזמר העברי")
        ):
            base_score += 40
        if not matched_perf and cand.get("from_catalog_id") and performers:
            matched_perf = performers[0]
    elif is_topic_or_provided:
        # אלבום רשמי ביוטיוב של אמן אחר (קאבר אלבומי)
        tier = "5_cover"
        base_score = 950
    else:
        tier = "5_cover"
        base_score = 800

    # בונוס לתוצאות גבוהות בדירוג החיפוש ולמזהים מתוך הקטלוג
    rank_bonus = max(0, 40 - rank_idx * 3)
    cat_bonus = 50 if cand.get("from_catalog_id") else 0
    total_score = base_score + rank_bonus + cat_bonus + penalty

    if total_score < 300:
        return None

    return {
        "video_id": cand["video_id"],
        "url": f"https://www.youtube.com/watch?v={cand['video_id']}",
        "video_title": vid_title,
        "channel": vid_channel,
        "duration": dur_str,
        "description": vid_desc[:200],
        "tier": tier,
        "tier_label": TIER_LABELS_HEB[tier],
        "matched_performer": matched_perf or "",
        "matched_album": matched_alb or "",
        "score": total_score,
    }


def find_candidates_for_song(
    song: Dict[str, Any],
    topic_tracks_map: Dict[str, List[Dict[str, Any]]],
    search_cache: Dict[str, List[Dict[str, Any]]],
    all_other_multiword_titles: Set[str],
) -> Tuple[List[Dict[str, Any]], bool]:
    """מאתר ומדרג מועמדי יוטיוב עבור שיר בודד. מחזיר (רשימת מועמדים מדורגת, האם בוצע חיפוש רשת חדש)."""
    target_phrases = build_song_target_phrases(song)
    raw_candidates: List[Dict[str, Any]] = []
    did_network = False

    # 1. בדיקה מול רצועות האלבומים הרשמיים של נעמי שמר וחבורת בימות (OLAK5uy_...)
    for tp in target_phrases:
        if tp in topic_tracks_map:
            for tr in topic_tracks_map[tp]:
                raw_candidates.append(tr)

    # 2. בדיקת מזהי יוטיוב קיימים מתוך הקטלוג (אקו"ם / סטריאו ומונו / פזמונט)
    for yid in song.get("youtube_ids", []):
        cache_key = f"VID_ID::{yid}"
        if cache_key in search_cache:
            raw_candidates.extend(search_cache[cache_key])
        else:
            det = fetch_video_details_by_id(yid)
            did_network = True
            search_cache[cache_key] = [det] if det else []
            if det:
                raw_candidates.append(det)

    # 3. חיפוש ראשי ביוטיוב: "נעמי שמר <שם השיר>"
    q_primary = f"נעמי שמר {song['title']}"
    if q_primary in search_cache:
        raw_candidates.extend(search_cache[q_primary])
    else:
        res = youtube_search_raw(q_primary)
        did_network = True
        search_cache[q_primary] = res
        raw_candidates.extend(res)

    # סינון ודירוג ראשוני
    scored_map: Dict[str, Dict[str, Any]] = {}
    for idx, cand in enumerate(raw_candidates):
        vid = cand.get("video_id", "")
        if not vid:
            continue
        scored = classify_and_score_candidate(cand, song, target_phrases, all_other_multiword_titles, idx)
        if scored:
            if vid not in scored_map or scored["score"] > scored_map[vid]["score"]:
                scored_map[vid] = scored

    # 4. חיפוש משני עם מבצע מקורי (גם בהיפוך שם משפחה/פרטי) כדי לוודא שגם כשיש ביצוע של נעמי שמר נאתר גם את הביצוע המקורי
    best_tier_so_far = min((c["tier"] for c in scored_map.values()), default="6_not_found")
    has_orig_tier = any(c["tier"] in ("2_album_original", "4_original_performance") for c in scored_map.values())
    secondary_queries: List[str] = []
    if (best_tier_so_far > "2_album_original" or not has_orig_tier) and song.get("performers"):
        for raw_p in song["performers"][:2]:
            if "נעמי שמר" in raw_p or "שמר נעמי" in raw_p:
                continue
            q_raw = f"{song['title']} {raw_p}"
            if q_raw not in secondary_queries:
                secondary_queries.append(q_raw)
            p_vars = expand_performer_variants(raw_p)
            pref_p = p_vars[-1] if p_vars else raw_p
            if pref_p and "נעמי שמר" not in pref_p and "שמר נעמי" not in pref_p:
                q_p = f"{song['title']} {pref_p}"
                if q_p not in secondary_queries:
                    secondary_queries.append(q_p)
            break
    if not scored_map:
        for alt in song.get("alt_titles", [])[:1]:
            if alt != song["title"]:
                secondary_queries.append(f"נעמי שמר {alt}")
        if song.get("opening_line"):
            ol_words = song["opening_line"].split()[:5]
            if len(ol_words) >= 2:
                secondary_queries.append(f"נעמי שמר {' '.join(ol_words)}")

    for sq in secondary_queries[:3]:
        if sq in search_cache:
            sec_res = search_cache[sq]
        elif best_tier_so_far > "2_album_original" or not has_orig_tier:
            sec_res = youtube_search_raw(sq)
            did_network = True
            search_cache[sq] = sec_res
        else:
            continue
        for idx, cand in enumerate(sec_res):
            vid = cand.get("video_id", "")
            if not vid:
                continue
            scored = classify_and_score_candidate(cand, song, target_phrases, all_other_multiword_titles, idx)
            if scored:
                if vid not in scored_map or scored["score"] > scored_map[vid]["score"]:
                    scored_map[vid] = scored

    sorted_candidates = sorted(scored_map.values(), key=lambda x: (-x["score"], x["tier"]))
    return sorted_candidates[:12], did_network


def main() -> None:
    print("טוען את הקטלוג המאוחד...")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    songs: List[Dict[str, Any]] = catalog["songs"]
    print(f"נטענו {len(songs)} שירים מתוך הקטלוג.")

    print("שולף רצועות מתוך פלייליסטי האלבומים הרשמיים של נעמי שמר ביוטיוב (Topic)...")
    topic_tracks_map = fetch_official_topic_albums()
    print(f"נטענו {len(topic_tracks_map)} מפתחות שירים מתוך אלבומי Topic רשמיים.")

    search_cache: Dict[str, List[Dict[str, Any]]] = {}
    if os.path.exists(YT_SEARCH_CACHE_PATH):
        try:
            with open(YT_SEARCH_CACHE_PATH, "r", encoding="utf-8") as f:
                search_cache = json.load(f)
            print(f"נטענו {len(search_cache)} שאילתות חיפוש קיימות מהמטמון.")
        except Exception:
            search_cache = {}

    # בניית קבוצת כל שמות השירים המרובי-מילים לצורך מניעת התאמות שגויות בשירים בני מילה אחת
    all_multiword_titles: Set[str] = set()
    for s in songs:
        nt = norm_heb(s["title"])
        if len(nt.split()) >= 2:
            all_multiword_titles.add(nt)

    song_candidates: Dict[str, List[Dict[str, Any]]] = {}
    new_network_calls = 0

    print(f"מחפש ומדרג ביצועי יוטיוב לכל {len(songs)} השירים (במקביל)...")

    def worker(idx_song: Tuple[int, Dict[str, Any]]) -> Tuple[int, str, List[Dict[str, Any]], bool]:
        idx, s = idx_song
        cands, net = find_candidates_for_song(s, topic_tracks_map, search_cache, all_multiword_titles)
        return idx, s["normalized_key"], cands, net

    batch_size = 30
    for start in range(0, len(songs), batch_size):
        batch = [(i, songs[i]) for i in range(start, min(start + batch_size, len(songs)))]
        batch_did_net = False
        with ThreadPoolExecutor(max_workers=5) as ex:
            for idx, norm_key, cands, net in ex.map(worker, batch):
                song_candidates[norm_key] = cands
                if net:
                    batch_did_net = True
                    new_network_calls += 1
        if batch_did_net:
            with open(YT_SEARCH_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(search_cache, f, ensure_ascii=False)
        done_count = min(start + batch_size, len(songs))
        found_so_far = sum(1 for c in song_candidates.values() if c)
        print(f"  -> הושלמו {done_count}/{len(songs)} שירים (נמצאו סרטונים ל-{found_so_far} שירים)...")

    # הקצאת סרטון ייחודי לכל שיר (ללא כפילויות video_id בין שירים)
    # נקצה קודם לשירים שבהם ציון ההתאמה גבוה יותר כדי שכל סרטון ישויך לשיר המתאים לו ביותר
    songs_by_best_score = sorted(
        songs,
        key=lambda s: (
            -(song_candidates.get(s["normalized_key"], [{}])[0].get("score", 0) if song_candidates.get(s["normalized_key"]) else 0),
            s["title"],
        ),
    )

    used_video_ids: Set[str] = set()
    # עבור כל שיר נשמור: (best_cand, orig_cand, naomi_cand, alts)
    # אם לשיר יש גם ביצוע מקורי של אמן אחר וגם ביצוע של נעמי שמר עצמה — נכלול את שניהם בפלייליסט!
    NAOMI_ENSEMBLE_IS_ORIGINAL_SONGS = {
        "הופה היי",
        "לא ביאליק",
        "מנגנות ויואלדי",
        "יובל",
        "אקטואליה",
        # נעמי שמר שרה נעמי שמר (1967) - שירים שנעמי שמר ביצעה לראשונה באלבום הסולו שלה
        "ארבעה אחים",
        "אל תשאלו אותי",
        "עקידת יצחק",
        "בית חלומותיי",
        # נעמי שמר שרה לילדים ועודד תאומי (1971) - שירים מתוך האלבום המשותף
        "ג’ינג’י",
        "ג'ינג'י",
        "קלי קלות",
        "צירצורים",
        "שיר החצב",
        "הדוד שמחה",
        "פו הדב",
        # כיצד שוברים חמסין (1975) - שירים שנעמי שמר ביצעה לראשונה באלבום הסולו שלה
        "משנכנס אדר",
        "נגיד",
        "נצא השדה",
        "החופש הגדול",
        "לנוע ולנדוד",
        "כיצד שוברים חמסין",
        "שנים עשר ירחים",
        "בראש השנה",
        "אלף בית",
        # שירים נוספים בביצוע בכורה של נעמי שמר (שגרסאות מאוחרות שלהם הן קאברים)
        "נומי נוגה",
        "אין דבר",
        "לחם האוהבים",
    }
    LATE_COVER_PERFORMERS_EXCLUDE_DUAL = (
        "גיתית שובל",
        "ורדה זמיר",
        "זמיר ורדה",
        "רביד גואטה",
        "קרן הדר",
        "אריאל הורוביץ",
        "האחיות שמר 24",
        "עודד תאומי",
        "oded teomi",
        "רונית אופיר",
        "דולי מודעי",
        "צילה דגן",
        "cilla dagan",
        "שוקולד מנטה מסטיק",
    )

    dual_selection_by_key: Dict[str, Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Dict[str, Any]]]] = {}

    for s in songs_by_best_score:
        key = s["normalized_key"]
        cands = song_candidates.get(key, [])
        best_cand: Optional[Dict[str, Any]] = None
        orig_cand: Optional[Dict[str, Any]] = None
        naomi_cand: Optional[Dict[str, Any]] = None
        alts: List[Dict[str, Any]] = []

        for c in cands:
            vid = c["video_id"]
            if vid in used_video_ids:
                alts.append(c)
                continue
            if best_cand is None:
                best_cand = c

            # בדיקה האם המועמד הוא ביצוע של נעמי שמר עצמה (רמה 1 או 3)
            if c["tier"] in ("1_album_naomi", "3_naomi_performance"):
                if naomi_cand is None:
                    naomi_cand = c
                else:
                    alts.append(c)
                continue

            # בדיקה האם המועמד הוא ביצוע מקורי של אמן/הרכב מקורי אחר (רמה 2 או 4)
            if c["tier"] in ("2_album_original", "4_original_performance") and orig_cand is None:
                mp = c.get("matched_performer", "")
                ma = c.get("matched_album", "")
                vt_ch = f"{c.get('video_title', '')} {c.get('channel', '')} {c.get('description', '')}"
                is_valid_distinct_orig = True
                if not mp or "נעמי שמר" in mp or "שמר נעמי" in mp or "Naomi Shemer" in mp:
                    is_valid_distinct_orig = False
                elif s["title"] in NAOMI_ENSEMBLE_IS_ORIGINAL_SONGS:
                    is_valid_distinct_orig = False
                elif ma == "אצלנו בפסנתר" and s["title"] not in ("פרי חדש", "שלום כיתה א'", "הכל פתוח"):
                    # הקלטה מחודשת מקלטת הווידאו מ-1993 לשירים ותיקים של נעמי שמר
                    is_valid_distinct_orig = False
                elif ma == "אחר קציר" and s["title"] in ("אל בורות המים", "לילה בחוף אכזיב"):
                    # ביצוע מחודש של הגבעטרון (1988) לשירים שנעמי שמר הקליטה במקור ב-1982
                    is_valid_distinct_orig = False
                elif any(lcp in mp.lower() or lcp in vt_ch.lower() for lcp in LATE_COVER_PERFORMERS_EXCLUDE_DUAL):
                    is_valid_distinct_orig = False
                elif "דורית פרקש" in mp and s["title"] in ("יובל", "נומי נוגה"):
                    is_valid_distinct_orig = False

                if is_valid_distinct_orig:
                    orig_cand = c
                    continue

            alts.append(c)

        # סימון ה-video_ids שנבחרו כמשומשים כדי למנוע כפילות בין שירים שונים
        if orig_cand and naomi_cand:
            used_video_ids.add(orig_cand["video_id"])
            used_video_ids.add(naomi_cand["video_id"])
            alts = [a for a in alts if a["video_id"] not in (orig_cand["video_id"], naomi_cand["video_id"])]
        elif best_cand:
            used_video_ids.add(best_cand["video_id"])
            alts = [a for a in cands if a["video_id"] != best_cand["video_id"]]

        dual_selection_by_key[key] = (best_cand, orig_cand, naomi_cand, alts)

    # בניית רשימת הפלייליסט הסופית במיון כרונולוגי: לפי שנה -> אלבומים לפי סדר הרצועות הפנימי -> סינגלים
    NAOMI_SOLO_ALBUM_IDS = {
        "naomi_shara_naomi_1967",
        "naomi_shara_leyladim_1971",
        "keitzad_shovrim_hamsin_1975",
        "al_hadvash_1981",
        "el_borot_hamayim_1982",
    }

    CANONICAL_ALBUMS = [
        ("shirim_mikineret_1958", 1958, "שירים מכנרת (יפה ירקוני ונעמי שמר)", ["שירים מכנרת"], [
            "אחינו הקטן", "אשכולית", "הדואר בא", "בגינה", "שיר סתיו", "שבת",
        ]),
        ("hamesh_hamesh_1958", 1958, "חמש חמש (המחזמר)", ["חמש חמש"], [
            "רב האור והתכלת", "בא הגדוד", "רומנס בכפר", "שיר הבר", "סמוך על התרנגול", "חפש את האישה", "שיר עבודה",
        ]),
        ("hadudaim_b_1958", 1958, "צמד הדודאים ב'", ["צמד הדודאים"], [
            "שיירת הרוכבים", "שיר לחג עשור",
        ]),
        ("shimon_bar_rachel_attas_1959", 1959, "שמעון בר ורחל אטאס – בשירי נעמי שמר", ["שמעון בר"], [
            "קפה שחור", "עיר לבנה", "קיצור החדשות", "זמר נודד", "מצעד האביב", "קרנבל",
        ]),
        ("aseret_hatzadikim_1960", 1960, "עשרת הצדיקים (להקת השעות הקטנות)", ["עשרת הצדיקים"], [
            "אוכל אדם", "עשרת הצדיקים", "על ליל אמש", "שיר השוק",
        ]),
        ("lehakat_hatzeirim_1961", 1961, "שירי נעמי שמר (להקת הצעירים)", ["להקת הצעירים"], [
            "הופה היי", "בשדה תלתן", "שיר לגדעון", "חמסינים במשלט",
        ]),
        ("shemesh_bamidbar_1963", 1963, "שמש במדבר (להקת הנח\"ל)", ["שמש במדבר"], [
            "מחר", "סוף העולם", "בלי מילים", "בלדה על סל תפירה", "מדם בלוזון המרגלת",
            "עוד לא אכלנו", "הטיול הגדול", "מטרייה בשניים", "מחבואים", "אצל ורדה השמנה",
        ]),
        ("biglal_masmer_1964", 1964, "בגלל מסמר (להקת פיקוד צפון)", ["בגלל מסמר"], [
            "הכול בגלל מסמר", "נעלה צפונה", "מי רוכב על מי",
        ]),
        ("ahayot_shemer_1966", 1966, "רביעיית האחיות שמר", ["האחיות שמר"], [
            "פרחי אולי", "לרקוד איתך", "הללויה", "לא לא לא",
        ]),
        ("hamelech_veani_1966", 1966, "המלך ואני (הפקת גיורא גודיק)", ["המלך ואני"], [
            "אשרוק לי שיר עליז", "אדון ומלך", "אקרא שלום", "חידתיות", "להתוודע",
            "בצל ובאופל", "שפחה שפחה", "דבר מה נפלא כל כך", "שלא נהיה ברברים", "בחלום", "משל סיאמי", "הנרקוד",
        ]),
        ("naomi_shara_naomi_1967", 1967, "נעמי שמר שרה נעמי שמר (ירושלים של זהב)", ["נעמי שמר שרה נעמי שמר"], [
            "ארבעה אחים", "אל תשאלו אותי", "מחר", "החייל שלי חזר", "על כנפי הכסף",
            "עקידת יצחק", "בית חלומותיי", "לכבודך", "מחבואים", "אחרי השקיעה בשדה", "ירושלים של זהב",
        ]),
        ("shuli_natan_1968", 1968, "שולי נתן שרה נעמי שמר", ["שולי נתן"], [
            "שיר ערש לצבעים", "זמר", "בקיץ", "קרן יער", "כפות רגליך לבנות", "בגני נטעתיך", "כי לא יהיה להם יום", "מתי",
        ]),
        ("naomi_shara_leyladim_1971", 1971, "נעמי שמר שרה לילדים (ועודד תאומי)", ["נעמי שמר שרה לילדים"], [
            "מה עושים העצים", "ג’ינג’י", "קלי קלות", "צירצורים", "שיר החצב",
            "הדוד שמחה", "שיר ערש לצבעים", "פו הדב", "שבחי מעוז",
        ]),
        ("havurat_bimot_1972", 1972, "שירי נעמי שמר (חבורת בימות)", ["חבורת בימות"], [
            "לשיר זה כמו להיות ירדן", "אין ויש", "בוא נרד לכרם", "שש עשרה", "חרוזי ביניים",
            "בארץ להד\"ם", "לא אמות כי אחיה", "שירו של אבא", "אנשים יפים", "מר נרקיס",
            "תחביב מיוחד במינו", "שיר ערש למקרים מיוחדים", "ארבעים", "המכשפות", "שני צלמי רחוב",
        ]),
        ("shar_brassens_1974", 1974, "יוסי בנאי שר ברסאנס (אין אהבות שמחות)", ["שר ברסאנס", "בראסנס", "יוסי בנאי"], [
            "אין אהבות שמחות", "לא אבקש את ידך", "הצוואה", "פרח בדמות פרה",
            "שוב כמו אתמול", "נעשיתי כזה קטן", "מרגו", "נשים נשים", "לאיש חסדי",
        ]),
        ("keitzad_shovrim_hamsin_1975", 1975, "כיצד שוברים חמסין (נעמי שמר)", ["כיצד שוברים חמסין"], [
            "משנכנס אדר", "נגיד", "נצא השדה", "החופש הגדול", "לנוע ולנדוד",
            "כיצד שוברים חמסין", "יש לי חבר", "בארץ להד\"ם", "שלומית בונה סוכה",
            "שנים עשר ירחים", "בראש השנה", "אלף בית",
        ]),
        ("masaot_binyamin_1976", 1976, "מסעות בנימין השלישי (המחזמר)", ["מסעות בנימין השלישי"], [
            "פתיחה", "שיר לכת", "שלג על עירי", "הגביר", "סינמה בלש",
            "יריד", "לכו נרננה", "שירת העשבים", "צמחי הביצה", "מכתב", "מתפרנסים", "מוטב בבית", "סימן שעוד לא הגענו",
        ]),
        ("hatiyul_hakatan_1977", 1977, "הטיול הקטן – כל שירי נעמי שמר לילדים", ["הטיול הקטן", "כל שירי נעמי שמר לילדים"], [
            "הטיול הקטן", "יש לי חג", "נר ראשון של חנוכה", "נומי נוגה", "חליל מקנה-סוף", "דוגרת", "גדי קטן",
        ]),
        ("hagashash_1979", 1979, "הגשש החיוור שרים נעמי שמר", ["הגשש החיוור"], [
            "למה צחקה מיכל", "אחותי רוחמה", "תפוח בדבש", "שלום כיתה א'", "מסעות בנימין מטודלה",
        ]),
        ("al_hadvash_1981", 1981, "על הדבש ועל העוקץ (נעמי שמר)", ["על הדבש ועל העוקץ"], [
            "על כל אלה", "אומרים ישנה ארץ", "אורחים לקיץ", "פגישה לאין קץ", "ברברה",
            "שירת העשבים", "חבלי משיח", "האיר השחר", "אין דבר", "יום ה בשבוע", "הפסנתר", "אנשים טובים",
        ]),
        ("elef_neshikot_1981", 1981, "אלף נשיקות (יהורם גאון)", ["אלף נשיקות"], [
            "כמו חצב", "דיוקן אמי", "את הכי הכי", "ראש קטן",
        ]),
        ("el_borot_hamayim_1982", 1982, "אל בורות המים (נעמי שמר)", ["אל בורות המים"], [
            "אל בורות המים", "סימן שעוד לא הגענו", "לילה בחוף אכזיב", "רגע מתוק",
            "כיבוי אורות", "קומי צאי", "הכל שטיח", "קולך מן הסופה",
            "שלג על עירי", "בכל שנה בסתיו גיורא", "על נהרות בבל", "ורד בר",
        ]),
        ("haerusim_1983", 1983, "האירוסים – זמרי בית אלפא", ["האירוסים"], [
            "פרדס חנה בשבת",
        ]),
        ("yareach_male_1986", 1986, "ירח מלא (יהורם גאון)", ["ירח מלא"], [
            "נסיכה שחורה", "ליבבתיני",
        ]),
        ("hafatzim_ishiyim_1987", 1987, "חפצים אישיים (משה בקר)", ["חפצים אישיים"], [
            "גג", "ילדה ברבור", "פרלוד", "אהבת אשתקד", "תות",
            "זמן", "פרח", "מה שלומך אחות", "גיא", "חפצים אישיים", "בראשון לספטמבר",
        ]),
        ("achar_katzir_1988", 1988, "אחר קציר – הגבעטרון בשירי נעמי שמר", ["אחר קציר", "הגבעטרון"], [
            "אחר קציר", "האילן הזקן",
        ]),
        ("muzika_haparvarim_1989", 1989, "מוזיקה (הפרברים)", ["מוזיקה"], [
            "מוזיקה", "אישה על החוף", "שיר ערבי נחל",
        ]),
        ("etzlenu_bapsanter_1993", 1993, "אצלנו בפסנתר (שירי הילדים של נעמי שמר)", ["אצלנו בפסנתר"], [
            "פרי חדש", "הכל פתוח",
        ]),
        ("dorit_farkash_1998", 1998, "חצי מאה עברה – דורית פרקש שרה נעמי שמר", ["דורית פרקש"], [
            "מי ידליק", "קפה תפארת",
        ]),
    ]

    MANUAL_YEARS = {
        "מנגנות ויואלדי": 1976,
        "לא ביאליק": 1976,
        "על ראש שמחתי": 1988,
        "מיכאל": 1968,
        "אילן": 1979,
        "בז על המרפסת": 1961,
        "התפוזים": 1964,
        "זאת הארץ": 1958,
        "זמרת השנה": 1979,
        "ט\"ו באב": 1958,
        "יום הולדת שמח": 1965,
        "סיפור אהבתי לכם": 1979,
        "פרידה": 2004,
        "פת במלח": 1988,
        "צי הצללים": 1965,
        "שיר פורח": 1963,
        "איש מוזר": 2001,
        "אקטואליה": 1991,
        "מתי": 1968,
        "מי ידליק": 1998,
        "רוקדת": 1958,
        "שיר המכביה": 1965,
        "תפוח בדבש": 1979,
        "הגברת ישראלה": 1960,
        "שנה טובה": 1992,
        "ט\"ו בשבט שלי": 1985,
        "ימי הענבים": 1974,
        "כד הקמח": 1971,
        "לא תנצחו אותי": 1984,
        "המעיל": 2001,
        "חד גדיא": 1979,
        "עלי שלכת": 1989,
        "עמוק בטל": 1973,
        "חפש את האישה": 1958,
        "הורה נחל עוז": 1953,
        "בלדה על מושבה נידחת": 1958,
        "שייקספיר איננו": 1964,
        "תישן חמודי תישן": 1968,
        "אוניית הכאב": 2004,
        "אל מחנה השחרורים": 1961,
        "ארץ ישראל שייכת לעם ישראל": 1990,
        "הדוכיפת": 1982,
        "הו מה נאה הוא הבוקר": 1956,
        "יום הולדת מתיה": 1980,
        "כמו נערה": 1964,
        "דולי": 1997,
        "אביב": 1978,
        "סביבון סב סב": 1977,
        "אהבתיך גם כך": 1956,
        "פרנואיד": 1978,
        "בכל שנה בסתיו גיורא": 1979,
        "אומרים ישנה ארץ": 1980,
        "על כל אלה": 1980,
        "העלמה": 1988,
        "איך את נראית": 1968,
        "אילו ציפורים": 1967,
        "שלגיה": 1966,
        "תלבשי לבן": 1985,
        "בקיץ": 1968,
        "ספני שלמה המלך": 1970,
        "אחותי רוחמה": 1979,
        "שלום כיתה א'": 1981,
        "נערת הסיפון": 1964,
        "לבנות שפיה": 1975,
        "כריש": 1978,
    }

    pizmonet_years: Dict[str, str] = {}
    piz_path = os.path.join(CACHE_DIR, "pizmonet_raw.json")
    if os.path.exists(piz_path):
        try:
            with open(piz_path, "r", encoding="utf-8") as pf:
                for ps in json.load(pf).get("songs", []):
                    if ps.get("year"):
                        pizmonet_years[ps["title"]] = ps["year"]
        except Exception:
            pass

    def resolve_single_year(s: Dict[str, Any], chosen: Optional[Dict[str, Any]]) -> int:
        """מחלץ את שנת היצירה/ההוצאה של שיר בודד."""
        t = s["title"]
        if t in MANUAL_YEARS:
            return MANUAL_YEARS[t]
        py = pizmonet_years.get(t, "")
        if py and py.isdigit() and 1948 <= int(py) <= 2004:
            return int(py)
        notes = " ".join(s.get("notes", []))
        m_notes = [int(x) for x in re.findall(r"(?:בשנת|משנת|שנת|ב-|\()\s*(19[4-9]\d|200[0-4])\b", notes)]
        if m_notes:
            return min(m_notes)
        m_notes_any = [int(x) for x in re.findall(r"\b(19[5-9]\d|200[0-3])\b", notes)]
        if m_notes_any:
            return min(m_notes_any)
        if chosen:
            m_vt = [int(x) for x in re.findall(r"\b(19[5-9]\d|200[0-4])\b", chosen.get("video_title", ""))]
            if m_vt:
                return min(m_vt)
            vd = chosen.get("description", "")
            if not any(comp in vd for comp in ("אסיף", "האוסף השלם", "סימני דרך", "ארבע אחרי הצהריים")):
                m_vd = [int(x) for x in re.findall(r"℗\s*(19[5-9]\d|200[0-4])\b", vd)]
                if m_vd:
                    return min(m_vd)
        albs_str = " ".join(
            a for a in s.get("albums", [])
            if not any(c in a for c in ("אסיף", "האוסף השלם", "סימני דרך", "100 שירים"))
        )
        m_alb = [int(x) for x in re.findall(r"\b(19[5-9]\d|200[0-4])\b", albs_str)]
        if m_alb:
            return min(m_alb)
        cy = s.get("year", "")
        if cy and cy.isdigit() and 1948 <= int(cy) <= 2004:
            return int(cy)
        return 2099

    def resolve_chrono_info(
        s: Dict[str, Any],
        chosen: Optional[Dict[str, Any]],
        exclude_naomi_solo: bool = False,
        only_naomi_solo: bool = False,
    ) -> Tuple[int, int, str, int]:
        """מחזיר (שנה כרונולוגית, אינדקס אלבום או 999 לסינגל, שם אלבום/סינגל, מספר רצועה באלבום או 999)."""
        t = s["title"]
        vblob = ""
        if chosen:
            vblob = f"{chosen.get('matched_album', '')} {chosen.get('video_title', '')} {chosen.get('description', '')} {chosen.get('channel', '')}"

        # 1. בדיקה אם הסרטון הנבחר משויך ישירות לאחד האלבומים הקנוניים שכוללים את השיר
        for alb_idx, (aid, ayr, atitle, kws, trks) in enumerate(CANONICAL_ALBUMS, 1):
            if exclude_naomi_solo and aid in NAOMI_SOLO_ALBUM_IDS:
                continue
            if only_naomi_solo and aid not in NAOMI_SOLO_ALBUM_IDS:
                continue
            if t in trks and any(k in vblob for k in kws):
                return ayr, alb_idx, atitle, trks.index(t) + 1

        # 2. בדיקה אם השיר שייך לאחד האלבומים הקנוניים
        for alb_idx, (aid, ayr, atitle, kws, trks) in enumerate(CANONICAL_ALBUMS, 1):
            if exclude_naomi_solo and aid in NAOMI_SOLO_ALBUM_IDS:
                continue
            if only_naomi_solo and aid not in NAOMI_SOLO_ALBUM_IDS:
                continue
            if t in trks:
                return ayr, alb_idx, atitle, trks.index(t) + 1

        # 3. שיר בודד (Single)
        return resolve_single_year(s, chosen), 999, "סינגל / ביצוע בודד", 999

    CREATOR_NAME_MAP = {
        "CHARLES AZNAOURIAN": "שארל אזנבור",
        "MILTON AGER": "מילטון אייג'ר",
        "RAYMOND O SULLIVAN": "גילברט או'סאליבן",
        "MONIQUE ANDREE SERF": "ברברה (מוניק סרף)",
        "HANS CARSTE": "הנס קרסטה",
        "ULISES HERMOSA": "האחים הרמוסה (לוס קיארקס)",
        "GONZALO HERMOSA GONZALES": "האחים הרמוסה (לוס קיארקס)",
        "MICHEL JEAN LEGRAND": "מישל לגראן",
        "JACQUES LOUIS RAYMOND MARCEL DEMY": "ז'אק דמי",
        "ANTONIO CARLOS JOBIM": "אנטוניו קרלוס ז'ובים",
        "NEWTON FERREIRA DE MENDONCA": "ניוטון מנדונסה",
        "רי'צרד רוג'רס": "ריצ'רד רוג'רס",
        "אוסקר המרשטין": "אוסקר המרשטיין",
        "אהרון זאב": "אהרן זאב",
        "רחל בלובשטיין": "רחל המשוררת",
        "רחל": "רחל המשוררת",
        "נחמן ביאליק חיים": "חיים נחמן ביאליק",
        "שאול טשרנחובסקי": "שאול טשרניחובסקי",
        "הלל עומר": "ע. הלל",
        "ע הלל": "ע. הלל",
        "מאנגר איציק": "איציק מאנגר",
        "אלתרמן נתן": "נתן אלתרמן",
        "שטרן אברהם": "אברהם שטרן (יאיר)",
        "אברהם שטרן": "אברהם שטרן (יאיר)",
    }

    def clean_co_creators(names: List[str]) -> List[str]:
        """מסנן את נעמי שמר מרשימת היוצרים, מנרמל שמות בעברית/לועזית ומסיר כפילויות."""
        filtered = []
        for n in names:
            ns = n.strip()
            if not ns or "שמר" in ns or "shemer" in ns.lower() or "ספיר" in ns:
                continue
            mapped = CREATOR_NAME_MAP.get(ns, CREATOR_NAME_MAP.get(ns.upper(), ns))
            filtered.append(mapped)
        heb_names = [n for n in filtered if any("\u0590" <= c <= "\u05FF" for c in n)]
        chosen_list = heb_names if heb_names else filtered
        dedup: List[str] = []
        for n in chosen_list:
            if n not in dedup:
                dedup.append(n)
        return dedup[:2]

    def build_creator_credits(s: Dict[str, Any]) -> Tuple[str, str, str]:
        """מחזיר (קטגוריית תפקיד לסינון, תווית תפקיד בעברית, פירוט יוצרים שותפים)."""
        roles = set(s.get("roles", []))
        co_authors = clean_co_creators(s.get("authors", []))
        co_composers = clean_co_creators(s.get("composers", []))
        if "translator" in roles:
            role_cat = "translation"
            if "composer" in roles and not co_composers:
                co_str = f"מקור: {', '.join(co_authors)}" if co_authors else ""
                role_label = f"תרגום ולחן: נעמי שמר ({co_str})" if co_str else "תרגום ולחן: נעמי שמר"
            else:
                orig_creators = co_composers or co_authors
                co_str = f"מקור: {', '.join(orig_creators)}" if orig_creators else ""
                role_label = f"תרגום: נעמי שמר ({co_str})" if co_str else "תרגום / נוסח עברי: נעמי שמר"
        elif "author" in roles and "composer" in roles:
            role_cat = "words_and_music"
            extra = []
            if co_authors:
                extra.append(f"עם {', '.join(co_authors)}")
            elif co_composers:
                extra.append(f"לחן נוסף: {', '.join(co_composers)}")
            co_str = ", ".join(extra)
            role_label = f"מילים ולחן: נעמי שמר ({co_str})" if co_str else "מילים ולחן: נעמי שמר"
        elif "composer" in roles:
            role_cat = "music_only"
            co_str = f"מילים: {', '.join(co_authors)}" if co_authors else ""
            role_label = f"לחן: נעמי שמר · {co_str}" if co_str else "לחן: נעמי שמר"
        elif "author" in roles:
            role_cat = "words_only"
            co_str = f"לחן: {', '.join(co_composers)}" if co_composers else ""
            role_label = f"מילים: נעמי שמר · {co_str}" if co_str else "מילים: נעמי שמר"
        elif "arranger" in roles:
            role_cat = "music_only"
            co_parts = []
            if co_authors:
                co_parts.append(f"מילים: {', '.join(co_authors)}")
            if co_composers:
                co_parts.append(f"לחן: {', '.join(co_composers)}")
            co_str = " · ".join(co_parts)
            role_label = f"עיבוד: נעמי שמר · {co_str}" if co_str else "עיבוד מוזיקלי: נעמי שמר"
        else:
            role_cat = "performance_only"
            co_parts = []
            if co_authors:
                co_parts.append(f"מילים: {', '.join(co_authors)}")
            if co_composers:
                co_parts.append(f"לחן: {', '.join(co_composers)}")
            co_str = " · ".join(co_parts)
            role_label = f"ביצוע: נעמי שמר ({co_str})" if co_str else "ביצוע / עיבוד: נעמי שמר"
        return role_cat, role_label, co_str

    def build_archive_links(s: Dict[str, Any]) -> List[Dict[str, str]]:
        """בונה קישורים ישירים לארכיונים (הספרייה הלאומית, שירונט, זמרשת ואקו\"ם)."""
        links: List[Dict[str, str]] = []
        nli_ids = s.get("nli_mms_ids", [])
        if nli_ids:
            links.append({
                "source": "nli",
                "label": "הספרייה הלאומית (בית לזמר העברי)",
                "url": f"https://www.nli.org.il/he/items/NNL_MUSIC_AL{nli_ids[0]}/NLI",
            })
        elif "nli" in s.get("sources", []):
            q_nli = urllib.parse.quote(f"נעמי שמר {s['title']}")
            links.append({
                "source": "nli",
                "label": "חיפוש בספרייה הלאומית",
                "url": f"https://www.nli.org.il/he/search?projectName=NLI&text={q_nli}",
            })
        shironet_urls = s.get("shironet_urls", [])
        if shironet_urls:
            links.append({
                "source": "shironet",
                "label": "מילים בשירונט",
                "url": shironet_urls[0],
            })
        if "zemereshet" in s.get("sources", []):
            q_zem = urllib.parse.quote(s["title"])
            links.append({
                "source": "zemereshet",
                "label": "הקלטה ומידע בזמרשת",
                "url": f"https://www.zemereshet.co.il/m/songs.asp?search={q_zem}",
            })
        acum_ids = s.get("acum_work_ids", [])
        if acum_ids:
            links.append({
                "source": "acum",
                "label": f"אקו\"ם #{acum_ids[0]}",
                "url": f"https://nocs.acum.org.il/acumsitesearchdb/issearch?workid={acum_ids[0]}",
            })
        return links

    def filter_catalog_performers(perfs: List[str]) -> List[str]:
        """מסנן מבצעים שכתובים רק באותיות לטיניות/UPPERCASE (מבצעים זרים של גרסת המקור שדלפו מאקו\"ם)."""
        return [p for p in perfs if any("\u0590" <= c <= "\u05FF" for c in p)]

    playlist_entries: List[Dict[str, Any]] = []
    tier_counts: Dict[str, int] = {k: 0 for k in TIER_LABELS_HEB}
    matched_songs_count = 0
    dual_songs_count = 0

    for s in songs:
        key = s["normalized_key"]
        best_cand, orig_cand, naomi_cand, alts = dual_selection_by_key.get(key, (None, None, None, []))
        role_cat, role_label, co_creators_str = build_creator_credits(s)
        arch_links = build_archive_links(s)
        song_notes = " ".join(s.get("notes", []))[:300]

        if orig_cand and naomi_cand:
            # יש לשיר גם ביצוע מקורי של אמן/הרכב אחר וגם ביצוע של נעמי שמר עצמה — נכלול את שניהם!
            matched_songs_count += 1
            dual_songs_count += 1
            tier_counts[orig_cand["tier"]] = tier_counts.get(orig_cand["tier"], 0) + 1
            tier_counts[naomi_cand["tier"]] = tier_counts.get(naomi_cand["tier"], 0) + 1

            # מיקום הביצוע המקורי (באלבום החיצוני שלו או כסינגל בשנה המקורית)
            orig_yr, orig_alb_idx, orig_alb_group, orig_trk_num = resolve_chrono_info(
                s, orig_cand, exclude_naomi_solo=True
            )
            # מיקום הביצוע של נעמי שמר: אם השיר מופיע באחד מאלבומי הסולו של נעמי שמר והסרטון ברמה 1, נשבץ אותו באלבום הסולו שלה
            naomi_yr, naomi_alb_idx, naomi_alb_group, naomi_trk_num = resolve_chrono_info(
                s, naomi_cand, only_naomi_solo=True
            )

            if naomi_alb_idx != 999 and naomi_cand["tier"] == "1_album_naomi":
                # הביצוע של נעמי שמר שייך לאלבום סולו שלה שיישמר ברצף מלא (ללא שבירת רצף האלבום).
                # אם הביצוע המקורי הוא סינגל, נוודא שהוא מופיע לפני אלבום הסולו של נעמי שמר
                if orig_alb_idx == 999:
                    orig_yr = min(orig_yr, naomi_yr)
                    if orig_yr == naomi_yr:
                        orig_sort_key = (0, orig_yr, naomi_alb_idx - 0.5, 999, s["title"], 0)
                    else:
                        orig_sort_key = (0, orig_yr, 999, 999, s["title"], 0)
                else:
                    orig_sort_key = (0, orig_yr, orig_alb_idx, orig_trk_num, s["title"], 0)
                naomi_sort_key = (0, naomi_yr, naomi_alb_idx, naomi_trk_num, s["title"], 1)
            else:
                # הביצוע של נעמי שמר הוא ביצוע בודד —
                # נציב את הביצוע של נעמי שמר אחרי הביצוע המקורי (ואם המקורי הוא חלק מאלבום חיצוני, מיד בסיום אותו אלבום כדי לא לשבור את רצף האלבום!)
                orig_sort_key = (0, orig_yr, orig_alb_idx, orig_trk_num, s["title"], 0)
                if orig_alb_idx != 999:
                    naomi_alb_group = f"ביצוע נעמי שמר (אחרי האלבום: {orig_alb_group})"
                    naomi_trk_num = 999
                    naomi_yr = orig_yr
                    naomi_sort_key = (0, orig_yr, orig_alb_idx, 900 + orig_trk_num, s["title"], 1)
                else:
                    naomi_alb_group = "סינגל / ביצוע בודד (ביצוע נעמי שמר)"
                    naomi_trk_num = 999
                    naomi_yr = orig_yr
                    naomi_sort_key = (0, orig_yr, 999, 999, s["title"], 1)

            # רשומה 1: הביצוע המקורי
            playlist_entries.append({
                "index": 0,
                "title": s["title"],
                "alt_titles": s.get("alt_titles", []),
                "opening_line": s.get("opening_line", ""),
                "year": str(orig_yr),
                "album_group": orig_alb_group,
                "album_track_number": orig_trk_num if orig_trk_num != 999 else "",
                "dual_role": "original_performance",
                "_sort_key": orig_sort_key,
                "roles": s.get("roles", []),
                "role_category": role_cat,
                "role_label_heb": role_label,
                "co_creators_heb": co_creators_str,
                "archive_links": arch_links,
                "notes": song_notes,
                "sources": s.get("sources", []),
                "catalog_performers": filter_catalog_performers(s.get("performers", [])),
                "catalog_albums": s.get("albums", []),
                "tier": orig_cand["tier"],
                "tier_label": TIER_LABELS_HEB[orig_cand["tier"]],
                "selected_video": orig_cand,
                "alternative_videos": [naomi_cand] + alts[:2],
            })
            # רשומה 2: הביצוע של נעמי שמר
            playlist_entries.append({
                "index": 0,
                "title": s["title"],
                "alt_titles": s.get("alt_titles", []),
                "opening_line": s.get("opening_line", ""),
                "year": str(naomi_yr),
                "album_group": naomi_alb_group,
                "album_track_number": naomi_trk_num if naomi_trk_num != 999 else "",
                "dual_role": "naomi_performance",
                "_sort_key": naomi_sort_key,
                "roles": s.get("roles", []),
                "role_category": role_cat,
                "role_label_heb": role_label,
                "co_creators_heb": co_creators_str,
                "archive_links": arch_links,
                "notes": song_notes,
                "sources": s.get("sources", []),
                "catalog_performers": filter_catalog_performers(s.get("performers", [])),
                "catalog_albums": s.get("albums", []),
                "tier": naomi_cand["tier"],
                "tier_label": TIER_LABELS_HEB[naomi_cand["tier"]],
                "selected_video": naomi_cand,
                "alternative_videos": [orig_cand] + alts[:2],
            })
        else:
            chosen = best_cand
            tier = chosen["tier"] if chosen else "6_not_found"
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            if chosen:
                matched_songs_count += 1
            chrono_yr, alb_order_idx, alb_group, trk_num = resolve_chrono_info(s, chosen)

            playlist_entries.append({
                "index": 0,
                "title": s["title"],
                "alt_titles": s.get("alt_titles", []),
                "opening_line": s.get("opening_line", ""),
                "year": str(chrono_yr),
                "album_group": alb_group,
                "album_track_number": trk_num if trk_num != 999 else "",
                "_sort_key": (0 if chosen else 1, chrono_yr, alb_order_idx, trk_num, s["title"], 0),
                "roles": s.get("roles", []),
                "role_category": role_cat,
                "role_label_heb": role_label,
                "co_creators_heb": co_creators_str,
                "archive_links": arch_links,
                "notes": song_notes,
                "sources": s.get("sources", []),
                "catalog_performers": filter_catalog_performers(s.get("performers", [])),
                "catalog_albums": s.get("albums", []),
                "tier": tier,
                "tier_label": TIER_LABELS_HEB[tier],
                "selected_video": chosen,
                "alternative_videos": alts[:3],
            })

    playlist_entries.sort(key=lambda x: x["_sort_key"])
    for idx, item in enumerate(playlist_entries, 1):
        item["index"] = idx
        item.pop("_sort_key", None)

    # שמירת קובצי הפלט
    out_json = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.json")
    out_csv = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.csv")
    out_md = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.md")

    total_videos_in_playlist = sum(1 for item in playlist_entries if item.get("selected_video"))
    summary_stats = {
        "total_songs": len(songs),
        "matched_songs": matched_songs_count,
        "dual_performance_songs": dual_songs_count,
        "total_playlist_videos": total_videos_in_playlist,
        "unmatched_songs": tier_counts.get("6_not_found", 0),
        "by_tier": {TIER_LABELS_HEB[k]: v for k, v in tier_counts.items()},
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "stats": summary_stats,
                "playlist": playlist_entries,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "#",
            "שנה",
            "אלבום / סינגל",
            "רצועה באלבום",
            "שם השיר",
            "תפקיד נעמי שמר ויוצרים שותפים",
            "סיווג הביצוע שנבחר",
            "קישור ליוטיוב",
            "מזהה סרטון (Video ID)",
            "כותרת הסרטון ביוטיוב",
            "ערוץ יוטיוב",
            "אורך",
            "מבצע מזוהה בסרטון",
            "אלבום מזוהה בסרטון",
            "מבצעים מתוך הקטלוג",
            "אלבומים מתוך הקטלוג",
            "שורת פתיחה (אתחלתא)",
            "קישורי ארכיון (הספרייה הלאומית / שירונט / זמרשת)",
            "קישור חלופי ביוטיוב",
        ])
        for item in playlist_entries:
            sel = item["selected_video"] or {}
            alt_url = item["alternative_videos"][0]["url"] if item["alternative_videos"] else ""
            arch_str = " | ".join(f"{a['label']}: {a['url']}" for a in item.get("archive_links", []))
            writer.writerow([
                item["index"],
                item.get("year", ""),
                item.get("album_group", ""),
                item.get("album_track_number", ""),
                item["title"],
                item.get("role_label_heb", ""),
                item["tier_label"],
                sel.get("url", ""),
                sel.get("video_id", ""),
                sel.get("video_title", ""),
                sel.get("channel", ""),
                sel.get("duration", ""),
                sel.get("matched_performer", ""),
                sel.get("matched_album", ""),
                " | ".join(item["catalog_performers"][:10]),
                " | ".join(item["catalog_albums"][:8]),
                item["opening_line"],
                arch_str,
                alt_url,
            ])

    matched_md_items = [item for item in playlist_entries if item.get("selected_video")]
    unmatched_md_items = [item for item in playlist_entries if not item.get("selected_video")]

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# פלייליסט יוטיוב מקיף לשירי נעמי שמר (בסדר כרונולוגי)\n\n")
        f.write("## סיכום התאמות לפי רמת תעדוף\n\n")
        f.write(f"- **סה\"כ שירים בקטלוג:** {summary_stats['total_songs']}\n")
        f.write(f"- **סה\"כ שירים שנמצא להם סרטון ייחודי ביוטיוב:** {summary_stats['matched_songs']}\n")
        f.write(f"- **שירים שבהם נכללו גם הביצוע המקורי וגם הביצוע של נעמי שמר:** {summary_stats['dual_performance_songs']}\n")
        f.write(f"- **סה\"כ סרטונים בפלייליסט:** {summary_stats['total_playlist_videos']}\n")
        for k, v in summary_stats["by_tier"].items():
            f.write(f"  - **{k}:** {v} רצועות\n")
        f.write("\n## 1. רשימת הסרטונים המלאה ביוטיוב (לפי שנה -> אלבומים לפי סדר הרצועות -> סינגלים)\n\n")
        f.write("| # | שנה | אלבום / סינגל | שם השיר | תפקיד ויוצרים | שורת פתיחה | סיווג הביצוע | כותרת הסרטון וקישור | ערוץ | אורך |\n")
        f.write("|---|-----|---------------|---------|---------------|------------|--------------|---------------------|------|------|\n")
        for item in matched_md_items:
            sel = item["selected_video"]
            t_clean = item["title"].replace("|", "\\|")
            yr_str = item.get("year", "")
            ag_str = item.get("album_group", "")
            trk_str = str(item.get("album_track_number", ""))
            alb_col = f"{ag_str} (#{trk_str})" if trk_str else ag_str
            alb_col = alb_col.replace("|", "\\|")
            role_col = item.get("role_label_heb", "").replace("|", "\\|")
            ol_col = item.get("opening_line", "").replace("|", "\\|")
            vt_clean = sel["video_title"].replace("|", "\\|").replace("[", "(").replace("]", ")")
            ch_clean = sel["channel"].replace("|", "\\|")
            f.write(
                f"| {item['index']} | {yr_str} | {alb_col} | {t_clean} | {role_col} | {ol_col} | {item['tier_label']} | "
                f"[{vt_clean}]({sel['url']}) | {ch_clean} | {sel.get('duration', '')} |\n"
            )

        f.write(f"\n## 2. פלייליסט ארכיון משלים – {len(unmatched_md_items)} שירים נדירים שאינם ביוטיוב (קישורים לספרייה הלאומית, שירונט וזמרשת)\n\n")
        f.write("| # | שנה | שם השיר | תפקיד נעמי שמר ויוצרים | מבצעים מתועדים | שורת פתיחה | קישורים לארכיון |\n")
        f.write("|---|-----|---------|------------------------|----------------|------------|------------------|\n")
        for item in unmatched_md_items:
            t_clean = item["title"].replace("|", "\\|")
            yr_str = item.get("year", "")
            role_col = item.get("role_label_heb", "").replace("|", "\\|")
            perfs_col = ", ".join(item.get("catalog_performers", [])[:3]).replace("|", "\\|") or "—"
            ol_col = item.get("opening_line", "").replace("|", "\\|") or "—"
            links_md = " · ".join(f"[{a['label']}]({a['url']})" for a in item.get("archive_links", [])) or "—"
            f.write(
                f"| {item['index']} | {yr_str} | {t_clean} | {role_col} | {perfs_col} | {ol_col} | {links_md} |\n"
            )

    print("\n=== סיכום תוצאות איתור סרטוני יוטיוב ===")
    print(f"סה\"כ שירים בקטלוג: {summary_stats['total_songs']}")
    print(f"שירים שנמצא להם סרטון: {summary_stats['matched_songs']}")
    print(f"שירים שבהם נכללו גם ביצוע מקורי וגם ביצוע של נעמי שמר: {summary_stats['dual_performance_songs']}")
    print(f"סה\"כ סרטונים בפלייליסט: {summary_stats['total_playlist_videos']}")
    for k, v in summary_stats["by_tier"].items():
        print(f"  {k}: {v}")
    print("\nנשמרו הקבצים:")
    print(f"  1. {out_csv}")
    print(f"  2. {out_json}")
    print(f"  3. {out_md}")

    try:
        from build_player_and_browser_script import generate_files
        generate_files()
    except Exception as e:
        print(f"שגיאה בעדכון הנגן והסקריפט לדפדפן: {e}")


if __name__ == "__main__":
    main()
