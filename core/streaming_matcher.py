"""Config-driven streaming track matcher (Deezer ISRC + iTunes IL) and Soundiiz exporter."""

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

from core.artists import ARTIST_ALIASES
from core.config import ComposerConfig, load_composer, load_overrides
from core.hebrew import (
    ascii_translit_matches,
    has_bad_keyword,
    heb_loose,
    norm_heb,
    strip_title_noise,
    title_similarity,
)
from core.ranking import partition_matched_blocks

SOUNDIIZ_CHUNK_SIZE = 200


def expand_performer_tokens(perf_str: str, creator_name_he: str = "") -> list[list[str]]:
    """Split a Hebrew performer description into performer units with Hebrew and Latin aliases."""
    if not perf_str:
        return []
    s = re.sub(r"\([^)]*\)", " ", str(perf_str))
    s = re.sub(r'"([^"]+)"', r"\1", s)
    s = re.sub(r"\bמשתתפי\s+(?:המחזמר\s+)?", "", s)
    parts = re.split(r"\s*(?:,|;|/| ו-| בליווי | והלהקות | ולהקת | עם )\s*|\s+ו(?=[א-ת])", s)
    if creator_name_he and creator_name_he in perf_str:
        parts.append(creator_name_he)

    units: list[list[str]] = []
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
        seen_v: list[str] = []
        for v in variants:
            if v and v not in seen_v:
                seen_v.append(v)
        if seen_v:
            units.append(seen_v)
    return units


def artist_matches_target(
    cand_artist: str,
    cand_title: str,
    cand_album: str,
    target_perf: str,
    creator_name_he: str = "",
) -> bool:
    """Check whether streaming track artist/title/album matches a target catalog performer."""
    if not target_perf:
        return False
    units = expand_performer_tokens(target_perf, creator_name_he=creator_name_he)
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
            if var in ca_norm or var in ca_loose:
                return True
            if ("various" in ca_norm or "אמנים" in ca_norm or "מחזמר" in combined_norm) and var in calb_norm:
                return True
            if re.search(rf"(?:^|\s){re.escape(var)}(?:$|\s)", ct_norm):
                return True
    return False


def album_matches_musical(
    cand_album: str,
    row_album_group: str,
    matched_album: str,
    catalog_albums: list[str],
    musical_keywords: list[str],
) -> bool:
    """Allow cast/musical rows when streaming album matches a configured musical or anthology keyword."""
    calb = heb_loose(cand_album)
    if not calb or not musical_keywords:
        return False
    target_blob = f"{row_album_group} {matched_album} {' '.join(catalog_albums)}"
    target_norm = heb_loose(target_blob)
    for m in musical_keywords:
        m_norm = heb_loose(m)
        if m_norm and m_norm in target_norm and m_norm in calb:
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
            if isinstance(data, dict) and isinstance(data.get("error"), dict):
                if data["error"].get("code") == 4:
                    time.sleep(1.5 * (2**attempt))
                    continue
            return data
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code in (403, 429, 500, 502, 503):
                time.sleep(2.5 * (attempt + 1))
                continue
            raise
        except Exception as exc:
            last_err = exc
            time.sleep(1.0 * (attempt + 1))
    if last_err:
        raise last_err
    return {}


def deezer_search(query: str, cache: StreamingCache, cache_only: bool = False) -> list[dict[str, Any]]:
    ds = cache.data["deezer_search"]
    if query in ds:
        return ds[query]
    if cache_only:
        return []
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


def deezer_track_detail(tid: int | str, cache: StreamingCache, cache_only: bool = False) -> dict[str, Any]:
    dt = cache.data["deezer_track"]
    k = str(tid)
    if k in dt:
        return dt[k]
    if cache_only:
        return {}
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


def itunes_search(query: str, cache: StreamingCache, cache_only: bool = False) -> list[dict[str, Any]]:
    it_cache = cache.data["itunes_search"]
    if query in it_cache:
        return it_cache[query]
    if cache_only:
        return []
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": query, "country": "IL", "media": "music", "entity": "song", "limit": 12}
    )
    time.sleep(2.1)
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


def clean_query_title(title: str) -> str:
    cleaned = re.sub(r"\(\s*לחן\s+[אב]['׳]?\s*\)", "", title)
    return re.sub(r"\s+", " ", cleaned).strip()


