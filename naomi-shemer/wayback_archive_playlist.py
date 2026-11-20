#!/usr/bin/env python3
"""Backward-compatible wrapper delegating Naomi Shemer Wayback archival checks to `core.backup`."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.backup import (  # noqa: E402
    archive_composer_wayback,
    check_wayback,
    save_to_wayback,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check and optionally archive Naomi Shemer video URLs on Wayback Machine.")
    parser.add_argument("--all", action="store_true", help="Check all videos (default: non-Topic rare channels)")
    parser.add_argument("--save", action="store_true", help="Submit unarchived URLs to web.archive.org/save/")
    parser.add_argument("--limit", type=int, default=50, help="Max URLs to check/save in one run")
    args = parser.parse_args()
    archive_composer_wayback("naomi-shemer", check_all=args.all, save=args.save, limit=args.limit)


if __name__ == "__main__":
    main()
