#!/usr/bin/env python3
"""Match all Naomi Shemer catalog songs & YouTube playlist rows to streaming tracks (Deezer ISRC + iTunes IL) and export Soundiiz-ready CSV chunks."""

from __future__ import annotations

import csv
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
PLAYLIST_JSON_PATH = BASE_DIR / "naomi_shemer_youtube_playlist.json"
CATALOG_JSON_PATH = BASE_DIR / "naomi_shemer_catalog.json"
EXPORT_DIR = BASE_DIR / "spotify_export"
CACHE_PATH = Path(
    "/Users/dmtsurel/.gemini/antigravity/brain/9a49a808-8c60-4b11-9069-859ff68f7c57/scratch/streaming_api_cache.json"
)
SOUNDIIZ_CHUNK_SIZE = 200

BAD_TRACK_KEYWORDS = (
    "קריוקי",
    "karaoke",
    "פלייבק",
    "playback",
    "instrumental",
    "אינסטרומנטלי",
    "backing track",
    "ringtone",
    "music box",
    "תיבת נגינה",
    "8-bit",
    "lullaby version",
    "מנגינה בלבד",
    "נעימה בלבד",
    "קלידן",
    "לימוד נגינה",
    "אקורדים",
    "הקדמה לשיר",
    "פתיחה דיבור",
    "(intro)",
    "(skit)",
    "מערכון",
    "מדבר עם",
    "ראיון אצל",
)

# Ambiguous song titles that collide with unrelated Hebrew/international hits;
# values list tokens that immediately disqualify a candidate artist/title/album.
HOMONYM_BLOCK_TOKENS: dict[str, tuple[str, ...]] = {
    "שנה טובה": ("קיפניס", "kipnis", "נרדי", "nardi", "אברהם טל", "שלמה גרוניך"),
    "אלף בית": ("נורית הירש", "nurit hirsh", "hirsch", "דיג דיג דוג", "עידן רייכל", "עפרה חזה", "ofra haza", "דליק"),
    "הופה היי": ("יגאל בשן", "yigal bashan", "עוזי חיטמן", "uzi hitman", "יונתן מילר", "הופה היי"),
    "שיר נולד": ("הכבש השישה עשר", "יוני רכטר", "yoni rechter", "יהונתן גפן", "פסטיגל", "festigal", "נינט"),
    "על נהרות בבל": ("boney m", "מידד טסה", "meydad tassa", "אייל גולן", "eyal golan", "צלילי העוד", "אהובה עוזרי"),
    "מר נרקיס": ("ליאור נרקיס", "lior narkis"),
    "תלבשי לבן": ("נועם דדון", "noam dadon"),
    "אין דבר": ("טל סונדק", "tal sondak", "הדס קליינמן", "hadas kleinman", "אביב בכר", "aviv bahar"),
    "מקי הסכינאי": ("bobby darin", "kurt weill", "mack the knife", "frank sinatra", "ella fitzgerald", "louis armstrong"),
}

# For short/generic titles or homonym magnet archive songs, only accept explicitly known performers
STRICT_ARCHIVE_ALLOWED_PERFORMERS: dict[str, tuple[str, ...]] = {
    "צבעים": ("נחמה הנדל", "nechama hendel", "אחינועם ניני", "achinoam nini", "noa", "גיל דור", "gil dor", "נעמי שמר", "naomi shemer"),
    "כף": ("תיאטרון האוהל", "נעמי שמר", "naomi shemer"),
    "חופש": ("רבקה מיכאלי", "rivka michaeli", "טוביה צפיר", "tuvia tzafir", "נעמי שמר", "naomi shemer"),
    "אחד אפס": ("נעמי שמר", "naomi shemer"),
    "שיר חדש": ("נעמי שמר", "naomi shemer"),
    "משחק": ("נעמי שמר", "naomi shemer"),
    "צפון": ("נעמי שמר", "naomi shemer"),
    "הד": ("נעמי שמר", "naomi shemer"),
    "ניר מה לבן": ("אדם", "adam", "נעמי שמר", "naomi shemer"),
    "מטריות שרבורג": ("נעמי שמר", "naomi shemer"),
}

# Archive alt_titles that are false homonyms (different holiday songs / generic phrases)
SKIP_ALT_TITLES_FOR_ARCHIVE = {
    "באנו חושך לגרש",
    "ימי החנוכה",
    "שממה וחוחים ושמים שממה ומישור",
    "וכששרו איזה פלא על המון במות בידור",
    "כבר שש כבר בוקר כבר אור אפור",
    "וביום הראשון בבוקר כשהשמש תצחק טובה",
    "זכר אזכר מעברים נצבו הרים כנד",
    "שלח לחמך על פני המים",
    "דער נייער שער",
    "נייער שער",
    "אותלו ודסדמונה",
    "שמותיהם של מקומות",
    "עולם עגול עגול ושירים בו יש כמו חול",
    "פלאי פלאים נבקע ענן טיפות טיפות",
}

NOISY_CATALOG_ALBUMS = {
    "שירונט",
    "פרויקט בן-יהודה",
    "הארץ",
    "הבלוג של מרית בן ישראל",
    "ח\"ח 2",
    "דא\"ה",
}

