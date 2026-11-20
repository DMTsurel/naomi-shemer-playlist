"""Generic 9-source Israeli composer catalog collector and normalizer."""

from __future__ import annotations

import concurrent.futures
import csv
import html
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from core.config import ComposerConfig, load_composer, load_overrides
from core.hebrew import (
    NIKUD_RE,
    clean_wiki_markup,
    clean_wiki_song_title,
    normalize_catalog_song_title,
)

BROWSER_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
}

ACUM_BASE_URL = "https://nocs.acum.org.il/acumsitesearchdb"
NLI_SRU_URL = "https://nli.alma.exlibrisgroup.com/view/sru/972NNL_INST"
NLI_NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "marc": "http://www.loc.gov/MARC21/slim",
}

ROLE_HEB_LABELS: dict[str, str] = {
    "author": "מילים",
    "composer": "לחן",
    "translator": "תרגום",
    "performer": "ביצוע",
    "arranger": "עיבוד",
}


def _strip_punct_compact(text: str) -> str:
    s = re.sub(r'(?<=[\u0590-\u05FF])["״׳\'\u2018\u2019\u201c\u201d]+(?=[\u0590-\u05FF])', "", text)
    s = re.sub(r"[\"'״׳`\u2018\u2019\u201c\u201d־\-–—,.!:?()\[\]/\\]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _load_json_cache(cache_path: Path, refresh: bool) -> Any | None:
    if not refresh and cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    return None


def _write_json_cache(cache_path: Path, data: Any, indent: int | None = 2) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")


def _creator_name_tokens(cfg: ComposerConfig) -> list[str]:
    tokens: list[str] = []
    for raw in [cfg.name_he, cfg.name_en, cfg.creator_acum_reversed_name, *cfg.creator_aliases]:
        val = (raw or "").strip()
        if val and val not in tokens:
            tokens.append(val)
    return tokens


def _mentions_creator_text(text: str, cfg: ComposerConfig) -> bool:
    if not text:
        return False
    low = text.lower()
    for tok in _creator_name_tokens(cfg):
        if tok.lower() in low:
            return True
    return False


# ---------------------------------------------------------------------------
# 1. Hebrew Wikipedia
# ---------------------------------------------------------------------------


def fetch_wikipedia_json(params: dict[str, str]) -> dict[str, Any]:
    """Query the Hebrew Wikipedia MediaWiki API and return parsed JSON."""
    query_params = dict(params, format="json")
    url = "https://he.wikipedia.org/w/api.php?" + urllib.parse.urlencode(query_params)
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def scrape_wikipedia(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect albums, compilations, books, translations, and songs from Hebrew Wikipedia."""
    synonym_map = overrides.get("synonym_map", {}) if isinstance(overrides, dict) else {}
    empty: dict[str, Any] = {
        "albums": [],
        "compilations": [],
        "books": [],
        "tribute_songs": [],
        "translated_songs": [],
        "songs": [],
    }
    wiki_page = str(cfg.sources.get("wiki_page") or "").strip()
    cache_path = raw_cache_dir / "wikipedia_raw.json"
    print(f"[1/9] קורא נתונים מוויקיפדיה ({wiki_page or cfg.name_he})...")
    cached = _load_json_cache(cache_path, refresh)
    if cached is not None:
        print(
            f"  -> נטען מהמטמון: {len(cached.get('albums', []))} אלבומים, "
            f"{len(cached.get('compilations', []))} אוספים, "
            f"{len(cached.get('books', []))} ספרים, "
            f"{len(cached.get('songs', []))} שירים."
        )
        return cached
    if cache_only or not wiki_page:
        if not wiki_page:
            print("  -> דולג (אין wiki_page מוגדר ב-composer.json).")
        return empty

    works_sections = set(cfg.sources.get("wiki_works_sections") or ["יצירותיה", "יצירותיו", "דיסקוגרפיה"])
    wikitext = ""
    try:
        sections_data = fetch_wikipedia_json({
            "action": "parse",
            "page": wiki_page,
            "prop": "sections",
        })
        works_section_idx = None
        for sec in sections_data.get("parse", {}).get("sections", []):
            if sec.get("line", "").strip() in works_sections:
                works_section_idx = sec["index"]
                break
        if works_section_idx:
            sec_data = fetch_wikipedia_json({
                "action": "parse",
                "page": wiki_page,
                "section": works_section_idx,
                "prop": "wikitext",
            })
            wikitext = sec_data.get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception as exc:
        print(f"  [!] אזהרה בטעינת דף ויקיפדיה '{wiki_page}': {exc}", file=sys.stderr)

    albums: list[dict[str, Any]] = []
    compilations: list[dict[str, Any]] = []
    translated_songs: list[dict[str, Any]] = []
    books: list[dict[str, Any]] = []
    tribute_songs: list[str] = []

    sub_sections = re.split(r"===\s*([^=]+?)\s*===", wikitext) if wikitext else []
    for i in range(1, len(sub_sections), 2):
        sec_title = sub_sections[i].strip()
        sec_body = sub_sections[i + 1]

        if sec_title == "אלבומים":
            for line in sec_body.splitlines():
                line = line.strip()
                if line.startswith("*"):
                    raw_item = clean_wiki_markup(line.lstrip("*").strip())
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", raw_item)
                    albums.append({
                        "raw": raw_item,
                        "year": year_match.group(1) if year_match else "",
                        "category": "album",
                        "source": "wikipedia",
                    })
        elif sec_title == "אוספים":
            for line in sec_body.splitlines():
                line = line.strip()
                if line.startswith("*"):
                    raw_item = clean_wiki_markup(line.lstrip("*").strip())
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", raw_item)
                    compilations.append({
                        "raw": raw_item,
                        "year": year_match.group(1) if year_match else "",
                        "category": "compilation",
                        "source": "wikipedia",
                    })
        elif sec_title == "תרגומי שירים":
            for row in sec_body.split("|-")[1:]:
                if "|}" in row:
                    row = row.split("|}")[0]
                cells = [clean_wiki_markup(c) for c in row.split("||")]
                if len(cells) >= 2:
                    first_cell = re.sub(r"^\s*\|\s*", "", cells[0].strip())
                    orig_title = cells[1].strip() if len(cells) > 1 else ""
                    performer = cells[2].strip() if len(cells) > 2 else ""
                    album_year = cells[3].strip() if len(cells) > 3 else ""
                    if first_cell and "שם השיר" not in first_cell:
                        translated_songs.append({
                            "title": clean_wiki_song_title(first_cell),
                            "original_title": orig_title,
                            "performer": performer,
                            "album_info": album_year,
                            "roles": ["translator"],
                            "source": "wikipedia_translations_table",
                        })
        elif sec_title == "ספרים":
            for line in sec_body.splitlines():
                line = line.strip()
                if line.startswith("*"):
                    raw_item = clean_wiki_markup(line.lstrip("*").strip())
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", raw_item)
                    books.append({
                        "raw": raw_item,
                        "year": year_match.group(1) if year_match else "",
                        "category": "book",
                        "source": "wikipedia",
                    })
        elif "שירים שנכתבו על" in sec_title:
            for line in sec_body.splitlines():
                line = line.strip()
                if line.startswith("*"):
                    tribute_songs.append(clean_wiki_markup(line.lstrip("*").strip()))

    songs_dict: dict[str, dict[str, Any]] = {}

    def add_wiki_song(
        title: str,
        role: str,
        source_detail: str,
        original_title: str = "",
        performer: str = "",
        album: str = "",
        lyricist: str = "",
    ) -> None:
        clean_t = clean_wiki_song_title(title)
        if not clean_t:
            return
        norm = normalize_catalog_song_title(clean_t, synonym_map)
        if not norm:
            return
        entry = songs_dict.setdefault(norm, {
            "title": clean_t,
            "roles": [],
            "wiki_sources": [],
            "original_title": "",
            "performers": [],
            "albums": [],
            "lyricist": "",
        })
        if role and role not in entry["roles"]:
            entry["roles"].append(role)
        if source_detail and source_detail not in entry["wiki_sources"]:
            entry["wiki_sources"].append(source_detail)
        if original_title and not entry["original_title"]:
            entry["original_title"] = original_title
        if performer and performer not in entry["performers"]:
            entry["performers"].append(performer)
        if album and album not in entry["albums"]:
            entry["albums"].append(album)
        if lyricist and not entry["lyricist"]:
            entry["lyricist"] = lyricist

    for ts in translated_songs:
        add_wiki_song(
            title=ts["title"],
            role="translator",
            source_detail="יצירותיה: תרגומי שירים",
            original_title=ts["original_title"],
            performer=ts["performer"],
            album=ts["album_info"],
        )

    wiki_template = str(cfg.sources.get("wiki_template") or "").strip()
    if wiki_template:
        try:
            tpl_data = fetch_wikipedia_json({
                "action": "parse",
                "page": wiki_template,
                "prop": "wikitext",
            })
            tpl_wt = tpl_data.get("parse", {}).get("wikitext", {}).get("*", "")
            for m in re.finditer(r"\|רשימה(\d)\s*=\s*(.*)", tpl_wt):
                grp_num = m.group(1)
                items_str = m.group(2)
                for target, label in re.findall(r"\[\[(?:([^|\]]+)\|)?([^\]]+)\]\]", items_str):
                    song_name = label or target
                    if grp_num == "2":
                        add_wiki_song(song_name, "author", f"{wiki_template} (כתבה ותרגמה)")
                    elif grp_num == "3":
                        add_wiki_song(song_name, "composer", f"{wiki_template} (הלחינה)")
        except Exception as exc:
            print(f"  [!] אזהרה בטעינת תבנית ויקיפדיה '{wiki_template}': {exc}", file=sys.stderr)

    for cat_spec in cfg.sources.get("wiki_categories") or []:
        if not isinstance(cat_spec, (list, tuple)) or len(cat_spec) < 2:
            continue
        cat_name, role = str(cat_spec[0]), str(cat_spec[1])
        try:
            cat_data = fetch_wikipedia_json({
                "action": "query",
                "list": "categorymembers",
                "cmtitle": cat_name,
                "cmlimit": "500",
            })
            for member in cat_data.get("query", {}).get("categorymembers", []):
                if member.get("ns") == 0:
                    add_wiki_song(member["title"], role, cat_name)
        except Exception as exc:
            print(f"  [!] אזהרה בטעינת קטגוריית ויקיפדיה '{cat_name}': {exc}", file=sys.stderr)

    for extra_page in cfg.sources.get("wiki_extra_pages") or []:
        page_title = str(extra_page.get("page") or "").strip()
        if not page_title:
            continue
        try:
            pdata = fetch_wikipedia_json({
                "action": "parse",
                "page": page_title,
                "prop": "wikitext",
            })
            wt = pdata.get("parse", {}).get("wikitext", {}).get("*", "")
        except Exception as exc:
            print(f"  [!] אזהרה בטעינת דף ויקיפדיה '{page_title}': {exc}", file=sys.stderr)
            continue

        parser_kind = extra_page.get("parser", "")
        src_detail = str(extra_page.get("source_detail") or page_title)
        perf_val = str(extra_page.get("performer") or "")
        alb_val = str(extra_page.get("album") or "")

        if parser_kind == "tracklist_template":
            for idx in range(1, 30):
                m_name = re.search(rf"\|\s*שם{idx}\s*=\s*(.*)", wt)
                m_lyrics = re.search(rf"\|\s*מילים{idx}\s*=\s*(.*)", wt)
                if m_name:
                    s_name = clean_wiki_song_title(m_name.group(1))
                    lyr = clean_wiki_markup(m_lyrics.group(1)) if m_lyrics else ""
                    role = "author" if _mentions_creator_text(lyr, cfg) else "composer"
                    add_wiki_song(
                        s_name,
                        role=role,
                        source_detail=src_detail,
                        performer=perf_val,
                        album=alb_val,
                        lyricist=lyr,
                    )
        elif parser_kind == "bullet_section":
            heading = str(extra_page.get("section_heading") or "== השירים ==")
            if heading in wt:
                sec_part = wt.split(heading, 1)[1].split("==")[0]
                for line in sec_part.splitlines():
                    line = line.strip()
                    if line.startswith("*"):
                        s_name = clean_wiki_song_title(line.lstrip("*").strip())
                        for r in extra_page.get("roles") or ["composer"]:
                            add_wiki_song(s_name, role=r, source_detail=src_detail, performer=perf_val, album=alb_val)
        elif parser_kind == "numbered_section":
            heading = str(extra_page.get("section_heading") or "== השירים בקלטת ==")
            skip_titles = set(extra_page.get("skip_titles") or [])
            if heading in wt:
                sec_part = wt.split(heading, 1)[1].split("==")[0]
                for line in sec_part.splitlines():
                    line = line.strip()
                    if line.startswith("#"):
                        s_name = clean_wiki_song_title(line.lstrip("#").strip())
                        if s_name and s_name not in skip_titles:
                            for r in extra_page.get("roles") or ["composer"]:
                                add_wiki_song(s_name, role=r, source_detail=src_detail, performer=perf_val, album=alb_val)

    result = {
        "albums": albums,
        "compilations": compilations,
        "books": books,
        "tribute_songs": tribute_songs,
        "translated_songs": translated_songs,
        "songs": list(songs_dict.values()),
    }
    _write_json_cache(cache_path, result)
    print(
        f"  -> הסתיים איסוף מוויקיפדיה: {len(albums)} אלבומים, "
        f"{len(compilations)} אוספים, {len(books)} ספרים, "
        f"{len(result['songs'])} שירים ייחודיים."
    )
    return result


# ---------------------------------------------------------------------------
# 2. Shironet
# ---------------------------------------------------------------------------


def scrape_shironet(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect works and discography from Shironet for `sources.shironet_prfid`."""
    prfid = cfg.sources.get("shironet_prfid")
    cache_path = raw_cache_dir / "shironet_raw.json"
    print(f"[2/9] קורא נתונים משירונט (prfid={prfid or '-'})...")
    cached = _load_json_cache(cache_path, refresh)
    if cached is not None:
        print(
            f"  -> נטען מהמטמון: {len(cached.get('songs', []))} שירים ייחודיים, "
            f"{len(cached.get('work_entries', []))} דפי שיר (wrkid), "
            f"{len(cached.get('albums', []))} אלבומים."
        )
        return cached
    if cache_only or not prfid:
        if not prfid:
            print("  -> דולג (אין shironet_prfid מוגדר ב-composer.json).")
        return {"songs": [], "work_entries": [], "albums": []}

    prfid_str = str(prfid).strip()
    col_ov = overrides.get("collector_overrides", {})
    skip_wrkids = {str(x) for x in col_ov.get("shironet_skip_wrkids", [])}
    shironet_classes = {
        1: ("author", f'שירים שנכתבו ע"י {cfg.name_he}'),
        2: ("composer", f'שירים שהולחנו ע"י {cfg.name_he}'),
        3: ("translator", f'שירים שתורגמו ע"י {cfg.name_he}'),
        4: ("performer", f'שירים שבוצעו ע"י {cfg.name_he}'),
    }

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    headers = dict(BROWSER_HEADERS)
    headers["Referer"] = f"https://shironet.mako.co.il/artist?type=works&lang=1&prfid={prfid_str}"

    def fetch_html(url: str) -> str:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                with opener.open(req, timeout=20) as resp:
                    text = resp.read().decode("utf-8", errors="replace")
                    if "Radware Block Page" not in text:
                        return text
            except Exception as exc:
                if attempt == 2:
                    print(f"  [!] שגיאה בטעינת {url}: {exc}", file=sys.stderr)
            time.sleep(1.0 + attempt)
        return ""

    fetch_html(headers["Referer"])
    time.sleep(0.4)

    work_entries: dict[str, dict[str, Any]] = {}
    song_link_pat = (
        rf'<a\s+href="(/artist\?type=lyrics&lang=1&prfid={re.escape(prfid_str)}&wrkid=(\d+))"\s+'
        r'class="artist_player_songlist">\s*(.*?)\s*</a>'
    )

    for cls_id, (role_key, role_label) in shironet_classes.items():
        page = 1
        max_page = 1
        while page <= max_page:
            url = (
                f"https://shironet.mako.co.il/artist?type=works&lang=1"
                f"&prfid={prfid_str}&class={cls_id}&sort=alpha&page={page}"
            )
            page_html = fetch_html(url)
            if not page_html:
                break
            matches = re.findall(song_link_pat, page_html, flags=re.DOTALL)
            for href, wrkid, raw_title in matches:
                if wrkid in skip_wrkids:
                    continue
                title = html.unescape(re.sub(r"\s+", " ", raw_title)).strip()
                entry = work_entries.setdefault(wrkid, {
                    "wrkid": wrkid,
                    "title": title,
                    "url": f"https://shironet.mako.co.il{href}",
                    "roles": [],
                    "albums": [],
                })
                if role_key not in entry["roles"]:
                    entry["roles"].append(role_key)

            page_nums = [int(p) for p in re.findall(r"page=(\d+)", page_html)]
            if page_nums:
                max_page = max(max_page, max(page_nums))
            print(f"  -> שירונט class={cls_id} ({role_label}) עמוד {page}/{max_page}: נמצאו {len(matches)} רשומות")
            page += 1
            time.sleep(0.35)

    disco_url = f"https://shironet.mako.co.il/artist?type=discography&lang=1&prfid={prfid_str}"
    disco_html = fetch_html(disco_url)
    disc_pat = (
        rf'<a\s+href="(/artist\?type=disc&lang=1&prfid={re.escape(prfid_str)}&discid=(\d+))"[^>]*>'
        r'\s*([^<]+?)\s*</a>'
    )
    disc_matches = re.findall(disc_pat, disco_html)
    seen_discs: set[str] = set()
    shironet_albums: list[dict[str, Any]] = []
    for href, discid, raw_album_title in disc_matches:
        if discid in seen_discs:
            continue
        seen_discs.add(discid)
        album_title = html.unescape(raw_album_title).strip()
        time.sleep(0.35)
        disc_page_html = fetch_html(f"https://shironet.mako.co.il{href}")
        track_matches = re.findall(song_link_pat, disc_page_html, flags=re.DOTALL)
        tracks = []
        for _t_href, wrkid, raw_t_title in track_matches:
            t_title = html.unescape(re.sub(r"\s+", " ", raw_t_title)).strip()
            tracks.append({"wrkid": wrkid, "title": t_title})
            if wrkid in work_entries and album_title not in work_entries[wrkid]["albums"]:
                work_entries[wrkid]["albums"].append(album_title)
        shironet_albums.append({
            "discid": discid,
            "title": album_title,
            "url": f"https://shironet.mako.co.il{href}",
            "tracks": tracks,
            "source": "shironet",
        })

    songs_by_norm: dict[str, dict[str, Any]] = {}
    synonym_map = overrides.get("synonym_map", {}) if isinstance(overrides, dict) else {}
    for wrkid, w in work_entries.items():
        norm = normalize_catalog_song_title(w["title"], synonym_map)
        if not norm:
            continue
        s = songs_by_norm.setdefault(norm, {
            "title": w["title"],
            "roles": [],
            "wrkids": [],
            "urls": [],
            "albums": [],
        })
        if wrkid not in s["wrkids"]:
            s["wrkids"].append(wrkid)
        if w["url"] not in s["urls"]:
            s["urls"].append(w["url"])
        for r in w["roles"]:
            if r not in s["roles"]:
                s["roles"].append(r)
        for a in w["albums"]:
            if a not in s["albums"]:
                s["albums"].append(a)

    result = {
        "songs": list(songs_by_norm.values()),
        "work_entries": list(work_entries.values()),
        "albums": shironet_albums,
    }
    _write_json_cache(cache_path, result)
    print(
        f"  -> הסתיים איסוף משירונט: {len(result['songs'])} שירים ייחודיים "
        f"({len(work_entries)} דפי שיר), {len(shironet_albums)} אלבומים."
    )
    return result


# ---------------------------------------------------------------------------
# 3. ACUM (works, performer records, album details, work details)
# ---------------------------------------------------------------------------


def fetch_acum_json(endpoint_and_query: str) -> dict[str, Any]:
    """Fetch JSON from ACUM SearchDB API with retry and rate-limit backoff."""
    url = f"{ACUM_BASE_URL}/{endpoint_and_query}"
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers=BROWSER_HEADERS)
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(5.0 * (attempt + 1))
                continue
            if attempt == 7:
                raise RuntimeError(f"Failed fetching ACUM {url}: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))
        except Exception as exc:
            if attempt == 7:
                raise RuntimeError(f"Failed fetching ACUM {url}: {exc}") from exc
            time.sleep(1.5 * (attempt + 1))
    return {}


def _parse_acum_performer_specs(cfg: ComposerConfig) -> tuple[list[tuple[str, str, bool]], set[str]]:
    specs: list[tuple[str, str, bool]] = []
    creator_perf_ids: set[str] = set()
    for item in cfg.sources.get("acum_performer_ids") or []:
        if isinstance(item, dict):
            pid = str(item.get("id") or "").strip()
            label = str(item.get("label") or pid)
            is_cr = bool(item.get("is_creator", True))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            pid, label, is_cr = str(item[0]).strip(), str(item[1]), True
        else:
            pid, label, is_cr = str(item).strip(), str(item), True
        if pid:
            specs.append((pid, label, is_cr))
            if is_cr:
                creator_perf_ids.add(pid)
    return specs, creator_perf_ids


def scrape_acum(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect works, performer tracks, albums, and work versions from ACUM."""
    del overrides
    acum_creator_id = str(cfg.sources.get("acum_creator_id") or "").strip()
    perf_specs, creator_perf_ids = _parse_acum_performer_specs(cfg)
    cache_path = raw_cache_dir / "acum_raw.json"
    print(f'[3/9] קורא נתונים מאקו"ם (creatorId={acum_creator_id or "-"})...')

    if not acum_creator_id and not perf_specs:
        cached = _load_json_cache(cache_path, refresh)
        if cached is not None:
            return cached
        print("  -> דולג (אין מזהי אקו\"ם מוגדרים ב-composer.json).")
        return {"works": [], "raw_beans": [], "albums": []}

    all_beans: list[dict[str, Any]] = []
    albums_list: list[dict[str, Any]] = []
    cached_acum = _load_json_cache(cache_path, refresh)
    if cached_acum is not None:
        all_beans = cached_acum.get("raw_beans", [])
        albums_list = cached_acum.get("albums", [])

    if not all_beans:
        if cache_only:
            if cached_acum and cached_acum.get("works"):
                return cached_acum
            return {"works": [], "raw_beans": [], "albums": albums_list}

        pages_cache_path = raw_cache_dir / "acum_pages_partial.json"
        fetched_pages: dict[str, list[dict[str, Any]]] = {}
        if not refresh and pages_cache_path.exists():
            fetched_pages = json.loads(pages_cache_path.read_text(encoding="utf-8"))

        if acum_creator_id:
            init_data = fetch_acum_json(f"searchdb?creatorId={urllib.parse.quote(acum_creator_id)}")
            result_type_infos = init_data.get("data", {}).get("resultTypeInfos", [])
            tasks: list[tuple[str, int]] = []
            for rti in result_type_infos:
                rt_key = rti["resultTypeKey"]
                count = int(rti.get("count", 0))
                page_results = rti.get("pageResults") or []
                fetched_pages[f"{rt_key}:1"] = page_results
                total_pages = (count + 9) // 10
                print(f"  -> אקו\"ם קטגוריה '{rt_key}': סה\"כ {count} רשומות ({total_pages} עמודים)")
                for p in range(2, total_pages + 1):
                    if f"{rt_key}:{p}" not in fetched_pages:
                        tasks.append((rt_key, p))

            def fetch_page(task: tuple[str, int]) -> tuple[str, list[dict[str, Any]]]:
                rt_key, page_num = task
                time.sleep(0.25)
                data = fetch_acum_json(
                    f"searchdb?creatorId={urllib.parse.quote(acum_creator_id)}&resultTypeKey={rt_key}&pageNumber={page_num}"
                )
                for info in data.get("data", {}).get("resultTypeInfos", []):
                    if info.get("resultTypeKey") == rt_key:
                        return f"{rt_key}:{page_num}", (info.get("pageResults") or [])
                return f"{rt_key}:{page_num}", []

            completed = 0
            if tasks:
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {executor.submit(fetch_page, t): t for t in tasks}
                    for future in concurrent.futures.as_completed(futures):
                        key, beans = future.result()
                        fetched_pages[key] = beans
                        completed += 1
                        if completed % 25 == 0 or completed == len(tasks):
                            print(f"  -> התקדמות אקו\"ם (יצירות וביצועים): {completed}/{len(tasks)} עמודים...")
                            _write_json_cache(pages_cache_path, fetched_pages, indent=None)

            for key in sorted(fetched_pages.keys(), key=lambda k: (k.split(":")[0], int(k.split(":")[1]))):
                all_beans.extend(fetched_pages[key])

        term_encoded = urllib.parse.quote(cfg.name_he)
        album_init = fetch_acum_json(f"searchdb?term={term_encoded}&resultTypeKey=album&pageNumber=1")
        album_total_pages = 1
        for info in album_init.get("data", {}).get("resultTypeInfos", []):
            if info.get("resultTypeKey") == "album":
                count = int(info.get("count", 0))
                albums_list.extend(info.get("pageResults") or [])
                album_total_pages = (count + 6) // 7

        for p in range(2, album_total_pages + 1):
            adata = fetch_acum_json(f"searchdb?term={term_encoded}&resultTypeKey=album&pageNumber={p}")
            for info in adata.get("data", {}).get("resultTypeInfos", []):
                if info.get("resultTypeKey") == "album":
                    albums_list.extend(info.get("pageResults") or [])

    perf_cache_path = raw_cache_dir / "acum_performer_beans.json"
    perf_beans: list[dict[str, Any]] = []
    cached_perf = _load_json_cache(perf_cache_path, refresh)
    if cached_perf is not None:
        perf_beans = cached_perf
        print(f"  -> נטענו מהמטמון {len(perf_beans)} רשומות ביצוע (performerId).")
    elif not cache_only and perf_specs:
        print(f"  -> שולף רשומות ביצוע מאקו\"ם עבור {len(perf_specs)} מזהי מבצע...")
        for perf_id, _perf_label, _is_cr in perf_specs:
            init_p = fetch_acum_json(f"searchdb?performerId={urllib.parse.quote(perf_id)}")
            for rti in init_p.get("data", {}).get("resultTypeInfos", []):
                rt_key = rti["resultTypeKey"]
                count = int(rti.get("count", 0))
                if count == 0:
                    continue
                perf_beans.extend(rti.get("pageResults") or [])
                total_p = (count + 9) // 10
                for p in range(2, total_p + 1):
                    time.sleep(0.22)
                    pdata = fetch_acum_json(
                        f"searchdb?performerId={urllib.parse.quote(perf_id)}&resultTypeKey={rt_key}&pageNumber={p}"
                    )
                    for info in pdata.get("data", {}).get("resultTypeInfos", []):
                        if info.get("resultTypeKey") == rt_key:
                            perf_beans.extend(info.get("pageResults") or [])
        _write_json_cache(perf_cache_path, perf_beans)
        print(f"  -> נשלפו {len(perf_beans)} רשומות ביצוע (performerId).")

    albums_details_cache_path = raw_cache_dir / "acum_albums_details.json"
    albums_details: dict[str, dict[str, Any]] = _load_json_cache(albums_details_cache_path, refresh) or {}
    if albums_details:
        print(f"  -> נטענו מהמטמון פרטי רצועות של {len(albums_details)} אלבומי אקו\"ם.")
    elif not cache_only and albums_list:
        print(f"  -> שולף רשימות רצועות מלאות (getalbuminfo) עבור {len(albums_list)} אלבומים באקו\"ם...")
        for idx, alb in enumerate(albums_list, 1):
            alb_num = str(alb.get("number", "")).strip()
            if not alb_num or alb_num in albums_details:
                continue
            time.sleep(0.22)
            ainfo = fetch_acum_json(f"getalbuminfo?albumId={alb_num}")
            ab = ainfo.get("data", {}).get("albumBean") or {}
            if ab:
                albums_details[alb_num] = ab
            if idx % 10 == 0 or idx == len(albums_list):
                print(f"  -> התקדמות אלבומי אקו\"ם: {idx}/{len(albums_list)} אלבומים...")
        _write_json_cache(albums_details_cache_path, albums_details)

    if cache_only and cached_acum and cached_acum.get("works") and not perf_cache_path.exists() and not albums_details_cache_path.exists():
        return cached_acum

    def _is_creator_bean(bean_item: dict[str, Any]) -> bool:
        if acum_creator_id and bean_item.get("creatorIpBaseNumber") == acum_creator_id:
            return True
        heb_n = bean_item.get("creatorHebName") or ""
        return cfg.name_he in heb_n

    def _has_creator_in_list(beans_list: list[dict[str, Any]] | None) -> bool:
        if not beans_list:
            return False
        return any(_is_creator_bean(b) for b in beans_list)

    def _extract_names(beans_list: list[dict[str, Any]] | None) -> list[str]:
        if not beans_list:
            return []
        names: list[str] = []
        for b in beans_list:
            n = (b.get("creatorHebName") or b.get("creatorEngName") or "").strip()
            if n and n not in names:
                names.append(n)
        return names

    work_to_acum_albums: dict[str, list[str]] = {}
    album_track_beans: list[dict[str, Any]] = []
    for alb in albums_list:
        alb_num = str(alb.get("number", "")).strip()
        ab = albums_details.get(alb_num, {})
        alb_title = (ab.get("title") or alb.get("title") or "").strip()
        versions = ab.get("versions") or []
        release_dates = [v.get("release_date", "") for v in versions if v.get("release_date")]
        publishers = [
            v.get("publisherHebName") or v.get("publisherEngName") or ""
            for v in versions
            if v.get("publisherHebName") or v.get("publisherEngName")
        ]
        alb["release_date"] = release_dates[0] if release_dates else ""
        alb["publisher"] = publishers[0] if publishers else ""
        tracks = ab.get("tracks") or []
        alb["tracks_names"] = [(t.get("workHebName") or t.get("workEngName") or "").strip() for t in tracks]
        for t in tracks:
            wid = str(t.get("workId") or t.get("workNumber") or "")
            creators = (
                (t.get("authors") or [])
                + (t.get("composers") or [])
                + (t.get("translators") or [])
                + (t.get("arrangers") or [])
                + (t.get("creators") or [])
            )
            perf_num = str((t.get("performer") or {}).get("number", ""))
            is_creator = any(_is_creator_bean(c) for c in creators) or perf_num in creator_perf_ids
            if is_creator:
                album_track_beans.append(t)
                if wid and alb_title:
                    work_to_acum_albums.setdefault(wid, [])
                    if alb_title not in work_to_acum_albums[wid]:
                        work_to_acum_albums[wid].append(alb_title)

    works_by_id: dict[str, dict[str, Any]] = {}
    combined_beans = all_beans + perf_beans + album_track_beans

    for bean in combined_beans:
        heb_name = (bean.get("workTranslatedHebName") or bean.get("workHebName") or "").strip()
        eng_name = (bean.get("workTranslatedEngName") or bean.get("workEngName") or "").strip()
        orig_name = ""
        if bean.get("original"):
            orig_name = (
                bean["original"].get("workHebName")
                or bean["original"].get("workEngName")
                or ""
            ).strip()
        elif bean.get("workTranslatedHebName") and bean.get("workHebName") != bean.get("workTranslatedHebName"):
            orig_name = (bean.get("workHebName") or "").strip()

        m_num = re.match(r"^(\d+)\s+([\u0590-\u05FF].*)$", heb_name)
        if m_num:
            heb_name = f"{m_num.group(2)} {m_num.group(1)}"

        work_id = str(bean.get("workTranslatedId") or bean.get("workId") or bean.get("workNumber") or "")
        if not work_id:
            continue

        w = works_by_id.setdefault(work_id, {
            "work_id": work_id,
            "work_number": bean.get("workNumber", ""),
            "title_heb": heb_name,
            "title_eng": eng_name,
            "original_title": orig_name,
            "work_type": bean.get("workType", ""),
            "roles": [],
            "authors": [],
            "composers": [],
            "translators": [],
            "arrangers": [],
            "performers": [],
            "albums": [],
            "youtube_ids": [],
            "versions_count": 0,
            "registration_date": bean.get("registration_date", ""),
            "publication_date": bean.get("publication_date", ""),
        })

        if heb_name and (not w["title_heb"] or w["title_heb"].isascii()):
            w["title_heb"] = heb_name
        if eng_name and not w["title_eng"]:
            w["title_eng"] = eng_name
        if orig_name and not w["original_title"]:
            w["original_title"] = orig_name

        authors_beans = (bean.get("authors") or []) + (bean.get("composersAndAuthors") or [])
        composers_beans = (bean.get("composers") or []) + (bean.get("composersAndAuthors") or [])
        translators_beans = list(bean.get("translators") or [])
        arrangers_beans = list(bean.get("arrangers") or [])

        for cr in bean.get("creators") or []:
            rc = cr.get("roleCode", "")
            if rc in ("A", "CA"):
                authors_beans.append(cr)
            if rc in ("C", "CA"):
                composers_beans.append(cr)
            if rc in ("SA", "TR"):
                translators_beans.append(cr)
            if rc == "AR":
                arrangers_beans.append(cr)

        if _has_creator_in_list(authors_beans) and "author" not in w["roles"]:
            w["roles"].append("author")
        if _has_creator_in_list(composers_beans) and "composer" not in w["roles"]:
            w["roles"].append("composer")
        if _has_creator_in_list(translators_beans) and "translator" not in w["roles"]:
            w["roles"].append("translator")
        if _has_creator_in_list(arrangers_beans) and "arranger" not in w["roles"]:
            w["roles"].append("arranger")

        for a in _extract_names(authors_beans):
            if a not in w["authors"]:
                w["authors"].append(a)
        for c in _extract_names(composers_beans):
            if c not in w["composers"]:
                w["composers"].append(c)
        for tr in _extract_names(translators_beans):
            if tr not in w["translators"]:
                w["translators"].append(tr)
        for ar in _extract_names(arrangers_beans):
            if ar not in w["arrangers"]:
                w["arrangers"].append(ar)

        perf = bean.get("performer")
        if perf:
            p_name = (perf.get("performerHebName") or perf.get("performerEngName") or "").strip()
            if p_name and p_name not in w["performers"]:
                w["performers"].append(p_name)
            if str(perf.get("number", "")) in creator_perf_ids and "performer" not in w["roles"]:
                w["roles"].append("performer")

        yt_id = (bean.get("youtubeId") or "").strip()
        if yt_id and yt_id not in w["youtube_ids"]:
            w["youtube_ids"].append(yt_id)

        if bean.get("isVersion") == "1":
            w["versions_count"] = max(w["versions_count"], 1)
        elif bean.get("workVersions") and bean["workVersions"].get("total"):
            try:
                wv_total = int(bean["workVersions"]["total"])
                if wv_total > w["versions_count"]:
                    w["versions_count"] = wv_total
            except ValueError:
                pass

    for wid, alb_titles in work_to_acum_albums.items():
        if wid in works_by_id:
            for at in alb_titles:
                if at not in works_by_id[wid]["albums"]:
                    works_by_id[wid]["albums"].append(at)

    workinfo_cache_path = raw_cache_dir / "acum_workinfo_cache.json"
    workinfo_cache: dict[str, dict[str, Any]] = _load_json_cache(workinfo_cache_path, refresh) or {}

    work_ids_to_fetch = [
        wid
        for wid, w in works_by_id.items()
        if w.get("versions_count", 0) > 0 and len(wid) == 7 and wid not in workinfo_cache
    ]

    if work_ids_to_fetch and not cache_only:
        print(f"  -> שולף פרטי ביצועים ואלבומים (getworkinfo) עבור {len(work_ids_to_fetch)} יצירות באקו\"ם...")

        def fetch_single_workinfo(wid: str) -> tuple[str, dict[str, Any]]:
            time.sleep(0.25)
            data = fetch_acum_json(f"getworkinfo?workId={wid}").get("data") or {}
            slim_versions = [
                {
                    "performer": v.get("performer"),
                    "creators": v.get("creators"),
                    "youtubeId": v.get("youtubeId", ""),
                    "time": v.get("time", ""),
                }
                for v in data.get("workVersions") or []
            ]
            slim_albums = [
                {"number": a.get("number", ""), "title": a.get("title", "")}
                for a in data.get("workAlbums") or []
            ]
            return wid, {
                "workVersionCount": data.get("workVersionCount", 0),
                "workVersions": slim_versions,
                "workAlbums": slim_albums,
                "publication_date": (data.get("work") or {}).get("publication_date", ""),
            }

        done_cnt = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fetch_single_workinfo, wid): wid for wid in work_ids_to_fetch}
            for fut in concurrent.futures.as_completed(futures):
                wid, info_dict = fut.result()
                workinfo_cache[wid] = info_dict
                done_cnt += 1
                if done_cnt % 40 == 0 or done_cnt == len(work_ids_to_fetch):
                    print(f"  -> התקדמות getworkinfo באקו\"ם: {done_cnt}/{len(work_ids_to_fetch)} יצירות...")
                    _write_json_cache(workinfo_cache_path, workinfo_cache, indent=None)
    elif workinfo_cache:
        print(f"  -> נטען מהמטמון מידע מפורט (getworkinfo) עבור {len(workinfo_cache)} יצירות.")

    for wid, winfo in workinfo_cache.items():
        if wid not in works_by_id:
            continue
        w = works_by_id[wid]
        if winfo.get("publication_date") and not w["publication_date"]:
            w["publication_date"] = winfo["publication_date"]
        wv_cnt = int(winfo.get("workVersionCount") or 0)
        if wv_cnt > w["versions_count"]:
            w["versions_count"] = wv_cnt
        for v in winfo.get("workVersions") or []:
            perf = v.get("performer")
            if perf:
                p_name = (perf.get("performerHebName") or perf.get("performerEngName") or "").strip()
                if p_name and p_name not in w["performers"]:
                    w["performers"].append(p_name)
                if str(perf.get("number", "")) in creator_perf_ids and "performer" not in w["roles"]:
                    w["roles"].append("performer")
            yt = (v.get("youtubeId") or "").strip()
            if yt and yt not in w["youtube_ids"]:
                w["youtube_ids"].append(yt)
            for cr in v.get("creators") or []:
                if cr.get("roleCode") == "AR":
                    ar_name = (cr.get("creatorHebName") or cr.get("creatorEngName") or "").strip()
                    if ar_name and ar_name not in w["arrangers"]:
                        w["arrangers"].append(ar_name)
                    if _is_creator_bean(cr) and "arranger" not in w["roles"]:
                        w["roles"].append("arranger")
        for a in winfo.get("workAlbums") or []:
            atitle = (a.get("title") or "").strip()
            if atitle and atitle not in w["albums"]:
                w["albums"].append(atitle)

    result = {
        "works": list(works_by_id.values()),
        "raw_beans": all_beans,
        "albums": albums_list,
    }
    if not cache_only:
        _write_json_cache(cache_path, result)
    print(f"  -> הסתיים איסוף מאקו\"ם: {len(result['works'])} יצירות ייחודיות, {len(albums_list)} אלבומים מפורטים.")
    return result


# ---------------------------------------------------------------------------
# 4. Stereo ve Mono
# ---------------------------------------------------------------------------


def scrape_stereo_ve_mono(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect discography and track credits from Stereo ve Mono."""
    svm_artist = str(cfg.sources.get("stereo_ve_mono_artist") or "").strip()
    cache_path = raw_cache_dir / "stereo_ve_mono_raw.json"
    print(f"[4/9] קורא נתונים מאתר סטריאו ומונו ({svm_artist or '-'})...")
    cached = _load_json_cache(cache_path, refresh)
    if cached is not None:
        print(
            f"  -> נטען מהמטמון: {len(cached.get('albums', []))} אלבומים/דפים, "
            f"{len(cached.get('songs', []))} שירים ייחודיים."
        )
        return cached
    if cache_only or not svm_artist:
        if not svm_artist:
            print("  -> דולג (אין stereo_ve_mono_artist מוגדר ב-composer.json).")
        return {"albums": [], "songs": []}

    col_ov = overrides.get("collector_overrides", {})
    skip_prefixes = tuple(col_ov.get("svm_skip_prefixes", []))
    full_credit_albums = list(col_ov.get("svm_full_credit_albums", []))
    allow_track_kws = list(col_ov.get("svm_allow_track_keywords", []))

    disco_url = f"http://stereo-ve-mono.com/discography?artist={urllib.parse.quote(svm_artist)}"
    req = urllib.request.Request(disco_url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        disco_html = resp.read().decode("utf-8", errors="replace")

    album_links: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for m in re.finditer(r'<a[^>]*href="(https?://stereo-ve-mono\.com/\d+)"[^>]*>(.*?)</a>', disco_html, re.DOTALL):
        href = m.group(1).strip()
        txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(2))).strip())
        if txt and txt != "למידע נוסף" and href not in seen_urls:
            seen_urls.add(href)
            album_links.append((href, txt))

    albums_data: list[dict[str, Any]] = []
    songs_dict: dict[str, dict[str, Any]] = {}

    for url, heading_title in album_links:
        time.sleep(0.2)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=BROWSER_HEADERS), timeout=20) as resp:
                page_html = resp.read().decode("utf-8", errors="replace")
        except Exception as exc:
            print(f"  [!] שגיאה בטעינת {url}: {exc}", file=sys.stderr)
            continue

        ed_match = re.search(r'<div class="editionDes">(.*?)</div>', page_html, re.DOTALL)
        edition_des = html.unescape(re.sub(r"<[^>]+>", "", ed_match.group(1))).strip() if ed_match else ""
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", heading_title) or re.search(r"\b(19\d{2}|20\d{2})\b", edition_des)
        year = year_match.group(1) if year_match else ""

        album_performer = ""
        if " - " in heading_title:
            album_performer = heading_title.split(" - ")[0].strip()
        elif cfg.name_he in heading_title:
            album_performer = cfg.name_he

        tracks_ul = re.search(r'<ul class="postTracks">(.*?)</ul>', page_html, re.DOTALL)
        tracks_list: list[dict[str, Any]] = []
        if tracks_ul:
            for li_html in re.findall(r"<li>(.*?)</li>", tracks_ul.group(1), re.DOTALL):
                yt_matches = re.findall(r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})", li_html)
                title_part = re.split(r"<span|<a", li_html, maxsplit=1)[0]
                title_part = html.unescape(re.sub(r"<[^>]+>", "", title_part)).strip()
                title_part = re.sub(r"^(?:[A-Da-d]?\d+|\d+)\.\s*", "", title_part).strip()
                title_part = re.sub(r"[\u200e\u200f]", "", title_part).strip()
                if not title_part or title_part.lower() == "audio":
                    continue
                if skip_prefixes and title_part.startswith(skip_prefixes):
                    continue

                track_performers: list[str] = []
                if " – " in title_part:
                    perf_part, song_part = title_part.split(" – ", 1)
                    title_part = song_part.strip()
                    for p in re.split(r"\s*,\s*|\s+ו(?=להקת|הגשש|צוות|חבורת|הפרברים|יהודית|אפרים|עופר)", perf_part.strip()):
                        p = p.strip()
                        if p and p not in track_performers:
                            track_performers.append(p)
                elif album_performer and album_performer != "לא משויכים":
                    for p in re.split(r"\s*,\s*", album_performer):
                        p = p.strip()
                        if p and p not in track_performers and p != "מבצעים שונים":
                            track_performers.append(p)

                credits_match = re.search(r"color:RoyalBlue[^>]*>(.*?)</span>", li_html, re.DOTALL)
                credits_text = html.unescape(credits_match.group(1)) if credits_match else ""
                credits_text = re.sub(r"[\u200e\u200f\xa0]", " ", credits_text)

                authors = [a.strip() for a in re.findall(r"©\s*([^♫⇄♭☚(]+)", credits_text) if a.strip()]
                composers = [c.strip() for c in re.findall(r"♫\s*([^©⇄♭☚(]+)", credits_text) if c.strip()]
                translators = [tr.strip() for tr in re.findall(r"⇄\s*([^©♫♭☚(]+)", credits_text) if tr.strip()]
                arrangers = [ar.strip() for ar in re.findall(r"♭\s*([^©♫⇄☚(]+)", credits_text) if ar.strip()]

                orig_match = re.search(r"עיין</span>\s*([^<]+)", li_html)
                orig_title = html.unescape(orig_match.group(1)).strip() if orig_match else ""

                roles: list[str] = []
                if any(cfg.name_he in a for a in authors):
                    roles.append("author")
                if any(cfg.name_he in c for c in composers):
                    roles.append("composer")
                if any(cfg.name_he in tr for tr in translators):
                    roles.append("translator")
                if any(cfg.name_he in ar for ar in arrangers):
                    roles.append("arranger")
                if any(cfg.name_he in p for p in track_performers) or heading_title == "לא משויכים":
                    if "performer" not in roles:
                        roles.append("performer")

                if not authors and not composers and not translators and heading_title != "לא משויכים":
                    if cfg.name_he in heading_title or any(fc in heading_title for fc in full_credit_albums):
                        if "author" not in roles:
                            roles.append("author")
                        if "composer" not in roles:
                            roles.append("composer")

                if (
                    heading_title != "לא משויכים"
                    and cfg.name_he not in heading_title
                    and not any(fc in heading_title for fc in full_credit_albums)
                    and not roles
                    and not any(kw in title_part for kw in allow_track_kws)
                ):
                    continue

                tracks_list.append({
                    "title": title_part,
                    "performers": track_performers,
                    "authors": authors,
                    "composers": composers,
                    "translators": translators,
                    "arrangers": arrangers,
                    "original_title": orig_title,
                    "roles": roles,
                    "youtube_ids": yt_matches,
                })

                synonym_map = overrides.get("synonym_map", {}) if isinstance(overrides, dict) else {}
                norm = normalize_catalog_song_title(title_part, synonym_map)
                if not norm:
                    continue
                s = songs_dict.setdefault(norm, {
                    "title": title_part,
                    "roles": [],
                    "authors": [],
                    "composers": [],
                    "translators": [],
                    "arrangers": [],
                    "original_title": "",
                    "performers": [],
                    "albums": [],
                    "youtube_ids": [],
                })
                for key, vals in (
                    ("roles", roles),
                    ("authors", authors),
                    ("composers", composers),
                    ("translators", translators),
                    ("arrangers", arrangers),
                    ("youtube_ids", yt_matches),
                ):
                    for item in vals:
                        if item and item not in s[key]:
                            s[key].append(item)
                if orig_title and not s["original_title"]:
                    s["original_title"] = orig_title
                for tp in track_performers:
                    if tp and tp not in s["performers"]:
                        s["performers"].append(tp)
                if heading_title != "לא משויכים" and heading_title not in s["albums"]:
                    s["albums"].append(heading_title)

        albums_data.append({
            "title": heading_title,
            "year": year,
            "performer": album_performer,
            "edition_description": edition_des,
            "url": url,
            "tracks_count": len(tracks_list),
            "tracks": tracks_list,
            "source": "stereo_ve_mono",
        })

    result = {"albums": albums_data, "songs": list(songs_dict.values())}
    _write_json_cache(cache_path, result)
    print(f"  -> הסתיים איסוף מסטריאו ומונו: {len(albums_data)} אלבומים/דפים, {len(result['songs'])} שירים ייחודיים.")
    return result


