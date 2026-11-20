# 🎵 אוספי מלחינים ישראלים (Playlists Hub)

מאגר זה מרכז פלייליסטים וקטלוגים מקיפים של מלחינים ישראלים מתוך איחוד מאגרי מוזיקה וארכיון (אקו"ם, הספרייה הלאומית, שירונט, זמרשת, ויקיפדיה, Discogs ו-MusicBrainz), כולל נגן אינטראקטיבי משותף לכל מלחין.

* 🌐 **שער האוספים (GitHub Pages):** https://dmtsurel.github.io/playlists/

## 📂 אוספים זמינים

* **[נעמי שמר (`naomi-shemer/`)](naomi-shemer/README.md)** — `705` ביצועי יוטיוב על פני `370` שירים + `81` שירי ארכיון משלימים (`451` שירים בקטלוג).
  * 🌐 **הנגן האינטראקטיבי:** https://dmtsurel.github.io/playlists/naomi-shemer/
  * ▶️ **פלייליסט ב-YouTube:** https://www.youtube.com/playlist?list=PLFHErlX6i22g

## 🏗️ ארכיטקטורה משותפת ובנייה

* `assets/` — נגן ה-Web המשותף לכל המלחינים (`player.css`, `player.js`).
* `core/` — מנוע Python משותף (`config.py`, `hebrew.py`, `artists.py`, `catalog_collector.py`, `youtube_finder.py`, `youtube_uploader.py`, `build_site.py`, `backup.py`, `health.py`, `ranking.py`, `streaming_matcher.py`, `qa.py`, `scaffold.py`).
* `AGENTS.md` + `.agents/skills/new-composer-playlist/` — כללי אוצרות, נגישות, איכות קול ומדריך הקמה לסוכן עבור מלחינים נוספים.
* `creators.json` — מרשם האוספים המזין אוטומטית את שער המלחינים ואת כלי הבנייה.
* `<slug>/composer.json` + `<slug>/overrides.json` — הגדרות דקלרטיביות ואוצרות ידנית פר מלחין.
* `scripts/cli.py` — כלי שורת פקודה אחיד לאיסוף, התאמת יוטיוב, בניית אוספים, ניטור תקינות, דירוג וייצוא:
  * `python3 scripts/cli.py list` / `matrix-json`
  * `python3 scripts/cli.py init-composer <slug> --name-he "..." --name-en "..."`
  * `python3 scripts/cli.py collect <slug>` / `find-videos <slug>`
  * `python3 scripts/cli.py build --all` (או `--standalone` להטמעה עצמאית בקובץ יחיד)
  * `python3 scripts/cli.py hub`
  * `python3 scripts/cli.py qa <slug>|--all [--strict]`
  * `python3 scripts/cli.py health <slug>|--all` / `heal <slug>|--all`
  * `python3 scripts/cli.py backup <slug>|--all` / `wayback <slug>|--all`
  * `python3 scripts/cli.py rank <slug>` / `spotify <slug>` / `upload <slug>`
