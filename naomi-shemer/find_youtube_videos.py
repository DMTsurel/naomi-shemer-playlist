#!/usr/bin/env python3
"""Backward-compatible shim delegating Naomi Shemer YouTube matching to `core.youtube_finder`."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.youtube_finder import (  # noqa: E402, F401
    FinderContext,
    fetch_video_details_by_id,
    find_composer_videos,
    youtube_search_raw,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Find and rank Naomi Shemer performances on YouTube.")
    parser.add_argument("--cache-only", action="store_true", help="Read cached search/Topic data without network calls")
    parser.add_argument("--dry-run", action="store_true", help="Run matching without writing output files")
    parser.add_argument("--no-rebuild", action="store_true", help="Skip rebuilding player HTML/JS after matching")
    args = parser.parse_args()
    find_composer_videos("naomi-shemer", cache_only=args.cache_only, dry_run=args.dry_run, rebuild=not args.no_rebuild)


if __name__ == "__main__":
    main()