# ---------------------------------------------------------------------------
# 5. Pizmonet
# ---------------------------------------------------------------------------


def scrape_pizmonet(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect songs, chart dates, and YouTube IDs from Pizmonet wiki API."""
    synonym_map = overrides.get("synonym_map", {}) if isinstance(overrides, dict) else {}
    pz_slug = str(cfg.sources.get("pizmonet_slug") or "").strip()
    cache_path = raw_cache_dir / "pizmonet_raw.json"
    print(f"[5/9] קורא נתונים מאתר פזמונט ({pz_slug or '-'})...")
    cached = _load_json_cache(cache_path, refresh)
    if cached is not None:
        print(f"  -> נטען מהמטמון: {len(cached.get('songs', []))} שירים מפזמונט.")
        return cached
    if cache_only or not pz_slug:
        if not pz_slug:
            print("  -> דולג (אין pizmonet_slug מוגדר ב-composer.json).")
        return {"songs": []}

    def fetch_pizmonet_api(params: dict[str, str]) -> dict[str, Any]:
        query_params = dict(params, format="json")
        url = "https://pizmonet.co.il/w/api.php?" + urllib.parse.urlencode(query_params)
        req = urllib.request.Request(url, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))

    songs_dict: dict[str, dict[str, Any]] = {}

    def add_pizmonet_song(
        title: str,
        roles: list[str],
        performer: str = "",
        year: str = "",
        youtube_id: str = "",
        authors: list[str] | None = None,
        composers: list[str] | None = None,
        arrangers: list[str] | None = None,
    ) -> None:
        clean_t = clean_wiki_markup(title)
        m_paren = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", clean_t)
        if m_paren and performer and m_paren.group(2).strip() in performer:
            clean_t = m_paren.group(1).strip()
        clean_t = clean_wiki_song_title(clean_t)
        norm = normalize_catalog_song_title(clean_t, synonym_map)
        if not norm:
            return
        entry = songs_dict.setdefault(norm, {
            "title": clean_t,
            "roles": [],
            "performers": [],
            "authors": [],
            "composers": [],
            "arrangers": [],
            "year": "",
            "youtube_ids": [],
        })
        for r in roles:
            if r not in entry["roles"]:
                entry["roles"].append(r)
        if performer:
            for p in re.split(r"\s+ו|\s*,\s*", clean_wiki_markup(performer)):
                p = p.strip()
                if p and p not in entry["performers"]:
                    entry["performers"].append(p)
        if year and not entry["year"]:
            entry["year"] = year
        if youtube_id and youtube_id not in entry["youtube_ids"]:
            entry["youtube_ids"].append(youtube_id)
        for a in authors or []:
            if a and a not in entry["authors"]:
                entry["authors"].append(a)
        for c in composers or []:
            if c and c not in entry["composers"]:
                entry["composers"].append(c)
        for ar in arrangers or []:
            if ar and ar not in entry["arrangers"]:
                entry["arrangers"].append(ar)

    pz_page = pz_slug.replace(" ", "_")
    try:
        artist_data = fetch_pizmonet_api({"action": "parse", "page": pz_page, "prop": "wikitext"})
        artist_wt = artist_data.get("parse", {}).get("wikitext", {}).get("*", "")
        for tpl in re.findall(r"\{\{שיר (?:שנתי|שבועי)(.*?)\}\}", artist_wt, re.DOTALL):
            s_match = re.search(r"\|שיר=([^\n|]+)", tpl)
            p_match = re.search(r"\|ביצוע=([^\n|]+)", tpl)
            c_match = re.search(r"\|קרדיט=([^\n|]+)", tpl)
            d_match = re.search(r"\b(19\d{2}|20\d{2})\b", tpl)
            if s_match:
                s_title = clean_wiki_markup(s_match.group(1))
                perf = clean_wiki_markup(p_match.group(1)) if p_match else ""
                cred = clean_wiki_markup(c_match.group(1)) if c_match else ""
                yr = d_match.group(1) if d_match else ""
                roles: list[str] = []
                if "מילים" in cred:
                    roles.append("author")
                if "לחן" in cred:
                    roles.append("composer")
                if "תרגום" in cred:
                    roles.append("translator")
                if "ביצוע" in cred or _mentions_creator_text(perf, cfg):
                    roles.append("performer")
                add_pizmonet_song(s_title, roles, performer=perf, year=yr)
    except Exception as exc:
        print(f"  [!] אזהרה בטעינת דף פזמונט '{pz_page}': {exc}", file=sys.stderr)

    pz_cat = str(cfg.sources.get("pizmonet_category") or f"קטגוריה:שירי_{pz_page}").strip()
    try:
        cat_pages = fetch_pizmonet_api({
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "generator": "categorymembers",
            "gcmtitle": pz_cat,
            "gcmlimit": "500",
        })
        for _pid, page_obj in (cat_pages.get("query", {}).get("pages") or {}).items():
            p_title = page_obj.get("title", "")
            wt = (page_obj.get("revisions") or [{}])[0].get("*", "")
            perf_m = re.search(r"\|ביצוע=([^\n|]+)", wt)
            lyr_m = re.search(r"\|מילים=([^\n|]+)", wt)
            comp_m = re.search(r"\|לחן=([^\n|]+)", wt)
            arr_m = re.search(r"\|עיבוד=([^\n|]+)", wt)
            yt_m = re.search(r"<youtube[^>]*>([A-Za-z0-9_-]{11})</youtube>", wt)
            yr_m = re.search(r"\b(19\d{2}|20\d{2})\b", wt)

            perf_str = clean_wiki_markup(perf_m.group(1)) if perf_m else ""
            lyr_str = clean_wiki_markup(lyr_m.group(1)) if lyr_m else ""
            comp_str = clean_wiki_markup(comp_m.group(1)) if comp_m else ""
            arr_str = clean_wiki_markup(arr_m.group(1)) if arr_m else ""
            yt_id = yt_m.group(1).strip() if yt_m else ""
            yr_str = yr_m.group(1) if yr_m else ""

            roles = []
            if _mentions_creator_text(lyr_str, cfg):
                roles.append("author")
            if _mentions_creator_text(comp_str, cfg):
                roles.append("composer")
            if _mentions_creator_text(perf_str, cfg):
                roles.append("performer")
            if _mentions_creator_text(arr_str, cfg):
                roles.append("arranger")

            add_pizmonet_song(
                title=p_title,
                roles=roles,
                performer=perf_str,
                year=yr_str,
                youtube_id=yt_id,
                authors=[lyr_str] if lyr_str else [],
                composers=[comp_str] if comp_str else [],
                arrangers=[arr_str] if arr_str else [],
            )
    except Exception as exc:
        print(f"  [!] אזהרה בטעינת קטגוריית פזמונט '{pz_cat}': {exc}", file=sys.stderr)

    result = {"songs": list(songs_dict.values())}
    _write_json_cache(cache_path, result)
    print(f"  -> הסתיים איסוף מפזמונט: {len(result['songs'])} שירים ייחודיים (כולל מזהי יוטיוב).")
    return result


# ---------------------------------------------------------------------------
# 6. Zemereshet
# ---------------------------------------------------------------------------


def scrape_zemereshet(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect early Hebrew songs from Zemereshet for `sources.zemereshet_artist_id`."""
    del overrides
    zem_id = cfg.sources.get("zemereshet_artist_id")
    cache_path = raw_cache_dir / "zemereshet_raw.json"
    print(f"[6/9] קורא נתונים מאתר זמרשת (id={zem_id or '-'})...")
    cached = _load_json_cache(cache_path, refresh)
    if cached is not None:
        print(f"  -> נטען מהמטמון: {len(cached.get('songs', []))} שירים מזמרשת.")
        return cached
    if cache_only or not zem_id:
        if not zem_id:
            print("  -> דולג (אין zemereshet_artist_id מוגדר ב-composer.json).")
        return {"songs": []}

    artist_url = f"https://www.zemereshet.co.il/artist.asp?id={zem_id}"
    with urllib.request.urlopen(urllib.request.Request(artist_url, headers=BROWSER_HEADERS), timeout=20) as resp:
        artist_html = resp.read().decode("utf-8", errors="replace")

    song_links: dict[str, str] = {}
    for m in re.finditer(r'href="(song\.asp\?id=(\d+))"[^>]*>(.*?)</a>', artist_html, re.DOTALL):
        sid = m.group(2)
        title = html.unescape(re.sub(r"<[^>]+>", "", m.group(3))).strip()
        if title and sid not in song_links:
            song_links[sid] = title

    songs_list: list[dict[str, Any]] = []
    escaped_name = re.escape(cfg.name_he)
    for sid, title in song_links.items():
        time.sleep(0.25)
        s_url = f"https://www.zemereshet.co.il/song.asp?id={sid}"
        with urllib.request.urlopen(urllib.request.Request(s_url, headers=BROWSER_HEADERS), timeout=20) as resp:
            s_html = resp.read().decode("utf-8", errors="replace")
        roles: list[str] = []
        if re.search(rf"מילים:.*?{escaped_name}", s_html, re.DOTALL) or f"מילים ולחן: {cfg.name_he}" in s_html:
            roles.append("author")
        if re.search(rf"לחן:.*?{escaped_name}", s_html, re.DOTALL) or f"מילים ולחן: {cfg.name_he}" in s_html:
            roles.append("composer")
        if not roles:
            roles = ["author", "composer"]
        songs_list.append({
            "zemereshet_id": sid,
            "title": title,
            "url": s_url,
            "roles": roles,
            "source": "zemereshet",
        })

    result = {"songs": songs_list}
    _write_json_cache(cache_path, result)
    print(f"  -> הסתיים איסוף מזמרשת: {len(songs_list)} שירים.")
    return result


# ---------------------------------------------------------------------------
# 7. Discogs
# ---------------------------------------------------------------------------


def scrape_discogs(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect Discogs releases and Hebrew tracklist entries for `sources.discogs_artist_id`."""
    discogs_id = cfg.sources.get("discogs_artist_id")
    cache_path = raw_cache_dir / "discogs_raw.json"
    print(f"[7/9] קורא נתונים מ-Discogs API (artist={discogs_id or '-'})...")

    if not discogs_id:
        cached = _load_json_cache(cache_path, refresh)
        if cached is not None:
            return cached
        print("  -> דולג (אין discogs_artist_id מוגדר ב-composer.json).")
        return {"releases": [], "songs": []}

    col_ov = overrides.get("collector_overrides", {})
    skip_rel_ids = {str(x) for x in col_ov.get("discogs_skip_release_ids", [])}
    skip_tracks = set(col_ov.get("discogs_skip_track_titles", [])) | {"אוברטורה", "Overture (אוברטורה)"}

    ua_prefix = "".join(part.capitalize() for part in cfg.slug.split("-") if part) or "Composer"
    discogs_headers = {
        "User-Agent": f"{ua_prefix}ComprehensiveCatalog/1.0 +https://discogs.com",
        "Accept": "application/json",
    }

    detailed_releases: list[dict[str, Any]] = []
    cached = _load_json_cache(cache_path, refresh)
    if cached is not None:
        detailed_releases = cached.get("releases", [])

    if not detailed_releases:
        if cache_only:
            return {"releases": [], "songs": []}
        url = f"https://api.discogs.com/artists/{discogs_id}/releases?per_page=100&page=1"
        req = urllib.request.Request(url, headers=discogs_headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for rel in [r for r in data.get("releases", []) if r.get("role") == "Main"]:
            rel_id = rel.get("id")
            rel_type = rel.get("type", "release")
            detailed_releases.append({
                "id": rel_id,
                "type": rel_type,
                "title": (rel.get("title") or "").strip(),
                "year": str(rel.get("year") or ""),
                "artist": (rel.get("artist") or cfg.name_he).replace("*", "").strip(),
                "tracks_count": 0,
                "tracks": [],
                "url": f"https://www.discogs.com/{rel_type}/{rel_id}",
                "source": "discogs",
            })

    missing_releases = [rel for rel in detailed_releases if not rel.get("tracks")]
    if missing_releases and not cache_only:
        print(f"  -> משלים רשימות שירים מ-Discogs עבור {len(missing_releases)} אלבומים...")
        for rel in missing_releases:
            rel_id = rel["id"]
            rel_type = rel["type"]
            resource_url = f"https://api.discogs.com/{rel_type}s/{rel_id}"
            for attempt in range(4):
                time.sleep(1.5)
                try:
                    with urllib.request.urlopen(urllib.request.Request(resource_url, headers=discogs_headers), timeout=20) as rr:
                        rel_detail = json.loads(rr.read().decode("utf-8"))
                        tracks = [(t.get("title") or "").strip() for t in (rel_detail.get("tracklist") or []) if (t.get("title") or "").strip()]
                        rel["tracks"] = tracks
                        rel["tracks_count"] = len(tracks)
                        break
                except urllib.error.HTTPError as exc:
                    if exc.code == 429 and attempt < 3:
                        time.sleep(15.0 * (attempt + 1))
                        continue
                    print(f"  [!] אזהרה: לא ניתן לשלוף פירוט Discogs עבור {rel['title']}: {exc}", file=sys.stderr)
                    break
                except Exception as exc:
                    print(f"  [!] אזהרה: לא ניתן לשלוף פירוט Discogs עבור {rel['title']}: {exc}", file=sys.stderr)
                    break

    discogs_smap = overrides.get("synonym_map", {}) if isinstance(overrides, dict) else {}
    songs_dict: dict[str, dict[str, Any]] = {}
    for rel in detailed_releases:
        if str(rel.get("id")) in skip_rel_ids:
            continue
        rel_title = rel["title"]
        rel_artist = rel["artist"]
        for raw_t in rel.get("tracks") or []:
            t_title = raw_t.strip()
            orig_t = ""
            if " = " in t_title:
                parts = [p.strip() for p in t_title.split(" = ")]
                heb_parts = [p for p in parts if any("\u0590" <= c <= "\u05FF" for c in p)]
                if heb_parts:
                    t_title = heb_parts[0]
            m_bilingual = re.match(r"^([A-Za-z0-9\s',?!.-]+)\(([\u0590-\u05FF][^)]+)\)$", t_title)
            if m_bilingual:
                orig_t = m_bilingual.group(1).strip()
                t_title = m_bilingual.group(2).strip()
            if t_title in skip_tracks:
                continue
            if any("\u0590" <= c <= "\u05FF" for c in t_title):
                norm = normalize_catalog_song_title(t_title, discogs_smap)
                if norm:
                    s = songs_dict.setdefault(norm, {
                        "title": t_title,
                        "original_title": orig_t,
                        "albums": [],
                        "performers": [],
                    })
                    if orig_t and not s.get("original_title"):
                        s["original_title"] = orig_t
                    if rel_title and rel_title not in s["albums"]:
                        s["albums"].append(rel_title)
                    if rel_artist and rel_artist not in s["performers"]:
                        s["performers"].append(rel_artist)

    result = {"releases": detailed_releases, "songs": list(songs_dict.values())}
    if not cache_only:
        _write_json_cache(cache_path, result)
    print(f"  -> הסתיים איסוף מ-Discogs: {len(detailed_releases)} אלבומים, {len(result['songs'])} שירים בעברית.")
    return result


# ---------------------------------------------------------------------------
# 8. MusicBrainz
# ---------------------------------------------------------------------------


def scrape_musicbrainz(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect MusicBrainz releases and Hebrew works for `sources.musicbrainz_artist_id`."""
    mb_smap = overrides.get("synonym_map", {}) if isinstance(overrides, dict) else {}
    mb_id = str(cfg.sources.get("musicbrainz_artist_id") or "").strip()
    cache_path = raw_cache_dir / "musicbrainz_raw.json"
    print(f"[8/9] קורא נתונים מ-MusicBrainz API (mbid={mb_id or '-'})...")
    cached = _load_json_cache(cache_path, refresh)
    if cached is not None:
        print(
            f"  -> נטען מהמטמון: {len(cached.get('releases', []))} אלבומים מ-MusicBrainz, "
            f"{len(cached.get('songs', []))} שירים."
        )
        return cached
    if cache_only or not mb_id:
        if not mb_id:
            print("  -> דולג (אין musicbrainz_artist_id מוגדר ב-composer.json).")
        return {"releases": [], "songs": []}

    ua_prefix = "".join(part.capitalize() for part in cfg.slug.split("-") if part) or "Composer"
    mb_headers = {
        "User-Agent": f"{ua_prefix}ComprehensiveCatalog/1.0 (https://musicbrainz.org)",
        "Accept": "application/json",
    }

    rel_url = f"https://musicbrainz.org/ws/2/release?artist={urllib.parse.quote(mb_id)}&inc=recordings&limit=100&fmt=json"
    with urllib.request.urlopen(urllib.request.Request(rel_url, headers=mb_headers), timeout=20) as resp:
        rel_data = json.loads(resp.read().decode("utf-8"))

    time.sleep(1.1)
    work_url = f"https://musicbrainz.org/ws/2/work?artist={urllib.parse.quote(mb_id)}&limit=100&fmt=json"
    with urllib.request.urlopen(urllib.request.Request(work_url, headers=mb_headers), timeout=20) as resp:
        work_data = json.loads(resp.read().decode("utf-8"))

    releases_list: list[dict[str, Any]] = []
    songs_dict: dict[str, dict[str, Any]] = {}

    for rel in rel_data.get("releases") or []:
        r_id = rel.get("id", "")
        r_title = (rel.get("title") or "").strip()
        r_date = (rel.get("date") or "")[:4]
        tracks: list[str] = []
        for med in rel.get("media") or []:
            for tr in med.get("tracks") or []:
                t_title = (tr.get("title") or "").strip()
                if t_title:
                    tracks.append(t_title)
                    if any("\u0590" <= c <= "\u05FF" for c in t_title):
                        norm = normalize_catalog_song_title(t_title, mb_smap)
                        if norm:
                            s = songs_dict.setdefault(norm, {"title": t_title, "albums": []})
                            if r_title and r_title not in s["albums"]:
                                s["albums"].append(r_title)
        releases_list.append({
            "id": r_id,
            "title": r_title,
            "year": r_date,
            "tracks_count": len(tracks),
            "tracks": tracks,
            "url": f"https://musicbrainz.org/release/{r_id}",
            "source": "musicbrainz",
        })

    for w in work_data.get("works") or []:
        w_title = (w.get("title") or "").strip()
        if any("\u0590" <= c <= "\u05FF" for c in w_title):
            norm = normalize_catalog_song_title(w_title, mb_smap)
            if norm:
                songs_dict.setdefault(norm, {"title": w_title, "albums": []})

    result = {"releases": releases_list, "songs": list(songs_dict.values())}
    _write_json_cache(cache_path, result)
    print(f"  -> הסתיים איסוף מ-MusicBrainz: {len(releases_list)} אלבומים, {len(result['songs'])} שירים ייחודיים.")
    return result


# ---------------------------------------------------------------------------
# 9. National Library of Israel (NLI SRU MARC21 API)
# ---------------------------------------------------------------------------


def fetch_nli_sru_records(query: str) -> list[ET.Element]:
    """Retrieve all paginated MARCXML records from NLI SRU API."""
    records: list[ET.Element] = []
    start_record = 1
    batch_size = 50
    while True:
        params = {
            "version": "1.2",
            "operation": "searchRetrieve",
            "recordSchema": "marcxml",
            "query": query,
            "maximumRecords": str(batch_size),
            "startRecord": str(start_record),
        }
        url = NLI_SRU_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=25) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        batch = root.findall(".//marc:record", NLI_NS)
        records.extend(batch)
        next_pos_txt = root.findtext("srw:nextRecordPosition", namespaces=NLI_NS)
        if not next_pos_txt or not batch:
            break
        next_pos = int(next_pos_txt)
        if next_pos <= start_record:
            break
        start_record = next_pos
        time.sleep(0.2)
    return records


def format_nli_person_name(raw_name: str) -> str:
    """Convert MARC 'Last, First,' format into 'First Last'."""
    name = raw_name.strip().rstrip(",.")
    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            return f"{parts[1]} {parts[0]}"
    return name


def scrape_nli(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    raw_cache_dir: Path,
    *,
    cache_only: bool = False,
    refresh: bool = False,
) -> dict[str, Any]:
    """Collect Beit LaZemer / National Sound Archive / personal archive records from NLI."""
    nli_author = str(cfg.sources.get("nli_author") or "").strip()
    archive_queries = list(cfg.sources.get("nli_archive_queries") or [])
    cache_path = raw_cache_dir / "nli_raw.json"
    print(f"[9/9] קורא נתונים מהספרייה הלאומית ({nli_author or cfg.name_he})...")
    cached = _load_json_cache(cache_path, refresh)
    if cached is not None:
        print(
            f"  -> נטען מהמטמון: {len(cached.get('songs', []))} שירים/דפי שיר, "
            f"{len(cached.get('albums', []))} אלבומים מהספרייה הלאומית."
        )
        return cached
    if cache_only or (not nli_author and not archive_queries):
        if not nli_author and not archive_queries:
            print("  -> דולג (אין הגדרות NLI ב-composer.json).")
        return {"songs": [], "albums": [], "dafshir_count": 0, "archive_count": 0}

    nli_inv = cfg.nli_creator_inverted
    col_ov = overrides.get("collector_overrides", {})
    non_song_titles = set(col_ov.get("nli_non_song_titles", []))
    skip_prefixes = tuple(col_ov.get("nli_skip_prefixes", []))

    dafshir_records: list[ET.Element] = []
    album_records: list[ET.Element] = []
    if nli_author:
        print("  -> שולף דפי שיר (DAFSHIR) מבית לזמר העברי בספרייה הלאומית...")
        dafshir_records = fetch_nli_sru_records(f'alma.creator="{nli_inv}" AND alma.local_field_999="DAFSHIR"')
        print(f"  -> נשלפו {len(dafshir_records)} דפי שיר רשמיים (DAFSHIR).")

        print("  -> שולף אלבומים מארכיון הצליל הלאומי בספרייה הלאומית...")
        album_records = fetch_nli_sru_records(f'alma.creator="{nli_inv}" AND alma.local_notes="Album_Ana_Digi"')
        print(f"  -> נשלפו {len(album_records)} אלבומים מארכיון הצליל הלאומי.")

    archive_records: list[ET.Element] = []
    for aq in archive_queries:
        archive_records.extend(fetch_nli_sru_records(aq))
    if archive_queries:
        print(f"  -> נשלפו {len(archive_records)} רשומות מארכיון היוצר.")

    songs_dict: dict[str, dict[str, Any]] = {}

    def clean_nli_text(s: str) -> str:
        s = NIKUD_RE.sub("", s)
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"[\s/:;,.]+$", "", s).strip()
        s = re.sub(
            r"\s*\((?:[^)]*(?:כתב יד|טקסט בלבד|דפוס|צילום|טיוטה|הדפסה|נוסח|סקיצה|עברית|אנגלית|אמהרית|יידיש|צרפתית|manuscript|arrangement|arrangment)[^)]*)\)\s*$",
            "",
            s,
            flags=re.I,
        ).strip()
        return re.sub(r"[\s/:;,.]+$", "", s).strip()

    def process_nli_song_record(rec: ET.Element, is_dafshir: bool) -> None:
        mms_id = rec.findtext('marc:controlfield[@tag="001"]', default="", namespaces=NLI_NS).strip()
        f008 = rec.findtext('marc:controlfield[@tag="008"]', default="", namespaces=NLI_NS)
        year = ""
        if len(f008) >= 11 and f008[7:11].isdigit():
            yr_num = int(f008[7:11])
            if 1920 <= yr_num <= 2030:
                year = str(yr_num)

        f245 = rec.find('marc:datafield[@tag="245"]', NLI_NS)
        if f245 is None:
            return
        raw_title = (f245.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "").strip()
        raw_title = clean_nli_text(raw_title)
        if not raw_title or raw_title.isdigit():
            return
        if (raw_title.startswith("[") and raw_title.endswith("]")) or raw_title in non_song_titles:
            return
        if skip_prefixes and raw_title.startswith(skip_prefixes):
            return
        if not is_dafshir and not any("\u0590" <= c <= "\u05FF" for c in raw_title):
            return

        m_num = re.match(r"^(\d+)\s+([\u0590-\u05FF].*)$", raw_title)
        if m_num:
            raw_title = f"{m_num.group(2)} {m_num.group(1)}"

        orig_title = ""
        f240 = rec.find('marc:datafield[@tag="240"]', NLI_NS)
        if f240 is not None:
            orig_title = (f240.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "").strip().rstrip(".")

        alt_titles: list[str] = []
        opening_line = ""
        for f246 in rec.findall('marc:datafield[@tag="246"]', NLI_NS):
            i_code = (f246.findtext('marc:subfield[@code="i"]', default="", namespaces=NLI_NS) or "").strip()
            a_val = clean_nli_text(f246.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "")
            if not a_val:
                continue
            if "אתחלתא" in i_code:
                opening_line = a_val
            elif "פזמון" not in i_code:
                if any("\u0590" <= c <= "\u05FF" for c in a_val):
                    alt_titles.append(a_val)
                elif not orig_title:
                    orig_title = a_val

        notes = ""
        f520 = rec.find('marc:datafield[@tag="520"]', NLI_NS)
        if f520 is not None:
            notes = (f520.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "").strip()
        if "פרודיה על השיר" in notes:
            return

        acum_ids = [
            b_val
            for f985 in rec.findall('marc:datafield[@tag="985"]', NLI_NS)
            for b_val in [(f985.findtext('marc:subfield[@code="b"]', default="", namespaces=NLI_NS) or "").strip()]
            if b_val
        ]
        source_books = [
            c_val
            for f593 in rec.findall('marc:datafield[@tag="593"]', NLI_NS)
            for c_val in [(f593.findtext('marc:subfield[@code="c"]', default="", namespaces=NLI_NS) or "").strip(" []")]
            if c_val
        ]

        authors: list[str] = []
        composers: list[str] = []
        translators: list[str] = []
        arrangers: list[str] = []
        performers: list[str] = []
        roles: list[str] = []

        for tag in ("100", "700", "110", "710"):
            for df in rec.findall(f'marc:datafield[@tag="{tag}"]', NLI_NS):
                if df.findtext('marc:subfield[@code="9"]', default="", namespaces=NLI_NS) == "lat":
                    continue
                raw_person = df.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or ""
                person = format_nli_person_name(raw_person)
                if not person:
                    continue
                relators = [(s.text or "").strip() for s in df.findall('marc:subfield[@code="e"]', NLI_NS) if s.text]
                is_creator = cfg.name_he in person or nli_inv in raw_person
                for rel in relators:
                    if "מחבר" in rel or "משורר" in rel:
                        if person not in authors:
                            authors.append(person)
                        if is_creator and "author" not in roles:
                            roles.append("author")
                    elif "מלחין" in rel:
                        if person not in composers:
                            composers.append(person)
                        if is_creator and "composer" not in roles:
                            roles.append("composer")
                    elif "מתרגם" in rel:
                        if person not in translators:
                            translators.append(person)
                        if is_creator and "translator" not in roles:
                            roles.append("translator")
                    elif "מעבד" in rel:
                        if person not in arrangers:
                            arrangers.append(person)
                        if is_creator and "arranger" not in roles:
                            roles.append("arranger")
                    elif "מבצע" in rel or "זמר" in rel:
                        if person not in performers:
                            performers.append(person)
                        if is_creator and "performer" not in roles:
                            roles.append("performer")

        if not roles:
            return
        if not is_dafshir and not composers and "translator" not in roles and "composer" not in roles and "arranger" not in roles:
            return

        nli_smap = overrides.get("synonym_map", {}) if isinstance(overrides, dict) else {}
        norm = normalize_catalog_song_title(raw_title, nli_smap)
        if not norm:
            return
        entry = songs_dict.setdefault(norm, {
            "title": raw_title,
            "alt_titles": [],
            "original_title": "",
            "year": "",
            "roles": [],
            "authors": [],
            "composers": [],
            "translators": [],
            "arrangers": [],
            "performers": [],
            "albums": [],
            "acum_work_ids": [],
            "nli_mms_ids": [],
            "opening_line": "",
            "notes": "",
            "is_dafshir": is_dafshir,
        })
        if is_dafshir:
            entry["is_dafshir"] = True
        if mms_id and mms_id not in entry["nli_mms_ids"]:
            entry["nli_mms_ids"].append(mms_id)
        for wid in acum_ids:
            if wid not in entry["acum_work_ids"]:
                entry["acum_work_ids"].append(wid)
        for at in alt_titles:
            if at not in entry["alt_titles"] and at != entry["title"]:
                entry["alt_titles"].append(at)
        if orig_title and not entry["original_title"]:
            entry["original_title"] = orig_title
        if year and not entry["year"]:
            entry["year"] = year
        if opening_line and not entry["opening_line"]:
            entry["opening_line"] = opening_line
        if notes and not entry["notes"]:
            entry["notes"] = notes
        for key, vals in (
            ("roles", roles),
            ("authors", authors),
            ("composers", composers),
            ("translators", translators),
            ("arrangers", arrangers),
            ("performers", performers),
            ("albums", source_books),
        ):
            for v in vals:
                if v and v not in entry[key]:
                    entry[key].append(v)

    for rec in dafshir_records:
        process_nli_song_record(rec, is_dafshir=True)
    for rec in archive_records:
        process_nli_song_record(rec, is_dafshir=False)

    nli_albums: list[dict[str, Any]] = []
    for rec in album_records:
        mms_id = rec.findtext('marc:controlfield[@tag="001"]', default="", namespaces=NLI_NS).strip()
        f245 = rec.find('marc:datafield[@tag="245"]', NLI_NS)
        if f245 is None:
            continue
        a_part = (f245.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "").strip(" /:")
        b_part = (f245.findtext('marc:subfield[@code="b"]', default="", namespaces=NLI_NS) or "").strip(" /:")
        full_title = f"{a_part}: {b_part}" if b_part else a_part
        f260 = rec.find('marc:datafield[@tag="260"]', NLI_NS) or rec.find('marc:datafield[@tag="264"]', NLI_NS)
        yr = ""
        if f260 is not None:
            c_txt = f260.findtext('marc:subfield[@code="c"]', default="", namespaces=NLI_NS) or ""
            m_yr = re.search(r"\b(19\d{2}|20\d{2})\b", c_txt)
            if m_yr:
                yr = m_yr.group(1)
        nli_albums.append({
            "mms_id": mms_id,
            "title": full_title,
            "year": yr,
            "type": "אלבום/הקלטה (ארכיון הצליל הלאומי - הספרייה הלאומית)",
            "performer": f"{cfg.name_he} / אמנים שונים",
            "url": f"https://www.nli.org.il/he/items/NNL_MUSIC_AL{mms_id}",
            "source": "nli",
        })

    result = {
        "songs": list(songs_dict.values()),
        "albums": nli_albums,
        "dafshir_count": len(dafshir_records),
        "archive_count": len(archive_records),
    }
    _write_json_cache(cache_path, result)
    print(
        f"  -> הסתיים איסוף מהספרייה הלאומית: {len(result['songs'])} שירים ייחודיים "
        f"({len(dafshir_records)} דפי שיר + {len(archive_records)} פריטי ארכיון), "
        f"{len(nli_albums)} אלבומים."
    )
    return result


