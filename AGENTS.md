# Multi-Composer Israeli Playlists — Project Rules & Curation Standards

This repository powers curated, source-merged Israeli composer catalogs, YouTube playlists, and interactive GitHub Pages players (`https://dmtsurel.github.io/playlists/`). Apply these rules to **every** composer added under this repo.

## 1. Repository Architecture

- `assets/` — Shared frontend player (`player.css`, `player.js`). Keep all UI logic composer-agnostic; read creator metadata from `window.PLAYLIST_DATA.config`.
- `core/` — Shared Python engine:
  - `config.py`: `creators.json` + `<slug>/composer.json` + `<slug>/overrides.json`.
  - `hebrew.py` & `artists.py`: Hebrew normalization (`norm_heb`, `heb_loose`), title similarity, transliteration, ACUM `"שם משפחה שם פרטי"` reversal fixes, and artist alias tables.
  - `build_site.py`: Normalization, integrity validation (`bad_video_ids`, unique primary `video_id`s, valid tiers), HTML/JS build (`index.html`, `playlist_data.js`), YouTube browser sync scripts (`create_playlist_in_browser.js`, `update_existing_playlist_in_browser.js`), exports (`.csv`, `.md`, `.m3u8`, `wayback_backup_urls.txt`), and root Hub (`index.html`).
  - `ranking.py`, `health.py`, `backup.py`, `streaming_matcher.py`, `qa.py`, `scaffold.py`.
- `scripts/cli.py` — Unified CLI (`list`, `matrix-json`, `build`, `hub`, `health`, `heal`, `backup`, `wayback`, `rank`, `spotify`, `qa`, `init-composer`).
- `<slug>/` — Composer-specific configs (`composer.json`, `overrides.json`) and generated/curated datasets (`playlist.json`, `catalog.json`, exports). **Do not duplicate shared CSS/JS/Python logic inside `<slug>/`.**

## 2. Attribution & Catalog Integrity Rules

