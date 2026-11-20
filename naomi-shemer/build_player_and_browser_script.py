#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backward-compatible shim delegating Naomi Shemer builds to core.build_site."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.artists import (  # noqa: E402, F401
    ACUM_INLINE_PAIR_SUBS,
    ACUM_PERFORMER_EXACT_MAP,
    _clean_artist_name,
    _clean_display_album,
    normalize_performer_name,
    normalize_performers_list,
)
from core.build_site import (  # noqa: E402
    build_composer,
    sync_all_secondary_exports as _core_sync_all_secondary_exports,
    validate_and_normalize_playlist as _core_validate_and_normalize_playlist,
)
from core.config import load_composer  # noqa: E402

BASE_DIR = str(Path(__file__).resolve().parent)


def validate_and_normalize_playlist(data: dict) -> bool:
    """Validate and normalize Naomi Shemer playlist data using composer.json config."""
    return _core_validate_and_normalize_playlist(data, load_composer("naomi-shemer"))


def sync_all_secondary_exports(data: dict) -> list[str]:
    """Regenerate CSV, MD, M3U8, streaming CSV, and Wayback URLs for Naomi Shemer."""
    return [str(p) for p in _core_sync_all_secondary_exports(data, load_composer("naomi-shemer"))]


def generate_files(standalone: bool = False) -> None:
    """Build all outputs for Naomi Shemer and regenerate the root Hub."""
    build_composer("naomi-shemer", standalone=standalone, rebuild_hub=True)


if __name__ == "__main__":
    generate_files()