# ---------------------------------------------------------------------------
# 10. Unified Catalog Merge & Output Writers
# ---------------------------------------------------------------------------


def build_unified_catalog(
    cfg: ComposerConfig,
    overrides: dict[str, Any],
    *,
    wiki_data: dict[str, Any],
    shironet_data: dict[str, Any],
    acum_data: dict[str, Any],
    svm_data: dict[str, Any],
    pizmonet_data: dict[str, Any],
    zemereshet_data: dict[str, Any],
    discogs_data: dict[str, Any],
    mb_data: dict[str, Any],
    nli_data: dict[str, Any],
) -> dict[str, Any]:
    """Deduplicate, normalize, and merge all 9 source payloads into a unified catalog."""
    synonym_map: dict[str, str] = dict(overrides.get("synonym_map", {}))
    excluded_songs: set[str] = set(overrides.get("excluded_normalized_songs", []))
    col_ov = overrides.get("collector_overrides", {})

    skip_shironet_wrkids = {str(x) for x in col_ov.get("shironet_skip_wrkids", [])}
    bad_performers = set(col_ov.get("bad_performers", []))
    bad_albums = set(col_ov.get("bad_albums", []))
    bad_yt_ids = set(overrides.get("bad_video_ids", {}).keys()) | set(col_ov.get("extra_bad_yt_ids", []))
    rare_vocal_songs = set(col_ov.get("creator_rare_vocal_songs", []))
    extra_alt_titles: dict[str, list[str]] = dict(col_ov.get("extra_alt_titles", {}))
    extra_yt_ids: dict[str, list[str]] = dict(col_ov.get("extra_youtube_ids", {}))
    extra_primary_perfs: dict[str, list[str]] = dict(col_ov.get("extra_primary_performers", {}))
    late_cover_markers = tuple(col_ov.get("late_cover_performer_markers", []))
    exclude_song_perfs: dict[str, list[str]] = dict(col_ov.get("exclude_song_performers", {}))
    bad_creators = set(col_ov.get("bad_creators", []))
    creator_overrides: dict[str, Any] = dict(col_ov.get("creator_overrides", {}))

    unified_songs: dict[str, dict[str, Any]] = {}

    def get_or_create_song(title: str) -> dict[str, Any] | None:
        norm = normalize_catalog_song_title(title, synonym_map)
        if not norm or norm in excluded_songs:
            return None
        if not any("\u0590" <= c <= "\u05FF" for c in norm):
            return None
        clean_t = NIKUD_RE.sub("", title).strip()
        raw_clean = _strip_punct_compact(clean_t)
        canonical_t = synonym_map.get(raw_clean, clean_t)
        if norm not in unified_songs:
            alt_list = [clean_t] if clean_t and clean_t != canonical_t else []
            unified_songs[norm] = {
                "normalized_key": norm,
                "title": canonical_t,
                "alt_titles": alt_list,
                "english_title": "",
                "original_title": "",
                "year": "",
                "sources": [],
                "roles": [],
                "authors": [],
                "composers": [],
                "translators": [],
                "arrangers": [],
                "performers": [],
                "albums": [],
                "acum_work_ids": [],
                "acum_versions_count": 0,
                "shironet_wrkids": [],
                "shironet_urls": [],
                "nli_mms_ids": [],
                "opening_line": "",
                "notes": [],
                "youtube_ids": [],
                "wiki_details": [],
            }
        else:
            existing = unified_songs[norm]
            if clean_t and clean_t != existing["title"] and clean_t not in existing["alt_titles"]:
                existing["alt_titles"].append(clean_t)
        return unified_songs[norm]

    def _extend_unique(target: list[Any], items: list[Any]) -> None:
        for it in items:
            if it and it not in target:
                target.append(it)

    # 1. Wikipedia
    for ws in wiki_data.get("songs", []):
        entry = get_or_create_song(ws["title"])
        if not entry:
            continue
        _extend_unique(entry["sources"], ["wikipedia"])
        _extend_unique(entry["roles"], ws.get("roles", []))
        if ws.get("original_title") and not entry["original_title"]:
            entry["original_title"] = ws["original_title"]
        _extend_unique(entry["performers"], ws.get("performers", []))
        _extend_unique(entry["albums"], ws.get("albums", []))
        if ws.get("lyricist") and ws["lyricist"] not in entry["authors"]:
            entry["authors"].append(ws["lyricist"])
        _extend_unique(entry["wiki_details"], ws.get("wiki_sources", []))

    # 2. Shironet
    for ss in shironet_data.get("songs", []):
        wrkids = [str(x) for x in ss.get("wrkids", [])]
        if wrkids and skip_shironet_wrkids and set(wrkids) <= skip_shironet_wrkids:
            continue
        entry = get_or_create_song(ss["title"])
        if not entry:
            continue
        _extend_unique(entry["sources"], ["shironet"])
        _extend_unique(entry["roles"], ss.get("roles", []))
        _extend_unique(entry["shironet_wrkids"], ss.get("wrkids", []))
        _extend_unique(entry["shironet_urls"], ss.get("urls", []))
        _extend_unique(entry["albums"], ss.get("albums", []))

    # 3. ACUM
    for aw in acum_data.get("works", []):
        title = aw.get("title_heb") or aw.get("title_eng") or ""
        entry = get_or_create_song(title)
        if not entry:
            continue
        _extend_unique(entry["sources"], ["acum"])
        if aw.get("title_heb") and not any("\u0590" <= c <= "\u05FF" for c in entry["title"]):
            entry["title"] = aw["title_heb"]
        if aw.get("title_eng") and not entry["english_title"]:
            entry["english_title"] = aw["title_eng"]
        if aw.get("original_title") and not entry["original_title"]:
            entry["original_title"] = aw["original_title"]
        if aw.get("publication_date") and not entry["year"]:
            entry["year"] = aw["publication_date"]
        for field in ("roles", "authors", "composers", "translators", "arrangers", "performers", "albums", "youtube_ids"):
            _extend_unique(entry[field], aw.get(field, []))
        if aw.get("work_id") and aw["work_id"] not in entry["acum_work_ids"]:
            entry["acum_work_ids"].append(aw["work_id"])
        entry["acum_versions_count"] += int(aw.get("versions_count", 0) or 0)

    # 4. Stereo ve Mono
    for svs in svm_data.get("songs", []):
        entry = get_or_create_song(svs["title"])
        if not entry:
            continue
        _extend_unique(entry["sources"], ["stereo_ve_mono"])
        for field in ("roles", "authors", "composers", "translators", "arrangers", "performers", "albums", "youtube_ids"):
            _extend_unique(entry[field], svs.get(field, []))
        if svs.get("original_title") and not entry["original_title"]:
            entry["original_title"] = svs["original_title"]

    # 5. Pizmonet
    for pzs in pizmonet_data.get("songs", []):
        entry = get_or_create_song(pzs["title"])
        if not entry:
            continue
        _extend_unique(entry["sources"], ["pizmonet"])
        if pzs.get("year") and not entry["year"]:
            entry["year"] = pzs["year"]
        for field in ("roles", "performers", "authors", "composers", "arrangers", "youtube_ids"):
            _extend_unique(entry[field], pzs.get(field, []))

    # 6. Zemereshet
    for zms in zemereshet_data.get("songs", []):
        entry = get_or_create_song(zms["title"])
        if not entry:
            continue
        _extend_unique(entry["sources"], ["zemereshet"])
        _extend_unique(entry["roles"], zms.get("roles", []))

    # 7. Discogs
    creator_discogs_tokens = [cfg.name_he, cfg.name_en, *cfg.creator_aliases]
    for ds in discogs_data.get("songs", []):
        norm = normalize_catalog_song_title(ds["title"], synonym_map)
        is_creator_solo = any(any(tok in p for tok in creator_discogs_tokens if tok) for p in ds.get("performers", []))
        if norm not in unified_songs and not is_creator_solo:
            continue
        entry = get_or_create_song(ds["title"])
        if not entry:
            continue
        _extend_unique(entry["sources"], ["discogs"])
        _extend_unique(entry["albums"], ds.get("albums", []))
        _extend_unique(entry["performers"], ds.get("performers", []))

    # 8. MusicBrainz
    for mbs in mb_data.get("songs", []):
        norm = normalize_catalog_song_title(mbs["title"], synonym_map)
        if norm not in unified_songs:
            continue
        entry = get_or_create_song(mbs["title"])
        if not entry:
            continue
        _extend_unique(entry["sources"], ["musicbrainz"])
        _extend_unique(entry["albums"], mbs.get("albums", []))

    # 9. National Library of Israel (NLI)
    alt_to_norm: dict[str, str] = {}
    acum_id_to_norm: dict[str, str] = {}
    for k_norm, s_ent in unified_songs.items():
        alt_to_norm[k_norm] = k_norm
        for at in s_ent.get("alt_titles", []):
            nat = normalize_catalog_song_title(at, synonym_map)
            if nat and nat not in alt_to_norm:
                alt_to_norm[nat] = k_norm
        for wid in s_ent.get("acum_work_ids", []):
            if wid:
                acum_id_to_norm[wid] = k_norm

    for nlis in nli_data.get("songs", []):
        matched_norm = None
        for wid in nlis.get("acum_work_ids", []):
            if wid in acum_id_to_norm:
                matched_norm = acum_id_to_norm[wid]
                break
        if not matched_norm:
            for cand in [nlis["title"]] + nlis.get("alt_titles", []):
                nc = normalize_catalog_song_title(cand, synonym_map)
                if nc and nc in alt_to_norm:
                    matched_norm = alt_to_norm[nc]
                    break
        if matched_norm and matched_norm in unified_songs:
            entry = unified_songs[matched_norm]
            clean_t = NIKUD_RE.sub("", nlis["title"]).strip()
            if clean_t and clean_t != entry["title"] and clean_t not in entry["alt_titles"]:
                entry["alt_titles"].append(clean_t)
        else:
            preferred_title = nlis["title"]
            for alt in nlis.get("alt_titles", []):
                if len(alt.split()) == len(preferred_title.split()) and len(alt) > len(preferred_title):
                    preferred_title = alt
                    break
            entry = get_or_create_song(preferred_title)
            if entry and preferred_title != nlis["title"]:
                clean_orig = NIKUD_RE.sub("", nlis["title"]).strip()
                if clean_orig and clean_orig != entry["title"] and clean_orig not in entry["alt_titles"]:
                    entry["alt_titles"].append(clean_orig)
        if not entry:
            continue
        _extend_unique(entry["sources"], ["nli"])
        if nlis.get("year") and not entry["year"]:
            entry["year"] = nlis["year"]
        if nlis.get("original_title") and not entry["original_title"]:
            entry["original_title"] = nlis["original_title"]
        if nlis.get("opening_line") and not entry["opening_line"]:
            entry["opening_line"] = nlis["opening_line"]
        for alt in nlis.get("alt_titles", []):
            clean_alt = NIKUD_RE.sub("", alt).strip()
            if clean_alt and clean_alt != entry["title"] and clean_alt not in entry["alt_titles"]:
                entry["alt_titles"].append(clean_alt)
        for field in ("roles", "authors", "composers", "translators", "arrangers", "performers", "albums", "acum_work_ids", "nli_mms_ids"):
            _extend_unique(entry[field], nlis.get(field, []))
        note_val = nlis.get("notes", "")
        if isinstance(note_val, str) and note_val:
            _extend_unique(entry["notes"], [note_val])
        elif isinstance(note_val, list):
            _extend_unique(entry["notes"], note_val)

    # Post-merge cleanup and curation overrides
    acum_rev_name = cfg.creator_acum_reversed_name
    for s_ent in unified_songs.values():
        s_norm = s_ent["normalized_key"]
        _extend_unique(s_ent["alt_titles"], extra_alt_titles.get(s_norm, []))
        _extend_unique(s_ent["youtube_ids"], extra_yt_ids.get(s_norm, []))

        is_perf_only = set(s_ent["roles"]) == {"performer"}
        has_acum_creator = (
            any(acum_rev_name in p for p in s_ent["performers"])
            or (s_norm in rare_vocal_songs)
            or is_perf_only
        )
        cleaned_perfs: list[str] = []
        late_cover_perfs: list[str] = []
        for p in s_ent["performers"]:
            if normalize_catalog_song_title(p, synonym_map) == s_norm or p in bad_performers:
                continue
            if (cfg.name_he in p or cfg.name_en in p) and acum_rev_name not in p and not has_acum_creator:
                continue
            if late_cover_markers and any(x in p for x in late_cover_markers):
                late_cover_perfs.append(p)
            else:
                cleaned_perfs.append(p)
        cleaned_perfs.extend(late_cover_perfs)
        if cfg.is_performer and (is_perf_only or s_norm in rare_vocal_songs):
            if not any(tok in p for p in cleaned_perfs for tok in (cfg.name_he, cfg.name_en, *cfg.creator_surname_tokens)):
                cleaned_perfs.insert(0, cfg.name_he)
        for extra_p in reversed(extra_primary_perfs.get(s_norm, [])):
            if extra_p in cleaned_perfs:
                cleaned_perfs.remove(extra_p)
            cleaned_perfs.insert(0, extra_p)
        for ex_perf_sub in exclude_song_perfs.get(s_norm, []):
            cleaned_perfs = [p for p in cleaned_perfs if ex_perf_sub not in p]

        s_ent["performers"] = cleaned_perfs
        s_ent["albums"] = [a for a in s_ent["albums"] if a not in bad_albums]
        s_ent["youtube_ids"] = [y for y in s_ent["youtube_ids"] if y not in bad_yt_ids]
        if bad_creators:
            s_ent["authors"] = [a for a in s_ent["authors"] if a not in bad_creators]
            s_ent["composers"] = [c for c in s_ent["composers"] if c not in bad_creators]

        if s_norm in creator_overrides:
            ov_spec = creator_overrides[s_norm]
            if isinstance(ov_spec, dict):
                s_ent["roles"] = list(ov_spec.get("roles", s_ent["roles"]))
                s_ent["authors"] = list(ov_spec.get("authors", s_ent["authors"]))
                s_ent["composers"] = list(ov_spec.get("composers", s_ent["composers"]))
                if ov_spec.get("translators"):
                    s_ent["translators"] = list(ov_spec["translators"])
            elif isinstance(ov_spec, (list, tuple)) and len(ov_spec) >= 4:
                s_ent["roles"] = list(ov_spec[0])
                s_ent["authors"] = list(ov_spec[1])
                s_ent["composers"] = list(ov_spec[2])
                if ov_spec[3]:
                    s_ent["translators"] = list(ov_spec[3])

    sorted_songs = sorted(
        unified_songs.values(),
        key=lambda x: (0 if any("\u0590" <= c <= "\u05FF" for c in x["title"]) else 1, x["title"]),
    )

    unified_collections: list[dict[str, Any]] = []
    for a in wiki_data.get("albums", []):
        unified_collections.append({
            "title": a["raw"],
            "year": a.get("year", ""),
            "type": "אלבום (ויקיפדיה)",
            "tracks_count": "",
            "performer": "",
            "source": "wikipedia",
            "id_or_url": "",
        })
    for c in wiki_data.get("compilations", []):
        unified_collections.append({
            "title": c["raw"],
            "year": c.get("year", ""),
            "type": "אוסף (ויקיפדיה)",
            "tracks_count": "",
            "performer": "",
            "source": "wikipedia",
            "id_or_url": "",
        })
    for b in wiki_data.get("books", []):
        unified_collections.append({
            "title": b["raw"],
            "year": b.get("year", ""),
            "type": "ספר שירים (ויקיפדיה)",
            "tracks_count": "",
            "performer": cfg.name_he,
            "source": "wikipedia",
            "id_or_url": "",
        })
    for sa in shironet_data.get("albums", []):
        unified_collections.append({
            "title": sa["title"],
            "year": "",
            "type": "אלבום (שירונט)",
            "tracks_count": str(len(sa.get("tracks", []))),
            "performer": cfg.name_he,
            "source": "shironet",
            "id_or_url": sa.get("url", ""),
        })
    for aa in acum_data.get("albums", []):
        perf_name = ""
        if aa.get("performer"):
            perf_name = aa["performer"].get("performerHebName") or aa["performer"].get("performerEngName") or ""
        unified_collections.append({
            "title": aa.get("title", ""),
            "year": aa.get("release_date", ""),
            "type": 'אלבום/אוסף (אקו"ם)',
            "tracks_count": str(aa.get("tracks_count", "")),
            "performer": perf_name,
            "source": "acum",
            "id_or_url": f"albumId={aa.get('number', '')}",
        })
    for sva in svm_data.get("albums", []):
        unified_collections.append({
            "title": sva["title"],
            "year": sva.get("year", ""),
            "type": "אלבום/תקליט (סטריאו ומונו)",
            "tracks_count": str(sva.get("tracks_count", "")),
            "performer": sva.get("performer", ""),
            "source": "stereo_ve_mono",
            "id_or_url": sva.get("url", ""),
        })
    for drel in discogs_data.get("releases", []):
        unified_collections.append({
            "title": drel["title"],
            "year": drel.get("year", ""),
            "type": f"תקליט/אלבום ({drel.get('type', 'release')} - Discogs)",
            "tracks_count": str(drel.get("tracks_count", "")),
            "performer": drel.get("artist", ""),
            "source": "discogs",
            "id_or_url": drel.get("url", ""),
        })
    for mrel in mb_data.get("releases", []):
        unified_collections.append({
            "title": mrel["title"],
            "year": mrel.get("year", ""),
            "type": "אלבום (MusicBrainz)",
            "tracks_count": str(mrel.get("tracks_count", "")),
            "performer": cfg.name_he,
            "source": "musicbrainz",
            "id_or_url": mrel.get("url", ""),
        })
    for nalb in nli_data.get("albums", []):
        unified_collections.append({
            "title": nalb["title"],
            "year": nalb.get("year", ""),
            "type": nalb.get("type", ""),
            "tracks_count": "",
            "performer": nalb.get("performer", ""),
            "source": "nli",
            "id_or_url": nalb.get("url", ""),
        })

    return {
        "songs": sorted_songs,
        "collections": unified_collections,
        "tribute_songs": wiki_data.get("tribute_songs", []),
        "stats": {
            "total_unique_songs": len(sorted_songs),
            "songs_with_performers": sum(1 for s in sorted_songs if s["performers"]),
            "songs_with_albums": sum(1 for s in sorted_songs if s["albums"]),
            "songs_with_youtube_ids": sum(1 for s in sorted_songs if s["youtube_ids"]),
            "songs_with_opening_line": sum(1 for s in sorted_songs if s["opening_line"]),
            "songs_in_acum": sum(1 for s in sorted_songs if "acum" in s["sources"]),
            "songs_in_nli": sum(1 for s in sorted_songs if "nli" in s["sources"]),
            "songs_in_shironet": sum(1 for s in sorted_songs if "shironet" in s["sources"]),
            "songs_in_stereo_ve_mono": sum(1 for s in sorted_songs if "stereo_ve_mono" in s["sources"]),
            "songs_in_wikipedia": sum(1 for s in sorted_songs if "wikipedia" in s["sources"]),
            "songs_in_discogs": sum(1 for s in sorted_songs if "discogs" in s["sources"]),
            "songs_in_musicbrainz": sum(1 for s in sorted_songs if "musicbrainz" in s["sources"]),
            "songs_in_pizmonet": sum(1 for s in sorted_songs if "pizmonet" in s["sources"]),
            "songs_in_zemereshet": sum(1 for s in sorted_songs if "zemereshet" in s["sources"]),
            "songs_in_at_least_two_sources": sum(1 for s in sorted_songs if len(s["sources"]) >= 2),
            "songs_in_at_least_three_sources": sum(1 for s in sorted_songs if len(s["sources"]) >= 3),
            "total_collections": len(unified_collections),
            "wiki_albums": len(wiki_data.get("albums", [])),
            "wiki_compilations": len(wiki_data.get("compilations", [])),
            "wiki_books": len(wiki_data.get("books", [])),
            "shironet_albums": len(shironet_data.get("albums", [])),
            "acum_albums": len(acum_data.get("albums", [])),
            "stereo_ve_mono_albums": len(svm_data.get("albums", [])),
            "discogs_releases": len(discogs_data.get("releases", [])),
            "musicbrainz_releases": len(mb_data.get("releases", [])),
            "nli_albums": len(nli_data.get("albums", [])),
        },
    }


