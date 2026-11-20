#!/usr/bin/env python3
"""Backward-compatible wrapper delegating Naomi Shemer YouTube metadata backup to `core.backup`."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.backup import (  # noqa: E402
    _parse_player_response,
    backup_composer_metadata,
    enrich_alternative_videos,
    fetch_video_metadata,
)


def main() -> None:
    backup_composer_metadata("naomi-shemer")


if __name__ == "__main__":
    main()
