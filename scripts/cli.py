#!/usr/bin/env python3
"""Unified CLI for multi-composer playlist building, health monitoring, backup, ranking, and streaming matching."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.backup import archive_composer_wayback, backup_composer_metadata  # noqa: E402
from core.build_site import build_all, build_composer, build_hub  # noqa: E402
from core.config import list_enabled_slugs, load_composer  # noqa: E402
from core.health import check_composer_health, heal_composer_playlist  # noqa: E402
from core.qa import audit_composer, format_qa_report  # noqa: E402
from core.ranking import rank_composer_playlist  # noqa: E402
from core.scaffold import scaffold_composer  # noqa: E402
from core.streaming_matcher import match_composer_streaming  # noqa: E402


def _resolve_targets(parser: argparse.ArgumentParser, slug: str | None, all_flag: bool) -> list[str]:
    if all_flag:
        return list_enabled_slugs()
    if not slug:
        parser.error("Provide <slug> or --all")
    return [slug]


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-composer Israeli music playlist CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List enabled composers from creators.json")
    sub.add_parser("matrix-json", help="Print enabled composer slugs as a compact JSON array for CI matrices")
    sub.add_parser("hub", help="Regenerate only the root index.html Hub page")

    p_build = sub.add_parser("build", help="Build site/player/exports for a composer or --all")
    p_build.add_argument("slug", nargs="?", help="Composer directory slug (e.g. naomi-shemer)")
    p_build.add_argument("--all", action="store_true", help="Build all enabled composers")
    p_build.add_argument("--standalone", action="store_true", help="Also emit self-contained single-file HTML")
    p_build.add_argument("--no-hub", action="store_true", help="Skip regenerating root index.html")

    p_health = sub.add_parser("health", help="Check YouTube playability via InnerTube for a composer or --all")
    p_health.add_argument("slug", nargs="?", help="Composer slug")
    p_health.add_argument("--all", action="store_true", help="Check all enabled composers")
    p_health.add_argument("--json-report", help="Optional JSON report path (single-composer mode)")
    p_health.add_argument("--skip-live-playlist", action="store_true", help="Skip live YouTube playlist comparison")
    p_health.add_argument("--auto-fix", action="store_true", help="Auto-promote healthy backups when unavailable")
    p_health.add_argument("--standalone", action="store_true", help="Emit standalone HTML when rebuilding")

    p_heal = sub.add_parser("heal", help="Run oEmbed health monitor & auto-heal for a composer or --all")
    p_heal.add_argument("slug", nargs="?", help="Composer slug")
    p_heal.add_argument("--all", action="store_true", help="Heal all enabled composers")
    p_heal.add_argument("--dry-run", action="store_true", help="Check health without modifying playlist files")
    p_heal.add_argument("--standalone", action="store_true", help="Emit standalone HTML when rebuilding")
    p_heal.add_argument("--no-backup", action="store_true", help="Skip metadata backup step when changes occur")

    p_backup = sub.add_parser("backup", help="Enrich alternatives and save full YouTube metadata backup JSON")
    p_backup.add_argument("slug", nargs="?", help="Composer slug")
    p_backup.add_argument("--all", action="store_true", help="Back up all enabled composers")

    p_wb = sub.add_parser("wayback", help="Check and optionally archive video URLs on Wayback Machine")
    p_wb.add_argument("slug", nargs="?", help="Composer slug")
    p_wb.add_argument("--all", action="store_true", help="Run across all enabled composers")
    p_wb.add_argument("--all-videos", action="store_true", help="Check all videos including - Topic channels")
    p_wb.add_argument("--save", action="store_true", help="Submit missing URLs to web.archive.org/save/")
    p_wb.add_argument("--limit", type=int, default=50, help="Max URLs to check per composer")

    p_rank = sub.add_parser("rank", help="Recompute canonical scores and re-rank primary Layer 1 songs")
    p_rank.add_argument("slug", help="Composer slug")
    p_rank.add_argument("--views-file", help="Path to song-wide views JSON file")
    p_rank.add_argument("--dry-run", action="store_true", help="Compute rank/score diffs without writing files")
    p_rank.add_argument("--no-rebuild", action="store_true", help="Skip rebuilding HTML/JS/exports after ranking")
    p_rank.add_argument("--standalone", action="store_true", help="Emit standalone HTML when rebuilding")

    p_sp = sub.add_parser("spotify", help="Match playlist & archive songs on Deezer ISRC / iTunes IL")
    p_sp.add_argument("slug", help="Composer slug")
    p_sp.add_argument("--cache-file", help="Path to Deezer/iTunes JSON cache")
    p_sp.add_argument("--output-dir", help="Override streaming export directory")
    p_sp.add_argument("--cache-only", action="store_true", help="Do not make network requests; read cache only")

    p_qa = sub.add_parser("qa", help="Run automated playlist, attribution, quality, and export QA audit")
    p_qa.add_argument("slug", nargs="?", help="Composer slug")
    p_qa.add_argument("--all", action="store_true", help="Audit all enabled composers")
    p_qa.add_argument("--strict", action="store_true", help="Exit with code 1 if any hard QA errors are found")
    p_qa.add_argument("--json-report", help="Optional path to write JSON QA report")

    p_init = sub.add_parser("init-composer", help="Scaffold a new composer directory, config, and overrides")
    p_init.add_argument("slug", help="Directory slug (lowercase hyphenated, e.g. sasha-argov)")
    p_init.add_argument("--name-he", required=True, help="Composer Hebrew display name")
    p_init.add_argument("--name-en", required=True, help="Composer English name")
    p_init.add_argument("--is-performer", action="store_true", help="Set if composer also recorded studio albums/performances")
    p_init.add_argument("--enable", action="store_true", help="Mark enabled=true immediately in creators.json")

    args = parser.parse_args()

    if args.command == "list":
        for slug in list_enabled_slugs():
            cfg = load_composer(slug)
            print(f"{slug:20s} | {cfg.name_he} ({cfg.name_en}) | performer={cfg.is_performer} | yt={cfg.youtube_playlist_id or '-'}")
        return 0

    if args.command == "matrix-json":
        print(json.dumps(list_enabled_slugs(), ensure_ascii=False))
        return 0

    if args.command == "hub":
        hub_path = build_hub()
        print(f"✔ עודכן שער המלחינים: {hub_path}")
        return 0

    if args.command == "build":
        if args.all:
            build_all(standalone=args.standalone)
            return 0
        if not args.slug:
            p_build.error("Provide <slug> or --all")
        build_composer(args.slug, standalone=args.standalone, rebuild_hub=not args.no_hub)
        return 0

    if args.command == "health":
        targets = _resolve_targets(p_health, args.slug, args.all)
        exit_code = 0
        for slug in targets:
            cfg = load_composer(slug)
            report_path = Path(args.json_report) if args.json_report else cfg.health_report_json
            if args.json_report and len(targets) > 1:
                report_path = cfg.dir / Path(args.json_report).name
            _, rc = check_composer_health(
                slug,
                json_report=report_path,
                skip_live_playlist=args.skip_live_playlist,
                auto_fix=args.auto_fix,
                standalone=args.standalone,
            )
            if rc != 0:
                exit_code = rc
        return exit_code

    if args.command == "heal":
        for slug in _resolve_targets(p_heal, args.slug, args.all):
            heal_composer_playlist(
                slug,
                dry_run=args.dry_run,
                standalone=args.standalone,
                run_backup=not args.no_backup,
            )
        return 0

    if args.command == "backup":
        for slug in _resolve_targets(p_backup, args.slug, args.all):
            backup_composer_metadata(slug)
        return 0

    if args.command == "wayback":
        for slug in _resolve_targets(p_wb, args.slug, args.all):
            archive_composer_wayback(slug, check_all=args.all_videos, save=args.save, limit=args.limit)
        return 0

    if args.command == "rank":
        res = rank_composer_playlist(
            args.slug,
            views_file=Path(args.views_file) if args.views_file else None,
            dry_run=args.dry_run,
            rebuild=not args.no_rebuild,
            standalone=args.standalone,
        )
        print(
            f"[{res['slug']}] dry_run={res['dry_run']} | p1_songs={res['total_p1_songs']} | "
            f"matched={res['total_matched']} | rank_diffs={res['rank_diffs']} | score_diffs={res['score_diffs']}"
        )
        for mv in res["moved_songs"][:15]:
            print(f"  rank {mv['old_rank']} -> {mv['new_rank']}: {mv['title']} ({mv['score']})")
        return 0

    if args.command == "spotify":
        match_composer_streaming(
            args.slug,
            cache_file=Path(args.cache_file) if args.cache_file else None,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            cache_only=args.cache_only,
        )
        return 0

    if args.command == "qa":
        targets = _resolve_targets(p_qa, args.slug, args.all)
        reports = [audit_composer(slug) for slug in targets]
        for rep in reports:
            print(format_qa_report(rep))
        if args.json_report:
            out_path = Path(args.json_report)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            payload: object = reports[0] if len(reports) == 1 else {"composers": reports}
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.strict and any(rep["error_count"] > 0 for rep in reports):
            return 1
        return 0

    if args.command == "init-composer":
        res = scaffold_composer(
            args.slug,
            name_he=args.name_he,
            name_en=args.name_en,
            is_performer=args.is_performer,
            enable=args.enable,
        )
        print(f"✔ Scaffolded composer '{res['slug']}' in {res['dir']} (registered={res['registered']}, enabled={res['enabled']})")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
