#!/usr/bin/env python3
"""Backward-compatible wrapper delegating Naomi Shemer InnerTube health checks to `core.health`."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.health import (  # noqa: E402
    _check_video_player,
    _fetch_live_playlist_ids,
    _fetch_yt_config,
    check_composer_health,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check YouTube health of Naomi Shemer playlist videos.")
    parser.add_argument("--json-report", help="Optional path to write JSON health report.")
    parser.add_argument("--skip-live-playlist", action="store_true", help="Skip live YouTube playlist comparison.")
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically replace unavailable videos with their best healthy backup and rebuild exports.",
    )
    args = parser.parse_args()

    _, rc = check_composer_health(
        "naomi-shemer",
        json_report=Path(args.json_report) if args.json_report else None,
        skip_live_playlist=args.skip_live_playlist,
        auto_fix=args.auto_fix,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
