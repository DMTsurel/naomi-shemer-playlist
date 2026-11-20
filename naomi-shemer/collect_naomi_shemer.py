#!/usr/bin/env python3
"""Backward-compatible shim delegating Naomi Shemer catalog collection to `core.catalog_collector`."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.catalog_collector import collect_composer_catalog  # noqa: E402
from core.config import load_overrides  # noqa: E402
from core.hebrew import clean_wiki_markup, clean_wiki_song_title, normalize_catalog_song_title  # noqa: E402, F401


def normalize_song_title(title: str) -> str:
    """Normalize a Naomi Shemer song title using overrides.json synonym_map."""
    return normalize_catalog_song_title(title, load_overrides("naomi-shemer").get("synonym_map", {}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect & merge Naomi Shemer catalog from 9 sources.")
    parser.add_argument("--cache-only", action="store_true", help="Read raw_cache only without network calls")
    parser.add_argument("--refresh", action="store_true", help="Re-fetch enabled sources ignoring cached files")
    parser.add_argument("--dry-run", action="store_true", help="Merge catalog without writing files")
    args = parser.parse_args()
    collect_composer_catalog("naomi-shemer", cache_only=args.cache_only, refresh=args.refresh, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
