#!/usr/bin/env python3
"""Backward-compatible wrapper delegating Naomi Shemer streaming matching to `core.streaming_matcher`."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.streaming_matcher import (  # noqa: E402
    StreamingCache,
    clean_query_title,
    match_composer_streaming,
    primary_artist_query,
)

SCRATCH_CACHE_PATH = Path(
    "/Users/dmtsurel/.gemini/antigravity/brain/9a49a808-8c60-4b11-9069-859ff68f7c57/scratch/streaming_api_cache.json"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Match Naomi Shemer songs against Deezer/iTunes IL for Spotify import.")
    parser.add_argument("--cache-file", help="Optional path to streaming API JSON cache")
    parser.add_argument("--output-dir", help="Optional output directory override")
    parser.add_argument("--cache-only", action="store_true", help="Read cache only without HTTP requests")
    args = parser.parse_args()

    cache_path = Path(args.cache_file) if args.cache_file else (SCRATCH_CACHE_PATH if SCRATCH_CACHE_PATH.exists() else None)
    match_composer_streaming(
        "naomi-shemer",
        cache_file=cache_path,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        cache_only=args.cache_only,
    )


if __name__ == "__main__":
    main()