# Hebrew <-> English / Latin aliases for performers & ensembles in our catalog
ARTIST_ALIASES: dict[str, tuple[str, ...]] = {
    "נעמי שמר": ("naomi shemer", "shemer naomi"),
    "הגשש החיוור": ("hagashash hahiver", "ha-gashash ha-hiver", "gashash hahiver", "hagashash hachiver", "ha gashash", "the pale tracker"),
    "שולי נתן": ("shuli natan", "shuly natan", "shuly nathan", "shuli nathan"),
    "יוסי בנאי": ("yossi banai", "yosi banai", "banai yossi"),
    "הגבעטרון": ("hagevatron", "gevatron", "hagivatron", "givatron"),
    "יהורם גאון": ("yehoram gaon", "yehoram ga'on", "gaon yehoram"),
    "חבורת בימות": ("bimot", "chavurat bimot", "havurat bimot"),
    "להקת פיקוד המרכז": ("lehakat pikud hamerkaz", "pikud hamerkaz", "central command ensemble"),
    "להקת הנח\"ל": ("lehakat hanachal", "lehakat hanahal", "hanahal", "hanachal", "nachal"),
    "להקת הנחל": ("lehakat hanachal", "lehakat hanahal", "hanahal", "hanachal", "nachal"),
    "משה בקר": ("moshe becker", "moshe beker"),
    "הדודאים": ("hadudaim", "dudaim", "ha-duda'im"),
    "האחיות שמר": ("shemer sisters", "achayot shemer", "haachayot shemer", "האחיות שמר"),
    "הכל עובר חביבי": ("hakol over habibi", "ha'kol over habibi"),
    "רבקה מיכאלי": ("rivka michaeli", "rivka mikhaeli"),
    "יפה ירקוני": ("yafa yarkoni", "yaffa yarkoni"),
    "חוה אלברשטיין": ("chava alberstein", "hava alberstein"),
    "חווה אלברשטיין": ("chava alberstein", "hava alberstein"),
    "שלישיית גשר הירקון": ("gesher hayarkon trio", "gesher hayarkon", "shlishiyat gesher hayarkon"),
    "אריק לביא": ("arik lavi", "arieh lavi"),
    "להקת פיקוד הצפון": ("lehakat pikud hatzafon", "pikud hatzafon"),
    "להקת פיקוד הדרום": ("lehakat pikud hadarom", "pikud hadarom"),
    "ריקה זראי": ("rika zarai",),
    "רוחמה רז": ("ruchama raz", "ruhama raz"),
    "אריק איינשטיין": ("arik einstein",),
    "שמעון בר": ("shimon bar",),
    "הפרברים": ("haparvarim", "parvarim", "ha-parvarim"),
    "דורית ראובני": ("dorit reuveni",),
    "אילנה רובינא": ("ilana rovina", "ilana ruvina"),
    "רבקה רז": ("rivka raz",),
    "דורית פרקש": ("dorit farkash", "dorit farkas"),
    "דודו זכאי": ("dudu zakai",),
    "שושנה דמארי": ("shoshana damari",),
    "נחמה הנדל": ("nechama hendel", "nehama hendel", "helena hendel"),
    "שושיק שני": ("shoshik shani",),
    "שמעון ישראלי": ("shimon israeli",),
    "צילה דגן": ("tzila dagan", "tsila dagan"),
    "שלישיית התאומים": ("hateomim", "teomim", "shlishiyat hateomim", "התאומים"),
    "האחים והאחיות": ("haachim vehaachayot", "ha'achim veha'achayot", "brothers and sisters"),
    "אילנית": ("ilanit",),
    "נתנאלה": ("netanela", "natanela"),
    "בני אמדורסקי": ("benny amdursky", "beni amdursky", "benny amdurski", "beni amdurski"),
    "שוקולד מנטה מסטיק": ("shokolad menta mastik", "chocolat menta mastik"),
    "התרנגולים": ("hatarnegolim", "tarnegolim"),
    "בצל ירוק": ("batzal yarok", "batsal yarok"),
    "בנות בצל ירוק 80": ("batzal yarok", "batsal yarok"),
    "רחל אטאס": ("rachel atas", "rahel atas"),
    "דודו אלהרר": ("dudu elharar",),
    "שולה חן": ("shula chen", "shula hen"),
    "מירי אלוני": ("miri aloni",),
    "חנן יובל": ("chanan yovel", "hanan yovel"),
    "עודד תאומי": ("oded teomi",),
    "אורה זיטנר": ("ora zitner",),
    "אחינועם ניני": ("achinoam nini", "noa"),
    "גיל דור": ("gil dor",),
    "אופירה גלוסקא": ("ofira gluska", "ophira gluska"),
    "גיתית שובל": ("gitit shoval",),
    "עופר לוי": ("ofer levi",),
    "לאה לופטין": ("lea lupatin", "leah lupatin"),
    "חיים צינוביץ'": ("haim tzinovich", "haim zinovich"),
    "עפרה חזה": ("ofra haza",),
    "יהודית רביץ": ("yehudit ravitz",),
    "גידי גוב": ("gidi gov",),
    "נורית גלרון": ("nurit galron",),
    "ריקי גל": ("riki gal", "ricki gal"),
    "שלמה ארצי": ("shlomo artzi",),
    "מתי כספי": ("matti caspi", "mati caspi"),
    "משינה": ("mashina", "mashinah"),
    "שולי רנד": ("shuli rand",),
    "שלומי שבת": ("shlomi shabat", "shlomi shabbat"),
    "אברהם פריד": ("avraham fried",),
    "דודו טסה": ("dudu tassa", "tassa dudu"),
    "אריאל הורוביץ": ("ariel horowitz", "ariel horovitz"),
    "גבי ברלין": ("gabi berlin",),
    "יגאל בשן": ("yigal bashan",),
    "גלי עטרי": ("gali atari",),
    "החלונות הגבוהים": ("hachalonot hagvohim", "hahalonot hagvohim", "the high windows"),
    "אדם": ("adam",),
    "השלושרים": ("hashlosharim", "hashelosharim", "shlosharim"),
    "ציפי שביט": ("tzipi shavit", "tsipi shavit"),
    "נתן דטנר": ("nathan datner", "natan datner"),
    "עוזי מאירי": ("uzi meiri",),
    "צמד דרום": ("tzemed darom", "tsemed darom"),
    "צמד רעים": ("tzemed reim", "tsemed re'im", "tzemed re'im"),
    "שלישיית המעפיל": ("hameafil", "shlishiyat hamaapil"),
    "אהוד בנאי": ("ehud banai",),
    "ירדנה ארזי": ("yardena arazi",),
    "דני ליטני": ("dani litani", "danny litani"),
    "אלי גורנשטיין": ("eli gorenstein",),
    "ישראל גוריון": ("israel gurion",),
    "אפי בן ישראל": ("efi ben israel",),
    "דפנה ארמוני": ("dafna armoni",),
    "אסתר עופרים": ("esther ofarim", "ester ofarim"),
    "האחים אסנר": ("esner brothers", "haachim esner"),
    "דני רובס": ("dani robas", "danny robas"),
    "חבורת רננים": ("renanim", "chavurat renanim", "havurat renanim"),
    "אילן ואילנית": ("ilan & ilanit", "ilan and ilanit", "ilan veilanit"),
    "דני גרנות": ("dani granot", "danny granot"),
    "רותי הולצמן": ("ruti holzman", "ruthie holtzman"),
    "עמיקם גורביץ'": ("amikam gurevich", "amikam gurevitz"),
    "מקהלת הילדים ע\"ש צדיקוב": ("tzadikov", "zadikov", "tzadikov choir"),
    "מקהלת צדיקוב": ("tzadikov", "zadikov", "tzadikov choir"),
    "צביקה פיק": ("zvika pick", "svika pick"),
    "בני אלבז": ("beni elbaz", "benny elbaz"),
    "בועז שרעבי": ("boaz sharabi",),
    "מיטל טרבלסי": ("meital trabelsi", "meytal trabelsi"),
    "שירי מימון": ("shiri maimon",),
    "להקת חיל האוויר": ("air force entertainment troupe", "heil haavir", "cheil haavir"),
    "להקת חיל הים": ("israel navy troupe", "heil hayam", "cheil hayam"),
    "תיאטרון הסמבטיון": ("sambatyon", "sambation", "רחל אטאס", "אריק איינשטיין", "rachel atas", "arik einstein"),
    "טוביה צפיר": ("tuvia tzafir",),
    "רוני בר נוף": ("roni bar nof",),
    "שירולי": ("shiruli",),
    "חנן בן ארי": ("hanan ben ari",),
    "עליזה עזיקרי": ("aliza azikri",),
    "שם-טוב לוי": ("shem-tov levi", "shem tov levi"),
    "שם טוב לוי": ("shem-tov levi", "shem tov levi"),
    "אבי טולדנו": ("avi toledano",),
    "סקסטה": ("sexta",),
    "עמיר בניון": ("amir benayoun",),
    "דורון נשר": ("doron nesher",),
    "טליה שפירא": ("talia shapira",),
    "הרמוניקס": ("harmonics",),
    "מאיר בנאי": ("meir banai",),
    "שלמה בראבא ומוני מושונוב": ("baraba", "moni moshonov"),
    "חבורת שחפים": ("shachafim", "shhafim"),
    "בועז קראוזר": ("boaz krauzer",),
    "רונית רולנד": ("ronit roland",),
    "מיקי קם": ("miki kam", "micky kam"),
    "רינת גבאי": ("rinat gabay", "rinat gabai"),
    "שלמה גרוניך": ("shlomo gronich",),
    "מרדכי פופיק ארנון": ("popik arnon",),
    "קבוצת כנרת": ("kinneret", "kvutzat kinneret"),
    "אלון אולארצ'יק": ("alon oleartchik",),
    "אריאל זילבר": ("ariel zilber",),
    "מרגלית צנעני": ("margalit tzanani", "margol"),
    "אושיק לוי": ("oshik levi",),
    "רבקה זוהר": ("rivka zohar",),
    "אילי גורליצקי": ("ili gorlitzky", "ili gorlizky"),
    "ג'ינה ג'וי": ("gina joy",),
    "ליאור ייני": ("lior yeini", "lior yeyni"),
    "שלמה וישינסקי": ("shlomo vishinsky",),
    "שלומית אהרון": ("shlomit aharon",),
    "שייקה לוי": ("shaike levi",),
    "בני ברמן": ("benny berman", "benni berman"),
    "הגבעטרון": ("hagevatron", "gevatron", "hagivatron", "givatron"),
}

assert all(isinstance(v, tuple) for v in ARTIST_ALIASES.values()), "All alias values must be tuples!"


