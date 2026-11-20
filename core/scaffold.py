"""Composer skeleton generator for onboarding new Israeli composers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import CREATORS_JSON_PATH, REPO_ROOT


def scaffold_composer(
    slug: str,
    name_he: str,
    name_en: str,
    is_performer: bool = False,
    enable: bool = False,
    base_dir: Path | None = None,
    register: bool = True,
) -> dict[str, Any]:
    """Create `<slug>/composer.json`, `overrides.json`, starter `README.md`, and optional `creators.json` entry."""
    target_dir = base_dir if base_dir is not None else (REPO_ROOT / slug)
    cfg_path = target_dir / "composer.json"
    if cfg_path.exists():
        raise FileExistsError(f"Composer config already exists: {cfg_path}")

    target_dir.mkdir(parents=True, exist_ok=True)
    storage_prefix = f"{slug.replace('-', '_')}_playlist_"

    he_words = [w for w in name_he.split() if w]
    en_words = [w for w in name_en.lower().split() if w]
    default_aliases = [name_he]
    if len(he_words) == 2:
        default_aliases.append(f"{he_words[1]} {he_words[0]}")
    if name_en and name_en not in default_aliases:
        default_aliases.append(name_en)
    default_surnames: list[str] = []
    for tok in (he_words[-1] if he_words else "", en_words[-1] if en_words else ""):
        if len(tok) >= 3 and tok not in default_surnames:
            default_surnames.append(tok)
    nli_inverted = f"{he_words[-1]}, {' '.join(he_words[:-1])}" if len(he_words) >= 2 else name_he

    if is_performer:
        dual_mode = "original_plus_creator"
        tier_filter_options = [
            ["1_album_creator", f"אלבום של {name_he}"],
            ["2_album_original", "אלבום מבצע מקורי"],
            ["3_creator_performance", f"ביצוע {name_he}"],
            ["4_original_performance", "ביצוע מקורי"],
            ["5_cover", "ביצוע נוסף / קאבר"],
        ]
        role_filter_options = [
            ["words_and_music", f"מילים ולחן: {name_he}"],
            ["music_only", "לחן בלבד"],
            ["words_only", "מילים בלבד"],
            ["translation", "תרגום"],
            ["performance_only", "ביצוע בלבד"],
        ]
    else:
        dual_mode = "original_only"
        tier_filter_options = [
            ["2_album_original", "אלבום מבצע מקורי"],
            ["4_original_performance", "ביצוע מקורי"],
            ["5_cover", "ביצוע נוסף / קאבר"],
        ]
        role_filter_options = [
            ["words_and_music", f"מילים ולחן: {name_he}"],
            ["music_only", "לחן בלבד"],
            ["words_only", "מילים בלבד"],
            ["translation", "תרגום"],
        ]

    composer_cfg: dict[str, Any] = {
        "slug": slug,
        "name_he": name_he,
        "name_en": name_en,
        "playlist_title_he": f"שירי {name_he}",
        "collection_prefix_he": f"משירי {name_he}",
        "subtitle_he": f"האוסף המקיף מאוחד ממאגרי אקו\"ם, הספרייה הלאומית, שירונט, זמרשת ועוד — מסודר מהקלאסיקות הגדולות אל הפנינים הנדירות.",
        "hub_description_he": f"האוסף הכרונולוגי והקאנוני המקיף של שירי {name_he}: ביצועים מקוריים, אלבומים היסטוריים ו-{{unmatched_songs}} שירי ארכיון משלימים שאינם ביוטיוב.",
        "playlist_description_he": f"פלייליסט מקיף וכרונולוגי של שירי {name_he}, מאוחד ממקורות אקו\"ם, הספרייה הלאומית, שירונט, זמרשת ויוטיוב.",
        "meta_description_template": f"האוסף המקיף של שירי {name_he} ({{total_catalog_songs}} שירים): {{total_videos}} ביצועים ביוטיוב ו-{{unmatched_songs}} שירי ארכיון.",
        "og_description_template": f"נגן אינטראקטיבי וקטלוג מלא של שירי {name_he}.",
        "footer_label_he": f"קטלוג שירי {name_he}",
        "storage_prefix": storage_prefix,
        "youtube_playlist_id": "",
        "spotify_playlist_url": "",
        "profile": {
            "is_performer": is_performer,
            "dual_performance_mode": dual_mode,
            "default_role_label_heb": f"מילים ולחן: {name_he}",
            "creator_performance_tag_he": f"ביצוע {name_he}",
            "creator_album_tiers": ["1_album_creator"],
            "creator_performance_tiers": ["1_album_creator", "3_creator_performance"],
            "tier_filter_options": tier_filter_options,
            "role_filter_options": role_filter_options,
            "creator_aliases": default_aliases,
            "creator_surname_tokens": default_surnames,
            "creator_tie_markers": [],
            "creator_dual_role": "creator_performance",
            "active_year_range": [1920, 2030],
        },
        "files": {
            "playlist_json": "playlist.json",
            "catalog_json": "catalog.json",
            "songs_csv": "songs.csv",
            "albums_csv": "albums.csv",
            "summary_md": "summary.md",
            "playlist_csv": "playlist.csv",
            "playlist_md": "playlist.md",
            "streaming_import_csv": "streaming_import.csv",
            "stream_m3u8": "youtube_stream.m3u8",
            "wayback_txt": "wayback_backup_urls.txt",
            "metadata_backup_json": "youtube_full_metadata_backup.json",
            "health_report_md": "health_check_report.md",
            "health_report_json": "health_report.json",
            "spotify_export_dir": "spotify_export",
            "legacy_player_html": "",
        },
        "sources": {
            "acum_creator_id": "",
            "acum_performer_ids": [],
            "shironet_prfid": None,
            "discogs_artist_id": None,
            "musicbrainz_artist_id": "",
            "zemereshet_artist_id": None,
            "stereo_ve_mono_artist": name_he.replace(" ", "_"),
            "nli_author": name_he,
            "nli_creator_inverted": nli_inverted,
            "nli_archive_queries": [],
            "wiki_page": name_he,
            "wiki_works_sections": ["יצירותיו", "יצירותיה", "דיסקוגרפיה"],
            "wiki_extra_pages": [],
            "zemereshet_slug": name_he,
            "pizmonet_slug": name_he,
        },
        "discography": {
            "official_topic_playlists": [],
            "solo_album_keywords": [],
            "musical_album_keywords": [f"שירי {name_he}", name_en.lower()],
            "verified_albums": [],
            "trusted_creator_channels": [],
            "canonical_albums": [],
        },
        "ranking": {
            "mode": "sqrt_mult",
            "anthology_cap": 100.0,
            "canonical_anthologies": [],
            "translation_full_credit_titles": [],
            "tail_video_ids": [],
            "tail_performer_keywords": ["סקיצה נדירה"],
            "tv_album_group": "תוכניות טלוויזיה ומופעים מלאים",
        },
        "block_meta": {
            "p1": {"label": "🌟 הקלאסיקות הגדולות", "short": "🌟 קלאסיקות"},
            "p2": {"label": "💿 אלבומים, הצגות והרכבים", "short": "💿 אלבומים והרכבים"},
            "p3": {"label": "💎 פנינים נדירות וארכיון", "short": "💎 פנינים נדירות"},
            "e1": {"label": "➕ גרסאות נוספות — הקלאסיקות", "short": "➕ ביצועים נוספים"},
            "e2": {"label": "➕ גרסאות נוספות — אלבומים והרכבים", "short": "➕ ביצועים נוספים"},
            "e3": {"label": "➕ גרסאות נוספות — פנינים נדירות", "short": "➕ ביצועים נוספים"},
            "tail": {"label": "🎙️ סקיצות אולפן וראיונות ארכיוניים", "short": "🎙️ סקיצות"},
            "tv": {"label": "📺 תוכניות טלוויזיה ומופעים מלאים", "short": "📺 תוכניות מלאות"},
        },
        "jump_groups": [
            {"id": "p1", "blocks": ["p1"], "short": "🌟 קלאסיקות", "title": "הקלאסיקות הגדולות"},
            {"id": "p2", "blocks": ["p2"], "short": "💿 אלבומים והרכבים", "title": "אלבומים, הצגות והרכבים"},
            {"id": "p3", "blocks": ["p3"], "short": "💎 פנינים נדירות", "title": "פנינים נדירות וארכיון"},
            {"id": "extras", "blocks": ["e1", "e2", "e3"], "short": "➕ ביצועים נוספים", "title": "גרסאות וביצועים נוספים"},
            {"id": "tail", "blocks": ["tail"], "short": "🎙️ סקיצות", "title": "סקיצות אולפן וראיונות ארכיוניים"},
            {"id": "tv", "blocks": ["tv"], "short": "📺 תוכניות מלאות", "title": "תוכניות טלוויזיה ומופעים מלאים"},
        ],
    }

    overrides_cfg: dict[str, Any] = {
        "bad_video_ids": {},
        "performance_only_strict_creator_match": True,
        "songs_requiring_explicit_creator": [],
        "homonym_block_tokens": {},
        "strict_archive_allowed_performers": {},
        "skip_alt_titles_for_archive": [],
        "noisy_catalog_albums": [],
        "synonym_map": {},
        "excluded_normalized_songs": [],
        "excluded_non_creator_notes": [],
        "streaming_performer_overrides": {},
        "split_composition_guards": {},
        "collector_overrides": {},
        "finder_overrides": {},
    }

    readme_text = "\n".join([
        f"# 🎵 שירי {name_he} – האוסף המקיף",
        "",
        f"תשתית האוסף והנגן עבור **{name_he}** (`{name_en}`).",
        "",
        "## זרימת עבודה",
        "1. מלאו את מזהי המקורות ב-`composer.json` (אקו\"ם, הספרייה הלאומית, שירונט, ויקיפדיה, זמרשת, Discogs, MusicBrainz).",
        f"2. איסוף ואיתור ראשוני: `python3 scripts/cli.py collect {slug}` ולאחר מכן `python3 scripts/cli.py find-videos {slug}`.",
        "3. עברו על `catalog.json` ו-`playlist.json` לפי כללי האוצרות והדירוג (`AGENTS.md` וה־skill `.agents/skills/new-composer-playlist/`).",
        f"4. הריצו בדיקות איכות ובנייה: `python3 scripts/cli.py qa {slug} --strict` ו-`python3 scripts/cli.py build {slug}`.",
        "5. העבירו ל-`\"enabled\": true` ב-`creators.json` ובנו את השער: `python3 scripts/cli.py build --all`.",
        "",
    ])

    overrides_path = target_dir / "overrides.json"
    readme_path = target_dir / "README.md"

    cfg_path.write_text(json.dumps(composer_cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    overrides_path.write_text(json.dumps(overrides_cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme_path.write_text(readme_text, encoding="utf-8")

    registered = False
    if register and CREATORS_JSON_PATH.exists():
        reg = json.loads(CREATORS_JSON_PATH.read_text(encoding="utf-8"))
        creators = reg.setdefault("creators", [])
        if not any(c.get("slug") == slug for c in creators):
            creators.append({"slug": slug, "enabled": enable})
            CREATORS_JSON_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            registered = True

    return {
        "slug": slug,
        "dir": str(target_dir),
        "composer_json": str(cfg_path),
        "overrides_json": str(overrides_path),
        "readme_md": str(readme_path),
        "registered": registered,
        "enabled": enable,
    }
