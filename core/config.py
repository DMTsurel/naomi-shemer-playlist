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
    creator_aliases: list[str] = field(default_factory=list)
    creator_surname_tokens: list[str] = field(default_factory=list)
    creator_tie_markers: list[str] = field(default_factory=list)
    creator_dual_role: str = "creator_performance"
    active_year_range: tuple[int, int] = (1920, 2030)
    custom_dir: Path | None = None

    @property
    def dir(self) -> Path:
        return self.custom_dir if self.custom_dir is not None else (REPO_ROOT / self.slug)

    def _file_path(self, key: str, default_name: str) -> Path:
        return self.dir / self.files.get(key, default_name)

    @property
    def playlist_json(self) -> Path:
        return self._file_path("playlist_json", "playlist.json")

    @property
    def catalog_json(self) -> Path:
        return self._file_path("catalog_json", "catalog.json")

    @property
    def songs_csv(self) -> Path:
        return self._file_path("songs_csv", "songs.csv")

    @property
    def albums_csv(self) -> Path:
        return self._file_path("albums_csv", "albums.csv")

    @property
    def summary_md(self) -> Path:
        return self._file_path("summary_md", "summary.md")

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
    def metadata_backup_json(self) -> Path:
        return self._file_path("metadata_backup_json", "youtube_full_metadata_backup.json")

    @property
    def health_report_md(self) -> Path:
        return self._file_path("health_report_md", "health_check_report.md")

    @property
    def health_report_json(self) -> Path:
        return self._file_path("health_report_json", "health_report.json")

    @property
    def spotify_export_dir(self) -> Path:
        return self._file_path("spotify_export_dir", "spotify_export")

    @property
    def default_streaming_cache(self) -> Path:
        custom = self.files.get("streaming_cache_json", "")
        return (self.dir / custom) if custom else (self.dir / "raw_cache" / "streaming_api_cache.json")

    @property
    def musical_album_keywords(self) -> list[str]:
        return list(self.discography.get("musical_album_keywords", []))

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

    @property
    def raw_cache_dir(self) -> Path:
        return self.dir / "raw_cache"

    @property
    def youtube_search_cache_json(self) -> Path:
        return self.raw_cache_dir / "youtube_search_cache.json"

    @property
    def youtube_topic_albums_cache_json(self) -> Path:
        return self.raw_cache_dir / "youtube_topic_albums.json"

    @property
    def upload_progress_json(self) -> Path:
        return self.raw_cache_dir / "youtube_upload_progress.json"

    @property
    def oauth_token_json(self) -> Path:
        return self.raw_cache_dir / "youtube_oauth_token.json"

    @property
    def creator_album_tier(self) -> str:
        return self.creator_album_tiers[0] if self.creator_album_tiers else "1_album_creator"

    @property
    def creator_performance_tier(self) -> str:
        album_tier = self.creator_album_tier
        for t in self.creator_performance_tiers:
            if t != album_tier:
                return t
        return "3_creator_performance"

    @property
    def creator_acum_reversed_name(self) -> str:
        explicit = str(self.sources.get("acum_reversed_name") or "").strip()
        if explicit:
            return explicit
        words = [w for w in self.name_he.split() if w]
        if len(words) == 2:
            return f"{words[1]} {words[0]}"
        return self.name_he

    @property
    def nli_creator_inverted(self) -> str:
        explicit = str(self.sources.get("nli_creator_inverted") or "").strip()
        if explicit:
            return explicit
        base = str(self.sources.get("nli_author") or self.name_he).strip()
        parts = [p for p in base.split() if p]
        if len(parts) >= 2:
            return f"{parts[-1]}, {' '.join(parts[:-1])}"
        return base


def load_registry() -> dict[str, Any]:
    """Load root creators.json registry."""
    return json.loads(CREATORS_JSON_PATH.read_text(encoding="utf-8"))


def list_enabled_slugs() -> list[str]:
    """Return slugs of enabled composers in registry order."""
    reg = load_registry()
    return [c["slug"] for c in reg.get("creators", []) if c.get("enabled", True)]


def _default_creator_aliases(name_he: str, name_en: str) -> list[str]:
    aliases: list[str] = []
    words_he = [w for w in name_he.split() if w]
    candidates = [name_he]
    if len(words_he) == 2:
        candidates.append(f"{words_he[1]} {words_he[0]}")
    if name_en:
        candidates.append(name_en)
    for item in candidates:
        s = item.strip()
        if s and s not in aliases:
            aliases.append(s)
    return aliases


def _default_surname_tokens(name_he: str, name_en: str) -> list[str]:
    tokens: list[str] = []
    for raw in (name_he, name_en.lower()):
        parts = [p.strip() for p in raw.split() if p.strip()]
        if parts and len(parts[-1]) >= 3 and parts[-1] not in tokens:
            tokens.append(parts[-1])
    return tokens


def load_composer(slug: str, composer_dir: Path | None = None) -> ComposerConfig:
    """Load and validate `<slug>/composer.json`."""
    reg = load_registry() if CREATORS_JSON_PATH.exists() else {}
    target_dir = composer_dir if composer_dir is not None else (REPO_ROOT / slug)
    cfg_path = target_dir / "composer.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing composer config: {cfg_path}")
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    prof = raw.get("profile", {})
    name_he = raw["name_he"]
    name_en = raw.get("name_en", slug)
    aliases = list(prof.get("creator_aliases") or _default_creator_aliases(name_he, name_en))
    surname_tokens = list(prof.get("creator_surname_tokens") or _default_surname_tokens(name_he, name_en))
    yr_raw = prof.get("active_year_range")
    if isinstance(yr_raw, (list, tuple)) and len(yr_raw) == 2:
        year_range = (int(yr_raw[0]), int(yr_raw[1]))
    else:
        year_range = (1920, 2030)
    return ComposerConfig(
        slug=raw.get("slug", slug),
        name_he=name_he,
        name_en=name_en,
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
        creator_aliases=aliases,
        creator_surname_tokens=surname_tokens,
        creator_tie_markers=list(prof.get("creator_tie_markers", [])),
        creator_dual_role=str(prof.get("creator_dual_role") or "creator_performance"),
        active_year_range=year_range,
        custom_dir=composer_dir,
    )


def load_overrides(slug: str, composer_dir: Path | None = None) -> dict[str, Any]:
    """Load optional `<slug>/overrides.json` curation rules."""
    target_dir = composer_dir if composer_dir is not None else (REPO_ROOT / slug)
    ov_path = target_dir / "overrides.json"
    if not ov_path.exists():
        return {}
    return json.loads(ov_path.read_text(encoding="utf-8"))
