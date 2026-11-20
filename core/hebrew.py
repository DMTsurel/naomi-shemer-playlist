"""Shared Hebrew normalization, duration parsing, and track-matching utilities."""

from __future__ import annotations

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