def primary_artist_query(perf: str) -> str:
    """Clean performer string down to searchable core artist name."""
    s = re.sub(r"\([^)]*\)", " ", perf or "")
    s = re.sub(r"\bמשתתפי\s+(?:המחזמר\s+)?", "", s)
    s = re.split(r"[,/|]", s)[0].strip()
    return re.sub(r"\s+", " ", s)


class ComposerStreamingMatcher:
    """Stateful streaming matcher parameterized by composer config and overrides JSON."""

    def __init__(self, cfg: ComposerConfig, overrides: dict[str, Any]):
        self.cfg = cfg
        self.overrides = overrides
        self.homonym_block: dict[str, list[str]] = overrides.get("homonym_block_tokens", {})
        self.strict_archive_performers: dict[str, list[str]] = overrides.get(
            "strict_archive_allowed_performers", {}
        )
        self.skip_alt_titles: set[str] = set(overrides.get("skip_alt_titles_for_archive", []))
        self.noisy_albums: set[str] = set(overrides.get("noisy_catalog_albums", []))
        self.performer_overrides: dict[str, dict[str, str]] = overrides.get(
            "streaming_performer_overrides", {}
        )
        self.split_guards: dict[str, list[dict[str, Any]]] = overrides.get("split_composition_guards", {})
        self.perf_only_strict = bool(overrides.get("performance_only_strict_creator_match", True))
        self.musical_keywords = cfg.musical_album_keywords or [
            f"שירי {cfg.name_he}",
            cfg.name_en.lower(),
        ]
        self.creator_album_markers = tuple(
            m for m in (heb_loose(cfg.name_he), heb_loose(cfg.name_en)) if m
        )

    def hits_homonym_block(self, song_title: str, cand_title: str, cand_artist: str, cand_album: str) -> bool:
        base_t = strip_title_noise(song_title)
        blocked = self.homonym_block.get(song_title) or self.homonym_block.get(base_t)
        if not blocked:
            return False
        blob = f"{cand_title} {cand_artist} {cand_album}".lower()
        blob_norm = norm_heb(blob)
        for tok in blocked:
            t_low = tok.lower()
            if t_low in blob or norm_heb(t_low) in blob_norm:
                return True
        return False

    def fails_split_composition_guard(
        self,
        song_title: str,
        cand_title: str,
        cand_artist: str,
        cand_album: str,
    ) -> bool:
        blob = f"{cand_artist} {cand_title} {cand_album}".lower()
        for key, rules in self.split_guards.items():
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

    def has_split_guard(self, song_title: str) -> bool:
        return any(k in song_title for k in self.split_guards)

    def score_candidate(
        self,
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
        ctitle = str(cand.get("title") or "")
        cartist = str(cand.get("artist") or "")
        calbum = str(cand.get("album") or "")
        dur = int(cand.get("duration") or 0)

        if dur and (dur < 35 or dur > 900):
            return None
        if has_bad_keyword(ctitle, cartist, calbum):
            return None
        if self.hits_homonym_block(song_title, ctitle, cartist, calbum):
            return None

        if role_category == "performance_only" and self.perf_only_strict:
            if not artist_matches_target(cartist, ctitle, calbum, self.cfg.name_he, self.cfg.name_he):
                return None

        if self.fails_split_composition_guard(song_title, ctitle, cartist, calbum):
            return None

        if is_archive and song_title in self.strict_archive_performers:
            allowed_strict = self.strict_archive_performers[song_title]
            blob = norm_heb(f"{cartist} {calbum} {ctitle}")
            if not any(norm_heb(a) in blob for a in allowed_strict):
                return None

        base_title = strip_title_noise(song_title)
        titles_to_check = [base_title]
        for at in alt_titles or []:
            if at in self.skip_alt_titles:
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

        match_kind = ""
        perf_score = 0.0

        if target_perf and artist_matches_target(cartist, ctitle, calbum, target_perf, self.cfg.name_he):
            match_kind = "exact_performer"
            perf_score = 300.0
            if translit_ok:
                best_tsim = 0.88
        elif album_matches_musical(calbum, row_album_group, matched_album, catalog_albums, self.musical_keywords):
            match_kind = "musical_album"
            perf_score = 220.0
            if translit_ok:
                best_tsim = 0.87
        elif translit_ok:
            return None
        elif allow_fallback_perf or is_archive:
            matched_fb = None
            for fb in allowed_fallbacks:
                if not fb or len(norm_heb(fb)) < 3:
                    continue
                if artist_matches_target(cartist, ctitle, calbum, fb, self.cfg.name_he):
                    matched_fb = fb
                    break
            if matched_fb:
                match_kind = "catalog_performer_fallback" if not is_archive else "archive_verified_performer"
                perf_score = 240.0 if (self.cfg.name_he in matched_fb) else 200.0
            elif is_archive:
                calb_n = heb_loose(calbum)
                if any(m in calb_n for m in self.creator_album_markers):
                    match_kind = "archive_naomi_album"
                    perf_score = 180.0
                else:
                    for ca in catalog_albums:
                        if ca in self.noisy_albums or re.match(r"^(?:MUS|הד|דא\"ה|ח\"ח)", ca):
                            continue
                        ca_clean = re.sub(r"^\d+\s+", "", ca).strip()
                        if len(heb_loose(ca_clean)) >= 6 and heb_loose(ca_clean) in calb_n:
                            match_kind = "archive_catalog_album"
                            perf_score = 175.0
                            break

        if not match_kind:
            return None

        bonus = 0.0
        calb_loose = heb_loose(calbum)
        if any(m in calb_loose for m in self.creator_album_markers):
            bonus += 15.0
        if not is_archive and matched_album and heb_loose(strip_title_noise(matched_album)) in calb_loose:
            bonus += 25.0
        rank_bonus = min(20.0, math.log10(1 + max(0, int(cand.get("rank") or 0))) * 3.0)
        return (round(best_tsim * 100.0 + perf_score + bonus + rank_bonus, 2), match_kind)

    def find_unverified_hints(self, pool: list[dict[str, Any]], song_title: str) -> list[dict[str, Any]]:
        base_title = strip_title_noise(song_title)
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for cand in pool:
            ctitle = str(cand.get("title") or "")
            cartist = str(cand.get("artist") or "")
            calbum = str(cand.get("album") or "")
            dur = int(cand.get("duration") or 0)
            if dur and (dur < 40 or dur > 720):
                continue
            if has_bad_keyword(ctitle, cartist, calbum):
                continue
            if self.hits_homonym_block(song_title, ctitle, cartist, calbum):
                continue
            if song_title in self.strict_archive_performers:
                continue
            if title_similarity(base_title, ctitle) >= 0.90:
                key = (norm_heb(ctitle), norm_heb(cartist))
                if key not in seen:
                    seen.add(key)
                    out.append(cand)
                if len(out) >= 3:
                    break
        return out


def match_composer_streaming(
    slug: str,
    cache_file: Path | None = None,
    output_dir: Path | None = None,
    cache_only: bool = False,
) -> dict[str, Any]:
    """Match playlist + archive songs against Deezer/iTunes IL and write Soundiiz CSV exports."""
    cfg = load_composer(slug)
    ov = load_overrides(slug)
    matcher = ComposerStreamingMatcher(cfg, ov)

    pdata = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    cdata = json.loads(cfg.catalog_json.read_text(encoding="utf-8")) if cfg.catalog_json.exists() else {"songs": []}
    cmap = {s["title"]: s for s in cdata.get("songs", [])}

    playlist = pdata["playlist"]
    matched_rows = [x for x in playlist if x.get("selected_video")]
    unmatched_rows = [x for x in playlist if not x.get("selected_video")]

    blocks = partition_matched_blocks(matched_rows, cfg)
    skipped_rows: list[dict[str, Any]] = []
    for it in blocks["tv"]:
        skipped_rows.append({"row": it, "reason": "תוכנית טלוויזיה / מופע שלם"})
    for it in blocks["tail"]:
        skipped_rows.append({"row": it, "reason": "סקיצה נדירה / קטע ארכיוני מהאולפן"})

    music_rows: list[dict[str, Any]] = []
    for blk_key in ("p1", "p2", "p3", "e1", "e2", "e3"):
        is_primary = blk_key.startswith("p")
        for it in blocks[blk_key]:
            it_copy = dict(it)
            it_copy["_block"] = blk_key
            it_copy["_is_primary"] = is_primary
            music_rows.append(it_copy)

    print(
        f"[{cfg.slug}] Loaded {len(music_rows)} music rows, {len(skipped_rows)} skipped TV/sketches, "
        f"{len(unmatched_rows)} archive songs."
    )

    cache_path = cache_file or cfg.default_streaming_cache
    export_dir = output_dir or cfg.spotify_export_dir
    cache = StreamingCache(cache_path)

    unique_queries = sorted({clean_query_title(x["title"]) for x in music_rows + unmatched_rows})
    missing_q = [q for q in unique_queries if q not in cache.data["deezer_search"]]
    print(f"Pass 1A (Deezer title searches): {len(unique_queries)} total, {len(missing_q)} uncached...")
    if missing_q and not cache_only:
        def _dz(q: str) -> tuple[str, list[dict[str, Any]]]:
            time.sleep(0.14)
            return q, deezer_search(q, cache, cache_only=False)

        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = [ex.submit(_dz, q) for q in missing_q]
            for fut in as_completed(futs):
                fut.result()
        cache.save()

    def _effective_target_perf(it: dict[str, Any], is_arch: bool) -> tuple[str, dict[str, str] | None]:
        sv = it.get("selected_video") or {}
        if not is_arch and it["title"] in matcher.performer_overrides:
            ov_entry = matcher.performer_overrides[it["title"]]
            return ov_entry.get("performer", ""), ov_entry
        return sv.get("matched_performer", ""), None

    extra_dz_queries: set[str] = set()
    for it in music_rows:
        qt = clean_query_title(it["title"])
        mp, _ = _effective_target_perf(it, False)
        pa = primary_artist_query(mp)
        pool = cache.data["deezer_search"].get(qt, [])
        if pa and not any(artist_matches_target(c["artist"], c["title"], c["album"], mp, cfg.name_he) for c in pool):
            extra_dz_queries.add(f"{qt} {pa}")
        for alt in (it.get("alt_titles") or [])[:1]:
            if alt not in matcher.skip_alt_titles and clean_query_title(alt) != qt:
                extra_dz_queries.add(clean_query_title(alt))
    for it in unmatched_rows:
        qt = clean_query_title(it["title"])
        for p in (it.get("catalog_performers") or [])[:2]:
            extra_dz_queries.add(f"{qt} {primary_artist_query(p)}")
        if cfg.name_he not in " ".join(it.get("catalog_performers") or []):
            extra_dz_queries.add(f"{qt} {cfg.name_he}")

    missing_extra = [q for q in sorted(extra_dz_queries) if q not in cache.data["deezer_search"]]
    print(f"Pass 1B (Deezer targeted title+artist searches): {len(extra_dz_queries)} total, {len(missing_extra)} uncached...")
    if missing_extra and not cache_only:
        def _dz2(q: str) -> tuple[str, list[dict[str, Any]]]:
            time.sleep(0.14)
            return q, deezer_search(q, cache, cache_only=False)

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
        queries.append(f"{qt} {cfg.name_he}")
        for alt in (it.get("alt_titles") or [])[:1]:
            if alt not in matcher.skip_alt_titles:
                queries.append(clean_query_title(alt))
        seen_ids: set[Any] = set()
        pool: list[dict[str, Any]] = []
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
            cat_perfs = [cfg.name_he]
            eff_target = cfg.name_he
            eff_fallback = False
        else:
            cat_perfs = list(
                dict.fromkeys((it.get("catalog_performers") or []) + (cs.get("performers") or []) + [cfg.name_he])
            )
            eff_target = target_perf
            eff_fallback = allow_fallback
        cat_albs = list(dict.fromkeys((it.get("catalog_albums") or []) + (cs.get("albums") or [])))
        scored: list[tuple[float, str, dict[str, Any]]] = []
        for cand in pool:
            cid_key = f"{source_tag}:{cand.get('id')}"
            if cid_key in used_ids:
                continue
            res = matcher.score_candidate(
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

    used_deezer_ids: set[str] = set()
    used_isrcs: set[str] = set()
    used_norm_pairs: set[tuple[str, str]] = set()
    prelim_dz: dict[str, dict[str, Any]] = {}

    for idx, it in enumerate(music_rows):
        it["_row_uid"] = f"m_{it['index']}_{it['selected_video']['video_id']}"
    for idx, it in enumerate(unmatched_rows):
        it["_row_uid"] = f"u_{idx}_{it['title']}"

    ordered_eval = (
        [it for it in music_rows if it["_is_primary"]]
        + unmatched_rows
        + [it for it in music_rows if not it["_is_primary"]]
    )

    itunes_needed: list[tuple[dict[str, Any], str, str]] = []
    for it in ordered_eval:
        is_arch = it["_row_uid"].startswith("u_")
        target_perf, _ = _effective_target_perf(it, is_arch)
        pool = collect_deezer_pool(it, target_perf)
        hit = evaluate_row_on_pool(
            it,
            pool,
            target_perf=target_perf,
            allow_fallback=bool(it.get("_is_primary")) and (not matcher.has_split_guard(it["title"])),
            is_archive=is_arch,
            used_ids=used_deezer_ids,
            source_tag="dz",
        )
        if hit:
            prelim_dz[it["_row_uid"]] = hit
            used_deezer_ids.add(f"dz:{hit['cand']['id']}")
        else:
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
                    itunes_needed.append((it, cfg.name_he, f"{qt} {cfg.name_he}"))

    dz_track_ids = [hit["cand"]["id"] for hit in prelim_dz.values()]
    uncached_tids = [tid for tid in dz_track_ids if str(tid) not in cache.data["deezer_track"]]
    print(f"Pass 1C (Deezer /track ISRCs): {len(dz_track_ids)} matches, {len(uncached_tids)} uncached...")
    if uncached_tids and not cache_only:
        def _dt(tid: Any) -> dict[str, Any]:
            time.sleep(0.14)
            return deezer_track_detail(tid, cache, cache_only=False)

        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = [ex.submit(_dt, tid) for tid in uncached_tids]
            for fut in as_completed(futs):
                fut.result()
        cache.save()

    uncached_it_qs = list(dict.fromkeys(q for _, _, q in itunes_needed if q not in cache.data["itunes_search"]))
    print(f"Pass 2 (iTunes IL fallback): {len(itunes_needed)} missed rows ({len(uncached_it_qs)} uncached queries)...")
    if uncached_it_qs and not cache_only:
        for q in uncached_it_qs:
            itunes_search(q, cache, cache_only=False)
        cache.save()

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
    for it in ordered_eval:
        uid = it["_row_uid"]
        is_arch = uid.startswith("u_")
        sv = it.get("selected_video") or {}
        target_perf, ov_entry = _effective_target_perf(it, is_arch)

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
            if committed and ov_entry and not is_arch:
                upgrades_notes.append({
                    "song": it["title"],
                    "youtube_perf": f"{sv.get('matched_performer', '')} (שורה #{it['index']})",
                    "streaming_perf": f"{rec['stream_artist']} — {rec['stream_album']} (ISRC `{rec['isrc']}`)",
                    "note": ov_entry.get("note", "שדרוג ביצוע אולפן בסטרימינג."),
                })
            elif committed and hit["match_kind"] in ("catalog_performer_fallback", "musical_album") and target_perf and not is_arch:
                upgrades_notes.append({
                    "song": it["title"],
                    "youtube_perf": target_perf,
                    "streaming_perf": f"{rec['stream_artist']} — {rec['stream_album']}" + (f" (`{rec['isrc']}`)" if rec["isrc"] else ""),
                    "note": f"התאמה דרך `{hit['match_kind']}` (המבצע המקורי ביוטיוב לא הופץ בנפרד בסטרימינג).",
                })

        if not committed:
            qt = clean_query_title(it["title"])
            q_cands: list[str] = []
            if not is_arch:
                pa = primary_artist_query(target_perf)
                q_cands.append(f"{qt} {pa}".strip() if pa else qt)
            else:
                perfs = it.get("catalog_performers") or []
                q_cands.append(f"{qt} {primary_artist_query(perfs[0])}".strip() if perfs else f"{qt} {cfg.name_he}")
            it_pool: list[dict[str, Any]] = []
            seen_it: set[Any] = set()
            for q in q_cands:
                for c in cache.data["itunes_search"].get(q, []):
                    if c.get("id") and c["id"] not in seen_it:
                        seen_it.add(c["id"])
                        it_pool.append(c)
            hit2 = evaluate_row_on_pool(
                it,
                it_pool,
                target_perf=target_perf,
                allow_fallback=bool(it.get("_is_primary")) and (not matcher.has_split_guard(it["title"])),
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
            hints = matcher.find_unverified_hints(collect_deezer_pool(it, ""), it["title"])
            if hints:
                unverified_archive_hints.append({"song": it["title"], "year": it.get("year", ""), "hints": hints[:2]})

    by_block: dict[str, list[dict[str, Any]]] = {k: [] for k in ("p1", "p2", "p3", "e1", "e2", "e3")}
    for it in music_rows:
        uid = it["_row_uid"]
        if uid in final_results:
            by_block[it["_block"]].append(final_results[uid])

    archive_hits = [final_results[it["_row_uid"]] for it in unmatched_rows if it["_row_uid"] in final_results]
    dated_arch = [a for a in archive_hits if str(a.get("year", "")).isdigit()]
    undated_arch = [a for a in archive_hits if not str(a.get("year", "")).isdigit()]

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

    export_dir.mkdir(parents=True, exist_ok=True)
    for old_p in export_dir.glob("soundiiz_part_*.csv"):
        old_p.unlink()

    full_csv_path = export_dir / "soundiiz_full_all.csv"
    fieldnames = ["title", "artist", "album", "isrc"]

    def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for t in rows:
                w.writerow({
                    "title": t["stream_title"],
                    "artist": t["stream_artist"],
                    "album": t["stream_album"],
                    "isrc": t["isrc"],
                })

    _write_csv(full_csv_path, ordered_tracks)
    part_paths: list[tuple[Path, int]] = []
    num_parts = max(1, math.ceil(len(ordered_tracks) / SOUNDIIZ_CHUNK_SIZE))
    for i in range(num_parts):
        chunk = ordered_tracks[i * SOUNDIIZ_CHUNK_SIZE : (i + 1) * SOUNDIIZ_CHUNK_SIZE]
        pp = export_dir / f"soundiiz_part_{i + 1}.csv"
        _write_csv(pp, chunk)
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

    (export_dir / "spotify_streaming_matches.json").write_text(
        json.dumps({"stats": summary_stats, "tracks": ordered_tracks, "archive_discoveries": archive_hits}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    rep_lines = [
        f"# 🎧 דוח התאמה לספוטיפיי ולשירותי סטרימינג — {cfg.playlist_title_he}",
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
        "1. היכנס ל-[Soundiiz](https://soundiiz.com/) ← בחר **Import Playlist** ← **From File (CSV)** ← העלה את `soundiiz_part_1.csv` ← יבא אל פלייליסט זמני ב-Spotify.",
        "2. חזור על הצעד עבור כל חלק (`soundiiz_part_2.csv`, וכו' — כל קובץ הוא מתחת לתקרת ה-200 החינמית).",
        f"3. פתח את אפליקציית **Spotify במחשב** ← צור פלייליסט חדש **`{cfg.playlist_title_he}`** ← היכנס לחלק 1, לחץ **`Cmd+A`** וגרור לפלייליסט הראשי; אח\"כ עבור לחלקים הבאים, **`Cmd+A`**, וגרור מיד בסופו (ואז מחק את הזמניים). הסדר המדויק נשמר 1:1!",
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
        rep_lines.append(f"* `#{it['index']}` **{it['title']}** — {it['selected_video'].get('matched_performer', '')} ({sr['reason']})")

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
        rep_lines.append(
            f"| #{um['index']} | {um['title']} | {um.get('canonical_layer')} | {sv.get('matched_performer', '')} | {'ראשי' if um.get('_is_primary') else 'ביצוע נוסף'} |"
        )
    rep_lines.append("")

    (export_dir / "spotify_match_report.md").write_text("\n".join(rep_lines), encoding="utf-8")

    print("\n=== SPOTIFY MATCH SUMMARY ===")
    for k, v in summary_stats.items():
        print(f"  {k}: {v}")
    for pp, cnt in part_paths:
        print(f"  CSV part: {pp.name} ({cnt} rows)")

    return {
        "slug": cfg.slug,
        "stats": summary_stats,
        "export_dir": str(export_dir),
        "parts": [(pp.name, cnt) for pp, cnt in part_paths],
    }
