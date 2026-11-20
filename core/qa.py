"""Automated multi-composer playlist, attribution, audio-quality, and export QA auditor."""

from __future__ import annotations

import json
import re
from typing import Any

from core.artists import ACUM_PERFORMER_EXACT_MAP
from core.config import ComposerConfig, load_composer, load_overrides
from core.hebrew import has_bad_keyword, norm_heb, parse_duration_seconds
from core.ranking import partition_matched_blocks

_AI_FANMIX_MARKERS: tuple[str, ...] = (
    "בינה מלאכותית",
    "ללא תזמורת",
    "מיקס מעריצים",
    "שיפוץ סאונד",
    " ai ",
    "(ai)",
)
_NON_SONG_MARKERS: tuple[str, ...] = (
    "ראיון",
    "סקיצה",
    "פרודיה",
    "חזרה,",
    "מערכון",
    "שירה בציבור",
    "הקהל שר",
)
_STUDIO_TIERS: set[str] = {"1_album_naomi", "1_album_creator", "2_album_original"}
_LIVE_MARKERS_HE: tuple[str, ...] = ("בהופעה", "הופעה חיה", "צוותא", "קונצרט")


def _parse_year(val: Any) -> int | None:
    s = str(val or "").strip()
    if re.fullmatch(r"\d{4}", s):
        return int(s)
    return None


def _is_creator_credited(item: dict[str, Any], cfg: ComposerConfig) -> bool:
    sel = item.get("selected_video") or {}
    blob = " ".join(
        str(x or "")
        for x in (sel.get("matched_performer"), sel.get("video_title"), sel.get("channel"))
    )
    name_he_norm = norm_heb(cfg.name_he)
    if name_he_norm and name_he_norm in norm_heb(blob):
        return True
    name_en_low = cfg.name_en.strip().lower()
    if name_en_low and name_en_low in blob.lower():
        return True
    return False


def _issue(code: str, index: Any, title: str, video_id: str, detail: str) -> dict[str, Any]:
    return {
        "code": code,
        "index": index,
        "title": title,
        "video_id": video_id,
        "detail": detail,
    }


def _check_primary_pairing(
    primary_items: list[dict[str, Any]],
    cfg: ComposerConfig,
    warnings: list[dict[str, Any]],
) -> None:
    by_title: dict[str, list[dict[str, Any]]] = {}
    for it in primary_items:
        by_title.setdefault(it.get("title", ""), []).append(it)

    creator_tiers = set(cfg.creator_performance_tiers)
    mode = cfg.dual_performance_mode

    for title, group in by_title.items():
        if mode == "original_only" and len(group) > 1:
            warnings.append(
                _issue(
                    "PRIMARY_MULTI_NON_PERFORMER",
                    group[0].get("index"),
                    title,
                    group[0]["selected_video"]["video_id"],
                    f"dual_performance_mode=original_only but {len(group)} versions appear in p1..p3",
                )
            )
            continue

        if mode == "original_plus_creator":
            if len(group) > 2:
                warnings.append(
                    _issue(
                        "PRIMARY_OVER_TWO",
                        group[0].get("index"),
                        title,
                        group[0]["selected_video"]["video_id"],
                        f"{len(group)} versions in primary block p1..p3 (max 2 expected)",
                    )
                )
            elif len(group) == 2:
                is_c0 = group[0].get("tier") in creator_tiers
                is_c1 = group[1].get("tier") in creator_tiers
                vid0 = group[0]["selected_video"]["video_id"]
                vid1 = group[1]["selected_video"]["video_id"]
                if is_c0 and is_c1:
                    warnings.append(
                        _issue(
                            "PRIMARY_DOUBLE_CREATOR",
                            group[1].get("index"),
                            title,
                            vid1,
                            "Two creator performances paired back-to-back in primary block",
                        )
                    )
                elif (not is_c0) and (not is_c1):
                    warnings.append(
                        _issue(
                            "PRIMARY_DOUBLE_NON_CREATOR",
                            group[1].get("index"),
                            title,
                            vid1,
                            "Two non-creator performances paired together in primary block",
                        )
                    )
                elif is_c0 and group[1].get("tier") == "5_cover":
                    warnings.append(
                        _issue(
                            "PRIMARY_COVER_AFTER_CREATOR_ORIGINAL",
                            group[1].get("index"),
                            title,
                            vid1,
                            f"Cover #{group[1].get('index')} paired right after creator original ({vid0})",
                        )
                    )