def norm_heb(s: str) -> str:
    """Normalize Hebrew/Latin text for matching."""
    if not s:
        return ""
    s = str(s).lower()
    s = re.sub(r"[\u0591-\u05C7]", "", s)  # strip nikkud
    s = re.sub(r"[\"'״׳”’‘“()\[\]{}<>!?.,:;–—\-_/\\|+]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def heb_loose(s: str) -> str:
    """Apply tolerant ktiv male/haser folding on already normalized text."""
    s = norm_heb(s)
    s = s.replace("חווה", "חוה").replace("אמא", "אימא").replace("אבא", "איבא")
    s = s.replace("יי", "י").replace("וו", "ו")
    return s


def strip_title_noise(s: str) -> str:
    """Remove parentheticals/remaster/live/melody tags from a track or catalog title."""
    s = str(s or "")
    s = re.sub(r"\(\s*לחן\s+[אב]['׳]?\s*\)", "", s)
    # Remove trailing - Remastered / Live / מתוך / Album Version tags
    s = re.sub(
        r"\s*[-–]\s*(?:remaster(?:ed)?|live|גרסה.*|מתוך.*|acoustic|radio edit|bonus track|album version).*$",
        "",
        s,
        flags=re.IGNORECASE,
    )
    # Remove trailing noise in parentheses
    s = re.sub(
        r"\((?:[^)]*(?:remaster|live|מתוך|הקלטה|גרסה|אלבום|מופע|בהופעה|עם|feat\.|bonus|version|edit|20\d\d|19\d\d)[^)]*)\)",
        "",
        s,
        flags=re.IGNORECASE,
    )
    # Remove leading catalog prefixes like "05 1 חגיגה" or "אצלנו בפסנתר -12-"
    s = re.sub(r"\s+", " ", s).strip()
    return s


_HEB_TO_LATIN_CHAR: dict[str, str] = {
    "א": "[aeouiyh]?",
    "ב": "[bv]",
    "ג": "[gj]",
    "ד": "d",
    "ה": "[haeiou]?",
    "ו": "[vouwi]?",
    "ז": "z",
    "ח": "(?:ch|kh|h)",
    "ט": "t",
    "י": "[yi]?",
    "כ": "(?:ch|kh|k|c)",
    "ך": "(?:ch|kh|k)",
    "ל": "l",
    "מ": "m",
    "ם": "m",
    "נ": "n",
    "ן": "n",
    "ס": "[sc]",
    "ע": "[aeoiuyh']?",
    "פ": "[pf]",
    "ף": "[pf]",
    "צ": "(?:tz|ts|z|c)",
    "ץ": "(?:tz|ts|z)",
    "ק": "[kq]",
    "ר": "r",
    "ש": "(?:sh|s)",
    "ת": "t",
}


def ascii_translit_matches(heb_title: str, cand_title: str) -> bool:
    """Check whether an ASCII-only track title is a phonetic romanization of the Hebrew song title."""
    c_ascii = re.sub(r"[^a-z\s]", " ", norm_heb(strip_title_noise(cand_title))).strip()
    if not c_ascii or re.search(r"[א-ת]", norm_heb(cand_title)):
        return False
    h_words = [w for w in norm_heb(strip_title_noise(heb_title)).split() if w]
    if not h_words:
        return False
    c_compact = re.sub(r"[\s']+", "", c_ascii)
    # Single short word (like אור -> Or) must match tightly by word count and pattern
    if len(h_words) == 1 and len(c_ascii.split()) != 1:
        return False
    pat_parts = []
    for hw in h_words:
        p = "[aeoiuyh']*".join(_HEB_TO_LATIN_CHAR.get(ch, "") for ch in hw)
        pat_parts.append(p)
    full_pat = "^[aeoiuyh']*" + "[aeoiuyh']*".join(pat_parts) + "[aeoiuyh']*$"
    return bool(re.match(full_pat, c_compact))


def _heb_tok_eq(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4 and (a == "ה" + b or b == "ה" + a):
        return True
    return False


def title_similarity(query_title: str, cand_title: str) -> float:
    """Return 0..1 similarity score between expected song title and streaming track title."""
    q_clean = norm_heb(strip_title_noise(query_title))
    c_clean = norm_heb(strip_title_noise(cand_title))
    if not q_clean or not c_clean:
        return 0.0
    if q_clean == c_clean or heb_loose(q_clean) == heb_loose(c_clean):
        return 1.0

    # Check if candidate has "Artist - Title" or "Title - Live" prefix/suffix separated by hyphen
    raw_parts = [norm_heb(p) for p in re.split(r"\s[-–/|]\s", str(cand_title or "")) if norm_heb(p)]
    for part in raw_parts:
        if part == q_clean or heb_loose(part) == heb_loose(q_clean):
            return 0.98

    q_toks = heb_loose(q_clean).split()
    c_toks = heb_loose(c_clean).split()
    if not q_toks or not c_toks:
        return 0.0

    # Short 1-2 word titles must not match much longer multi-word titles unless delimited cleanly
    if len(q_toks) <= 2:
        if len(c_toks) <= len(q_toks) + 1 and all(any(_heb_tok_eq(qt, ct) for ct in c_toks) for qt in q_toks):
            return 0.90
        return 0.0

    matched_q = sum(1 for qt in q_toks if any(_heb_tok_eq(qt, ct) for ct in c_toks))
    if matched_q == len(q_toks):
        extra = len(c_toks) - len(q_toks)
        if extra <= 0:
            return 0.96
        if extra <= 2:
            return 0.89
        if extra <= 4 and q_clean in c_clean:
            return 0.85
    # High symmetric similarity for multi-word titles with slight spelling shifts
    denom = len(set(q_toks) | set(c_toks))
    return round(matched_q / denom, 3) if denom else 0.0


def has_bad_keyword(cand_title: str, cand_artist: str, cand_album: str) -> bool:
    blob = f"{cand_title} {cand_artist} {cand_album}".lower()
    return any(kw in blob for kw in BAD_TRACK_KEYWORDS)


def hits_homonym_block(song_title: str, cand_title: str, cand_artist: str, cand_album: str) -> bool:
    base_t = strip_title_noise(song_title)
    blocked = HOMONYM_BLOCK_TOKENS.get(song_title) or HOMONYM_BLOCK_TOKENS.get(base_t)
    if not blocked:
        return False
    blob = f"{cand_title} {cand_artist} {cand_album}".lower()
    blob_norm = norm_heb(blob)
    for tok in blocked:
        t_low = tok.lower()
        if t_low in blob or norm_heb(t_low) in blob_norm:
            return True
    return False


def expand_performer_tokens(perf_str: str) -> list[list[str]]:
    """Split a Hebrew performer description into performer units, each with Hebrew+Latin alias variants."""
    if not perf_str:
        return []
    s = re.sub(r"\([^)]*\)", " ", str(perf_str))
    s = re.sub(r'"([^"]+)"', r"\1", s)
    # Remove role descriptors like 'משתתפי המחזמר' / 'משתתפי אצלנו בפסנתר' -> handled separately by album too
    s = re.sub(r"\bמשתתפי\s+(?:המחזמר\s+)?", "", s)
    parts = re.split(r"\s*(?:,|;|/| ו-| בליווי | והלהקות | ולהקת | ונעמי | עם )\s*|\s+ו(?=[א-ת])", s)
    units: list[list[str]] = []
    # Re-add נעמי שמר if split ate the 'ו' in 'ונעמי שמר'
    if "ונעמי שמר" in perf_str or "נעמי שמר" in perf_str:
        parts.append("נעמי שמר")
    for raw_p in parts:
        p = raw_p.strip()
        if not p or len(p) < 2:
            continue
        p_norm = norm_heb(p)
        variants = [p_norm, heb_loose(p)]
        for k, aliases in ARTIST_ALIASES.items():
            kn = norm_heb(k)
            if kn == p_norm or (len(kn) >= 5 and kn in p_norm):
                for al in aliases:
                    variants.append(norm_heb(al))
        # Deduplicate variants
        seen_v = []
        for v in variants:
            if v and v not in seen_v:
                seen_v.append(v)
        if seen_v:
            units.append(seen_v)
    return units


def artist_matches_target(cand_artist: str, cand_title: str, cand_album: str, target_perf: str) -> bool:
    """Check whether streaming track artist/title/album matches a target catalog performer."""
    if not target_perf:
        return False
    units = expand_performer_tokens(target_perf)
    if not units:
        return False
    ca_norm = norm_heb(cand_artist)
    ct_norm = norm_heb(cand_title)
    calb_norm = norm_heb(cand_album)
    ca_loose = heb_loose(cand_artist)
    combined_norm = f"{ca_norm} {ct_norm} {calb_norm}"
    for variants in units:
        for var in variants:
            if len(var) < 3:
                continue
            # Match primarily on artist, or artist alias inside album/title if artist is 'Various Artists' / cast
            if var in ca_norm or var in ca_loose:
                return True
            if ("various" in ca_norm or "אמנים" in ca_norm or "מחזמר" in combined_norm) and var in calb_norm:
                return True
            # Require word-boundary match in title if track artist is generic
            if re.search(rf"(?:^|\s){re.escape(var)}(?:$|\s)", ct_norm):
                return True
    return False


def album_matches_musical(cand_album: str, row_album_group: str, matched_album: str, catalog_albums: list[str]) -> bool:
    """Allow musical/cast rows when streaming album explicitly matches musical/show title or Naomi Shemer collection."""
    calb = heb_loose(cand_album)
    if not calb:
        return False
    musicals = ("אצלנו בפסנתר", "etslenu bapsanter", "מסעות בנימין השלישי", "חמש חמש", "hamesh hamesh", "המלך ואני", "חבורת בימות", "bimot", "חפצים אישיים", "שירי נעמי שמר", "naomi shemer")
    target_blob = f"{row_album_group} {matched_album} {' '.join(catalog_albums)}"
    target_norm = heb_loose(target_blob)
    for m in musicals:
        if heb_loose(m) in target_norm and heb_loose(m) in calb:
            return True
    return False


class StreamingCache:
    """Incremental JSON disk cache for Deezer and iTunes IL HTTP responses."""

    def __init__(self, path: Path):
        self.path = path
        if path.exists():
            try:
                self.data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                self.data = {"deezer_search": {}, "deezer_track": {}, "itunes_search": {}}
        else:
            self.data = {"deezer_search": {}, "deezer_track": {}, "itunes_search": {}}
        self.dirty = 0

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
        self.dirty = 0

    def mark_dirty(self) -> None:
        self.dirty += 1
        if self.dirty >= 25:
            self.save()


def http_get_json(url: str, timeout: int = 15, retries: int = 4) -> dict[str, Any]:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # Deezer soft rate-limit returns JSON {"error": {"code": 4, ...}}
            if isinstance(data, dict) and isinstance(data.get("error"), dict):
                code = data["error"].get("code")
                if code == 4:
                    time.sleep(1.5 * (2**attempt))
                    continue
            return data
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (403, 429, 500, 502, 503):
                time.sleep(2.5 * (attempt + 1))
                continue
            raise
        except Exception as e:
            last_err = e
            time.sleep(1.0 * (attempt + 1))
    if last_err:
        raise last_err
    return {}


def deezer_search(query: str, cache: StreamingCache) -> list[dict[str, Any]]:
    ds = cache.data["deezer_search"]
    if query in ds:
        return ds[query]
    url = "https://api.deezer.com/search?" + urllib.parse.urlencode({"q": query, "limit": 25})
    try:
        res = http_get_json(url)
        items = [
            {
                "id": it.get("id"),
                "title": it.get("title", ""),
                "artist": (it.get("artist") or {}).get("name", ""),
                "album": (it.get("album") or {}).get("title", ""),
                "duration": int(it.get("duration") or 0),
                "link": it.get("link", ""),
                "rank": int(it.get("rank") or 0),
            }
            for it in (res.get("data") or [])
        ]
        ds[query] = items
        cache.mark_dirty()
        return items
    except Exception:
        return []


def deezer_track_detail(tid: int | str, cache: StreamingCache) -> dict[str, Any]:
    dt = cache.data["deezer_track"]
    k = str(tid)
    if k in dt:
        return dt[k]
    try:
        res = http_get_json(f"https://api.deezer.com/track/{k}")
        if not res or res.get("error"):
            return {}
        info = {
            "id": res.get("id"),
            "isrc": (res.get("isrc") or "").strip(),
            "title": res.get("title", ""),
            "artist": (res.get("artist") or {}).get("name", ""),
            "album": (res.get("album") or {}).get("title", ""),
            "duration": int(res.get("duration") or 0),
            "release_date": res.get("release_date", ""),
            "link": res.get("link", ""),
        }
        dt[k] = info
        cache.mark_dirty()
        return info
    except Exception:
        return {}


def itunes_search(query: str, cache: StreamingCache) -> list[dict[str, Any]]:
    it_cache = cache.data["itunes_search"]
    if query in it_cache:
        return it_cache[query]
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": query, "country": "IL", "media": "music", "entity": "song", "limit": 12}
    )
    time.sleep(2.1)  # polite iTunes pacing
    try:
        res = http_get_json(url, timeout=18, retries=3)
        items = [
            {
                "id": r.get("trackId"),
                "title": r.get("trackName", ""),
                "artist": r.get("artistName", ""),
                "album": r.get("collectionName", ""),
                "duration": int(round((r.get("trackTimeMillis") or 0) / 1000.0)),
                "link": r.get("trackViewUrl", ""),
                "release_date": (r.get("releaseDate") or "")[:10],
            }
            for r in (res.get("results") or [])
        ]
        it_cache[query] = items
        cache.mark_dirty()
        return items
    except Exception:
        return []


def score_candidate(
    cand: dict[str, Any],
    song_title: str,
    alt_titles: list[str],
    target_perf: str,
    allowed_fallbacks: list[str],
    row_album_group: str,
    matched_album: str,
    catalog_albums: list[str],
    allow_fallback_perf: bool,
    is_archive: bool,
    role_category: str = "",
) -> tuple[float, str] | None:
    """Evaluate candidate streaming track and return (score, match_kind) or None."""
    ctitle = str(cand.get("title") or "")
    cartist = str(cand.get("artist") or "")
    calbum = str(cand.get("album") or "")
    dur = int(cand.get("duration") or 0)

    if dur and (dur < 35 or dur > 900):
        return None
    if has_bad_keyword(ctitle, cartist, calbum):
        return None
    if hits_homonym_block(song_title, ctitle, cartist, calbum):
        return None

    # For songs where Naomi Shemer is ONLY a performer (not author/composer/translator),
    # strictly accept ONLY recordings performed by Naomi Shemer herself.
    if role_category == "performance_only":
        if not artist_matches_target(cartist, ctitle, calbum, "נעמי שמר"):
            return None

    # Special guard on split Sapaney compositions
    if "ספני שלמה המלך" in song_title:
        blob = f"{cartist} {ctitle} {calbum}".lower()
        if "(לחן ב')" in song_title:
            if any(x in blob for x in ("סמבטיון", "sambatyon", "אטאס", "atas", "איינשטיין", "einstein")):
                return None
            if not any(x in blob for x in ("רובינא", "rovina", "ruvina", "נעמי שמר", "naomi shemer")):
                return None
        elif "(לחן א')" in song_title:
            if "רובינא" in blob or "rovina" in blob or "ruvina" in blob:
                return None
            if not any(x in blob for x in ("סמבטיון", "sambatyon", "אטאס", "atas", "איינשטיין", "einstein", "פרוסט")):
                return None

    # Strict archive performer allowlist for short/ambiguous archive titles
    if is_archive and song_title in STRICT_ARCHIVE_ALLOWED_PERFORMERS:
        allowed_strict = STRICT_ARCHIVE_ALLOWED_PERFORMERS[song_title]
        blob = norm_heb(f"{cartist} {calbum} {ctitle}")
        if not any(norm_heb(a) in blob for a in allowed_strict):
            return None

    # Check title similarity against main title (+ clean variant alts if not junk opening lines)
    base_title = strip_title_noise(song_title)
    titles_to_check = [base_title]
    for at in alt_titles or []:
        if at in SKIP_ALT_TITLES_FOR_ARCHIVE:
            continue
        if is_archive and len(norm_heb(at).split()) < 2 and len(norm_heb(base_title).split()) >= 2:
            continue
        titles_to_check.append(at)

    best_tsim = 0.0
    for qt in titles_to_check:
        sim = title_similarity(qt, ctitle)
        if qt != base_title:
            sim *= 0.94
        best_tsim = max(best_tsim, sim)

    min_sim = 0.88 if is_archive else 0.85
    translit_ok = best_tsim < min_sim and ascii_translit_matches(base_title, ctitle)
    if best_tsim < min_sim and not translit_ok:
        return None

    # Check performer / album verification
    match_kind = ""
    perf_score = 0.0

    # Special override rule: '#190 למה צחקה מיכל' targets HaGashash HaHiver first on Spotify
    if target_perf and artist_matches_target(cartist, ctitle, calbum, target_perf):
        match_kind = "exact_performer"
        perf_score = 300.0
        if translit_ok:
            best_tsim = 0.88
    elif album_matches_musical(calbum, row_album_group, matched_album, catalog_albums):
        match_kind = "musical_album"
        perf_score = 220.0
        if translit_ok:
            best_tsim = 0.87
    elif translit_ok:
        return None
    elif allow_fallback_perf or is_archive:
        # Check catalog performers (excluding tiny/ambiguous names unless full name matches)
        matched_fb = None
        for fb in allowed_fallbacks:
            if not fb or len(norm_heb(fb)) < 3:
                continue
            if artist_matches_target(cartist, ctitle, calbum, fb):
                matched_fb = fb
                break
        if matched_fb:
            match_kind = "catalog_performer_fallback" if not is_archive else "archive_verified_performer"
            perf_score = 240.0 if ("נעמי שמר" in matched_fb) else 200.0
        elif is_archive:
            # Check album mentioning Naomi Shemer or verified catalog albums (skipping generic source names)
            calb_n = heb_loose(calbum)
            if "נעמי שמר" in calb_n or "naomi shemer" in calb_n:
                match_kind = "archive_naomi_album"
                perf_score = 180.0
            else:
                for ca in catalog_albums:
                    if ca in NOISY_CATALOG_ALBUMS or re.match(r"^(?:MUS|הד|דא\"ה|ח\"ח)", ca):
                        continue
                    ca_clean = re.sub(r"^\d+\s+", "", ca).strip()
                    if len(heb_loose(ca_clean)) >= 6 and heb_loose(ca_clean) in calb_n:
                        match_kind = "archive_catalog_album"
                        perf_score = 175.0
                        break

    if not match_kind:
        return None

    bonus = 0.0
    if "נעמי שמר" in heb_loose(calbum) or "naomi shemer" in heb_loose(calbum):
        bonus += 15.0
    if not is_archive and matched_album and heb_loose(strip_title_noise(matched_album)) in heb_loose(calbum):
        bonus += 25.0
    rank_bonus = min(20.0, math.log10(1 + max(0, int(cand.get("rank") or 0))) * 3.0)
    return (round(best_tsim * 100.0 + perf_score + bonus + rank_bonus, 2), match_kind)


def find_unverified_hints(
    pool: list[dict[str, Any]], song_title: str, alt_titles: list[str]
) -> list[dict[str, Any]]:
    """Collect title-only hits that lacked artist/album verification so user can review manually."""
    base_title = strip_title_noise(song_title)
    out = []
    seen = set()
    for cand in pool:
        ctitle = str(cand.get("title") or "")
        cartist = str(cand.get("artist") or "")
        calbum = str(cand.get("album") or "")
        dur = int(cand.get("duration") or 0)
        if dur and (dur < 40 or dur > 720):
            continue
        if has_bad_keyword(ctitle, cartist, calbum):
            continue
        if hits_homonym_block(song_title, ctitle, cartist, calbum):
            continue
        if song_title in STRICT_ARCHIVE_ALLOWED_PERFORMERS:
            continue
        sim = title_similarity(base_title, ctitle)
        if sim >= 0.90:
            key = (norm_heb(ctitle), norm_heb(cartist))
            if key not in seen:
                seen.add(key)
                out.append(cand)
            if len(out) >= 3:
                break
    return out


def clean_query_title(t: str) -> str:
    t = re.sub(r"\(\s*לחן\s+[אב]['׳]?\s*\)", "", t)
    return re.sub(r"\s+", " ", t).strip()


def primary_artist_query(perf: str) -> str:
    """Clean performer string down to searchable core name."""
    s = re.sub(r"\([^)]*\)", " ", perf or "")
    s = re.sub(r"\bמשתתפי\s+(?:המחזמר\s+)?", "", s)
    s = re.split(r"[,/|]", s)[0].strip()
    return re.sub(r"\s+", " ", s)


def main() -> None:
    pdata = json.loads(PLAYLIST_JSON_PATH.read_text(encoding="utf-8"))
    cdata = json.loads(CATALOG_JSON_PATH.read_text(encoding="utf-8"))
    cmap = {s["title"]: s for s in cdata["songs"]}

    playlist = pdata["playlist"]
    matched_rows = [x for x in playlist if x.get("selected_video")]
    unmatched_rows = [x for x in playlist if not x.get("selected_video")]

    # Partition music rows vs skipped TV/sketches & Primary vs Extras (preserving exact order)
    skipped_rows: list[dict[str, Any]] = []
    music_rows: list[dict[str, Any]] = []
    seen_primary_titles: set[str] = set()
    for it in matched_rows:
        sv = it["selected_video"]
        ag = it.get("album_group", "")
        mp = sv.get("matched_performer", "")
        if ag == "תוכניות טלוויזיה ומופעים מלאים":
            skipped_rows.append({"row": it, "reason": "תוכנית טלוויזיה / מופע שלם"})
            continue
        if sv["video_id"] == "k0RE3k8k1pQ" or "סקיצה נדירה" in mp:
            skipped_rows.append({"row": it, "reason": "סקיצה נדירה / קטע ארכיוני מהאולפן"})
            continue
        # Preserve contiguous primary block vs extras block
        is_extra = it["title"] in seen_primary_titles
        if not is_extra:
            seen_primary_titles.add(it["title"])
        it_copy = dict(it)
        it_copy["_block"] = f"e{it['canonical_layer']}" if is_extra else f"p{it['canonical_layer']}"
        it_copy["_is_primary"] = not is_extra
        music_rows.append(it_copy)

    print(f"Loaded {len(music_rows)} music rows, {len(skipped_rows)} skipped TV/sketches, {len(unmatched_rows)} archive songs.")

    cache = StreamingCache(CACHE_PATH)

    # Pass 1A: Deezer search once per unique catalog song title (451 titles)
    unique_queries = sorted({clean_query_title(x["title"]) for x in music_rows + unmatched_rows})
    missing_q = [q for q in unique_queries if q not in cache.data["deezer_search"]]
    print(f"Pass 1A (Deezer title searches): {len(unique_queries)} total, {len(missing_q)} uncached...")
    if missing_q:
        def _dz(q: str) -> tuple[str, list]:
            time.sleep(0.14)
            return q, deezer_search(q, cache)
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = [ex.submit(_dz, q) for q in missing_q]
            for fut in as_completed(futs):
                fut.result()
        cache.save()

    # Build targeted Deezer queries for rows needing specific performer+title search
    extra_dz_queries: set[str] = set()
    for it in music_rows:
        qt = clean_query_title(it["title"])
        sv = it["selected_video"]
        mp = "הגשש החיוור" if it["title"] == "למה צחקה מיכל" else sv.get("matched_performer", "")
        pa = primary_artist_query(mp)
        pool = cache.data["deezer_search"].get(qt, [])
        # Also query Hebrew + artist if title search returned >= 15 items or nothing matching artist
        if pa and not any(artist_matches_target(c["artist"], c["title"], c["album"], mp) for c in pool):
            extra_dz_queries.add(f"{qt} {pa}")
        for alt in (it.get("alt_titles") or [])[:1]:
            if alt not in SKIP_ALT_TITLES_FOR_ARCHIVE and clean_query_title(alt) != qt:
                extra_dz_queries.add(clean_query_title(alt))
    for it in unmatched_rows:
        qt = clean_query_title(it["title"])
        for p in (it.get("catalog_performers") or [])[:2]:
            extra_dz_queries.add(f"{qt} {primary_artist_query(p)}")
        if "נעמי שמר" not in " ".join(it.get("catalog_performers") or []):
            extra_dz_queries.add(f"{qt} נעמי שמר")

    missing_extra = [q for q in sorted(extra_dz_queries) if q not in cache.data["deezer_search"]]
    print(f"Pass 1B (Deezer targeted title+artist searches): {len(extra_dz_queries)} total, {len(missing_extra)} uncached...")
    if missing_extra:
        def _dz2(q: str) -> tuple[str, list]:
            time.sleep(0.14)
            return q, deezer_search(q, cache)
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = [ex.submit(_dz2, q) for q in missing_extra]
            for fut in as_completed(futs):
                fut.result()
        cache.save()

    def collect_deezer_pool(it: dict[str, Any], target_perf: str) -> list[dict[str, Any]]:
        qt = clean_query_title(it["title"])
        queries = [qt]
        if target_perf:
            pa = primary_artist_query(target_perf)
            if pa:
                queries.append(f"{qt} {pa}")
        for p in (it.get("catalog_performers") or [])[:2]:
            queries.append(f"{qt} {primary_artist_query(p)}")
        queries.append(f"{qt} נעמי שמר")
        for alt in (it.get("alt_titles") or [])[:1]:
            if alt not in SKIP_ALT_TITLES_FOR_ARCHIVE:
                queries.append(clean_query_title(alt))
        seen_ids = set()
        pool = []
        for q in queries:
            for cand in cache.data["deezer_search"].get(q, []):
                cid = cand.get("id")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    pool.append(cand)
        return pool

    def evaluate_row_on_pool(
        it: dict[str, Any],
        pool: list[dict[str, Any]],
        target_perf: str,
        allow_fallback: bool,
        is_archive: bool,
        used_ids: set[str],
        source_tag: str,
    ) -> dict[str, Any] | None:
        sv = it.get("selected_video") or {}
        cs = cmap.get(it["title"], {})
        role_cat = it.get("role_category", "")
        if role_cat == "performance_only":
            cat_perfs = ["נעמי שמר"]
            eff_target = "נעמי שמר"
            eff_fallback = False
        else:
            cat_perfs = list(dict.fromkeys((it.get("catalog_performers") or []) + (cs.get("performers") or []) + ["נעמי שמר"]))
            eff_target = target_perf
            eff_fallback = allow_fallback
        cat_albs = list(dict.fromkeys((it.get("catalog_albums") or []) + (cs.get("albums") or [])))
        scored = []
        for cand in pool:
            cid_key = f"{source_tag}:{cand.get('id')}"
            if cid_key in used_ids:
                continue
            res = score_candidate(
                cand=cand,
                song_title=it["title"],
                alt_titles=it.get("alt_titles") or [],
                target_perf=eff_target,
                allowed_fallbacks=cat_perfs,
                row_album_group=it.get("album_group", ""),
                matched_album=sv.get("matched_album", ""),
                catalog_albums=cat_albs,
                allow_fallback_perf=eff_fallback,
                is_archive=is_archive,
                role_category=role_cat,
            )
            if res:
                scored.append((res[0], res[1], cand))
        if not scored:
            return None
        scored.sort(key=lambda t: (-t[0], int(t[2].get("duration") or 0)))
        top_score, top_kind, top_cand = scored[0]
        return {"score": top_score, "match_kind": top_kind, "cand": top_cand, "source_tag": source_tag}

    # Initial Deezer matching pass to identify misses before hitting iTunes IL
    used_deezer_ids: set[str] = set()
    used_isrcs: set[str] = set()
    used_norm_pairs: set[tuple[str, str]] = set()
    prelim_dz: dict[str, dict[str, Any]] = {}

    # Priority order: primary music rows -> archive songs -> extra music rows
    for idx, it in enumerate(music_rows):
        it["_row_uid"] = f"m_{it['index']}_{it['selected_video']['video_id']}"
    for idx, it in enumerate(unmatched_rows):
        it["_row_uid"] = f"u_{idx}_{it['title']}"

    ordered_eval = (
        [it for it in music_rows if it["_is_primary"]]
        + unmatched_rows
        + [it for it in music_rows if not it["_is_primary"]]
    )

    itunes_needed: list[tuple[dict[str, Any], str, str]] = []  # (item, target_perf, query)
    for it in ordered_eval:
        is_arch = it["_row_uid"].startswith("u_")
        sv = it.get("selected_video") or {}
        if it["title"] == "למה צחקה מיכל" and not is_arch:
            target_perf = "הגשש החיוור"
        else:
            target_perf = sv.get("matched_performer", "")
        pool = collect_deezer_pool(it, target_perf)
        hit = evaluate_row_on_pool(
            it,
            pool,
            target_perf=target_perf,
            allow_fallback=bool(it.get("_is_primary")) and ("ספני שלמה המלך" not in it["title"]),
            is_archive=is_arch,
            used_ids=used_deezer_ids,
            source_tag="dz",
        )
        if hit:
            prelim_dz[it["_row_uid"]] = hit
            used_deezer_ids.add(f"dz:{hit['cand']['id']}")
        else:
            # Queue for iTunes IL fallback
            qt = clean_query_title(it["title"])
            if not is_arch:
                pa = primary_artist_query(target_perf)
                q_str = f"{qt} {pa}".strip() if pa else qt
                itunes_needed.append((it, target_perf, q_str))
            else:
                perfs = it.get("catalog_performers") or []
                if perfs:
                    itunes_needed.append((it, perfs[0], f"{qt} {primary_artist_query(perfs[0])}".strip()))
                elif len(norm_heb(qt).split()) >= 2:
                    itunes_needed.append((it, "נעמי שמר", f"{qt} נעמי שמר"))

    # Pass 1C: Fetch /track/{id} for ALL Deezer matches to obtain official ISRCs
    dz_track_ids = [hit["cand"]["id"] for hit in prelim_dz.values()]
    uncached_tids = [tid for tid in dz_track_ids if str(tid) not in cache.data["deezer_track"]]
    print(f"Pass 1C (Deezer /track ISRCs): {len(dz_track_ids)} matches, {len(uncached_tids)} uncached...")
    if uncached_tids:
        def _dt(tid: Any) -> dict[str, Any]:
            time.sleep(0.14)
            return deezer_track_detail(tid, cache)
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = [ex.submit(_dt, tid) for tid in uncached_tids]
            for fut in as_completed(futs):
                fut.result()
        cache.save()

    # Pass 2: Apple iTunes Israel fallback ONLY for missed rows
    uncached_it_qs = list(dict.fromkeys(q for _, _, q in itunes_needed if q not in cache.data["itunes_search"]))
    print(f"Pass 2 (iTunes IL fallback): {len(itunes_needed)} missed rows ({len(uncached_it_qs)} uncached queries)...")
    for q in uncached_it_qs:
        itunes_search(q, cache)
    cache.save()

    # Final assembly, ISRC + (title,artist) deduplication, and ordering
    # Track matched results keyed by _row_uid
    final_results: dict[str, dict[str, Any]] = {}
    upgrades_notes: list[dict[str, Any]] = []
    unverified_archive_hints: list[dict[str, Any]] = []

    def try_commit_match(uid: str, res_dict: dict[str, Any]) -> bool:
        isrc = (res_dict.get("isrc") or "").strip().upper()
        pair = (heb_loose(strip_title_noise(res_dict["stream_title"])), heb_loose(res_dict["stream_artist"]))
        if isrc and isrc in used_isrcs:
            return False
        if pair in used_norm_pairs:
            return False
        if isrc:
            used_isrcs.add(isrc)
        used_norm_pairs.add(pair)
        final_results[uid] = res_dict
        return True

    used_it_ids: set[str] = set()
    # Evaluate in same priority order: primary -> archive -> extras
    for it in ordered_eval:
        uid = it["_row_uid"]
        is_arch = uid.startswith("u_")
        sv = it.get("selected_video") or {}
        if it["title"] == "למה צחקה מיכל" and not is_arch:
            target_perf = "הגשש החיוור"
        else:
            target_perf = sv.get("matched_performer", "")

        committed = False
        if uid in prelim_dz:
            hit = prelim_dz[uid]
            cand = hit["cand"]
            det = cache.data["deezer_track"].get(str(cand["id"]), {})
            rec = {
                "catalog_title": it["title"],
                "year": it.get("year", ""),
                "layer": int(it.get("canonical_layer", 3)),
                "youtube_index": it.get("index"),
                "youtube_performer": sv.get("matched_performer", ""),
                "stream_title": det.get("title") or cand.get("title", ""),
                "stream_artist": det.get("artist") or cand.get("artist", ""),
                "stream_album": det.get("album") or cand.get("album", ""),
                "isrc": det.get("isrc", ""),
                "provider": "deezer_isrc" if det.get("isrc") else "deezer",
                "provider_url": det.get("link") or cand.get("link", ""),
                "duration_sec": det.get("duration") or cand.get("duration", 0),
                "match_kind": hit["match_kind"],
                "score": hit["score"],
                "is_archive_discovery": is_arch,
                "block": "p3_archive" if is_arch else it.get("_block", ""),
            }
            committed = try_commit_match(uid, rec)
            if committed and it["title"] == "למה צחקה מיכל" and not is_arch:
                upgrades_notes.append(
                    {
                        "song": "למה צחקה מיכל",
                        "youtube_perf": "גיתית שובל (הוקלטה ביוטיוב כקאבר ב-#190)",
                        "streaming_perf": f"{rec['stream_artist']} — {rec['stream_album']} (ISRC `{rec['isrc']}`)",
                        "note": "שדרוג לביצוע האולפן המקורי של הגשש החיוור הקיים בסטרימינג!",
                    }
                )
            elif committed and hit["match_kind"] in ("catalog_performer_fallback", "musical_album") and target_perf and not is_arch:
                upgrades_notes.append(
                    {
                        "song": it["title"],
                        "youtube_perf": target_perf,
                        "streaming_perf": f"{rec['stream_artist']} — {rec['stream_album']}" + (f" (`{rec['isrc']}`)" if rec["isrc"] else ""),
                        "note": f"התאמה דרך `{hit['match_kind']}` (המבצע המקורי ביוטיוב לא הופץ בנפרד בסטרימינג).",
                    }
                )

        if not committed:
            # Check iTunes pool
            qt = clean_query_title(it["title"])
            q_cands = []
            if not is_arch:
                pa = primary_artist_query(target_perf)
                q_cands.append(f"{qt} {pa}".strip() if pa else qt)
            else:
                perfs = it.get("catalog_performers") or []
                if perfs:
                    q_cands.append(f"{qt} {primary_artist_query(perfs[0])}".strip())
                else:
                    q_cands.append(f"{qt} נעמי שמר")
            it_pool = []
            seen_it = set()
            for q in q_cands:
                for c in cache.data["itunes_search"].get(q, []):
                    if c.get("id") and c["id"] not in seen_it:
                        seen_it.add(c["id"])
                        it_pool.append(c)
            hit2 = evaluate_row_on_pool(
                it,
                it_pool,
                target_perf=target_perf,
                allow_fallback=bool(it.get("_is_primary")) and ("ספני שלמה המלך" not in it["title"]),
                is_archive=is_arch,
                used_ids=used_it_ids,
                source_tag="it",
            )
            if hit2:
                used_it_ids.add(f"it:{hit2['cand']['id']}")
                c2 = hit2["cand"]
                rec2 = {
                    "catalog_title": it["title"],
                    "year": it.get("year", ""),
                    "layer": int(it.get("canonical_layer", 3)),
                    "youtube_index": it.get("index"),
                    "youtube_performer": sv.get("matched_performer", ""),
                    "stream_title": c2.get("title", ""),
                    "stream_artist": c2.get("artist", ""),
                    "stream_album": c2.get("album", ""),
                    "isrc": "",
                    "provider": "itunes_il",
                    "provider_url": c2.get("link", ""),
                    "duration_sec": c2.get("duration", 0),
                    "match_kind": hit2["match_kind"],
                    "score": hit2["score"],
                    "is_archive_discovery": is_arch,
                    "block": "p3_archive" if is_arch else it.get("_block", ""),
                }
                committed = try_commit_match(uid, rec2)

        if not committed and is_arch and it.get("role_category") != "performance_only":
            hints = find_unverified_hints(collect_deezer_pool(it, ""), it["title"], it.get("alt_titles") or [])
            if hints:
                unverified_archive_hints.append({"song": it["title"], "year": it.get("year", ""), "hints": hints[:2]})

    # Build final ordered CSV rows:
    # p1 -> p2 -> p3 (with archive discoveries merged chronologically by year; undated at end of p3) -> e1 -> e2 -> e3
    by_block: dict[str, list[dict[str, Any]]] = {k: [] for k in ("p1", "p2", "p3", "e1", "e2", "e3")}
    for it in music_rows:
        uid = it["_row_uid"]
        if uid in final_results:
            by_block[it["_block"]].append(final_results[uid])

    archive_hits = [final_results[it["_row_uid"]] for it in unmatched_rows if it["_row_uid"] in final_results]
    dated_arch = [a for a in archive_hits if str(a.get("year", "")).isdigit()]
    undated_arch = [a for a in archive_hits if not str(a.get("year", "")).isdigit()]

    # Merge dated archive hits chronologically into p3
    p3_merged: list[dict[str, Any]] = []
    used_arch_ids: set[int] = set()
    for p3_item in by_block["p3"]:
        p3_yr = int(p3_item["year"]) if str(p3_item.get("year", "")).isdigit() else 9999
        for i, ah in enumerate(dated_arch):
            if i not in used_arch_ids and int(ah["year"]) <= p3_yr:
                p3_merged.append(ah)
                used_arch_ids.add(i)
        p3_merged.append(p3_item)
    for i, ah in enumerate(dated_arch):
        if i not in used_arch_ids:
            p3_merged.append(ah)
    p3_merged.extend(undated_arch)
    by_block["p3"] = p3_merged

    ordered_tracks = by_block["p1"] + by_block["p2"] + by_block["p3"] + by_block["e1"] + by_block["e2"] + by_block["e3"]

    # Also add Gitit Shoval's studio recording for 'למה צחקה מיכל' in e2 if HaGashash won #190 and Gitit isn't duplicated
    # (Optional extra: let's check if already present; clean if only unique ISRC!)

    # Write outputs to spotify_export/
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    # Remove any stale soundiiz_part_*.csv from prior runs
    for old_p in EXPORT_DIR.glob("soundiiz_part_*.csv"):
        old_p.unlink()

    full_csv_path = EXPORT_DIR / "soundiiz_full_all.csv"
    fieldnames = ["title", "artist", "album", "isrc"]
    with open(full_csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for t in ordered_tracks:
            w.writerow(
                {
                    "title": t["stream_title"],
                    "artist": t["stream_artist"],
                    "album": t["stream_album"],
                    "isrc": t["isrc"],
                }
            )

    part_paths: list[tuple[Path, int]] = []
    num_parts = max(1, math.ceil(len(ordered_tracks) / SOUNDIIZ_CHUNK_SIZE))
    for i in range(num_parts):
        chunk = ordered_tracks[i * SOUNDIIZ_CHUNK_SIZE : (i + 1) * SOUNDIIZ_CHUNK_SIZE]
        pp = EXPORT_DIR / f"soundiiz_part_{i + 1}.csv"
        with open(pp, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for t in chunk:
                w.writerow(
                    {
                        "title": t["stream_title"],
                        "artist": t["stream_artist"],
                        "album": t["stream_album"],
                        "isrc": t["isrc"],
                    }
                )
        part_paths.append((pp, len(chunk)))

    isrc_count = sum(1 for t in ordered_tracks if t["isrc"])
    itunes_count = sum(1 for t in ordered_tracks if t["provider"] == "itunes_il")
    matched_songs_unique = len({t["catalog_title"] for t in ordered_tracks})
    unmatched_music = [it for it in music_rows if it["_row_uid"] not in final_results]
    still_missing_archive = [it for it in unmatched_rows if it["_row_uid"] not in final_results]

    summary_stats = {
        "total_catalog_songs": len(cmap),
        "music_rows_evaluated": len(music_rows),
        "archive_songs_evaluated": len(unmatched_rows),
        "skipped_tv_and_sketches": len(skipped_rows),
        "total_streaming_tracks": len(ordered_tracks),
        "unique_songs_covered": matched_songs_unique,
        "deezer_isrc_exact": isrc_count,
        "deezer_without_isrc": sum(1 for t in ordered_tracks if t["provider"] == "deezer"),
        "itunes_il_fallback": itunes_count,
        "archive_discoveries": len(archive_hits),
        "soundiiz_parts": len(part_paths),
    }

    json_out = EXPORT_DIR / "spotify_streaming_matches.json"
    json_out.write_text(
        json.dumps({"stats": summary_stats, "tracks": ordered_tracks, "archive_discoveries": archive_hits}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Generate rich Hebrew audit report
    rep_lines = [
        "# 🎧 דוח התאמה לספוטיפיי ולשירותי סטרימינג — שירי נעמי שמר (גרסה ב' המלאה)",
        "",
        "## 📊 סיכום מספרי",
        f"* **סה\"כ רצועות מוכנות לייבוא בספוטיפיי:** **{len(ordered_tracks)}** (מכסות **{matched_songs_unique}** מתוך **{len(cmap)}** שירים בקטלוג)",
        f"* **רצועות עם קוד `ISRC` מדויק (Deezer Master API):** **{isrc_count}** (`{isrc_count * 100 // max(1, len(ordered_tracks))}%`)",
        f"* **השלמות דרך Apple iTunes Israel (ללא ISRC):** **{itunes_count}**",
        f"* **🌟 שירי ארכיון (ללא יוטיוב) שאותרו בסטרימינג:** **{len(archive_hits)}** מתוך {len(unmatched_rows)}",
        f"* **רצועות מיוטיוב שדולגו (תוכניות טלוויזיה מלאות וסקיצות אולפן):** {len(skipped_rows)}",
        f"* **קבצי Soundiiz Free שנוצרו (עד 200 שורות בכל חלק):** **{len(part_paths)}** חלקים + קובץ מאוחד `soundiiz_full_all.csv`",
        "",
        "---",
        "",
        f"## 🌟 פניני ארכיון שאינן ביוטיוב — ונמצאו בסטרימינג! ({len(archive_hits)})",
        "",
    ]
    if archive_hits:
        rep_lines += [
            "| # | שם השיר בקטלוג | שנה | שם בסטרימינג | מבצע | אלבום | ISRC | אופן אימות |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for i, ah in enumerate(archive_hits, 1):
            isrc_s = f"`{ah['isrc']}`" if ah["isrc"] else f"{ah['provider']} (ללא ISRC)"
            rep_lines.append(
                f"| {i} | **{ah['catalog_title']}** | {ah['year'] or '—'} | [{ah['stream_title']}]({ah['provider_url']}) | {ah['stream_artist']} | {ah['stream_album']} | {isrc_s} | {ah['match_kind']} |"
            )
    else:
        rep_lines.append("לא נמצאו רצועות ארכיון מאומתות בסבב זה.")

    rep_lines += [
        "",
        "---",
        "",
        f"## 🔄 שדרוגים והתאמות חלופיות בביצועי יוטיוב ({len(upgrades_notes)})",
        "",
        "| שיר | מבצע ביוטיוב | ביצוע שנמצא לסטרימינג | הערה |",
        "|---|---|---|---|",
    ]
    for u in upgrades_notes[:80]:
        rep_lines.append(f"| **{u['song']}** | {u['youtube_perf']} | {u['streaming_perf']} | {u['note']} |")

    rep_lines += [
        "",
        "---",
        "",
        "## 📦 איך יוצרים את הפלייליסט ב-Spotify בחשבון חינמי (ללא Premium)",
        "",
        "מכיוון שהעברת מעל 200 שירים חינם ב-Soundiiz מתאפשרת בחלוקה לקבצים של עד 200 שורות, הכנו מראש חלקים מסודרים:",
    ]
    for pp, cnt in part_paths:
        rep_lines.append(f"* `{pp.name}` — **{cnt} רצועות**")
    rep_lines += [
        "",
        "### שלבי הביצוע (כ-3 דקות):",
        "1. היכנס ל-[Soundiiz](https://soundiiz.com/) ← בחר **Import Playlist** ← **From File (CSV)** ← העלה את `soundiiz_part_1.csv` ← יבא אל פלייליסט זמני `Naomi 1` ב-Spotify.",
        "2. חזור על הצעד עבור כל חלק (`soundiiz_part_2.csv`, וכו' — כל קובץ הוא מתחת לתקרת ה-200 החינמית).",
        "3. פתח את אפליקציית **Spotify במחשב** ← צור פלייליסט חדש **`שירי נעמי שמר`** ← היכנס ל-`Naomi 1`, לחץ **`Cmd+A`** וגרור לפלייליסט הראשי; אח\"כ עבור אל `Naomi 2`, **`Cmd+A`**, וגרור מיד בסופו (ואז מחק את הזמניים). הסדר המדויק נשמר 1:1!",
        "4. **שלב הבומרנג חזרה אלינו:** פתח את [Exportify](https://exportify.app/) (עובד בחינם גם ללא Premium), ייצא את הפלייליסט `שירי נעמי שמר` ל-CSV והעבר לנו — ונוציא ממנו דף תצוגה מקדימה נפרד עם נגן היברידי (YouTube + Spotify) + שירי הארכיון!",
        "",
        "---",
        "",
        f"## ⚠️ מועמדים משירי הארכיון ללא אימות מבצע/אלבום ({len(unverified_archive_hints)} — לא נכללו ב-CSV)",
        "",
    ]
    for uh in unverified_archive_hints[:30]:
        hs = " | ".join(f"{h['title']} — {h['artist']} ({h['album']})" for h in uh["hints"])
        rep_lines.append(f"* **{uh['song']}** ({uh['year'] or 'ללא שנה'}): {hs}")

    rep_lines += [
        "",
        "---",
        "",
        f"## ⏭️ תוכניות טלוויזיה וסקיצות שדולגו ({len(skipped_rows)})",
        "",
    ]
    for sr in skipped_rows:
        it = sr["row"]
        rep_lines.append(f"* `#{it['index']}` **{it['title']}** — {it['selected_video'].get('matched_performer','')} ({sr['reason']})")

    rep_lines += [
        "",
        "---",
        "",
        f"## ❌ ביצועים שלא אותרו בספוטיפיי/סטרימינג ({len(unmatched_music)} מתוך הפלייליסט, ועוד {len(still_missing_archive)} משירי הארכיון)",
        "",
        "| # | שיר | שכבה | מבצע | הערה |",
        "|---|---|---|---|---|",
    ]
    for um in unmatched_music:
        sv = um.get("selected_video") or {}
        rep_lines.append(f"| #{um['index']} | {um['title']} | {um.get('canonical_layer')} | {sv.get('matched_performer','')} | {'ראשי' if um.get('_is_primary') else 'ביצוע נוסף'} |")
    rep_lines.append("")

    (EXPORT_DIR / "spotify_match_report.md").write_text("\n".join(rep_lines), encoding="utf-8")

    print("\n=== SPOTIFY PHASE 1 SUMMARY ===")
    for k, v in summary_stats.items():
        print(f"  {k}: {v}")
    for pp, cnt in part_paths:
        print(f"  CSV part: {pp.name} ({cnt} rows)")


if __name__ == "__main__":
    main()
