"""Generic composer-agnostic YouTube performance discovery and initial playlist builder."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import threading
import time
from typing import Any
import requests

from core.artists import CREATOR_NAME_MAP, ENGLISH_TO_HEB_ARTISTS, expand_performer_variants
from core.config import ComposerConfig, load_composer, load_overrides
from core.hebrew import FINDER_SPELLING_VARIANTS, NIKUD_RE, parse_duration_seconds

HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
}

GENERIC_REJECT_KEYWORDS: tuple[str, ...] = (
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
    "פרודיה",
    "בשפת הסימנים",
    "שפת הסימנים",
    "טריילר",
    "הקדמה לשיר",
    "rokdim",
    "שם הריקוד",
    "for string orchestra",
    "string orchestra",
    "הרצאה",
    "סיור מודרך",
    "פודקאסט",
    "acapella",
    "vocals only",
    "נערך באמצעות ai",
)

GENERIC_ALBUM_NAMES: set[str] = {
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

GENERIC_TRUSTED_CHANNELS: tuple[str, ...] = (
    "כאן | מוזיקה",
    "אוצר הזמר העברי",
    "שיר עד",
    "רון בכר",
    "דוד אסף",
)


@dataclass
class FinderContext:
    """Declarative runtime context for composer-agnostic YouTube matching."""

    cfg: ComposerConfig
    overrides: dict[str, Any]
    finder_ov: dict[str, Any] = field(default_factory=dict)
    creator_album_tier: str = "1_album_creator"
    creator_perf_tier: str = "3_creator_performance"
    tier_labels: dict[str, str] = field(default_factory=dict)
    english_to_heb_artists: list[tuple[str, str]] = field(default_factory=list)
    reject_keywords: list[str] = field(default_factory=list)
    generic_album_names: set[str] = field(default_factory=set)
    bad_video_ids: set[str] = field(default_factory=set)
    songs_requiring_explicit_creator: set[str] = field(default_factory=set)
    homonym_block_tokens: dict[str, list[str]] = field(default_factory=dict)
    split_composition_guards: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    performance_only_strict: bool = True
    verified_albums: list[str] = field(default_factory=list)
    solo_album_keywords: list[str] = field(default_factory=list)
    trusted_channels: tuple[str, ...] = GENERIC_TRUSTED_CHANNELS
    canonical_albums: list[dict[str, Any]] = field(default_factory=list)
    creator_solo_album_ids: set[str] = field(default_factory=set)
    creator_aliases: list[str] = field(default_factory=list)
    creator_surname_tokens: list[str] = field(default_factory=list)
    creator_tie_markers: list[str] = field(default_factory=list)
    active_year_range: tuple[int, int] = (1920, 2030)

    @classmethod
    def from_composer(cls, cfg: ComposerConfig, overrides: dict[str, Any]) -> FinderContext:
        finder_ov = dict(overrides.get("finder_overrides", {}))
        alb_tier = cfg.creator_album_tier
        perf_tier = cfg.creator_performance_tier
        tier_labels = {
            alb_tier: f"1. אלבום של {cfg.name_he}",
            "2_album_original": "2. אלבום של המבצע המקורי / אוסף רשמי",
            perf_tier: f"3. ביצוע של {cfg.name_he}",
            "4_original_performance": "4. ביצוע מקורי",
            "5_cover": "5. ביצוע מחודש / קאבר",
            "6_not_found": "6. לא נמצא סרטון תואם",
        }
        eng_map = [(k.lower(), v) for k, v in ENGLISH_TO_HEB_ARTISTS] + [
            (str(pair[0]).lower(), str(pair[1]))
            for pair in finder_ov.get("extra_english_to_heb_artists", [])
            if isinstance(pair, (list, tuple)) and len(pair) >= 2
        ]
        reject_kws = list(GENERIC_REJECT_KEYWORDS) + [str(x).lower() for x in finder_ov.get("extra_reject_keywords", [])]
        gen_albums = set(GENERIC_ALBUM_NAMES) | set(finder_ov.get("extra_generic_album_names", []))
        canonical_albums = list(cfg.discography.get("canonical_albums", []))
        solo_ids = {str(a["id"]) for a in canonical_albums if a.get("is_creator_solo") and a.get("id")}
        trusted_extra = tuple(str(ch).lower() for ch in cfg.discography.get("trusted_creator_channels", []))
        return cls(
            cfg=cfg,
            overrides=overrides,
            finder_ov=finder_ov,
            creator_album_tier=alb_tier,
            creator_perf_tier=perf_tier,
            tier_labels=tier_labels,
            english_to_heb_artists=eng_map,
            reject_keywords=reject_kws,
            generic_album_names=gen_albums,
            bad_video_ids=set((overrides.get("bad_video_ids") or {}).keys()),
            songs_requiring_explicit_creator=set(overrides.get("songs_requiring_explicit_creator", [])),
            homonym_block_tokens=dict(overrides.get("homonym_block_tokens", {})),
            split_composition_guards=dict(overrides.get("split_composition_guards", {})),
            performance_only_strict=bool(overrides.get("performance_only_strict_creator_match", True)),
            verified_albums=list(cfg.discography.get("verified_albums", [])),
            solo_album_keywords=list(cfg.discography.get("solo_album_keywords", [])),
            trusted_channels=GENERIC_TRUSTED_CHANNELS + trusted_extra,
            canonical_albums=canonical_albums,
            creator_solo_album_ids=solo_ids,
            creator_aliases=list(cfg.creator_aliases),
            creator_surname_tokens=list(cfg.creator_surname_tokens),
            creator_tie_markers=list(cfg.creator_tie_markers),
            active_year_range=cfg.active_year_range,
        )


def norm_heb_finder(text: str, ctx: FinderContext) -> str:
    """Normalize Hebrew/English text with finder spelling variants and artist transliterations."""
    if not text:
        return ""
    s = NIKUD_RE.sub("", text).lower()
    for eng_a, heb_a in ctx.english_to_heb_artists:
        s = s.replace(eng_a, heb_a)
    for full_w, def_w in FINDER_SPELLING_VARIANTS:
        s = s.replace(full_w, def_w)
    s = re.sub(r'(?<=[\u0590-\u05FF])["״׳\'\u2018\u2019\u201c\u201d]+(?=[\u0590-\u05FF])', "", s)
    s = re.sub(r"[\"״'׳`–—\-_,.:;!?()\[\]/\\|•·]", " ", s)
    s = re.sub(r"\bיי", "י", s)
    s = re.sub(r"\bוו", "ו", s)
    return re.sub(r"\s+", " ", s).strip()


def find_lockups(obj: Any) -> list[dict[str, Any]]:
    """Recursively extract YouTube `lockupViewModel` playlist entries."""
    res: list[dict[str, Any]] = []
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


def _iter_topic_playlist_specs(cfg: ComposerConfig) -> list[tuple[str, str, str, str]]:
    specs: list[tuple[str, str, str, str]] = []
    for item in cfg.discography.get("official_topic_playlists", []):
        if isinstance(item, dict):
            specs.append((
                str(item.get("playlist_id") or ""),
                str(item.get("album") or ""),
                str(item.get("performer") or cfg.name_he),
                str(item.get("tier") or cfg.creator_album_tier),
            ))
        elif isinstance(item, (list, tuple)) and len(item) >= 4:
            specs.append((str(item[0]), str(item[1]), str(item[2]), str(item[3])))
    return [s for s in specs if s[0]]


def fetch_official_topic_albums(ctx: FinderContext, *, cache_only: bool = False) -> dict[str, list[dict[str, Any]]]:
    """Fetch or load tracks from configured official YouTube/Topic album playlists."""
    cache_path = ctx.cfg.youtube_topic_albums_cache_json
    skip_ids = set(ctx.finder_ov.get("topic_skip_video_ids", [])) | ctx.bad_video_ids
    if cache_path.exists():
        raw_map = json.loads(cache_path.read_text(encoding="utf-8"))
        rekeyed: dict[str, list[dict[str, Any]]] = {}
        for k, tr_list in raw_map.items():
            for tr in tr_list:
                if tr.get("video_id") in skip_ids:
                    continue
                nk = norm_heb_finder(tr.get("clean_track_title", k), ctx)
                rekeyed.setdefault(nk, []).append(tr)
        return rekeyed

    playlist_specs = _iter_topic_playlist_specs(ctx.cfg)
    if cache_only or not playlist_specs:
        return {}

    strip_artists = [re.escape(str(a)) for a in ctx.finder_ov.get("topic_strip_artists", [ctx.cfg.name_he])]
    strip_prefixes = [re.escape(str(p)) for p in ctx.finder_ov.get("topic_strip_album_prefixes", [])]
    artist_alt = "|".join(strip_artists) if strip_artists else re.escape(ctx.cfg.name_he)
    prefix_alt = "|".join(strip_prefixes) if strip_prefixes else ""

    tracks_by_norm_title: dict[str, list[dict[str, Any]]] = {}
    for pid, alb_name, perf_name, tier in playlist_specs:
        try:
            lups: list[dict[str, Any]] = []
            for attempt in range(3):
                r = requests.get("https://www.youtube.com/playlist", params={"list": pid}, headers=HEADERS, timeout=15)
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
                if raw_t.startswith("הקדמה - ") or vid in skip_ids:
                    continue
                clean_t = re.sub(r"^\(\"?\.{0,3}\s*", "", raw_t).strip()
                clean_t = re.sub(r"^[a-z_]+\s+", "", clean_t).strip()
                if prefix_alt:
                    clean_t = re.sub(rf"^(?:(?:{artist_alt})\s*[-–:]\s*|(?:{prefix_alt})\s*-\d+-\s*)", "", clean_t).strip()
                else:
                    clean_t = re.sub(rf"^(?:{artist_alt})\s*[-–:]\s*", "", clean_t).strip()
                clean_t = re.sub(
                    rf"\s*(?:\(מתוך האלבום.*|\(קליפ,.*|[-–]?\s*הביצוע המקורי.*|\(הביצוע המקורי\)|[-–]\s*(?:{artist_alt}).*)$",
                    "",
                    clean_t,
                ).strip()
                clean_t = clean_t.strip("\"' .")
                nt = norm_heb_finder(clean_t, ctx)
                track_info = {
                    "video_id": vid,
                    "title": raw_t,
                    "clean_track_title": clean_t,
                    "channel": f"{ctx.cfg.name_he} - Topic" if tier == ctx.creator_album_tier else "Release - Topic",
                    "duration": "",
                    "description": f"Provided to YouTube · {perf_name} · מתוך האלבום: {alb_name}",
                    "album_name": alb_name,
                    "performer_name": perf_name,
                    "forced_tier": tier,
                    "playlist_id": pid,
                }
                tracks_by_norm_title.setdefault(nt, []).append(track_info)
                m_paren = re.match(r"^(.+?)\s*\((.+?)\)\s*$", clean_t)
                if m_paren:
                    for part in (m_paren.group(1), m_paren.group(2)):
                        np = norm_heb_finder(part, ctx)
                        if np:
                            tracks_by_norm_title.setdefault(np, []).append(track_info)
        except Exception as exc:
            print(f"  [!] שגיאה בשליפת פלייליסט אלבום {pid}: {exc}")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(tracks_by_norm_title, ensure_ascii=False, indent=2), encoding="utf-8")
    return tracks_by_norm_title


def youtube_search_raw(query: str) -> list[dict[str, Any]]:
    """Run a YouTube search query and return parsed top ~20 video metadata dicts."""
    for attempt in range(3):
        try:
            r = requests.get("https://www.youtube.com/results", params={"search_query": query}, headers=HEADERS, timeout=15)
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
            results: list[dict[str, Any]] = []
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


def fetch_video_details_by_id(video_id: str, creator_name_he: str = "") -> dict[str, Any] | None:
    """Fetch basic title, channel, and duration for an existing catalog YouTube ID."""
    try:
        r = requests.get("https://www.youtube.com/watch", params={"v": video_id}, headers=HEADERS, timeout=15)
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
        who = creator_name_he or "היוצר"
        return {
            "video_id": video_id,
            "title": title,
            "channel": channel,
            "duration": dur_str,
            "description": f'מזהה יוטיוב מתוך מאגרי {who} (אקו"ם / סטריאו ומונו / פזמונט)',
            "from_catalog_id": True,
        }
    except Exception:
        return None


def build_song_target_phrases(song: dict[str, Any], ctx: FinderContext) -> list[str]:
    """Build normalized target phrases (title, alt titles, opening line) for song matching."""
    phrases: list[str] = []
    for rc in [song["title"]] + song.get("alt_titles", []):
        if not rc:
            continue
        n_full = norm_heb_finder(rc, ctx)
        if n_full and n_full not in phrases:
            phrases.append(n_full)
        m_p = re.match(r"^(.+?)\s*\((.+?)\)\s*$", rc)
        if m_p:
            for p in (m_p.group(1), m_p.group(2)):
                np = norm_heb_finder(p, ctx)
                if np and len(np) >= 2 and np not in phrases:
                    phrases.append(np)
        if "/" in rc:
            for p in rc.split("/"):
                np = norm_heb_finder(p, ctx)
                if np and len(np) >= 2 and np not in phrases:
                    phrases.append(np)

    if song.get("opening_line"):
        nol = norm_heb_finder(song["opening_line"], ctx)
        if nol and len(nol.split()) >= 2:
            phrases.append(nol)
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
    target_phrases: list[str],
    all_other_multiword_titles: set[str],
    ctx: FinderContext,
) -> bool:
    """Return True if video title/Topic metadata matches target song without multi-word collisions."""
    ntitle = norm_heb_finder(vid_title, ctx)
    ndesc = norm_heb_finder(vid_desc, ctx)
    if not ntitle:
        return False

    ntitle_for_1word = ntitle
    for conf_perf in ctx.finder_ov.get("confusable_1word_performers", []):
        ntitle_for_1word = ntitle_for_1word.replace(str(conf_perf), " ")

    is_topic_channel = "- topic" in vid_channel.lower()
    clean_vid_title_no_parens = norm_heb_finder(re.sub(r"\s*\([^)]*\)", "", vid_title), ctx)

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
        if re.search(pattern, check_t) or ("provided to youtube" in ndesc and re.search(pattern, ndesc)):
            matched_phrase = tp
            break

    if not matched_phrase:
        return False

    target_set = set(target_phrases)
    match_exceptions = {
        (norm_heb_finder(pair[0], ctx), norm_heb_finder(pair[1], ctx))
        for pair in ctx.finder_ov.get("title_match_exceptions", [])
        if isinstance(pair, (list, tuple)) and len(pair) >= 2
    }
    if len(matched_phrase.split()) <= 2:
        for other_t in all_other_multiword_titles:
            if other_t in target_set or (matched_phrase in other_t.split() and other_t == matched_phrase):
                continue
            if (matched_phrase, other_t) in match_exceptions:
                continue
            if re.search(rf"(?:^|\s){re.escape(other_t)}(?:\s|$)", ntitle):
                return False
        if (
            f"הדרך {matched_phrase}" in ntitle
            or f"{matched_phrase} הקטנה" in ntitle
            or (matched_phrase in ("יריד", "היריד") and "יריד המזרח" in ntitle)
        ):
            return False
    return True


def is_creator_performer_in_video(
    vid_title: str,
    vid_channel: str,
    vid_desc: str,
    other_performers: list[str],
    song_performers: list[str],
    ctx: FinderContext,
) -> bool:
    """Return True when the composer themselves is the performing artist on the video."""
    if not ctx.cfg.is_performer:
        return False

    ch_lower = vid_channel.lower()
    name_he = ctx.cfg.name_he
    name_en = ctx.cfg.name_en
    esc_he = re.escape(name_he)
    esc_en = re.escape(name_en)
    esc_names = f"{esc_he}|{esc_en}" if name_en else esc_he
    surname_alt = "|".join(re.escape(t) for t in ctx.creator_surname_tokens if t) or esc_he

    if f"{name_he.lower()} - topic" in ch_lower or (name_en and f"{name_en.lower()} - topic" in ch_lower):
        return True
    if "provided to youtube" in vid_desc.lower():
        if re.search(rf"^[^·]*·\s*(?:{esc_names})\b", vid_desc, flags=re.I):
            return True
        return False

    combined_td = f"{vid_title} {vid_desc}"
    ensemble_blocks = ("קולולם", "חבורת הזמר", "בביצוע מקהלת") + tuple(ctx.finder_ov.get("non_creator_ensemble_markers", []))
    if any(x in combined_td for x in ensemble_blocks):
        return False
    for guard in ctx.finder_ov.get("non_creator_title_guards", []):
        triggers = [str(x).lower() for x in guard.get("title_contains_any", [])]
        unless = str(guard.get("unless_contains") or "").lower()
        vt_low = vid_title.lower()
        if any(tr in vt_low for tr in triggers) and (not unless or unless not in vt_low):
            return False

    m_by_creator_sung = re.search(rf"מאת\s+{esc_he}\s*,?\s*שר(?:ה|ים|ות)\s+([^\n|•·]+)", combined_td)
    if m_by_creator_sung and name_he not in m_by_creator_sung.group(1):
        return False

    m_perf_credit = re.search(
        r"(?:ביצוע|בצוע|שירה)\s*:\s*((?:(?!(?:מילים|מלים|לחן|עיבוד|תרגום|מתוך)\b)[^\n|•·])+)",
        vid_desc,
    )
    if m_perf_credit:
        credited = m_perf_credit.group(1).strip().lower()
        if not any(tok.lower() in credited for tok in ctx.creator_surname_tokens):
            return False

    duet_markers = tuple(ctx.finder_ov.get("creator_duet_markers", []))
    duet_pairs = ctx.finder_ov.get("creator_duet_pairs", [])
    if (
        re.search(
            rf"(?:ביצוע|בצוע|שירה|שרה|שרות|שרים)\s*:\s*(?:(?!(?:מילים|מלים|לחן|עיבוד|תרגום|מתוך|ביצוע|שירה)\b)[^\n|•·])*{esc_he}",
            combined_td,
        )
        or re.search(rf"(?:בביצוע|שרה|שר)\s+{esc_he}|(?:שרות|שרים)\s+{esc_he}(?:\s*,|\s+ו)", combined_td)
        or re.search(rf"(?<!מאת\s){esc_he}\s+(?:שרה\b(?!\s+[א-ת])|שר\b(?!\s+[א-ת])|בשירה)", combined_td)
        or any(dm in combined_td for dm in duet_markers)
        or any(all(str(part) in combined_td for part in pair) for pair in duet_pairs if len(pair) >= 2)
    ):
        return True

    if re.search(
        rf"(?:מילים|מלים|לחן|תרגום|עברית|נוסח עברי|מאת|שירי|משירי|מחווה ל|ערב|by)\s*[:\-–]?\s*(?:{esc_names})",
        vid_title,
        flags=re.I,
    ):
        return False
    if re.search(rf"שר[הים]?\s+(?:את\s+)?[^\s]+.*{esc_he}", vid_title):
        return False

    if re.match(rf"^\s*{esc_he}\s+ו.+?\s+[-–]\s+", vid_title):
        return True

    ntitle = norm_heb_finder(vid_title, ctx)
    creator_norm_aliases = {norm_heb_finder(a, ctx) for a in ([name_he, name_en] + ctx.creator_aliases) if a}
    for op in other_performers:
        for v_op in expand_performer_variants(op):
            nop = norm_heb_finder(v_op, ctx)
            if nop and nop not in creator_norm_aliases and len(nop) >= 3:
                if re.search(rf"(?:^|\s){re.escape(nop)}(?:\s|$)", ntitle):
                    return False

    rev_name = ctx.cfg.creator_acum_reversed_name
    creator_check_tokens = [tok for tok in (name_he, rev_name, name_en, *ctx.creator_aliases) if tok]
    creator_in_catalog_perfs = any(any(tok in p for tok in creator_check_tokens) for p in song_performers)
    if not creator_in_catalog_perfs:
        return False

    if re.match(rf"^\s*(?:{esc_names})\s*[-–]", vid_title, flags=re.I):
        return True

    if re.search(rf"(?:כתבה והלחינה|כתב והלחין|מילים ולחן)\s*:\s*{esc_he}", vid_desc) and f"{name_he} שר" not in vid_desc:
        return False

    hyphen_parts = [p.strip() for p in re.split(r"\s+[-–|]\s+", vid_title) if p.strip()]
    if len(hyphen_parts) >= 3 and "רון בכר" not in vid_title:
        return False

    if re.search(rf"[-–|]\s*(?:{esc_names})\s*(?:[-–|(]|$)", vid_title, flags=re.I):
        if any(tc in ch_lower for tc in ctx.trusted_channels):
            return True

    _unused = surname_alt
    return False


def match_known_performer(
    vid_title: str,
    vid_channel: str,
    vid_desc: str,
    performers: list[str],
    ctx: FinderContext,
) -> tuple[str | None, int]:
    """Find the earliest matching catalog performer (excluding the composer) on the video."""
    title_without_composer_credits = re.sub(
        r"(?:מילים|מלים|לחן|עיבוד|תרגום|מאת)\s*:\s*[^,;|()\n]+",
        " ",
        vid_title,
    )
    combined_title_ch = norm_heb_finder(f"{title_without_composer_credits} {vid_channel}", ctx)
    ndesc = norm_heb_finder(vid_desc, ctx)
    creator_exact = {ctx.cfg.name_he, ctx.cfg.name_en, ctx.cfg.creator_acum_reversed_name}
    for idx, perf in enumerate(performers):
        if perf.strip() in creator_exact:
            continue
        variants = expand_performer_variants(perf)
        display_perf = variants[-1] if len(variants) >= 2 and len(variants[0].split()) == 2 else (variants[0] if variants else perf)
        for v_perf in variants:
            nperf = norm_heb_finder(v_perf, ctx)
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


def match_known_album(
    vid_title: str,
    vid_desc: str,
    song_albums: list[str],
    song_title: str,
    ctx: FinderContext,
) -> str | None:
    """Match a verified composer album or catalog album in video title/description."""
    nsong = norm_heb_finder(song_title, ctx)
    ndesc = norm_heb_finder(vid_desc, ctx)
    ntitle = norm_heb_finder(vid_title, ctx)
    norm_generic = {norm_heb_finder(g, ctx) for g in ctx.generic_album_names}

    for valb in ctx.verified_albums:
        nvalb = norm_heb_finder(valb, ctx)
        if nvalb and nvalb != nsong:
            if re.search(rf"(?:^|\s){re.escape(nvalb)}(?:\s|$)", f"{ntitle} {ndesc}"):
                return valb

    for alb in song_albums:
        base_alb = re.sub(r"\s*\([^)]*\)", "", alb).strip()
        nalb = norm_heb_finder(base_alb, ctx)
        if not nalb or len(nalb) < 4 or nalb == nsong or nalb in norm_generic:
            continue
        if re.search(rf"(?:^|\s){re.escape(nalb)}(?:\s|$)", ndesc):
            return base_alb
    return None


def has_conflicting_composer_credit(
    vid_title: str,
    vid_desc: str,
    song: dict[str, Any],
    ctx: FinderContext,
) -> bool:
    """Return True when video explicitly credits an unrelated composer."""
    combined = f"{vid_title}\n{vid_desc}"
    surname_alt = "|".join(re.escape(t) for t in ctx.creator_surname_tokens if t) or re.escape(ctx.cfg.name_he)
    if re.search(rf"(?:מילים|מלים|תרגום|נוסח עברי|עברית)\s*:\s*[^\n|•·,;]*(?:{surname_alt})", combined, flags=re.I):
        return False
    if f"למילותיה של {ctx.cfg.name_he}" in combined or f"למילותיו של {ctx.cfg.name_he}" in combined:
        return False
    matches = re.findall(r"(?:מילים ולחן|מלים ולחן|לחן|composer)\s*:\s*([^\n|•·,;]+)", combined, flags=re.I)
    if not matches:
        return False
    allowed_comp_norm = norm_heb_finder(
        " ".join(song.get("composers", []) + song.get("authors", []) + [ctx.cfg.name_he, ctx.cfg.name_en, "עממי", "נחלת הכלל"]),
        ctx,
    )
    for m in matches:
        cm = norm_heb_finder(m, ctx)
        if not cm:
            continue
        if any(tok.lower() in cm for tok in ctx.creator_surname_tokens) or "עממי" in cm:
            continue
        words = [w for w in cm.split() if len(w) >= 3]
        if words and not any(w in allowed_comp_norm for w in words):
            return True
    return False


def _hits_homonym_block(song_title: str, vid_title: str, vid_channel: str, vid_desc: str, ctx: FinderContext) -> bool:
    clean_base = re.sub(r"\(\s*לחן\s+[אב]['׳]?\s*\)", "", song_title).strip()
    blocked = ctx.homonym_block_tokens.get(song_title) or ctx.homonym_block_tokens.get(clean_base)
    if not blocked:
        return False
    norm_song = norm_heb_finder(song_title, ctx)
    blob_low = f"{vid_title} {vid_channel} {vid_desc}".lower()
    blob_norm = norm_heb_finder(f"{vid_title} {vid_channel} {vid_desc}", ctx)
    ch_low = vid_channel.lower()
    ch_norm = norm_heb_finder(vid_channel, ctx)
    for tok in blocked:
        t_low = str(tok).lower()
        t_norm = norm_heb_finder(str(tok), ctx)
        if t_norm and t_norm == norm_song:
            # Self-title token (e.g. a band named identically to the song): inspect channel name only
            if t_low in ch_low or t_norm in ch_norm:
                return True
        elif t_low in blob_low or (t_norm and t_norm in blob_norm):
            return True
    return False


def _fails_split_guard(song_title: str, vid_title: str, vid_channel: str, vid_desc: str, ctx: FinderContext) -> bool:
    blob = f"{vid_channel} {vid_title} {vid_desc}".lower()
    for key, rules in ctx.split_composition_guards.items():
        if key not in song_title:
            continue
        for rule in rules:
            marker = rule.get("title_contains", "")
            if marker and marker not in song_title:
                continue
            reject_any = [str(x).lower() for x in rule.get("reject_any", [])]
            require_any = [str(x).lower() for x in rule.get("require_any", [])]
            if reject_any and any(x in blob for x in reject_any):
                return True
            if require_any and not any(x in blob for x in require_any):
                return True
    return False


def _matches_rule_spec(spec: dict[str, Any], song_title: str, text_raw: str) -> bool:
    target_title = spec.get("title")
    if target_title and song_title != target_title:
        return False
    if "unless_title_in" in spec and song_title in spec["unless_title_in"]:
        return False
    if "contains_any" in spec and any(tok in text_raw for tok in spec["contains_any"]):
        return True
    if "contains_any_lower" in spec:
        low = text_raw.lower()
        if any(str(tok).lower() in low for tok in spec["contains_any_lower"]):
            return True
    return False


def classify_and_score_candidate(
    cand: dict[str, Any],
    song: dict[str, Any],
    target_phrases: list[str],
    all_other_multiword_titles: set[str],
    rank_idx: int,
    ctx: FinderContext,
) -> dict[str, Any] | None:
    """Classify a candidate video into a tier and compute its quality score."""
    vid = cand.get("video_id", "")
    if not vid or vid in ctx.bad_video_ids:
        return None

    vid_title = cand.get("title", "")
    vid_channel = cand.get("channel", "")
    vid_desc = cand.get("description", "")
    dur_str = cand.get("duration", "")

    if cand.get("forced_tier"):
        tier = cand["forced_tier"]
        base_score = 5000 if tier == ctx.creator_album_tier else 4000
        matched_perf = cand.get("performer_name", ctx.cfg.name_he)
        if tier == "2_album_original":
            alb_name = cand.get("album_name", "")
            for ov_rule in ctx.finder_ov.get("topic_tier_overrides", []):
                if ov_rule.get("album_name") != alb_name:
                    continue
                if "title" in ov_rule and song["title"] == ov_rule["title"]:
                    tier = ov_rule["tier"]
                    if tier == "1_album_naomi" and ctx.creator_album_tier != "1_album_naomi":
                        tier = ctx.creator_album_tier
                    base_score = int(ov_rule.get("score", base_score))
                    if ov_rule.get("performer"):
                        matched_perf = str(ov_rule["performer"])
                    break
                if "exclude_titles" in ov_rule and song["title"] not in ov_rule["exclude_titles"]:
                    tier = ov_rule["tier"]
                    base_score = int(ov_rule.get("score", 950))
                    break
        return {
            "video_id": vid,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "video_title": vid_title,
            "channel": vid_channel,
            "duration": dur_str,
            "description": vid_desc,
            "tier": tier,
            "tier_label": ctx.tier_labels.get(tier, tier),
            "matched_performer": matched_perf,
            "matched_album": cand.get("album_name", ""),
            "score": base_score,
        }

    # 1. Hard reject karaoke / playback / tutorials / blocked keywords
    combined_all_lower = f"{vid_title} {vid_channel} {vid_desc}".lower()
    song_title_lower = song["title"].lower()
    for rk in ctx.reject_keywords:
        if rk in combined_all_lower and rk not in song_title_lower:
            return None
    if re.search(r"(?:[-–|]\s*ריקוד\b|\bdance\b)", vid_title.lower()) and "ריקוד" not in song_title_lower:
        return None

    # 2. Hard reject explicit conflicting composer credit, homonym tokens, and split guards
    if has_conflicting_composer_credit(vid_title, vid_desc, song, ctx):
        return None
    if _hits_homonym_block(song["title"], vid_title, vid_channel, vid_desc, ctx):
        return None
    if _fails_split_guard(song["title"], vid_title, vid_channel, vid_desc, ctx):
        return None

    # 3. Title matching check
    if not cand.get("from_catalog_id"):
        if not title_matches_song(vid_title, vid_channel, vid_desc, target_phrases, all_other_multiword_titles, ctx):
            return None

    # 4. Duration validation (parse_duration_seconds returns -1 when missing)
    is_topic_or_provided = (
        "- topic" in vid_channel.lower()
        or "provided to youtube" in vid_desc.lower()
        or "auto-generated by youtube" in vid_desc.lower()
    )
    dur_sec = parse_duration_seconds(dur_str)
    if dur_sec >= 0:
        if dur_sec < 40 or dur_sec > 450:
            return None

    penalty = 0
    if dur_sec >= 0:
        if dur_sec < 70:
            penalty -= 350
        elif dur_sec > 330 and "מחרוזת" not in song["title"]:
            penalty -= 250
    if "מחרוזת" in vid_title and "מחרוזת" not in song["title"]:
        penalty -= 700
    if "גרסה מחודשת" in f"{vid_title} {vid_desc}":
        penalty -= 600
    if "מופע" in vid_title and "מופע" not in song["title"]:
        penalty -= 50

    performers = song.get("performers", [])
    albums = song.get("albums", [])
    creator_sings = is_creator_performer_in_video(vid_title, vid_channel, vid_desc, performers, performers, ctx)
    matched_perf, perf_idx = match_known_performer(vid_title, vid_channel, vid_desc, performers, ctx)
    matched_alb = match_known_album(vid_title, vid_desc, albums, song["title"], ctx)

    combined_all_norm = norm_heb_finder(f"{vid_title} {vid_channel} {vid_desc}", ctx)
    mentions_creator = any(
        norm_heb_finder(alias, ctx) in combined_all_norm
        for alias in (ctx.creator_aliases + ctx.creator_tie_markers)
        if alias
    )

    if ctx.performance_only_strict and set(song.get("roles", [])) == {"performer"} and not creator_sings:
        return None
    if song["title"] in ctx.songs_requiring_explicit_creator and not mentions_creator:
        return None

    matches_opening = False
    if song.get("opening_line") and len(song["opening_line"].split()) >= 3:
        nol_short = " ".join(norm_heb_finder(song["opening_line"], ctx).split()[:3])
        if nol_short and nol_short in combined_all_norm:
            matches_opening = True

    verified_albums_norm = {norm_heb_finder(va, ctx) for va in ctx.verified_albums}
    has_verified_album = bool(matched_alb and norm_heb_finder(matched_alb, ctx) in verified_albums_norm)

    if not cand.get("from_catalog_id"):
        if not (mentions_creator or matched_perf or has_verified_album or matches_opening):
            return None

    is_archival_original = bool(
        re.search(
            r"(?:הביצוע המקורי|ביצוע מקורי(?!\s*:)|הביצוע הראשון(?!\s*:)|הקלטה מקורית|קול ישראל|בית לזמר העברי|זמריר|אוצרות ארכיון ישראלי - רון בכר)",
            f"{vid_title} {vid_desc}",
        )
    )

    combined_tcd = f"{vid_title} {vid_channel} {vid_desc}"
    late_cover_markers = tuple(ctx.finder_ov.get("late_cover_album_markers", []))
    is_late_cover_album = any(cov_kw in combined_tcd for cov_kw in late_cover_markers) or any(
        _matches_rule_spec(rule, song["title"], combined_tcd)
        for rule in ctx.finder_ov.get("song_late_cover_exclusions", [])
    )

    is_official_album_channel = is_topic_or_provided or (
        bool(matched_alb)
        and any(
            ch_kw in vid_channel.lower()
            for ch_kw in ("הערוץ הרשמי", "official", "פונוקול", "ישראפון", "האלבומים הגדולים", "shir ivri")
        )
    )

    td_blob = f"{vid_title} {vid_desc}"
    official_ensemble_boost = False
    for eb in ctx.finder_ov.get("official_ensemble_boost_markers", []):
        inc = str(eb.get("include") or "")
        exc = str(eb.get("exclude") or "")
        if inc and inc in td_blob and (not exc or exc not in td_blob):
            official_ensemble_boost = True
            break

    if creator_sings and (is_topic_or_provided or any(k in td_blob for k in ctx.solo_album_keywords)):
        tier = ctx.creator_album_tier
        base_score = 4800
        matched_perf = ctx.cfg.name_he
        if not matched_alb:
            for k in ctx.solo_album_keywords:
                if k in td_blob:
                    matched_alb = k
                    break
    elif is_official_album_channel and not is_late_cover_album and (perf_idx <= 3 or official_ensemble_boost):
        tier = "2_album_original"
        base_score = 3900 if is_topic_or_provided else 3780
    elif creator_sings:
        tier = ctx.creator_perf_tier
        base_score = 2800
        matched_perf = ctx.cfg.name_he
    elif not is_late_cover_album and (matched_perf or (is_archival_original and mentions_creator) or cand.get("from_catalog_id")):
        tier = "4_original_performance"
        base_score = 1800
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
        tier = "5_cover"
        base_score = 950
    else:
        tier = "5_cover"
        base_score = 800

    rank_bonus = max(0, 40 - rank_idx * 3)
    cat_bonus = 50 if cand.get("from_catalog_id") else 0
    total_score = base_score + rank_bonus + cat_bonus + penalty
    if total_score < 300:
        return None

    return {
        "video_id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "video_title": vid_title,
        "channel": vid_channel,
        "duration": dur_str,
        "description": vid_desc[:200],
        "tier": tier,
        "tier_label": ctx.tier_labels.get(tier, tier),
        "matched_performer": matched_perf or "",
        "matched_album": matched_alb or "",
        "score": total_score,
    }


def find_candidates_for_song(
    song: dict[str, Any],
    topic_tracks_map: dict[str, list[dict[str, Any]]],
    search_cache: dict[str, list[dict[str, Any]]],
    all_other_multiword_titles: set[str],
    ctx: FinderContext,
    *,
    cache_only: bool = False,
    cache_lock: threading.Lock | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """Find, classify, and score up to 12 YouTube candidates for a single catalog song."""
    target_phrases = build_song_target_phrases(song, ctx)
    raw_candidates: list[dict[str, Any]] = []
    did_network = False

    def _cache_get(key: str) -> list[dict[str, Any]] | None:
        if cache_lock is not None:
            with cache_lock:
                return search_cache.get(key)
        return search_cache.get(key)

    def _cache_set(key: str, val: list[dict[str, Any]]) -> None:
        if cache_lock is not None:
            with cache_lock:
                search_cache[key] = val
        else:
            search_cache[key] = val

    for tp in target_phrases:
        if tp in topic_tracks_map:
            raw_candidates.extend(topic_tracks_map[tp])

    for yid in song.get("youtube_ids", []):
        cache_key = f"VID_ID::{yid}"
        cached_item = _cache_get(cache_key)
        if cached_item is not None:
            raw_candidates.extend(cached_item)
        elif not cache_only:
            det = fetch_video_details_by_id(yid, creator_name_he=ctx.cfg.name_he)
            did_network = True
            val = [det] if det else []
            _cache_set(cache_key, val)
            if det:
                raw_candidates.append(det)

    q_primary = f"{ctx.cfg.name_he} {song['title']}"
    cached_prim = _cache_get(q_primary)
    if cached_prim is not None:
        raw_candidates.extend(cached_prim)
    elif not cache_only:
        res = youtube_search_raw(q_primary)
        did_network = True
        _cache_set(q_primary, res)
        raw_candidates.extend(res)

    scored_map: dict[str, dict[str, Any]] = {}
    for idx, cand in enumerate(raw_candidates):
        vid = cand.get("video_id", "")
        if not vid:
            continue
        scored = classify_and_score_candidate(cand, song, target_phrases, all_other_multiword_titles, idx, ctx)
        if scored and (vid not in scored_map or scored["score"] > scored_map[vid]["score"]):
            scored_map[vid] = scored

    best_tier_so_far = min((c["tier"] for c in scored_map.values()), default="6_not_found")
    has_orig_tier = any(c["tier"] in ("2_album_original", "4_original_performance") for c in scored_map.values())
    creator_names_skip = {ctx.cfg.name_he, ctx.cfg.creator_acum_reversed_name, ctx.cfg.name_en}

    secondary_queries: list[str] = []
    if (best_tier_so_far > "2_album_original" or not has_orig_tier) and song.get("performers"):
        for raw_p in song["performers"][:2]:
            if any(cn and cn in raw_p for cn in creator_names_skip):
                continue
            q_raw = f"{song['title']} {raw_p}"
            if q_raw not in secondary_queries:
                secondary_queries.append(q_raw)
            p_vars = expand_performer_variants(raw_p)
            pref_p = p_vars[-1] if p_vars else raw_p
            if pref_p and not any(cn and cn in pref_p for cn in creator_names_skip):
                q_p = f"{song['title']} {pref_p}"
                if q_p not in secondary_queries:
                    secondary_queries.append(q_p)
            break
    if not scored_map:
        for alt in song.get("alt_titles", [])[:1]:
            if alt != song["title"]:
                secondary_queries.append(f"{ctx.cfg.name_he} {alt}")
        if song.get("opening_line"):
            ol_words = song["opening_line"].split()[:5]
            if len(ol_words) >= 2:
                secondary_queries.append(f"{ctx.cfg.name_he} {' '.join(ol_words)}")

    for sq in secondary_queries[:3]:
        sec_res = _cache_get(sq)
        if sec_res is None:
            if not cache_only and (best_tier_so_far > "2_album_original" or not has_orig_tier):
                sec_res = youtube_search_raw(sq)
                did_network = True
                _cache_set(sq, sec_res)
            else:
                continue
        for idx, cand in enumerate(sec_res):
            vid = cand.get("video_id", "")
            if not vid:
                continue
            scored = classify_and_score_candidate(cand, song, target_phrases, all_other_multiword_titles, idx, ctx)
            if scored and (vid not in scored_map or scored["score"] > scored_map[vid]["score"]):
                scored_map[vid] = scored

    sorted_candidates = sorted(scored_map.values(), key=lambda x: (-x["score"], x["tier"]))
    return sorted_candidates[:12], did_network


def _resolve_single_year(song: dict[str, Any], chosen: dict[str, Any] | None, ctx: FinderContext, pizmonet_years: dict[str, str]) -> int:
    manual_years: dict[str, int] = ctx.finder_ov.get("manual_years", {})
    t = song["title"]
    if t in manual_years:
        return int(manual_years[t])
    min_yr, max_yr = ctx.active_year_range
    notes_any_max = max_yr - 1 if max_yr == 2004 else max_yr
    fallback_min_yr = 1950 if min_yr == 1948 else min_yr
    comp_ignore = tuple(ctx.finder_ov.get("compilation_year_ignore_keywords", []))

    py = str(pizmonet_years.get(t, ""))
    if py and py.isdigit() and min_yr <= int(py) <= max_yr:
        return int(py)

    notes = " ".join(song.get("notes", []))
    m_notes = [int(x) for x in re.findall(r"(?:בשנת|משנת|שנת|ב-|\()\s*(19\d{2}|20\d{2})\b", notes) if min_yr <= int(x) <= max_yr]
    if m_notes:
        return min(m_notes)
    m_notes_any = [int(x) for x in re.findall(r"\b(19\d{2}|20\d{2})\b", notes) if fallback_min_yr <= int(x) <= notes_any_max]
    if m_notes_any:
        return min(m_notes_any)

    if chosen:
        m_vt = [int(x) for x in re.findall(r"\b(19\d{2}|20\d{2})\b", chosen.get("video_title", "")) if fallback_min_yr <= int(x) <= max_yr]
        if m_vt:
            return min(m_vt)
        vd = chosen.get("description", "")
        if not (comp_ignore and any(comp in vd for comp in comp_ignore)):
            m_vd = [int(x) for x in re.findall(r"℗\s*(19\d{2}|20\d{2})\b", vd) if fallback_min_yr <= int(x) <= max_yr]
            if m_vd:
                return min(m_vd)

    albs_str = " ".join(a for a in song.get("albums", []) if not (comp_ignore and any(c in a for c in comp_ignore)))
    m_alb = [int(x) for x in re.findall(r"\b(19\d{2}|20\d{2})\b", albs_str) if fallback_min_yr <= int(x) <= max_yr]
    if m_alb:
        return min(m_alb)

    cy = str(song.get("year", ""))
    if cy and cy.isdigit() and min_yr <= int(cy) <= max_yr:
        return int(cy)
    return 2099


def _resolve_chrono_info(
    song: dict[str, Any],
    chosen: dict[str, Any] | None,
    ctx: FinderContext,
    pizmonet_years: dict[str, str],
    *,
    exclude_creator_solo: bool = False,
    only_creator_solo: bool = False,
) -> tuple[int, int, str, int]:
    t = song["title"]
    vblob = ""
    if chosen:
        vblob = f"{chosen.get('matched_album', '')} {chosen.get('video_title', '')} {chosen.get('description', '')} {chosen.get('channel', '')}"

    for alb_idx, alb in enumerate(ctx.canonical_albums, 1):
        aid = str(alb["id"])
        ayr = int(alb["year"])
        atitle = str(alb["title"])
        kws = list(alb.get("keywords", []))
        trks = list(alb.get("tracks", []))
        if exclude_creator_solo and aid in ctx.creator_solo_album_ids:
            continue
        if only_creator_solo and aid not in ctx.creator_solo_album_ids:
            continue
        if t in trks and any(k in vblob for k in kws):
            return ayr, alb_idx, atitle, trks.index(t) + 1

    for alb_idx, alb in enumerate(ctx.canonical_albums, 1):
        aid = str(alb["id"])
        ayr = int(alb["year"])
        atitle = str(alb["title"])
        trks = list(alb.get("tracks", []))
        if exclude_creator_solo and aid in ctx.creator_solo_album_ids:
            continue
        if only_creator_solo and aid not in ctx.creator_solo_album_ids:
            continue
        if t in trks:
            return ayr, alb_idx, atitle, trks.index(t) + 1

    return _resolve_single_year(song, chosen, ctx, pizmonet_years), 999, "סינגל / ביצוע בודד", 999


def _clean_co_creators(names: list[str], ctx: FinderContext) -> list[str]:
    filtered: list[str] = []
    name_tokens_low = [t.lower() for t in ([ctx.cfg.name_he, ctx.cfg.name_en] + ctx.creator_surname_tokens) if t]
    for n in names:
        ns = n.strip()
        if not ns:
            continue
        ns_low = ns.lower()
        if any(tok in ns_low for tok in name_tokens_low):
            continue
        mapped = CREATOR_NAME_MAP.get(ns, CREATOR_NAME_MAP.get(ns.upper(), ns))
        filtered.append(mapped)
    heb_names = [n for n in filtered if any("\u0590" <= c <= "\u05FF" for c in n)]
    chosen_list = heb_names if heb_names else filtered
    dedup: list[str] = []
    for n in chosen_list:
        if n not in dedup:
            dedup.append(n)
    return dedup[:2]


def _build_creator_credits(song: dict[str, Any], ctx: FinderContext) -> tuple[str, str, str]:
    roles = set(song.get("roles", []))
    co_authors = _clean_co_creators(song.get("authors", []), ctx)
    co_composers = _clean_co_creators(song.get("composers", []), ctx)
    who = ctx.cfg.name_he
    if "translator" in roles:
        role_cat = "translation"
        if "composer" in roles and not co_composers:
            co_str = f"מקור: {', '.join(co_authors)}" if co_authors else ""
            role_label = f"תרגום ולחן: {who} ({co_str})" if co_str else f"תרגום ולחן: {who}"
        else:
            orig_creators = co_composers or co_authors
            co_str = f"מקור: {', '.join(orig_creators)}" if orig_creators else ""
            role_label = f"תרגום: {who} ({co_str})" if co_str else f"תרגום / נוסח עברי: {who}"
    elif "author" in roles and "composer" in roles:
        role_cat = "words_and_music"
        extra = []
        if co_authors:
            extra.append(f"עם {', '.join(co_authors)}")
        elif co_composers:
            extra.append(f"לחן נוסף: {', '.join(co_composers)}")
        co_str = ", ".join(extra)
        role_label = f"מילים ולחן: {who} ({co_str})" if co_str else f"מילים ולחן: {who}"
    elif "composer" in roles:
        role_cat = "music_only"
        co_str = f"מילים: {', '.join(co_authors)}" if co_authors else ""
        role_label = f"לחן: {who} · {co_str}" if co_str else f"לחן: {who}"
    elif "author" in roles:
        role_cat = "words_only"
        co_str = f"לחן: {', '.join(co_composers)}" if co_composers else ""
        role_label = f"מילים: {who} · {co_str}" if co_str else f"מילים: {who}"
    elif "arranger" in roles:
        role_cat = "music_only"
        co_parts = []
        if co_authors:
            co_parts.append(f"מילים: {', '.join(co_authors)}")
        if co_composers:
            co_parts.append(f"לחן: {', '.join(co_composers)}")
        co_str = " · ".join(co_parts)
        role_label = f"עיבוד: {who} · {co_str}" if co_str else f"עיבוד מוזיקלי: {who}"
    else:
        role_cat = "performance_only"
        co_parts = []
        if co_authors:
            co_parts.append(f"מילים: {', '.join(co_authors)}")
        if co_composers:
            co_parts.append(f"לחן: {', '.join(co_composers)}")
        co_str = " · ".join(co_parts)
        role_label = f"ביצוע: {who} ({co_str})" if co_str else f"ביצוע / עיבוד: {who}"
    return role_cat, role_label, co_str


def _build_archive_links(song: dict[str, Any], ctx: FinderContext) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    open_nli_mms = ctx.finder_ov.get("open_nli_audio_mms", {})
    direct_zem = ctx.finder_ov.get("direct_zemereshet_songs", {})

    audio_mms = open_nli_mms.get(song["title"])
    if audio_mms:
        links.append({
            "source": "nli_audio",
            "label": "🎧 האזנה להקלטה בספרייה הלאומית",
            "url": f"https://www.nli.org.il/he/items/NNL_MUSIC_AL{audio_mms}/NLI",
        })
    nli_ids = song.get("nli_mms_ids", [])
    if nli_ids:
        links.append({
            "source": "nli",
            "label": "הספרייה הלאומית (בית לזמר העברי)",
            "url": f"https://www.nli.org.il/he/items/NNL_MUSIC_AL{nli_ids[0]}/NLI",
        })
    elif "nli" in song.get("sources", []):
        import urllib.parse

        q_nli = urllib.parse.quote(f"{ctx.cfg.name_he} {song['title']}")
        links.append({
            "source": "nli",
            "label": "חיפוש בספרייה הלאומית",
            "url": f"https://www.nli.org.il/he/search?projectName=NLI&text={q_nli}",
        })
    shironet_urls = song.get("shironet_urls", [])
    if shironet_urls:
        links.append({"source": "shironet", "label": "מילים בשירונט", "url": shironet_urls[0]})
    if "zemereshet" in song.get("sources", []) or song["title"] in direct_zem:
        zem_info = direct_zem.get(song["title"])
        if zem_info:
            zid, has_zem_audio = zem_info[0], bool(zem_info[1])
            links.append({
                "source": "zemereshet_audio" if has_zem_audio else "zemereshet",
                "label": "🎧 האזנה להקלטה בזמרשת" if has_zem_audio else "מידע ומילים בזמרשת",
                "url": f"https://www.zemereshet.co.il/m/song.asp?id={zid}",
            })
        else:
            import urllib.parse

            q_zem = urllib.parse.quote(song["title"])
            links.append({
                "source": "zemereshet",
                "label": "הקלטה ומידע בזמרשת",
                "url": f"https://www.zemereshet.co.il/m/songs.asp?search={q_zem}",
            })
    acum_ids = song.get("acum_work_ids", [])
    if acum_ids:
        links.append({
            "source": "acum",
            "label": f'אקו"ם #{acum_ids[0]}',
            "url": f"https://nocs.acum.org.il/acumsitesearchdb/issearch?workid={acum_ids[0]}",
        })
    return links


def find_composer_videos(
    slug: str,
    *,
    cache_only: bool = False,
    catalog_path: Path | None = None,
    output_dir: Path | None = None,
    dry_run: bool = False,
    rebuild: bool = True,
    standalone: bool = False,
    composer_dir: Path | None = None,
) -> dict[str, Any]:
    """Match catalog songs against YouTube, classify tiers, order chronologically, and write outputs."""
    cfg = load_composer(slug, composer_dir=composer_dir)
    overrides = load_overrides(slug, composer_dir=composer_dir)
    ctx = FinderContext.from_composer(cfg, overrides)

    cat_path = catalog_path if catalog_path is not None else cfg.catalog_json
    print("טוען את הקטלוג המאוחד...")
    catalog = json.loads(cat_path.read_text(encoding="utf-8"))
    songs: list[dict[str, Any]] = catalog.get("songs", [])
    print(f"נטענו {len(songs)} שירים מתוך הקטלוג.")

    print(f"שולף רצועות מתוך פלייליסטי האלבומים הרשמיים של {cfg.name_he} ביוטיוב (Topic)...")
    topic_tracks_map = fetch_official_topic_albums(ctx, cache_only=cache_only)
    print(f"נטענו {len(topic_tracks_map)} מפתחות שירים מתוך אלבומי Topic רשמיים.")

    search_cache: dict[str, list[dict[str, Any]]] = {}
    search_cache_path = cfg.youtube_search_cache_json
    if search_cache_path.exists():
        try:
            search_cache = json.loads(search_cache_path.read_text(encoding="utf-8"))
            print(f"נטענו {len(search_cache)} שאילתות חיפוש קיימות מהמטמון.")
        except Exception:
            search_cache = {}

    vid_to_dur: dict[str, str] = {}
    for cached_items in search_cache.values():
        for cit in cached_items:
            cvid = cit.get("video_id", "")
            cdur = cit.get("duration", "")
            if cvid and cdur:
                vid_to_dur[cvid] = cdur
    for tlist in topic_tracks_map.values():
        for tr in tlist:
            if not tr.get("duration") and tr.get("video_id") in vid_to_dur:
                tr["duration"] = vid_to_dur[tr["video_id"]]

    all_multiword_titles: set[str] = set()
    for s in songs:
        nt = norm_heb_finder(s["title"], ctx)
        if len(nt.split()) >= 2:
            all_multiword_titles.add(nt)

    song_candidates: dict[str, list[dict[str, Any]]] = {}
    cache_lock = threading.Lock()
    print(f"מחפש ומדרג ביצועי יוטיוב לכל {len(songs)} השירים (במקביל)...")

    def worker(idx_song: tuple[int, dict[str, Any]]) -> tuple[int, str, list[dict[str, Any]], bool]:
        idx, s = idx_song
        cands, net = find_candidates_for_song(
            s,
            topic_tracks_map,
            search_cache,
            all_multiword_titles,
            ctx,
            cache_only=cache_only,
            cache_lock=cache_lock,
        )
        return idx, s["normalized_key"], cands, net

    batch_size = 30
    for start in range(0, len(songs), batch_size):
        batch = [(i, songs[i]) for i in range(start, min(start + batch_size, len(songs)))]
        batch_did_net = False
        with ThreadPoolExecutor(max_workers=5) as ex:
            for _idx, norm_key, cands, net in ex.map(worker, batch):
                song_candidates[norm_key] = cands
                if net:
                    batch_did_net = True
        if batch_did_net and not cache_only:
            search_cache_path.parent.mkdir(parents=True, exist_ok=True)
            search_cache_path.write_text(json.dumps(search_cache, ensure_ascii=False), encoding="utf-8")
        done_count = min(start + batch_size, len(songs))
        found_so_far = sum(1 for c in song_candidates.values() if c)
        print(f"  -> הושלמו {done_count}/{len(songs)} שירים (נמצאו סרטונים ל-{found_so_far} שירים)...")

    songs_by_best_score = sorted(
        songs,
        key=lambda s: (
            -(song_candidates.get(s["normalized_key"], [{}])[0].get("score", 0) if song_candidates.get(s["normalized_key"]) else 0),
            s["title"],
        ),
    )

    creator_orig_songs = set(ctx.finder_ov.get("creator_is_original_songs", []))
    late_cover_excl_dual = tuple(str(x).lower() for x in ctx.finder_ov.get("late_cover_performers_exclude_dual", []))
    dual_album_exclusions = list(ctx.finder_ov.get("dual_album_exclusions", []))
    primary_orig_perfs: dict[str, list[str]] = ctx.finder_ov.get("primary_original_performers", {})

    is_dual_mode = cfg.is_performer and cfg.dual_performance_mode == "original_plus_creator"
    used_video_ids: set[str] = set()
    dual_selection_by_key: dict[
        str, tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, list[dict[str, Any]]]
    ] = {}

    creator_perf_markers = [cfg.name_he, cfg.creator_acum_reversed_name, cfg.name_en] + ctx.creator_aliases

    for s in songs_by_best_score:
        key = s["normalized_key"]
        cands = song_candidates.get(key, [])
        best_cand: dict[str, Any] | None = None
        orig_cand: dict[str, Any] | None = None
        creator_cand: dict[str, Any] | None = None
        alts: list[dict[str, Any]] = []
        known_orig_perfs = tuple(primary_orig_perfs.get(s["title"], []))

        if is_dual_mode:
            orig_candidates: list[dict[str, Any]] = []
            for c in cands:
                vid = c["video_id"]
                if vid in used_video_ids:
                    alts.append(c)
                    continue
                if best_cand is None:
                    best_cand = c

                if c["tier"] in (ctx.creator_album_tier, ctx.creator_perf_tier):
                    if creator_cand is None:
                        creator_cand = c
                    else:
                        alts.append(c)
                    continue

                if c["tier"] in ("2_album_original", "4_original_performance"):
                    mp = c.get("matched_performer", "")
                    ma = c.get("matched_album", "")
                    vt_ch = f"{c.get('video_title', '')} {c.get('channel', '')} {c.get('description', '')}"
                    is_valid_distinct_orig = True
                    if not mp or any(cm and cm in mp for cm in creator_perf_markers):
                        is_valid_distinct_orig = False
                    elif s["title"] in creator_orig_songs:
                        is_valid_distinct_orig = False
                    elif any(lcp in mp.lower() or lcp in vt_ch.lower() for lcp in late_cover_excl_dual):
                        is_valid_distinct_orig = False
                    else:
                        for dex in dual_album_exclusions:
                            if dex.get("album") and ma == dex["album"]:
                                if "unless_title_in" in dex and s["title"] not in dex["unless_title_in"]:
                                    is_valid_distinct_orig = False
                                    break
                                if "title_in" in dex and s["title"] in dex["title_in"]:
                                    is_valid_distinct_orig = False
                                    break
                            elif dex.get("performer_contains") and dex["performer_contains"] in mp:
                                if s["title"] in dex.get("title_in", []):
                                    is_valid_distinct_orig = False
                                    break

                    if is_valid_distinct_orig:
                        if known_orig_perfs and any(kp in mp for kp in known_orig_perfs):
                            c = dict(c)
                            c["score"] = c.get("score", 0) + 300
                        orig_candidates.append(c)
                        continue

                alts.append(c)

            if orig_candidates:
                orig_cand = max(orig_candidates, key=lambda x: x.get("score", 0))
                alts.extend(c for c in orig_candidates if c["video_id"] != orig_cand["video_id"])

            if orig_cand and creator_cand:
                used_video_ids.add(orig_cand["video_id"])
                used_video_ids.add(creator_cand["video_id"])
                alts = [a for a in alts if a["video_id"] not in (orig_cand["video_id"], creator_cand["video_id"])]
            elif best_cand:
                used_video_ids.add(best_cand["video_id"])
                alts = [a for a in cands if a["video_id"] != best_cand["video_id"]]
        else:
            # Non-performer / original-only mode: single best candidate per song
            avail: list[dict[str, Any]] = []
            for c in cands:
                if c["video_id"] in used_video_ids:
                    alts.append(c)
                    continue
                if known_orig_perfs and c["tier"] in ("2_album_original", "4_original_performance"):
                    if any(kp in c.get("matched_performer", "") for kp in known_orig_perfs):
                        c = dict(c)
                        c["score"] = c.get("score", 0) + 300
                avail.append(c)
            if avail:
                best_cand = max(avail, key=lambda x: x.get("score", 0))
                used_video_ids.add(best_cand["video_id"])
                alts = [a for a in cands if a["video_id"] != best_cand["video_id"]]

        dual_selection_by_key[key] = (best_cand, orig_cand, creator_cand, alts)

    pizmonet_years: dict[str, str] = {}
    piz_path = cfg.raw_cache_dir / "pizmonet_raw.json"
    if piz_path.exists():
        try:
            for ps in json.loads(piz_path.read_text(encoding="utf-8")).get("songs", []):
                if ps.get("year"):
                    pizmonet_years[ps["title"]] = str(ps["year"])
        except Exception:
            pass

    playlist_entries: list[dict[str, Any]] = []
    tier_counts: dict[str, int] = {k: 0 for k in ctx.tier_labels}
    matched_songs_count = 0
    dual_songs_count = 0

    for s in songs:
        key = s["normalized_key"]
        best_cand, orig_cand, creator_cand, alts = dual_selection_by_key.get(key, (None, None, None, []))
        role_cat, role_label, co_creators_str = _build_creator_credits(s, ctx)
        arch_links = _build_archive_links(s, ctx)
        song_notes = " ".join(s.get("notes", [])).strip()
        heb_perfs = [p for p in s.get("performers", []) if any("\u0590" <= c <= "\u05FF" for c in p)]

        if orig_cand and creator_cand:
            matched_songs_count += 1
            dual_songs_count += 1
            tier_counts[orig_cand["tier"]] = tier_counts.get(orig_cand["tier"], 0) + 1
            tier_counts[creator_cand["tier"]] = tier_counts.get(creator_cand["tier"], 0) + 1

            orig_yr, orig_alb_idx, orig_alb_group, orig_trk_num = _resolve_chrono_info(
                s, orig_cand, ctx, pizmonet_years, exclude_creator_solo=True
            )
            cr_yr, cr_alb_idx, cr_alb_group, cr_trk_num = _resolve_chrono_info(
                s, creator_cand, ctx, pizmonet_years, only_creator_solo=True
            )

            if cr_alb_idx != 999 and creator_cand["tier"] == ctx.creator_album_tier:
                if orig_alb_idx == 999:
                    orig_yr = min(orig_yr, cr_yr)
                    if orig_yr == cr_yr:
                        orig_sort_key = (0, orig_yr, cr_alb_idx - 0.5, 999, s["title"], 0)
                    else:
                        orig_sort_key = (0, orig_yr, 999, 999, s["title"], 0)
                else:
                    orig_sort_key = (0, orig_yr, orig_alb_idx, orig_trk_num, s["title"], 0)
                cr_sort_key = (0, cr_yr, cr_alb_idx, cr_trk_num, s["title"], 1)
            else:
                orig_sort_key = (0, orig_yr, orig_alb_idx, orig_trk_num, s["title"], 0)
                if orig_alb_idx != 999:
                    cr_alb_group = f"ביצוע {cfg.name_he} (אחרי האלבום: {orig_alb_group})"
                    cr_trk_num = 999
                    cr_yr = orig_yr
                    cr_sort_key = (0, orig_yr, orig_alb_idx, 900 + orig_trk_num, s["title"], 1)
                else:
                    cr_alb_group = f"סינגל / ביצוע בודד (ביצוע {cfg.name_he})"
                    cr_trk_num = 999
                    cr_yr = orig_yr
                    cr_sort_key = (0, orig_yr, 999, 999, s["title"], 1)

            playlist_entries.append({
                "index": 0,
                "title": s["title"],
                "alt_titles": s.get("alt_titles", []),
                "opening_line": s.get("opening_line", ""),
                "year": str(orig_yr) if orig_yr != 2099 else "",
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
                "catalog_performers": heb_perfs,
                "catalog_albums": s.get("albums", []),
                "tier": orig_cand["tier"],
                "tier_label": ctx.tier_labels[orig_cand["tier"]],
                "selected_video": orig_cand,
                "alternative_videos": [creator_cand] + alts[:2],
            })
            playlist_entries.append({
                "index": 0,
                "title": s["title"],
                "alt_titles": s.get("alt_titles", []),
                "opening_line": s.get("opening_line", ""),
                "year": str(cr_yr) if cr_yr != 2099 else "",
                "album_group": cr_alb_group,
                "album_track_number": cr_trk_num if cr_trk_num != 999 else "",
                "dual_role": cfg.creator_dual_role,
                "_sort_key": cr_sort_key,
                "roles": s.get("roles", []),
                "role_category": role_cat,
                "role_label_heb": role_label,
                "co_creators_heb": co_creators_str,
                "archive_links": arch_links,
                "notes": song_notes,
                "sources": s.get("sources", []),
                "catalog_performers": heb_perfs,
                "catalog_albums": s.get("albums", []),
                "tier": creator_cand["tier"],
                "tier_label": ctx.tier_labels[creator_cand["tier"]],
                "selected_video": creator_cand,
                "alternative_videos": [orig_cand] + alts[:2],
            })
        else:
            chosen = best_cand
            tier = chosen["tier"] if chosen else "6_not_found"
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            if chosen:
                matched_songs_count += 1
            chrono_yr, alb_order_idx, alb_group, trk_num = _resolve_chrono_info(s, chosen, ctx, pizmonet_years)

            playlist_entries.append({
                "index": 0,
                "title": s["title"],
                "alt_titles": s.get("alt_titles", []),
                "opening_line": s.get("opening_line", ""),
                "year": str(chrono_yr) if chrono_yr != 2099 else "",
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
                "catalog_performers": heb_perfs,
                "catalog_albums": s.get("albums", []),
                "tier": tier,
                "tier_label": ctx.tier_labels.get(tier, tier),
                "selected_video": chosen,
                "alternative_videos": alts[:3],
            })

    playlist_entries.sort(key=lambda x: x["_sort_key"])
    for idx, item in enumerate(playlist_entries, 1):
        item["index"] = idx
        item.pop("_sort_key", None)

    total_videos_in_playlist = sum(1 for item in playlist_entries if item.get("selected_video"))
    summary_stats = {
        "total_songs": len(songs),
        "matched_songs": matched_songs_count,
        "dual_performance_songs": dual_songs_count,
        "total_playlist_videos": total_videos_in_playlist,
        "unmatched_songs": tier_counts.get("6_not_found", 0),
        "by_tier": {ctx.tier_labels[k]: v for k, v in tier_counts.items()},
    }
    payload = {"stats": summary_stats, "playlist": playlist_entries}

    if not dry_run:
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            out_json = output_dir / cfg.playlist_json.name
            out_csv = output_dir / cfg.playlist_csv.name
            out_md = output_dir / cfg.playlist_md.name
        else:
            out_json = cfg.playlist_json
            out_csv = cfg.playlist_csv
            out_md = cfg.playlist_md
            out_json.parent.mkdir(parents=True, exist_ok=True)

        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "#",
                "שנה",
                "אלבום / סינגל",
                "רצועה באלבום",
                "שם השיר",
                f"תפקיד {cfg.name_he} ויוצרים שותפים",
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
        md_lines = [
            f"# פלייליסט יוטיוב מקיף ל{cfg.playlist_title_he} (בסדר כרונולוגי)",
            "",
            "## סיכום התאמות לפי רמת תעדוף",
            "",
            f'- **סה"כ שירים בקטלוג:** {summary_stats["total_songs"]}',
            f"- **שירים שנמצא להם סרטון ייחודי ביוטיוב:** {summary_stats['matched_songs']}",
            f"- **שירים שבהם נכללו גם ביצוע מקורי וגם ביצוע של {cfg.name_he}:** {summary_stats['dual_performance_songs']}",
            f'- **סה"כ סרטונים בפלייליסט:** {summary_stats["total_playlist_videos"]}',
        ]
        for k, v in summary_stats["by_tier"].items():
            md_lines.append(f"  - **{k}:** {v} רצועות")
        md_lines.extend([
            "",
            "## 1. רשימת הסרטונים המלאה ביוטיוב (לפי שנה -> אלבומים לפי סדר הרצועות -> סינגלים)",
            "",
            "| # | שנה | אלבום / סינגל | שם השיר | תפקיד ויוצרים | שורת פתיחה | סיווג הביצוע | כותרת הסרטון וקישור | ערוץ | אורך |",
            "|---|-----|---------------|---------|---------------|------------|--------------|---------------------|------|------|",
        ])
        for item in matched_md_items:
            sel = item["selected_video"]
            t_clean = item["title"].replace("|", "\\|")
            yr_str = item.get("year", "")
            ag_str = item.get("album_group", "")
            trk_str = str(item.get("album_track_number", ""))
            alb_col = (f"{ag_str} (#{trk_str})" if trk_str else ag_str).replace("|", "\\|")
            role_col = item.get("role_label_heb", "").replace("|", "\\|")
            ol_col = item.get("opening_line", "").replace("|", "\\|")
            vt_clean = sel["video_title"].replace("|", "\\|").replace("[", "(").replace("]", ")")
            ch_clean = sel["channel"].replace("|", "\\|")
            md_lines.append(
                f"| {item['index']} | {yr_str} | {alb_col} | {t_clean} | {role_col} | {ol_col} | {item['tier_label']} | "
                f"[{vt_clean}]({sel['url']}) | {ch_clean} | {sel.get('duration', '')} |"
            )
        md_lines.extend([
            "",
            f"## 2. פלייליסט ארכיון משלים – {len(unmatched_md_items)} שירים נדירים שאינם ביוטיוב (קישורים לספרייה הלאומית, שירונט וזמרשת)",
            "",
            f"| # | שנה | שם השיר | תפקיד {cfg.name_he} ויוצרים | מבצעים מתועדים | שורת פתיחה | קישורים לארכיון |",
            "|---|-----|---------|------------------------|----------------|------------|------------------|",
        ])
        for item in unmatched_md_items:
            t_clean = item["title"].replace("|", "\\|")
            yr_str = item.get("year", "")
            role_col = item.get("role_label_heb", "").replace("|", "\\|")
            perfs_col = ", ".join(item.get("catalog_performers", [])[:3]).replace("|", "\\|") or "—"
            ol_col = item.get("opening_line", "").replace("|", "\\|") or "—"
            links_md = " · ".join(f"[{a['label']}]({a['url']})" for a in item.get("archive_links", [])) or "—"
            md_lines.append(f"| {item['index']} | {yr_str} | {t_clean} | {role_col} | {perfs_col} | {ol_col} | {links_md} |")
        out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

        print("\n=== סיכום תוצאות איתור סרטוני יוטיוב ===")
        print(f'סה"כ שירים בקטלוג: {summary_stats["total_songs"]}')
        print(f"שירים שנמצא להם סרטון: {summary_stats['matched_songs']}")
        print(f"שירים שבהם נכללו גם ביצוע מקורי וגם ביצוע של {cfg.name_he}: {summary_stats['dual_performance_songs']}")
        print(f'סה"כ סרטונים בפלייליסט: {summary_stats["total_playlist_videos"]}')
        for k, v in summary_stats["by_tier"].items():
            print(f"  {k}: {v}")
        print("\nנשמרו הקבצים:")
        print(f"  1. {out_csv}")
        print(f"  2. {out_json}")
        print(f"  3. {out_md}")

        if rebuild and output_dir is None:
            from core.build_site import build_composer

            build_composer(cfg.slug, standalone=standalone, rebuild_hub=True)

    return payload
