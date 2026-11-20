#!/usr/bin/env python3
"""Backward-compatible wrapper delegating secondary exports to `core.build_site.sync_all_secondary_exports`."""

from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.build_site import sync_all_secondary_exports  # noqa: E402
from core.config import load_composer  # noqa: E402


def main() -> None:
    cfg = load_composer("naomi-shemer")
    data = json.loads(cfg.playlist_json.read_text(encoding="utf-8"))
    written = sync_all_secondary_exports(data, cfg)
    matched_count = sum(1 for x in data.get("playlist", []) if x.get("selected_video"))
    print(f"Exported {len(written)} secondary files for {matched_count} matched entries.")


if __name__ == "__main__":
    main()
