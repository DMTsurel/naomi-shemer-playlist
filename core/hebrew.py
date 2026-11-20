"""Shared Hebrew normalization, duration parsing, and track-matching utilities."""

from __future__ import annotations

import html
import re

NIKUD_RE = re.compile(r"[\u0591-\u05C7]")

BAD_TRACK_KEYWORDS: tuple[str, ...] = (
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


def parse_duration_seconds(dur_str: str) -> int:
    """Parse `MM:SS` or `HH:MM:SS` into integer seconds, or -1 if absent."""
    if not dur_str:
        return -1
    parts = [p for p in str(dur_str).strip().split(":") if p.isdigit()]
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return -1


def get_decade(year_str: str) -> str:
    """Map a 4-digit recording year into UI decade filter buckets."""
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


def norm_heb(s: str) -> str:
    """Normalize Hebrew/Latin text by stripping nikkud and punctuation."""
    if not s:
        return ""
    s = str(s).lower()
    s = NIKUD_RE.sub("", s)
    s = re.sub(r"[\"'״׳”’‘“()\[\]{}<>!?.,:;–—\-_/\\|+]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def heb_loose(s: str) -> str:
    """Apply tolerant ktiv male/haser folding on text."""
    s = norm_heb(s)
    s = s.replace("חווה", "חוה").replace("אמא", "אימא").replace("אבא", "איבא")
    return s.replace("יי", "י").replace("וו", "ו")


def strip_title_noise(s: str) -> str:
    """Remove parentheticals/remaster/live/melody tags from a track or catalog title."""
    s = str(s or "")
    s = re.sub(r"\(\s*לחן\s+[אב]['׳]?\s*\)", "", s)
    s = re.sub(
        r"\s*[-–]\s*(?:remaster(?:ed)?|live|גרסה.*|מתוך.*|acoustic|radio edit|bonus track|album version).*$",
        "",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(
        r"\((?:[^)]*(?:remaster|live|מתוך|הקלטה|גרסה|אלבום|מופע|בהופעה|עם|feat\.|bonus|version|edit|20\d\d|19\d\d)[^)]*)\)",
        "",
        s,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", s).strip()


def heb_tok_eq(a: str, b: str) -> bool:
    """Check Hebrew token equality with leading definite article ה tolerance."""
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4 and (a == "ה" + b or b == "ה" + a):
        return True
    return False


def title_similarity(query_title: str, cand_title: str) -> float:
    """Return 0..1 similarity score between expected song title and track title."""
    q_clean = norm_heb(strip_title_noise(query_title))
    c_clean = norm_heb(strip_title_noise(cand_title))
    if not q_clean or not c_clean:
        return 0.0
    if q_clean == c_clean or heb_loose(q_clean) == heb_loose(c_clean):
        return 1.0

    raw_parts = [norm_heb(p) for p in re.split(r"\s[-–/|]\s", str(cand_title or "")) if norm_heb(p)]
    for part in raw_parts:
        if part == q_clean or heb_loose(part) == heb_loose(q_clean):
            return 0.98

    q_toks = heb_loose(q_clean).split()
    c_toks = heb_loose(c_clean).split()
    if not q_toks or not c_toks:
        return 0.0

    if len(q_toks) <= 2:
        if len(c_toks) <= len(q_toks) + 1 and all(any(heb_tok_eq(qt, ct) for ct in c_toks) for qt in q_toks):
            return 0.90
        return 0.0

    matched_q = sum(1 for qt in q_toks if any(heb_tok_eq(qt, ct) for ct in c_toks))
    if matched_q == len(q_toks):
        extra = len(c_toks) - len(q_toks)
        if extra <= 0:
            return 0.96
        if extra <= 2:
            return 0.89
        if extra <= 4 and q_clean in c_clean:
            return 0.85
    denom = len(set(q_toks) | set(c_toks))
    return round(matched_q / denom, 3) if denom else 0.0


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
    """Check whether an ASCII-only track title is a phonetic romanization of a Hebrew song title."""
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


def has_bad_keyword(cand_title: str, cand_artist: str, cand_album: str) -> bool:
    """Return True if a candidate track mentions karaoke, backing tracks, skits, or interviews."""
    blob = f"{cand_title} {cand_artist} {cand_album}".lower()
    return any(kw in blob for kw in BAD_TRACK_KEYWORDS)


FINDER_SPELLING_VARIANTS: list[tuple[str, str]] = [
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
    ('אל"ף בי"ת', "אלף בית"),
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


def clean_wiki_markup(text: str) -> str:
    """Strip Hebrew Wikipedia tags, internal links, and footnotes."""
    if not text:
        return ""
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/>]*/\s*>", "", text)
    text = re.sub(r"\{\{הערה\|.*?\}\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def clean_wiki_song_title(title: str) -> str:
    """Remove Wikipedia/Pizmonet parenthetical disambiguations like '(שיר)'."""
    title = clean_wiki_markup(title)
    title = re.sub(r"\s*\((?:שיר|אלבום|מחזמר|סרט|תוכנית)[^)]*\)\s*$", "", title)
    return title.strip()


def _strip_punct_for_catalog(text: str) -> str:
    text = re.sub(r'(?<=[\u0590-\u05FF])["״׳\'\u2018\u2019\u201c\u201d]+(?=[\u0590-\u05FF])', "", text)
    text = re.sub(r"[\"'״׳`\u2018\u2019\u201c\u201d־\-–—,.!:?()\[\]/\\]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_catalog_song_title(title: str, synonym_map: dict[str, str] | None = None) -> str:
    """Normalize a Hebrew song title for cross-database deduplication with synonym resolution."""
    if not title:
        return ""
    t = html.unescape(title).strip()
    t = NIKUD_RE.sub("", t)
    t = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", t)
    t = re.sub(r"\s*\((?:שיר|אלבום|מחזמר|סרט|תוכנית)[^)]*\)\s*$", "", t)
    m_num = re.match(r"^(\d+)\s+([\u0590-\u05FF].*)$", t)
    if m_num:
        t = f"{m_num.group(2)} {m_num.group(1)}"
    t_clean = _strip_punct_for_catalog(t)
    smap = synonym_map or {}
    while t_clean in smap:
        nxt = _strip_punct_for_catalog(smap[t_clean])
        if nxt == t_clean:
            break
        t_clean = nxt
    return t_clean
