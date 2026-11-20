"""Declarative composer, registry, and curation overrides loaders."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
CREATORS_JSON_PATH = REPO_ROOT / "creators.json"

DEFAULT_TIER_FILTER_OPTIONS: list[list[str]] = [
    ["1_album_creator", "אלבום של היוצר"],
    ["2_album_original", "אלבום מבצע מקורי"],
    ["3_creator_performance", "ביצוע היוצר"],
    ["4_original_performance", "ביצוע מקורי"],
    ["5_cover", "ביצוע נוסף / קאבר"],
]

DEFAULT_ROLE_FILTER_OPTIONS: list[list[str]] = [
    ["words_and_music", "מילים ולחן"],
    ["music_only", "לחן בלבד"],
    ["words_only", "מילים בלבד"],
    ["translation", "תרגום"],
    ["performance_only", "ביצוע בלבד"],
]


@dataclass
class ComposerConfig:
    """Loaded declarative configuration for one composer collection."""

    slug: str
    name_he: str
    name_en: str
    playlist_title_he: str
    collection_prefix_he: str
    subtitle_he: str
    hub_description_he: str
    playlist_description_he: str
    meta_description_template: str
    og_description_template: str
    footer_label_he: str
    storage_prefix: str
    youtube_playlist_id: str = ""
    spotify_playlist_url: str = ""
    is_performer: bool = False
    dual_performance_mode: str = "original_only"
    default_role_label_heb: str = ""
    creator_performance_tag_he: str = ""
    creator_album_tiers: list[str] = field(default_factory=lambda: ["1_album_naomi", "1_album_creator"])
    creator_performance_tiers: list[str] = field(
        default_factory=lambda: ["1_album_naomi", "3_naomi_performance", "1_album_creator", "3_creator_performance"]
    )
    tier_filter_options: list[list[str]] = field(default_factory=lambda: [list(x) for x in DEFAULT_TIER_FILTER_OPTIONS])
    role_filter_options: list[list[str]] = field(default_factory=lambda: [list(x) for x in DEFAULT_ROLE_FILTER_OPTIONS])
    files: dict[str, str] = field(default_factory=dict)
    sources: dict[str, Any] = field(default_factory=dict)
    discography: dict[str, Any] = field(default_factory=dict)
    ranking: dict[str, Any] = field(default_factory=dict)
    block_meta: dict[str, dict[str, str]] = field(default_factory=dict)
    jump_groups: list[dict[str, Any]] = field(default_factory=list)
    base_url: str = "https://dmtsurel.github.io/playlists"

    @property
    def dir(self) -> Path:
        return REPO_ROOT / self.slug

    def _file_path(self, key: str, default_name: str) -> Path:
        return self.dir / self.files.get(key, default_name)

    @property
    def playlist_json(self) -> Path:
        return self._file_path("playlist_json", "playlist.json")

    @property
    def catalog_json(self) -> Path:
        return self._file_path("catalog_json", "catalog.json")

    @property
    def playlist_csv(self) -> Path:
        return self._file_path("playlist_csv", "playlist.csv")

    @property
    def playlist_md(self) -> Path:
        return self._file_path("playlist_md", "playlist.md")

    @property
    def streaming_import_csv(self) -> Path:
        return self._file_path("streaming_import_csv", "streaming_import.csv")

    @property
    def stream_m3u8(self) -> Path:
        return self._file_path("stream_m3u8", "youtube_stream.m3u8")

    @property
    def wayback_txt(self) -> Path:
        return self._file_path("wayback_txt", "wayback_backup_urls.txt")

    @property
    def index_html(self) -> Path:
        return self.dir / "index.html"

    @property
    def playlist_data_js(self) -> Path:
        return self.dir / "playlist_data.js"

    @property
    def legacy_player_html(self) -> Path | None:
        name = self.files.get("legacy_player_html", "")
        return (self.dir / name) if name else None

    @property
    def create_js(self) -> Path:
        return self.dir / self.files.get("create_js", "create_playlist_in_browser.js")

    @property
    def update_js(self) -> Path:
        return self.dir / self.files.get("update_js", "update_existing_playlist_in_browser.js")

    @property
    def public_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.slug}/"

    @property
    def js_function_suffix(self) -> str:
        return "".join(part.capitalize() for part in self.slug.split("-") if part) or "Composer"

    @property
    def tail_video_ids(self) -> set[str]:
        return set(self.ranking.get("tail_video_ids", []))

    @property
    def tail_performer_keywords(self) -> tuple[str, ...]:
        return tuple(self.ranking.get("tail_performer_keywords", ["סקיצה נדירה"]))

    @property
    def tv_album_group(self) -> str:
        return str(self.ranking.get("tv_album_group", "תוכניות טלוויזיה ומופעים מלאים"))


def load_registry() -> dict[str, Any]:
    """Load root creators.json registry."""
    return json.loads(CREATORS_JSON_PATH.read_text(encoding="utf-8"))


def list_enabled_slugs() -> list[str]:
    """Return slugs of enabled composers in registry order."""
    reg = load_registry()
    return [c["slug"] for c in reg.get("creators", []) if c.get("enabled", True)]


def load_composer(slug: str) -> ComposerConfig:
    """Load and validate `<slug>/composer.json`."""
    reg = load_registry()
    cfg_path = REPO_ROOT / slug / "composer.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing composer config: {cfg_path}")
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    prof = raw.get("profile", {})
    name_he = raw["name_he"]
    return ComposerConfig(
        slug=raw.get("slug", slug),
        name_he=name_he,
        name_en=raw.get("name_en", slug),
        playlist_title_he=raw.get("playlist_title_he", f"שירי {name_he}"),
        collection_prefix_he=raw.get("collection_prefix_he", f"משירי {name_he}"),
        subtitle_he=raw.get("subtitle_he", ""),
        hub_description_he=raw.get("hub_description_he", ""),
        playlist_description_he=raw.get("playlist_description_he", ""),
        meta_description_template=raw.get("meta_description_template", ""),
        og_description_template=raw.get("og_description_template", ""),
        footer_label_he=raw.get("footer_label_he", f"קטלוג שירי {name_he}"),
        storage_prefix=raw.get("storage_prefix", f"{slug.replace('-', '_')}_playlist_"),
        youtube_playlist_id=raw.get("youtube_playlist_id", ""),
        spotify_playlist_url=raw.get("spotify_playlist_url", ""),
        is_performer=bool(prof.get("is_performer", False)),
        dual_performance_mode=prof.get("dual_performance_mode", "original_only"),
        default_role_label_heb=prof.get("default_role_label_heb", f"מילים ולחן: {name_he}"),
        creator_performance_tag_he=prof.get("creator_performance_tag_he", f"ביצוע {name_he}"),
        creator_album_tiers=list(prof.get("creator_album_tiers", ["1_album_naomi", "1_album_creator"])),
        creator_performance_tiers=list(
            prof.get("creator_performance_tiers", ["1_album_naomi", "3_naomi_performance", "1_album_creator", "3_creator_performance"])
        ),
        tier_filter_options=list(prof.get("tier_filter_options", DEFAULT_TIER_FILTER_OPTIONS)),
        role_filter_options=list(prof.get("role_filter_options", DEFAULT_ROLE_FILTER_OPTIONS)),
        files=dict(raw.get("files", {})),
        sources=dict(raw.get("sources", {})),
        discography=dict(raw.get("discography", {})),
        ranking=dict(raw.get("ranking", {})),
        block_meta=dict(raw.get("block_meta", {})),
        jump_groups=list(raw.get("jump_groups", [])),
        base_url=raw.get("base_url") or reg.get("base_url", "https://dmtsurel.github.io/playlists"),
    )


def load_overrides(slug: str) -> dict[str, Any]:
    """Load optional `<slug>/overrides.json` curation rules."""
    ov_path = REPO_ROOT / slug / "overrides.json"
    if not ov_path.exists():
        return {}
    return json.loads(ov_path.read_text(encoding="utf-8"))
