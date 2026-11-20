---
name: new-composer-playlist
description: >-
  End-to-end workflow and quality standards for building, curating, verifying, and
  publishing a new Israeli composer's catalog, YouTube playlist, and web player under
  this repository. Use when onboarding a new composer/lyricist/performer, auditing
  song attribution or audio quality, or organizing multi-version Israeli music catalogs.
---

# Creating a New Composer Playlist

Follow these stages whenever onboarding a new composer or performer into this repository. Consult [curation-checklist.md](./references/curation-checklist.md) for detailed heuristics, edge cases, and verification traps learned from the Naomi Shemer flagship collection.

## Workflow Stages

### Stage 1: Scaffold & Configure
1. Run `python3 scripts/cli.py init-composer <slug> --name-he "<שם בעברית>" --name-en "<English Name>" [--is-performer]` (keep `--enable` off until data is verified).
2. Populate `<slug>/composer.json`:
   - `sources`: `acum_creator_id`, `acum_performer_ids`, `shironet_prfid`, `discogs_artist_id`, `nli_author`, `wiki_page`, `zemereshet_slug`, `pizmonet_slug`.
   - `discography`: verified `official_topic_playlists` (`OLAK...` / `PL...`), `solo_album_keywords`, and `musical_album_keywords`.
   - `ranking`: define `canonical_anthologies` (verified creator songbooks/anthologies totaling <= `anthology_cap: 100.0`) and `translation_full_credit_titles` (canonical hits that remain full-credit).
   - Set `profile.is_performer` (`true` -> `original_plus_creator`; `false` -> `original_only`).

### Stage 2: Build the Unified Song Catalog (`catalog.json`)
1. Run `python3 scripts/cli.py collect <slug>` (`core/catalog_collector.py`) to gather and deduplicate works across ACUM, NLI (בית לזמר העברי + National Sound Archive), Shironet, Wikipedia, Zemereshet, Pizmonet, Stereo VeMono, Discogs, and MusicBrainz (any unconfigured source in `composer.json["sources"]` is skipped cleanly).
2. Tune cross-database merges using `overrides.json["synonym_map"]` and `collector_overrides`, preserving `alt_titles`, `opening_line`, `year`, `roles`, `role_category`, `co_creators_heb`, and `archive_links` (including open-audio `nli_audio` / `zemereshet_audio` links).
3. Clean ACUM reversed names via `core.artists.normalize_performers_list` and strip copied multi-sentence historical paragraphs (facts + links only).
4. Split homonyms or dual compositions (e.g., two different melodies sharing a title) into separate entries and document rules in `overrides.json["split_composition_guards"]`.

### Stage 3: Discover & Select YouTube Performances (`playlist.json`)
1. Run `python3 scripts/cli.py find-videos <slug> --no-rebuild` (`core/youtube_finder.py`) to harvest official `- Topic` playlists and YouTube search matches while enforcing `core.hebrew.has_bad_keyword`, `overrides["bad_video_ids"]`, `overrides["homonym_block_tokens"]`, `overrides["split_composition_guards"]`, and `overrides["songs_requiring_explicit_creator"]`.
2. Scan trusted archival/label YouTube channels for missing songs, live premieres, Yiddish/translated variants, and rare studio sketches.
3. Audit popular covers via **song-wide YouTube view aggregation** across all versions so iconic covers and viral hits are surfaced intentionally alongside historical originals.
4. For `role_category == "performance_only"`, enforce strict creator credit (`overrides["performance_only_strict_creator_match"] = true`).
5. **Inspect `OLAK` album playlists manually/programmatically** so YouTube's auto-mapped tracks do not substitute a live concert clip where a studio `- Topic` track exists, and prefer full album masters over shortened compilation edits.

### Stage 4: Classify Tiers, Recording Years & Blocks
1. Assign accurate **recording year** (not reissue/CD compilation year) and set `is_true_original: true` strictly on verified historical premiere recordings.
2. Separate primary canon entries (`p1..p3`) from additional versions (`e1..e3`) following `dual_performance_mode`, and isolate archival studio sketches/interviews in `tail` and full TV/concert programs in `tv`.
3. Present edge cases (excluded false-positives, studio-vs-live swaps, dual-melody splits, non-performer borderline covers) to the user for explicit approval.

### Stage 5: Rank & Polish Order
1. Run `python3 scripts/cli.py rank <slug> --views-file <song_wide_views.json>` using Option C `sqrt_mult` (do not add Deezer rank weighting).
2. Reassign Layer 1/2/3 boundaries intentionally (keeping authentic early/classic repertoire in `p1` without kids/holiday point inflation).

### Stage 6: Audit, Health Check & Archival Backup
1. Run `python3 scripts/cli.py qa <slug> --strict` and resolve all `ERROR`s and actionable `WARNING`s.
2. Run `python3 scripts/cli.py health <slug>` and `python3 scripts/cli.py backup <slug>` to cache full metadata and populate multi-alternative `alternative_videos` failovers.
3. Run `python3 scripts/cli.py wayback <slug> --save` for rare non-Topic uploads.

### Stage 7: Streaming & Soundiiz Export (Optional)
1. Configure `streaming_performer_overrides` and `strict_archive_allowed_performers` in `overrides.json` to discover streaming-only archive gems safely.
2. Run `python3 scripts/cli.py spotify <slug>` and verify 0 `performance_only` leaks and `<= 200` rows per Soundiiz CSV part.

### Stage 8: Build, Enable & Publish
1. Set `"enabled": true` in `creators.json`.
2. Run `python3 scripts/cli.py build --all`.
3. Optionally create or push the live YouTube playlist via `python3 scripts/cli.py upload <slug> --cookies cookies.txt` (or `--oauth`, using `core/youtube_uploader.py`) or `<slug>/create_playlist_in_browser.js`.
4. Update root `README.md` and `<slug>/README.md` counts.
5. Run final checks: `py_compile`, `jsc` syntax check, `cli.py qa <slug> --strict`, clean `git status`, commit & push, and sync browser JS (`pbcopy < <slug>/update_existing_playlist_in_browser.js`).
