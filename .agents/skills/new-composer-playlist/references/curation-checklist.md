# Comprehensive Curation & Technical Checklist (Lessons From 248-Turn Flagship Build)

Detailed heuristics and pitfalls learned while building the Naomi Shemer collection (`705` videos, `451` catalog songs). Check every section when curating a new composer.

---

## 1. Multi-Source Catalog Assembly & Attribution

- **Cross-database merging tricks:** Different archives use slightly different titles (e.g., `"יום הולדת שמח"` in ACUM vs `"יום הולדת מוזר"` in NLI; `"שמרי נפשך"` vs `"שיר משמר"`). Merge on performer + year + opening line + normalized title, then record explicit aliases in `overrides.json["synonym_map"]`.
- **Excluded songs must be doubly erased:** Removing a false attribution only from `playlist.json` causes it to resurrect in `archiveSongs` (the "לא ביוטיוב" tab). Always delete excluded works from **both** `playlist.json` and `catalog.json`, and log them in `overrides.json["excluded_normalized_songs"]` + `excluded_non_creator_notes`.
- **ACUM data pitfalls:**
  - ACUM often formats performers as `"שם משפחה שם פרטי"` (`"בר שמעון"`, `"רז רוחמה"`, `"נתן שולי"`). Normalize using `core.artists.ACUM_PERFORMER_EXACT_MAP` / `ACUM_INLINE_PAIR_SUBS`.
  - Strip `ACUM_WRKNBR:` from user-visible badge labels (keep it only in the query URL).
