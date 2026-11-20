#!/usr/bin/env python3
"""Backward-compatible wrapper delegating Naomi Shemer auto-heal monitoring to `core.health`."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.health import (  # noqa: E402
    check_video_health,
    heal_composer_playlist,
    search_youtube_candidates,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Naomi Shemer playlist via oEmbed and auto-heal broken videos.")
    parser.add_argument("--dry-run", action="store_true", help="Check only without modifying files")
    args = parser.parse_args()
    heal_composer_playlist("naomi-shemer", dry_run=args.dry_run)


if __name__ == "__main__":
    main()