def save_catalog_outputs(
    cfg: ComposerConfig,
    catalog: dict[str, Any],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Write `catalog.json`, `songs.csv`, `albums.csv`, and `summary.md`."""
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / cfg.catalog_json.name
        songs_csv_path = output_dir / cfg.songs_csv.name
        albums_csv_path = output_dir / cfg.albums_csv.name
        md_path = output_dir / cfg.summary_md.name
    else:
        json_path = cfg.catalog_json
        songs_csv_path = cfg.songs_csv
        albums_csv_path = cfg.albums_csv
        md_path = cfg.summary_md
        json_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    with songs_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "שם השיר",
            "שמות חלופיים",
            'שם באנגלית (אקו"ם)',
            "שם היצירה המקורית (בתרגומים)",
            "שנת פרסום/הקלטה",
            f"תפקידי {cfg.name_he}",
            "מקורות",
            "מספר מקורות",
            "מחברים/פזמונאים",
            "מלחינים",
            "מתרגמים",
            "מעבדים",
            'מספר ביצועים באקו"ם',
            "מבצעים בולטים",
            "אלבומים/ספרים משויכים",
            'מזהי אקו"ם (Work IDs)',
            "מזהי הספרייה הלאומית (NLI MMS IDs)",
            "שורת פתיחה (אתחלתא - הספרייה הלאומית)",
            "קישורי שירונט",
            'מזהי יוטיוב (אקו"ם / סטריאו ומונו / פזמונט)',
        ])
        for s in catalog["songs"]:
            roles_heb = [ROLE_HEB_LABELS.get(r, r) for r in s["roles"]]
            writer.writerow([
                s["title"],
                " | ".join(s["alt_titles"]),
                s["english_title"],
                s["original_title"],
                s["year"],
                ", ".join(roles_heb),
                ", ".join(s["sources"]),
                len(s["sources"]),
                " | ".join(s["authors"]),
                " | ".join(s["composers"]),
                " | ".join(s["translators"]),
                " | ".join(s["arrangers"][:10]),
                s["acum_versions_count"],
                " | ".join(s["performers"][:20]),
                " | ".join(s["albums"][:15]),
                " | ".join(s["acum_work_ids"]),
                " | ".join(s["nli_mms_ids"]),
                s["opening_line"],
                " | ".join(s["shironet_urls"]),
                " | ".join(s["youtube_ids"]),
            ])

    with albums_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "שם האלבום / האוסף / הספר",
            "שנה",
            "סוג",
            "מבצע",
            "מספר רצועות",
            "מקור",
            "מזהה / קישור",
        ])
        for c in catalog["collections"]:
            writer.writerow([
                c["title"],
                c["year"],
                c["type"],
                c["performer"],
                c["tracks_count"],
                c["source"],
                c["id_or_url"],
            ])

    stats = catalog["stats"]
    lines: list[str] = [
        f"# קטלוג מקיף של אלבומי ושירי {cfg.name_he} (9 מקורות)",
        "",
        "## סיכום נתונים",
        "",
        f'- **סה"כ שירים ויצירות ייחודיות (לאחר איחוד וניקוי כפילויות):** {stats["total_unique_songs"]}',
        f"  - שירים עם רשימת מבצעים: {stats['songs_with_performers']}",
        f"  - שירים המשויכים לאלבום/ספר: {stats['songs_with_albums']}",
        f"  - שירים עם שורת פתיחה (אתחלתא מהספרייה הלאומית): {stats['songs_with_opening_line']}",
        f"  - שירים עם מזהה יוטיוב ישיר (מתוך המאגרים): {stats['songs_with_youtube_ids']}",
        "- **פילוח שירים לפי מקור:**",
        f'  - אקו"ם (ACUM): {stats["songs_in_acum"]} יצירות',
        f"  - הספרייה הלאומית (NLI - בית לזמר העברי וארכיון הצליל): {stats['songs_in_nli']} שירים",
        f"  - שירונט (Shironet): {stats['songs_in_shironet']} שירים",
        f"  - סטריאו ומונו (Stereo ve Mono): {stats['songs_in_stereo_ve_mono']} שירים",
        f"  - ויקיפדיה העברית: {stats['songs_in_wikipedia']} שירים",
        f"  - Discogs: {stats['songs_in_discogs']} שירים",
        f"  - MusicBrainz: {stats['songs_in_musicbrainz']} שירים",
        f"  - פזמונט (Pizmonet): {stats['songs_in_pizmonet']} שירים",
        f"  - זמרשת (Zemereshet): {stats['songs_in_zemereshet']} שירים",
        f"  - מופיעים בלפחות 2 מקורות: {stats['songs_in_at_least_two_sources']} שירים",
        f"  - מופיעים בלפחות 3 מקורות: {stats['songs_in_at_least_three_sources']} שירים",
        f'- **סה"כ רשומות אלבומים, אוספים וספרים:** {stats["total_collections"]}',
        f"  - אלבומים מלאים (ויקיפדיה): {stats['wiki_albums']}",
        f"  - אוספים (ויקיפדיה): {stats['wiki_compilations']}",
        f"  - ספרי שירים (ויקיפדיה): {stats['wiki_books']}",
        f"  - אלבומים בארכיון הצליל הלאומי (הספרייה הלאומית): {stats['nli_albums']}",
        f'  - אלבומים ואוספים במאגר אקו"ם: {stats["acum_albums"]}',
        f"  - אלבומים ותקליטים באתר סטריאו ומונו: {stats['stereo_ve_mono_albums']}",
        f"  - מהדורות ואלבומים ב-Discogs: {stats['discogs_releases']}",
        f"  - אלבומים ב-MusicBrainz: {stats['musicbrainz_releases']}",
        f"  - אלבומים בשירונט: {stats['shironet_albums']}",
        "",
        "## רשימת השירים המאוחדת",
        "",
        '| # | שם השיר | תפקידים | מקורות | מס\' ביצועים באקו"ם | מבצעים בולטים | מזהי יוטיוב |',
        "|---|---------|---------|--------|--------------------:|---------------|-------------|",
    ]
    for idx, s in enumerate(catalog["songs"], 1):
        roles_heb = ", ".join(ROLE_HEB_LABELS.get(r, r) for r in s["roles"])
        srcs = ", ".join(s["sources"])
        perfs = ", ".join(s["performers"][:4]).replace("|", "\\|")
        yts = ", ".join(s["youtube_ids"][:2])
        title_clean = s["title"].replace("|", "\\|")
        lines.append(
            f"| {idx} | {title_clean} | {roles_heb} | {srcs} | "
            f"{s['acum_versions_count']} | {perfs} | {yts} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "catalog_json": json_path,
        "songs_csv": songs_csv_path,
        "albums_csv": albums_csv_path,
        "summary_md": md_path,
    }


def collect_composer_catalog(
    slug: str,
    *,
    cache_only: bool = False,
    refresh: bool = False,
    sources_filter: set[str] | None = None,
    output_dir: Path | None = None,
    dry_run: bool = False,
    composer_dir: Path | None = None,
) -> dict[str, Any]:
    """Run all configured scrapers, merge into unified catalog, and optionally write outputs."""
    cfg = load_composer(slug, composer_dir=composer_dir)
    overrides = load_overrides(slug, composer_dir=composer_dir)
    raw_cache_dir = cfg.raw_cache_dir

    def _run_or_empty(name: str, fn: Any, empty: dict[str, Any]) -> dict[str, Any]:
        if sources_filter is not None and name not in sources_filter:
            return empty
        return fn(cfg, overrides, raw_cache_dir, cache_only=cache_only, refresh=refresh)

    wiki_data = _run_or_empty("wikipedia", scrape_wikipedia, {"albums": [], "compilations": [], "books": [], "tribute_songs": [], "translated_songs": [], "songs": []})
    shironet_data = _run_or_empty("shironet", scrape_shironet, {"songs": [], "work_entries": [], "albums": []})
    acum_data = _run_or_empty("acum", scrape_acum, {"works": [], "raw_beans": [], "albums": []})
    svm_data = _run_or_empty("stereo_ve_mono", scrape_stereo_ve_mono, {"albums": [], "songs": []})
    pizmonet_data = _run_or_empty("pizmonet", scrape_pizmonet, {"songs": []})
    zemereshet_data = _run_or_empty("zemereshet", scrape_zemereshet, {"songs": []})
    discogs_data = _run_or_empty("discogs", scrape_discogs, {"releases": [], "songs": []})
    mb_data = _run_or_empty("musicbrainz", scrape_musicbrainz, {"releases": [], "songs": []})
    nli_data = _run_or_empty("nli", scrape_nli, {"songs": [], "albums": [], "dafshir_count": 0, "archive_count": 0})

    catalog = build_unified_catalog(
        cfg,
        overrides,
        wiki_data=wiki_data,
        shironet_data=shironet_data,
        acum_data=acum_data,
        svm_data=svm_data,
        pizmonet_data=pizmonet_data,
        zemereshet_data=zemereshet_data,
        discogs_data=discogs_data,
        mb_data=mb_data,
        nli_data=nli_data,
    )

    if not dry_run:
        paths = save_catalog_outputs(cfg, catalog, output_dir=output_dir)
        print("\nנשמרו הקבצים הבאים:")
        for p in paths.values():
            print(f"  - {p}")
    return catalog