- **`performance_only` strictness:** For songs where the composer was only a performer/arranger (e.g., holiday/children's albums), keep them ONLY if `performance_only` attribution is explicitly verified — and **never** match third-party artists covering that traditional song in YouTube, `alternative_videos`, or Spotify exports.
- **Homonyms & duplicate titles:**
  - Short or biblical/holiday titles (`"אגדה"`, `"שנה טובה"`, `"דמעות"`, `"בראשית"`, `"אור וירושלים"`, `"האם השלישית"`, `"בים בם בום"`) frequently pull wrong songs by other Israeli composers (Rosenblum, Vilenski, Rechter, Wilensky, Hirsch, etc.).
  - Require explicit composer verification in `overrides.json["songs_requiring_explicit_creator"]` + block words in `homonym_block_tokens` + `bad_video_ids`.
- **Dual melodies / parodies / medleys:** If a poet's lyrics were set to music twice (or the composer wrote two different melodies, e.g., `(לחן א')` / `(לחן ב')`), keep separate entries rather than collapsing into one; rename mislabeled medleys honestly (e.g., `"אביב"` -> `"מחרוזת שירי אביב"`).

## 2. YouTube Discovery, Audio Quality & Verification

- **Studio master vs live concert (`OLAK` playlist trap):** YouTube Music album playlists (`OLAK5uy_...`) sometimes auto-link an album track to a *concert video* instead of the studio recording (observed in *אלף נשיקות* `"כמו חצב"`, where `WDzRA91O678` was a 2011 live clip while the real 1981 studio master sat separately on `YehoramGaonOfficial` `QPPugl_l2ak` and `- Topic` `KhU9CZW62jU`). Always cross-check `duration` and visuals/description on album tracks!
- **Full recording vs shortened compilation cut:** Compilation ContentID masters (like `מצעד הפזמונים` / condensed CD medleys, e.g., `2:37` instead of `4:13` on `"חמסינים במשלט"`) can have more views while missing entire verses. Always inspect duration gaps across versions of the same song and prefer the complete master.
- **Noisy 78rpm radio transfers vs commercial LP/CD masters:** When an official `- Topic` Hed Arzi / NMC master exists cleanly, prefer it as the primary recording and demote older archival Kol Israel disc transfers to `alternative_videos`.
- **Hard exclusions (always reject & blocklist):**
  - Karaoke / playback / instrumental-only / ringtone / tutorial chord videos.
  - AI-generated stem splits (`"נערך באמצעות AI"`, `"גרסה ללא תזמורת"`) and fan stereo/echo remixes (`"שיפוץ סאונד"`, `"מיקס מעריצים"`) when genuine studio/live performances exist.
  - Audience sing-alongs where you cannot hear the credited artist, plus studio chatter/sketches/rehearsals mistakenly placed in the main canon (move real archival sketches to `tail`).
  - Short clips (`< 65s`) unless the full song is genuinely brief (check children's songs before rejecting!).
- **Trusted channel sweeps:** Beyond keyword search per song, run full channel scans across official labels (NMC, Hed Arzi, Kan Gimel / `כאן | מוזיקה`, Helicon), composer/estate channels (e.g., children's family channels with archival tapes), and reputable Israeli music archivists — then verify composer credit on each candidate before adding!

## 3. Recording Dates, Tiers, Ordering & Ranking

- **Recording year != anthology year:** Batch-tagging songs from an anthology/CD box set (like *סימני דרך* or a 1995 reissue) overwrites real 1950s–1970s recording years with 1990s dates. Extract exact track recording years from album discography / Zemereshet / Stereo VeMono.
- **Real `[ביצוע מקורי]` badge:** Compute `is_true_original` using genuine historical premiere date — never mark a later creator cover as `[ביצוע מקורי]` when an earlier army troupe / theatre cast premiered the song.
- **No internal curation jargon in UI:** Never display `"שכבה א'"`, `"נוספים ב'"`, `"ביצוע מוביל"` or numeric tier prefixes awkwardly to listeners; use approachable labels like `🌟 הקלאסיקות הגדולות`, `💿 אלבומים והרכבים`, `💎 פנינים נדירות`, `➕ ביצועים נוספים`, `🎙️ סקיצות`, `📺 תוכניות מלאות`.
- **Single jump pill for `e1..e3`:** Collapse all extra-performance blocks (`e1`, `e2`, `e3`) under one `➕ ביצועים נוספים` jump pill in `jump_groups`.
- **Grouping & pairing in `p1..p3`:**
  - Keep non-performer composers cleanly on `dual_performance_mode = "original_only"` (1 primary per song in `p1..p3`).
  - For performer-composers (`"original_plus_creator"`), keep at most `[original]` + `[creator]` in `p1..p3`; never repeat the creator twice, never place two covers in `p1..p3`, and keep creator studio sketches grouped together in `tail`.
- **Option C Ranking (`sqrt_mult`):**
  - Aggregate views across ALL versions of each song (`song_wide_views`) rather than only the #1 video, so timeless standards with huge cover ecosystems (or split uploads) rank fairly.
  - Apply `Base × (1 + √(V / 1,000,000))` with `anthology_cap = 100.0` and zero kids/holiday artificial bonuses.
  - Skip Deezer-rank weighting (incomplete archive coverage and synthetic `100,000` rank plateaus).

## 4. Copyright, Web UX, YouTube Sync & CI/CD

- **Public text hygiene:** Never ship full copyrighted biography/notes prose scraped from NLI or Wikipedia into public HTML/JS/CSV exports. Keep opening line, composer/lyricist/performer/year credits, and outbound links to NLI / Shironet / ACUM / Zemereshet (`🎧` direct-listen links where open audio exists!).
- **YouTube playlist browser sync script traps:**
  - YouTube studio/playlist pages paginate (~100 items initially) and append a `"Recommended videos"` shelf below real playlist items — scroll container carefully and stop/exclude Recommended shelf DOM nodes before indexing!
  - Batch additions/reordering cleanly (~50 per batch where UI limits apply) and verify final order automatically at the end.
  - Regularly run `cli.py health` (`youtubei/v1/browse` with `params="wgYCCAA="`) because YouTube silently hides unavailable videos in public view while counting them in playlist totals.
  - Auto-heal (`cli.py heal`) must strictly filter out `overrides["bad_video_ids"]` so deleted tracks never auto-heal into a previously rejected bad upload.
- **Web UX standards:**
  - `tablist` / `tabpanel` separation (not hiding the main list), prominent top search bar, mobile stacked card rows (zero clipped archive links or missing performer names at `390px`), `direction: ltr` on media transport controls (`⏮ ▶ ⏭`), ARIA roles & `:focus-visible` keyboard navigation, dynamic Play CTA reflecting active filters, empty states with one-click reset, and `localStorage` state keyed by unique `storage_prefix` per composer.
- **Git & security:** Use `git pull --rebase` + `max-parallel: 1` in CI auto-heal workflows; never stage `.github_deploy_key*`, `raw_cache/`, or `__pycache__/`.