- **Strict `performance_only` guard:** If the creator only *performed* a work written by others (e.g., in children's/holiday albums), set `performance_only_strict_creator_match: true` in `overrides.json`. NEVER include other artists' covers of that work in YouTube or Spotify exports — only recordings actually performed by the creator.
- **Explicit proof for homonyms & generic titles:** Short/ambiguous titles (1–2 words) require an explicit creator tie in description/album/performer (`songs_requiring_explicit_creator`) and negative keyword filters (`homonym_block_tokens`, e.g., preventing Yoni Rechter's `"דמעות"` or Yair Rosenblum's `"האם השלישית"`).
- **Split distinct works sharing a title:** Same title + different music or lyrics must be split into separate catalog entries (e.g., `"שיר (לחן א')"` vs `"שיר (לחן ב')"` with `split_composition_guards`, or separate years when compositions differ).
- **Complete deletion of excluded songs:** When removing a non-creator or false-positive song, delete it from **both** `playlist.json` and `catalog.json` and record it in `overrides.json` (`excluded_normalized_songs` + `excluded_non_creator_notes`) so future runs never re-add it.
- **Name & metadata hygiene:** Normalize ACUM reversed names (`ACUM_PERFORMER_EXACT_MAP`) and never leave internal prefixes such as `ACUM_WRKNBR:` or placeholder year `2099` in user-visible outputs.

## 3. Audio Quality, Video Selection & Labeling

- **Source hierarchy:** Official `- Topic` / record-label studio album master > clean full official channel studio single > historical original recording > notable studio/live covers.
- **Full masters over truncated edits:** Prefer full archival/album masters over shortened compilation edits (even if the shortened edit has more views).
- **Trap check — YouTube Music `OLAK` live swaps:** YouTube Music album playlists sometimes map an album track to a *later live concert video* instead of the studio recording. Verify studio-tier tracks do not point to live concert footage when the studio master exists on `- Topic` / official OAC.
- **Mandatory exclusions:** Never select or promote karaoke, playback, instrumental-only backing tracks, AI-stripped vocals, amateur fan sound-remasters, sketches/speeches masquerading as the song, or short `< 65s` clips unless the real song itself is that short. Record bad IDs in `overrides["bad_video_ids"]`.
- **Authenticity of years & labels:**
  - `year` must reflect the **actual recording year**, not a later anthology/reissue CD year (use `chrono_index` for true chronological order).
  - Set `is_true_original: true` only on the genuine historical first recording (`[ביצוע מקורי]`). Do not label later creator self-covers as `[ביצוע מקורי]`.
  - Never expose internal taxonomy jargon (`"שכבה"`, `"נוספים"`, `"ביצוע מוביל"`) in visible UI strings.

## 4. Playlist Structure, Pairing & Ranking

- **Block order (`partition_matched_blocks`):** `p1` (Canon classics) -> `p2` (Albums, shows & ensembles) -> `p3` (Rare gems & archive) -> `e1..e3` (Additional performances, surfaced in UI under one unified jump pill `➕ ביצועים נוספים`) -> `tail` (Studio sketches & archival interviews grouped together) -> `tv` (Full TV programs & concerts at the very end).
- **Primary-block (`p1..p3`) pairing policy:**
  - If `profile.is_performer` is `true` (`dual_performance_mode = "original_plus_creator"`): at most 2 versions per song in `p1..p3`: `[true historical original]` + `[creator rendition]` (or vice versa per song policy). Never place **two creator versions** back-to-back, never place **two non-creator covers** in `p1..p3`, and never place a cover immediately after a creator original in `p1..p3`. Defer 3rd+ versions and non-creator second versions to `e1..e3`.
  - If `profile.is_performer` is `false` (`dual_performance_mode = "original_only"`): keep **only 1** primary version per song in `p1..p3`; put all covers/additional renditions in `e1..e3`.
- **Canonical Ranking (`ranking.py`):** Use Option C **`sqrt_mult`**:
  `round(Base * (1 + sqrt(song_wide_views / 1_000_000)), 1)`
  where `Base = acum_pts + min(anthology_cap, anth_pts) + wiki_pts + 6 * sources` (`anthology_cap = 100.0`, no artificial kids/holiday bonuses), weighted by aggregated **song-wide YouTube views across all cover versions** rather than a single selected video. **Do not** add Deezer-rank weighting into the formula (explicitly declined due to default `100,000` ties and incomplete catalog coverage).
- **Streaming export (`streaming_matcher.py`):** Exclude `tv` and `tail` items; respect `split_composition_guards`, `streaming_performer_overrides`, and `performance_only` strict creator guard; split Soundiiz CSV outputs into `<= 200` rows per file.

## 5. Copyright & Web UX Rules

- **Copyright safety:** Never embed copied multi-sentence biographical/historical paragraphs from NLI, Wikipedia, or books inside public `index.html`, `playlist_data.js`, or CSV exports. Publish only song titles, factual credits (`lyricist`, `composer`, `year`, `performer`), opening line quotes, and outbound archive links.
- **UX & accessibility invariants:**
  - Separate main playlist vs archive via ARIA `tablist`/`tabpanel` (never hide the main list behind a toggle button).
  - Keep prominent top search with real-time Hebrew-tolerant matching + clear button, dynamic Play CTA reflecting active filters (`▶ נגן N תוצאות`), empty states with one-click reset, and sticky mini-player (`<div class="mini-transport">`).
  - Keep transport buttons (`⏮ ▶ ⏭`) in `direction: ltr` even in `dir="rtl"` pages; render mobile (`<= 768px`) tables as stacked cards so no columns or archive links clip; never auto-play audio unprompted on page load.

## 6. Verification, Release & Safety

- Always run after data or code changes:
  1. `python3 scripts/cli.py build --all` (0 validation errors, builds Composer + exports + browser JS + Hub)
  2. `python3 scripts/cli.py qa <slug> --strict` (0 hard QA errors)
  3. `python3 -m py_compile core/*.py scripts/*.py` and `jsc` syntax check on modified JS
  4. Update count badges in `<slug>/README.md` and root `README.md` when track counts change
  5. Sync YouTube updater to macOS clipboard when playlist changed: `pbcopy < <slug>/update_existing_playlist_in_browser.js`
- **Never commit** `.github_deploy_key*`, `raw_cache/`, `__pycache__/`, or temporary `/tmp` test outputs.

## 7. Multi-Composer Roadmap (Future Phase 3)

Collection and initial YouTube matching (`naomi-shemer/collect_naomi_shemer.py`, `naomi-shemer/find_youtube_videos.py`) are not yet extracted into `core/`. When onboarding composer #2, extract those into `core/catalog_collector.py` and `core/youtube_finder.py` driven by `composer.json["sources"]` and `composer.json["discography"]`, then follow `.agents/skills/new-composer-playlist/SKILL.md`.
