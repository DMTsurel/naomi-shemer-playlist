#!/usr/bin/env python3
"""Unified CLI for building multi-composer playlists and the root Hub."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.build_site import build_all, build_composer, build_hub  # noqa: E402
from core.config import list_enabled_slugs, load_composer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-composer Israeli music playlist CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List enabled composers from creators.json")

    p_build = sub.add_parser("build", help="Build site/player/exports for a composer or --all")
    p_build.add_argument("slug", nargs="?", help="Composer directory slug (e.g. naomi-shemer)")
    p_build.add_argument("--all", action="store_true", help="Build all enabled composers")
    p_build.add_argument(
        "--standalone",
        action="store_true",
        help="Also emit a self-contained single-file HTML in the composer's legacy_player_html path",
    )
    p_build.add_argument("--no-hub", action="store_true", help="Skip regenerating root index.html")

    sub.add_parser("hub", help="Regenerate only the root index.html Hub page")

    args = parser.parse_args()

    if args.command == "list":
        for slug in list_enabled_slugs():
            cfg = load_composer(slug)
            print(f"{slug:20s} | {cfg.name_he} ({cfg.name_en}) | performer={cfg.is_performer} | yt={cfg.youtube_playlist_id or '-'}")
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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