def audit_composer(slug: str) -> dict[str, Any]:
    """Run hard-invariant errors and editorial/audio quality warnings on a composer."""
    cfg = load_composer(slug)
    ov = load_overrides(slug)
    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    playlist = data.get("playlist", [])

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    bad_ids: dict[str, str] = ov.get("bad_video_ids") or {}
    strict_perf_only = bool(ov.get("performance_only_strict_creator_match", True))
    excluded_norm = {norm_heb(x) for x in (ov.get("excluded_normalized_songs") or []) if norm_heb(x)}

    matched = [it for it in playlist if it.get("selected_video")]
    unmatched = [it for it in playlist if not it.get("selected_video")]

    blocks = partition_matched_blocks(matched, cfg)
    primary_items = blocks["p1"] + blocks["p2"] + blocks["p3"]
    primary_keys = {id(it) for it in primary_items}
    tv_keys = {id(it) for it in blocks["tv"]}
    tail_keys = {id(it) for it in blocks["tail"]}

    for item in playlist:
        idx = item.get("index")
        title = item.get("title", "")
        sel = item.get("selected_video") or {}
        vid = sel.get("video_id", "")

        if norm_heb(title) in excluded_norm:
            errors.append(
                _issue(
                    "EXCLUDED_SONG_PRESENT",
                    idx,
                    title,
                    vid,
                    "Song matches overrides['excluded_normalized_songs']",
                )
            )

        if str(item.get("year", "")).strip() == "2099":
            errors.append(_issue("PLACEHOLDER_YEAR", idx, title, vid, "Placeholder year '2099' present"))
        else:
            yr_num = _parse_year(item.get("year"))
            if yr_num is not None and (yr_num < 1920 or yr_num > 2030):
                warnings.append(_issue("SUSPICIOUS_YEAR", idx, title, vid, f"Unusual recording year: {yr_num}"))

        for perf in list(item.get("catalog_performers") or []) + ([sel.get("matched_performer", "")] if sel else []):
            if str(perf).strip() in ACUM_PERFORMER_EXACT_MAP:
                warnings.append(
                    _issue(
                        "REVERSED_ACUM_NAME",
                        idx,
                        title,
                        vid,
                        f"Unnormalized ACUM performer name: '{perf}'",
                    )
                )
                break

        if not vid:
            if not (item.get("archive_links") or []):
                warnings.append(_issue("ARCHIVE_NO_LINKS", idx, title, "", "Unmatched archive song has zero archive_links"))
            continue

        if vid in bad_ids:
            errors.append(
                _issue("BAD_VIDEO_PRIMARY", idx, title, vid, f"Blacklisted primary video: {bad_ids[vid]}")
            )
        for alt in item.get("alternative_videos") or []:
            avid = alt.get("video_id", "")
            if avid in bad_ids:
                warnings.append(
                    _issue("BAD_VIDEO_ALT", idx, title, avid, f"Blacklisted backup video: {bad_ids[avid]}")
                )

        if item.get("role_category") == "performance_only" and strict_perf_only:
            if not _is_creator_credited(item, cfg):
                errors.append(
                    _issue(
                        "PERF_ONLY_NON_CREATOR",
                        idx,
                        title,
                        vid,
                        f"performance_only song missing creator credit ({sel.get('matched_performer', '')})",
                    )
                )

        vtitle = sel.get("video_title", "")
        channel = sel.get("channel", "")
        perf = sel.get("matched_performer", "")
        desc = sel.get("description", "")
        is_tv = id(item) in tv_keys
        is_tail = id(item) in tail_keys
        is_primary = id(item) in primary_keys

        if (not is_tv) and (not is_tail) and has_bad_keyword(vtitle, channel, perf):
            errors.append(
                _issue(
                    "BAD_KEYWORD_PRIMARY",
                    idx,
                    title,
                    vid,
                    f"Matched karaoke/playback/bad keyword in '{vtitle}' / '{perf}'",
                )
            )

        blob_low = f" {vtitle} {desc} {perf} ".lower()
        if any(mk in blob_low for mk in _AI_FANMIX_MARKERS):
            warnings.append(
                _issue("AI_OR_FAN_MIX", idx, title, vid, f"Possible AI or fan-remixed audio in '{vtitle}'")
            )

        title_perf_low = f"{vtitle} {perf}".lower()
        if is_primary and any(mk in title_perf_low for mk in _NON_SONG_MARKERS):
            warnings.append(
                _issue(
                    "NON_SONG_IN_PRIMARY",
                    idx,
                    title,
                    vid,
                    f"Non-song/interview/sketch marker in primary block: '{vtitle}' ({perf})",
                )
            )

        if item.get("tier") in _STUDIO_TIERS and not is_tv:
            if any(mk in title_perf_low for mk in _LIVE_MARKERS_HE) or re.search(r"\blive\b", title_perf_low):
                warnings.append(
                    _issue(
                        "LIVE_IN_STUDIO_TIER",
                        idx,
                        title,
                        vid,
                        f"Live marker on studio tier {item.get('tier')}: '{vtitle}'",
                    )
                )

        if not is_tv:
            dur_sec = parse_duration_seconds(sel.get("duration", ""))
            if dur_sec <= 0:
                warnings.append(_issue("MISSING_DURATION", idx, title, vid, "Missing or unparseable video duration"))
            else:
                if (not is_tail) and dur_sec < 65:
                    warnings.append(
                        _issue("SUSPICIOUSLY_SHORT", idx, title, vid, f"Short duration {sel.get('duration')} (< 65s)")
                    )
                if dur_sec > 480:
                    warnings.append(
                        _issue("SUSPICIOUSLY_LONG", idx, title, vid, f"Long non-TV duration {sel.get('duration')} (> 8m)")
                    )

    _check_primary_pairing(primary_items, cfg, warnings)

    # Same-song duplicate recording & original-vs-cover year checks across matched entries
    by_title_all: dict[str, list[dict[str, Any]]] = {}
    for it in matched:
        if id(it) not in tv_keys:
            by_title_all.setdefault(it.get("title", ""), []).append(it)

    for title, group in by_title_all.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            a = group[i]
            pa = norm_heb((a.get("selected_video") or {}).get("matched_performer", ""))
            da = parse_duration_seconds((a.get("selected_video") or {}).get("duration", ""))
            if not pa or da <= 0:
                continue
            for j in range(i + 1, len(group)):
                b = group[j]
                pb = norm_heb((b.get("selected_video") or {}).get("matched_performer", ""))
                db = parse_duration_seconds((b.get("selected_video") or {}).get("duration", ""))
                if pb == pa and db > 0 and abs(da - db) <= 12:
                    warnings.append(
                        _issue(
                            "POSSIBLE_DUPLICATE_RECORDING",
                            b.get("index"),
                            title,
                            b["selected_video"]["video_id"],
                            f"Matches #{a.get('index')} ({a['selected_video']['video_id']}): same performer '{(b.get('selected_video') or {}).get('matched_performer', '')}' & ~duration ({da}s vs {db}s)",
                        )
                    )

        cover_years = [
            y
            for x in group
            if x.get("tier") == "5_cover"
            for y in [_parse_year(x.get("year"))]
            if y is not None
        ]
        if cover_years:
            min_cover_yr = min(cover_years)
            for x in group:
                if x.get("dual_role") == "original_performance":
                    orig_yr = _parse_year(x.get("year"))
                    if orig_yr is not None and orig_yr > min_cover_yr:
                        warnings.append(
                            _issue(
                                "ORIGINAL_LATER_THAN_COVER",
                                x.get("index"),
                                title,
                                x["selected_video"]["video_id"],
                                f"Original marked year {orig_yr} > earliest 5_cover year {min_cover_yr}",
                            )
                        )

    if cfg.playlist_data_js.exists():
        raw_js = cfg.playlist_data_js.read_text(encoding="utf-8")
        if raw_js.lstrip().startswith("window.PLAYLIST_DATA"):
            json_str = raw_js.split("=", 1)[1].strip().rstrip(";")
            pdata_js = json.loads(json_str)
            for row in list(pdata_js.get("songs") or []) + list(pdata_js.get("archiveSongs") or []):
                for lk in row.get("links") or []:
                    lbl = str(lk.get("label", ""))
                    if "ACUM_WRKNBR:" in lbl:
                        errors.append(
                            _issue(
                                "RAW_ACUM_LABEL_IN_EXPORT",
                                row.get("n"),
                                row.get("raw_title") or row.get("title", ""),
                                row.get("vid", ""),
                                f"Unstripped ACUM_WRKNBR prefix in label '{lbl}'",
                            )
                        )
                notes_val = str(row.get("notes") or "")
                if len(notes_val) > 220:
                    warnings.append(
                        _issue(
                            "LONG_NOTES_IN_EXPORT",
                            row.get("n"),
                            row.get("raw_title") or row.get("title", ""),
                            row.get("vid", ""),
                            f"Long notes paragraph ({len(notes_val)} chars) in public export",
                        )
                    )

    return {
        "slug": cfg.slug,
        "name_he": cfg.name_he,
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def format_qa_report(report: dict[str, Any], max_warnings: int = 30) -> str:
    """Format an audit report for readable CLI output."""
    lines = [
        f"QA Report [{report['slug']}] ({report['name_he']}): "
        f"{report['matched_count']} matched, {report['unmatched_count']} archive | "
        f"errors={report['error_count']} | warnings={report['warning_count']}"
    ]
    if report["errors"]:
        lines.append("  ERRORS:")
        for err in report["errors"]:
            lines.append(
                f"    [{err['code']}] #{err['index']} {err['title']} ({err['video_id']}): {err['detail']}"
            )
    if report["warnings"]:
        lines.append(f"  WARNINGS (showing {min(len(report['warnings']), max_warnings)}/{len(report['warnings'])}):")
        for warn in report["warnings"][:max_warnings]:
            lines.append(
                f"    [{warn['code']}] #{warn['index']} {warn['title']} ({warn['video_id']}): {warn['detail']}"
            )
    return "\n".join(lines)
