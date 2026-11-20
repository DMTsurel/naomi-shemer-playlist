"""Config-driven block partitioning and canonical Layer 1 ranking engine."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from core.build_site import build_composer
from core.config import ComposerConfig, load_composer


def partition_matched_blocks(
    matched_entries: list[dict[str, Any]],
    cfg: ComposerConfig,
) -> dict[str, list[dict[str, Any]]]:
    """Partition matched playlist items into p1..p3, e1..e3, tail, and tv preserving order."""
    blocks: dict[str, list[dict[str, Any]]] = {
        k: [] for k in ("p1", "p2", "p3", "e1", "e2", "e3", "tail", "tv")
    }
    in_extras_section = False
    seen_primary_titles: set[str] = set()
    prev_primary_lyr = 1
    tv_grp = cfg.tv_album_group
    tail_vids = cfg.tail_video_ids
    tail_kws = cfg.tail_performer_keywords

    for idx_item, item in enumerate(matched_entries):
        sel = item["selected_video"]
        ag = item.get("album_group", "")
        perf_raw = sel.get("matched_performer", "")
        lyr = int(item.get("canonical_layer", 2))
        lyr = lyr if lyr in (1, 2, 3) else 2

        is_tv_blk = ag == tv_grp
        is_tail_blk = (not is_tv_blk) and (
            sel["video_id"] in tail_vids or any(kw in perf_raw for kw in tail_kws)
        )
        if not in_extras_section:
            if (
                is_tv_blk
                or is_tail_blk
                or lyr < prev_primary_lyr
                or (
                    item["title"] in seen_primary_titles
                    and (idx_item == 0 or matched_entries[idx_item - 1]["title"] != item["title"])
                )
            ):
                in_extras_section = True
            else:
                seen_primary_titles.add(item["title"])
                prev_primary_lyr = lyr

        if is_tv_blk:
            blk_id = "tv"
        elif is_tail_blk:
            blk_id = "tail"
        elif not in_extras_section:
            blk_id = f"p{lyr}"
        else:
            blk_id = f"e{lyr}"

        blocks[blk_id].append(item)
    return blocks


def load_views_map(views_file: Path | None) -> dict[str, int]:
    """Load song-wide YouTube view counts (`{title: total_views | {total_views: int}}`)."""
    if not views_file or not views_file.exists():
        return {}
    raw = json.loads(views_file.read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for title, val in raw.items():
        if isinstance(val, dict):
            out[title] = int(val.get("total_views") or 0)
        elif isinstance(val, (int, float)):
            out[title] = int(val)
    return out


def compute_canonical_score(
    item: dict[str, Any],
    catalog_song: dict[str, Any],
    cfg: ComposerConfig,
    total_views: int = 0,
) -> float:
    """Compute composer-parameterized canonical score (`sqrt_mult`, `log`, or `linear`)."""
    ranking_cfg = cfg.ranking
    title = item.get("title", "")
    score_overrides = ranking_cfg.get("score_overrides") or {}
    if title in score_overrides:
        return round(float(score_overrides[title]), 1)

    mode = str(ranking_cfg.get("mode", "sqrt_mult"))
    anthology_cap = float(ranking_cfg.get("anthology_cap", 100.0))
    anthologies = ranking_cfg.get("canonical_anthologies", [])
    full_credit_trans = set(ranking_cfg.get("translation_full_credit_titles", []))

    rcat = item.get("role_category", "")
    acum_raw = int(item.get("acum_versions_count") or 0)
    eff_acum = acum_raw * 0.20 if (rcat == "translation" and title not in full_credit_trans) else float(acum_raw)
    acum_pts = min(eff_acum, 120.0) * 2.0 + max(0.0, eff_acum - 120.0) * 0.9

    albs = list(dict.fromkeys((item.get("catalog_albums") or []) + (catalog_song.get("albums") or [])))
    albs_str = " ".join(albs)
    anth_pts = min(
        anthology_cap,
        sum(float(a.get("points", 0.0)) for a in anthologies if a.get("keyword") and a["keyword"] in albs_str),
    )

    wiki_str = json.dumps(catalog_song.get("wiki_details", []), ensure_ascii=False)
    wiki_pts = 35.0 if (f"תבנית:{cfg.name_he}" in wiki_str or "קטגוריה:שירים" in wiki_str) else 0.0
    src_pts = 6.0 * len(item.get("sources", []))
    base = acum_pts + anth_pts + wiki_pts + src_pts

    v = max(0, int(total_views))
    if mode == "sqrt_mult":
        return round(base * (1.0 + math.sqrt(v / 1_000_000.0)), 1)
    if mode == "log":
        return round(base + 45.0 * math.log10(1.0 + v / 1000.0), 1)
    return round(base, 1)


def rank_composer_playlist(
    slug: str,
    views_file: Path | None = None,
    dry_run: bool = False,
    rebuild: bool = True,
    standalone: bool = False,
) -> dict[str, Any]:
    """Recompute canonical scores and re-rank primary Layer 1 songs for a composer."""
    cfg = load_composer(slug)
    pdata = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    cdata = json.loads(cfg.catalog_json.read_text(encoding="utf-8")) if cfg.catalog_json.exists() else {"songs": []}
    cmap = {s["title"]: s for s in cdata.get("songs", [])}
    views_map = load_views_map(views_file)

    playlist = pdata.get("playlist", [])
    matched = [it for it in playlist if it.get("selected_video")]
    unmatched = [it for it in playlist if not it.get("selected_video")]

    blocks = partition_matched_blocks(matched, cfg)
    p1 = blocks["p1"]
    e1 = blocks["e1"]

    p1_by_song: dict[str, list[dict[str, Any]]] = {}
    old_rank: dict[str, int] = {}
    for it in p1:
        t = it["title"]
        if t not in old_rank:
            old_rank[t] = len(old_rank) + 1
        p1_by_song.setdefault(t, []).append(it)

    e1_by_song: dict[str, list[dict[str, Any]]] = {}
    extra_non_p1_e1: list[dict[str, Any]] = []
    for it in e1:
        t = it["title"]
        if t in p1_by_song:
            e1_by_song.setdefault(t, []).append(it)
        else:
            extra_non_p1_e1.append(it)

    old_p1_titles = list(p1_by_song.keys())
    new_scores: dict[str, float] = {}
    score_diffs = 0
    for it in matched:
        t = it["title"]
        sc = compute_canonical_score(it, cmap.get(t, {}), cfg, total_views=views_map.get(t, 0))
        if t in p1_by_song:
            new_scores[t] = sc
        if sc != it.get("canonical_score"):
            score_diffs += 1
        if not dry_run:
            it["canonical_score"] = sc

    new_p1_titles = sorted(old_p1_titles, key=lambda t: (-new_scores[t], old_rank[t], t))
    rank_diffs = sum(1 for a, b in zip(old_p1_titles, new_p1_titles) if a != b)

    moved_songs: list[dict[str, Any]] = []
    for new_pos, t in enumerate(new_p1_titles, 1):
        old_pos = old_rank[t]
        if new_pos != old_pos:
            moved_songs.append({
                "title": t,
                "old_rank": old_pos,
                "new_rank": new_pos,
                "score": new_scores[t],
            })

    new_p1: list[dict[str, Any]] = []
    new_e1: list[dict[str, Any]] = []
    for t in new_p1_titles:
        new_p1.extend(p1_by_song[t])
        if t in e1_by_song:
            new_e1.extend(e1_by_song[t])
    new_e1.extend(extra_non_p1_e1)

    new_matched = (
        new_p1
        + blocks["p2"]
        + blocks["p3"]
        + new_e1
        + blocks["e2"]
        + blocks["e3"]
        + blocks["tail"]
        + blocks["tv"]
    )
    if not dry_run:
        for idx, it in enumerate(new_matched, 1):
            it["index"] = idx
        pdata["playlist"] = new_matched + unmatched
        cfg.playlist_json.write_text(json.dumps(pdata, ensure_ascii=False, indent=2), encoding="utf-8")
        if rebuild:
            build_composer(slug, standalone=standalone, rebuild_hub=True)

    return {
        "slug": cfg.slug,
        "dry_run": dry_run,
        "total_matched": len(matched),
        "total_p1_songs": len(old_p1_titles),
        "rank_diffs": rank_diffs,
        "score_diffs": score_diffs,
        "moved_songs": moved_songs,
        "top_10": [{"rank": i + 1, "title": t, "score": new_scores[t]} for i, t in enumerate(new_p1_titles[:10])],
    }
