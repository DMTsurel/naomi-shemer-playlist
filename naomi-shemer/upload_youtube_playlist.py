#!/usr/bin/env python3
"""Backward-compatible shim delegating Naomi Shemer YouTube upload to `core.youtube_uploader`."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.config import load_composer  # noqa: E402
from core.youtube_uploader import (  # noqa: E402, F401
    load_composer_video_ids,
    upload_composer_via_cookies,
    upload_composer_via_oauth,
)


def load_video_ids() -> list[dict[str, str]]:
    """Load matched Naomi Shemer YouTube video IDs from playlist JSON."""
    return load_composer_video_ids("naomi-shemer")


def upload_via_cookies(cookies_file: str) -> str:
    """Upload Naomi Shemer playlist using InnerTube + cookies.txt."""
    return upload_composer_via_cookies("naomi-shemer", cookies_file)


def upload_via_oauth() -> str:
    """Upload Naomi Shemer playlist using official YouTube Data API v3 + OAuth."""
    return upload_composer_via_oauth("naomi-shemer")


def main() -> None:
    parser = argparse.ArgumentParser(description="העלאת פלייליסט שירי נעמי שמר ליוטיוב")
    parser.add_argument("--cookies", help="נתיב לקובץ cookies.txt בפורמט Netscape/Mozilla")
    parser.add_argument("--oauth", action="store_true", help="שימוש ב-OAuth 2.0 רשמי (client_secret.json)")
    args = parser.parse_args()

    if args.cookies:
        upload_via_cookies(args.cookies)
    elif args.oauth:
        upload_via_oauth()
    else:
        cfg = load_composer("naomi-shemer")
        print("בחר שיטת העלאה:")
        print(f"  1. דפדפן: פתח {cfg.create_js}")
        print("  2. cookies.txt: python3 scripts/cli.py upload naomi-shemer --cookies cookies.txt")
        print("  3. OAuth: python3 scripts/cli.py upload naomi-shemer --oauth")


if __name__ == "__main__":
    main()
