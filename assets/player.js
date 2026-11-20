function esc(s) {
  if (s === null || s === undefined) return "";
  const d = document.createElement("div");
  d.textContent = String(s);
  return d.innerHTML;
}
const PLAYLIST_DATA = window.PLAYLIST_DATA || {};
const COMPOSER_CFG = PLAYLIST_DATA.config || {};
const SONGS = PLAYLIST_DATA.songs || [];
const ARCHIVE_SONGS = PLAYLIST_DATA.archiveSongs || [];
const STORAGE_PREFIX = COMPOSER_CFG.storage_prefix || "playlist_";
const CREATOR_NAME_HE = COMPOSER_CFG.name_he || "";
const COLLECTION_PREFIX_HE = COMPOSER_CFG.collection_prefix_he || (CREATOR_NAME_HE ? `משירי ${CREATOR_NAME_HE}` : "פלייליסט");
const CREATOR_ALBUM_TIERS = new Set(COMPOSER_CFG.creator_album_tiers || ["1_album_naomi", "1_album_creator"]);
const BLOCK_ORDER = ["p1", "p2", "p3", "e1", "e2", "e3", "tail", "tv"];
const EXTRAS_BLOCKS = new Set(["e1", "e2", "e3"]);
const BLOCK_META = Object.assign({
  p1:   { label: "🌟 הקלאסיקות הגדולות", short: "🌟 קלאסיקות" },
  p2:   { label: "💿 אלבומים, הצגות והרכבים", short: "💿 אלבומים והרכבים" },
  p3:   { label: "💎 פנינים נדירות וארכיון", short: "💎 פנינים נדירות" },
  e1:   { label: "➕ גרסאות נוספות — הקלאסיקות", short: "➕ ביצועים נוספים" },
  e2:   { label: "➕ גרסאות נוספות — אלבומים והרכבים", short: "➕ ביצועים נוספים" },
  e3:   { label: "➕ גרסאות נוספות — פנינים נדירות", short: "➕ ביצועים נוספים" },
  tail: { label: "🎙️ סקיצות אולפן וראיונות ארכיוניים", short: "🎙️ סקיצות" },
  tv:   { label: "📺 תוכניות טלוויזיה ומופעים מלאים", short: "📺 תוכניות מלאות" }
}, COMPOSER_CFG.block_meta || {});
const JUMP_GROUPS = (Array.isArray(COMPOSER_CFG.jump_groups) && COMPOSER_CFG.jump_groups.length) ? COMPOSER_CFG.jump_groups : [
  { id: "p1",     blocks: ["p1"],             short: "🌟 קלאסיקות",       title: "הקלאסיקות הגדולות" },
  { id: "p2",     blocks: ["p2"],             short: "💿 אלבומים והרכבים", title: "אלבומים, הצגות והרכבים" },
  { id: "p3",     blocks: ["p3"],             short: "💎 פנינים נדירות",   title: "פנינים נדירות וארכיון" },
  { id: "extras", blocks: ["e1", "e2", "e3"], short: "➕ ביצועים נוספים",  title: "גרסאות וביצועים נוספים" },
  { id: "tail",   blocks: ["tail"],           short: "🎙️ סקיצות",         title: "סקיצות אולפן וראיונות ארכיוניים" },
  { id: "tv",     blocks: ["tv"],             short: "📺 תוכניות מלאות",   title: "תוכניות טלוויזיה ומופעים מלאים" }
];

function normHeb(str) {
  if (!str) return "";
  return String(str)
    .toLowerCase()
    .replace(/[\u0591-\u05C7]/g, "")
    .replace(/["'״׳”’‘“]/g, "")
    .replace(/[־\-–—,.!:;?()\[\]\/\\]/g, " ")
    .replace(/וו+/g, "ו")
    .replace(/יי+/g, "י")
    .replace(/\s+/g, " ")
    .trim();
}

SONGS.forEach(s => {
  const joined = [
    s.title,
    s.raw_title,
    (s.alt_titles || []).join(" "),
    s.vtitle,
    s.perf,
    s.alb,
    s.alb_group,
    s.ch,
    s.role_label,
    s.co_creators,
    s.opening_line,
    String(s.n)
  ].filter(Boolean).join(" ");
  s._sRaw = joined.toLowerCase();
  s._sNorm = normHeb(joined);
});

ARCHIVE_SONGS.forEach(s => {
  const joined = [
    s.title,
    (s.alt_titles || []).join(" "),
    s.perfs,
    s.albums,
    s.role_label,
    s.co_creators,
    s.opening_line,
    s.year
  ].filter(Boolean).join(" ");
  s._sRaw = joined.toLowerCase();
  s._sNorm = normHeb(joined);
});

let favoriteVids = new Set();
try {
  if (window.localStorage) {
    const rawFavs = JSON.parse(localStorage.getItem(STORAGE_PREFIX + "favorites") || "[]");
    if (Array.isArray(rawFavs)) {
      rawFavs.forEach(v => { if (typeof v === "string" && v) favoriteVids.add(v); });
    }
  }
} catch (e) {}

let filteredSongs = [...SONGS];
let playingSong = SONGS[0] || null;
let currentIndex = 0; // Index of playingSong inside filteredSongs (-1 when hidden by active filters)
let currentAltIdx = -1; // -1 = primary video, 0..N = index in s.alts
let playHistory = [];
let ytPlayer = null;
let ytApiReady = false;
let ytApiFailed = false;
let pendingVideoLoad = null;
let shuffleEnabled = false;
let repeatOneEnabled = false;
let onePerSongOnly = false;
let favOnly = false;
let archAudioOnly = false;
let exactSongTitle = "";
let currentTab = "yt";
let isMainPlayerVisible = true;
let hasUserStartedPlayback = false;
let shareToastTimer = null;
let lastMiniVid = "";

function getActiveSong() {
  return playingSong || filteredSongs[0] || SONGS[0] || null;
}

function formatSec(sec) {
  if (!Number.isFinite(sec) || sec < 0) return "0:00";
  const total = Math.floor(sec);
  const hrs = Math.floor(total / 3600);
  const mins = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (hrs > 0) {
    return `${hrs}:${String(mins).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }
  return `${mins}:${String(s).padStart(2, "0")}`;
}

function updatePlaybackProgress() {
  const fill = document.getElementById("miniProgressFill");
  const timeEl = document.getElementById("miniTimeText");
  if (!fill && !timeEl) return;
  if (!ytApiReady || !ytPlayer || typeof ytPlayer.getCurrentTime !== "function" || typeof ytPlayer.getDuration !== "function") return;
  const st = typeof ytPlayer.getPlayerState === "function" ? ytPlayer.getPlayerState() : -1;
  if (st !== 1 && st !== 2) return;
  const dur = ytPlayer.getDuration();
  const cur = ytPlayer.getCurrentTime();
  if (dur > 0 && Number.isFinite(dur)) {
    const pct = Math.max(0, Math.min(100, (cur / dur) * 100));
    if (fill) fill.style.width = pct.toFixed(2) + "%";
    if (timeEl) timeEl.textContent = `${formatSec(cur)} / ${formatSec(dur)}`;
  }
}

function seekFromMiniBar(ev) {
  if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
  if (!ytApiReady || !ytPlayer || typeof ytPlayer.getDuration !== "function" || typeof ytPlayer.seekTo !== "function") return;
  const dur = ytPlayer.getDuration();
  if (!dur || dur <= 0) return;
  const wrap = document.getElementById("miniProgressWrap");
  if (!wrap) return;
  const rect = wrap.getBoundingClientRect();
  if (!rect.width) return;
  const ratio = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
  const targetSec = ratio * dur;
  ytPlayer.seekTo(targetSec, true);
  const fill = document.getElementById("miniProgressFill");
  const timeEl = document.getElementById("miniTimeText");
  if (fill) fill.style.width = (ratio * 100).toFixed(2) + "%";
  if (timeEl) timeEl.textContent = `${formatSec(targetSec)} / ${formatSec(dur)}`;
}

function updateMiniPlayerVisibility() {
  const bar = document.getElementById("miniPlayerBar");
  if (!bar) return;
  const st = (ytApiReady && ytPlayer && typeof ytPlayer.getPlayerState === "function") ? ytPlayer.getPlayerState() : -1;
  const isActivePlayback = (st === 1 || st === 2 || st === 3 || hasUserStartedPlayback);
  const shouldShow = (currentTab === "yt" && !isMainPlayerVisible) || (currentTab === "arch" && isActivePlayback);
  bar.classList.toggle("visible", Boolean(shouldShow));
}

function scrollToTopPlayer() {
  if (currentTab !== "yt") switchTab("yt");
  const el = document.querySelector(".sticky-player") || document.getElementById("ytFrameWrap");
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  else window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateMiniPlayerCard(s, vidOverride) {
  if (!s) return;
  const activeVid = vidOverride || s.vid;
  const thumb = document.getElementById("miniThumb");
  const titleEl = document.getElementById("miniTitle");
  const perfEl = document.getElementById("miniPerf");
  if (thumb) thumb.src = `https://i.ytimg.com/vi/${encodeURIComponent(activeVid)}/mqdefault.jpg`;
  if (titleEl) titleEl.textContent = `${s.n}. ${s.raw_title}${s.year ? " (" + s.year + ")" : ""}`;
  if (perfEl) perfEl.textContent = `${s.perf || s.ch}${s.alb ? " · " + s.alb : ""}`;
  if (activeVid !== lastMiniVid) {
    lastMiniVid = activeVid;
    const fill = document.getElementById("miniProgressFill");
    const timeEl = document.getElementById("miniTimeText");
    if (fill) fill.style.width = "0%";
    if (timeEl) timeEl.textContent = s.dur ? `0:00 / ${s.dur}` : "";
  }
}

function updateMediaSession(s, vidOverride) {
  if (!s || typeof navigator === "undefined" || !("mediaSession" in navigator) || typeof MediaMetadata === "undefined") return;
  try {
    const activeVid = vidOverride || s.vid;
    const artistParts = [s.perf || s.ch || CREATOR_NAME_HE];
    if (s.year) artistParts.push(`(${s.year})`);
    const albTitle = (s.alb && !s.alb.startsWith("סינגל")) ? s.alb : COLLECTION_PREFIX_HE;
    navigator.mediaSession.metadata = new MediaMetadata({
      title: s.raw_title || s.title,
      artist: artistParts.join(" "),
      album: albTitle,
      artwork: [
        { src: `https://i.ytimg.com/vi/${encodeURIComponent(activeVid)}/mqdefault.jpg`, sizes: "320x180", type: "image/jpeg" },
        { src: `https://i.ytimg.com/vi/${encodeURIComponent(activeVid)}/hqdefault.jpg`, sizes: "480x360", type: "image/jpeg" }
      ]
    });
  } catch (e) {}
}

function initMediaSessionHandlers() {
  if (typeof navigator === "undefined" || !("mediaSession" in navigator)) return;
  const handlers = [
    ["play", () => { if (ytApiReady && ytPlayer && typeof ytPlayer.playVideo === "function") ytPlayer.playVideo(); else startPlaylistPlayback(); }],
    ["pause", () => { if (ytApiReady && ytPlayer && typeof ytPlayer.pauseVideo === "function") ytPlayer.pauseVideo(); }],
    ["previoustrack", () => playPrev()],
    ["nexttrack", () => playNext()]
  ];
  handlers.forEach(([action, fn]) => {
    try {
      navigator.mediaSession.setActionHandler(action, fn);
    } catch (e) {}
  });
}

function syncPlayButtonUI() {
  const btn = document.getElementById("playPlaylistBtn");
  const miniBtn = document.getElementById("miniPlayBtn");
  const mainBtn = document.getElementById("mainPlayPauseBtn");
  if (!ytApiReady || !ytPlayer || typeof ytPlayer.getPlayerState !== "function") {
    if (btn) btn.textContent = "▶ נגן פלייליסט";
    if (miniBtn) miniBtn.textContent = "▶";
    if (mainBtn) mainBtn.textContent = "⏯";
    updateMiniPlayerVisibility();
    return;
  }
  const st = ytPlayer.getPlayerState();
  if (st === 1) {
    if (btn) btn.textContent = "⏸ השהה פלייליסט";
    if (miniBtn) miniBtn.textContent = "⏸";
    if (mainBtn) mainBtn.textContent = "⏸";
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "playing";
  } else if (st === 2) {
    if (btn) btn.textContent = "▶ המשך פלייליסט";
    if (miniBtn) miniBtn.textContent = "▶";
    if (mainBtn) mainBtn.textContent = "▶";
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "paused";
  } else {
    if (btn) btn.textContent = "▶ נגן פלייליסט";
    if (miniBtn) miniBtn.textContent = "▶";
    if (mainBtn) mainBtn.textContent = "⏯";
  }
  updateMiniPlayerVisibility();
}

function startPlaylistPlayback() {
  if (currentTab !== "yt") switchTab("yt");
  if (!filteredSongs.length) return;
  hasUserStartedPlayback = true;
  if (ytApiReady && ytPlayer && typeof ytPlayer.getPlayerState === "function") {
    const st = ytPlayer.getPlayerState();
    if (st === 1) {
      ytPlayer.pauseVideo();
    } else {
      ytPlayer.playVideo();
    }
    syncPlayButtonUI();
    return;
  }
  playSongAt(currentIndex >= 0 ? currentIndex : 0, true, true);
}

function loadYouTubeIframeAPI() {
  const tag = document.createElement("script");
  tag.src = "https://www.youtube.com/iframe_api";
  tag.onerror = function() {
    ytApiFailed = true;
    if (pendingVideoLoad) {
      const req = pendingVideoLoad;
      pendingVideoLoad = null;
      loadVideoByIdOrSrc(req.vid, req.autoplay);
    }
  };
  document.head.appendChild(tag);
  setTimeout(() => {
    if (!ytApiReady && !ytApiFailed) {
      ytApiFailed = true;
      if (pendingVideoLoad) {
        const req = pendingVideoLoad;
        pendingVideoLoad = null;
        loadVideoByIdOrSrc(req.vid, req.autoplay);
      }
    }
  }, 6000);
}

window.onYouTubeIframeAPIReady = function() {
  try {
    const activeInit = getActiveSong();
    const initReq = pendingVideoLoad || { vid: activeInit ? activeInit.vid : "", autoplay: false };
    pendingVideoLoad = null;
    ytPlayer = new YT.Player("ytFrame", {
      width: "100%",
      height: "100%",
      videoId: initReq.vid,
      playerVars: {
        rel: 0,
        enablejsapi: 1,
        playsinline: 1,
        autoplay: initReq.autoplay ? 1 : 0
      },
      events: {
        onReady: function() {
          ytApiReady = true;
          const req = pendingVideoLoad || initReq;
          pendingVideoLoad = null;
          if (req && req.autoplay) {
            if (req.vid !== initReq.vid) ytPlayer.loadVideoById(req.vid);
            else ytPlayer.playVideo();
          } else if (req && req.vid !== initReq.vid) {
            ytPlayer.cueVideoById(req.vid);
          }
          syncPlayButtonUI();
        },
        onStateChange: function(ev) {
          if (ev.data === 1) {
            hasUserStartedPlayback = true;
          } else if (ev.data === 0) { // YT.PlayerState.ENDED
            if (repeatOneEnabled && ytPlayer && typeof ytPlayer.seekTo === "function") {
              ytPlayer.seekTo(0, true);
              ytPlayer.playVideo();
            } else {
              playNext();
            }
          }
          syncPlayButtonUI();
        },
        onError: function(ev) {
          handleVideoPlaybackError(ev.data);
        }
      }
    });
  } catch (e) {
    ytApiFailed = true;
    if (pendingVideoLoad) {
      const req = pendingVideoLoad;
      pendingVideoLoad = null;
      loadVideoByIdOrSrc(req.vid, req.autoplay);
    }
  }
};

function handleVideoPlaybackError(errCode) {
  const s = getActiveSong();
  if (!s) return;
  const alts = s.alts || [];
  const nextAltIdx = currentAltIdx + 1;
  const banner = document.getElementById("failoverBanner");
  const npDet = document.getElementById("npDetails");
  if (nextAltIdx < alts.length) {
    currentAltIdx = nextAltIdx;
    const alt = alts[currentAltIdx];
    if (banner) {
      banner.style.display = "block";
      banner.innerHTML = `⚠️ הסרטון הראשי אינו זמין כעת (קוד ${esc(errCode)}). הנגן עבר אוטומטית למקור גיבוי #${currentAltIdx + 1}: <strong>${esc(alt.vtitle || alt.vid)}</strong>`;
    }
    if (npDet) npDet.open = true;
    const sel = document.getElementById("backupSelect");
    if (sel) sel.value = alt.vid;
    loadVideoByIdOrSrc(alt.vid, true);
    updateMiniPlayerCard(s, alt.vid);
    updateMediaSession(s, alt.vid);
    document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${encodeURIComponent(alt.vid)}`;
  } else {
    if (banner) {
      banner.style.display = "block";
      banner.innerHTML = `⚠️ הסרטון אינו זמין (קוד ${esc(errCode)}) ולא נמצאו מקורות גיבוי נוספים. עובר לשיר הבא...`;
    }
    setTimeout(() => playNext(), 1800);
  }
}

function loadVideoByIdOrSrc(vid, autoplay) {
  if (ytApiReady && ytPlayer && typeof ytPlayer.loadVideoById === "function") {
    if (autoplay) {
      ytPlayer.loadVideoById(vid);
    } else {
      ytPlayer.cueVideoById(vid);
    }
    if (typeof syncPlayButtonUI === "function") syncPlayButtonUI();
    return;
  }
  if (!ytApiFailed) {
    pendingVideoLoad = { vid, autoplay };
    return;
  }
  const wrap = document.getElementById("ytFrameWrap");
  const originParam = window.location.origin && window.location.origin !== "null" ? `&origin=${encodeURIComponent(window.location.origin)}` : "";
  const srcUrl = `https://www.youtube.com/embed/${encodeURIComponent(vid)}?enablejsapi=1&rel=0${autoplay ? "&autoplay=1" : ""}${originParam}`;
  let frame = document.getElementById("ytFrame");
  if (!frame || frame.tagName.toLowerCase() !== "iframe") {
    if (wrap) {
      wrap.innerHTML = `<iframe id="ytFrame" src="${srcUrl}" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
    }
  } else {
    frame.src = srcUrl;
  }
}

function switchVideoSource(vid) {
  const s = getActiveSong();
  if (!s) return;
  hasUserStartedPlayback = true;
  const banner = document.getElementById("failoverBanner");
  if (vid === s.vid) {
    currentAltIdx = -1;
    if (banner) banner.style.display = "none";
  } else {
    const alts = s.alts || [];
    currentAltIdx = alts.findIndex(a => a.vid === vid);
    const alt = alts[currentAltIdx];
    if (banner && alt) {
      banner.style.display = "block";
      banner.innerHTML = `🛡️ מנגן מקור גיבוי #${currentAltIdx + 1}: <strong>${esc(alt.vtitle || alt.vid)}</strong> (${esc(alt.ch || "")})`;
    }
  }
  loadVideoByIdOrSrc(vid, true);
  updateMiniPlayerCard(s, vid);
  updateMediaSession(s, vid);
  document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${encodeURIComponent(vid)}`;
}

function switchTab(tab, skipSync = false) {
  currentTab = tab === "arch" ? "arch" : "yt";
  const isYt = currentTab === "yt";
  const ytTabEl = document.getElementById("tabYtContent");
  if (ytTabEl) {
    ytTabEl.style.display = "block";
    ytTabEl.classList.toggle("tab-offscreen", !isYt);
  }
  document.getElementById("tabArchContent").style.display = isYt ? "none" : "block";
  const topArchBtn = document.getElementById("topArchToggleBtn");
  if (topArchBtn) topArchBtn.style.display = isYt ? "inline-flex" : "none";
  const backBtn = document.getElementById("backToPlayerBtn");
  if (backBtn) backBtn.style.display = isYt ? "none" : "inline-flex";
  const ytChip = document.getElementById("ytCountChip");
  if (ytChip) ytChip.style.display = isYt ? "" : "none";
  const footerBtn = document.getElementById("footerArchToggleBtn");
  if (footerBtn) {
    footerBtn.textContent = isYt
      ? `🏛️ הצג גם ${ARCHIVE_SONGS.length} שירים נדירים מהארכיון שאינם ביוטיוב`
      : `🎵 חזרה לנגן הפלייליסט הראשי (${SONGS.length} ביצועים)`;
  }
  updateMiniPlayerVisibility();
  if (!skipSync) {
    syncUrlAndStorageState();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function saveFavorites() {
  try {
    if (window.localStorage) {
      localStorage.setItem(STORAGE_PREFIX + "favorites", JSON.stringify(Array.from(favoriteVids)));
    }
  } catch (e) {}
}

function syncFavUI() {
  const cntEl = document.getElementById("favCountSpan");
  if (cntEl) cntEl.textContent = String(favoriteVids.size);
  const favFilterBtn = document.getElementById("favOnlyBtn");
  if (favFilterBtn) {
    favFilterBtn.classList.toggle("btn-active", favOnly);
    favFilterBtn.setAttribute("aria-pressed", favOnly ? "true" : "false");
  }
  const curSong = getActiveSong();
  const npFav = document.getElementById("npFavBtn");
  const miniFav = document.getElementById("miniFavBtn");
  if (curSong) {
    const isFav = favoriteVids.has(curSong.vid);
    if (npFav) {
      npFav.textContent = isFav ? "❤️" : "♡";
      npFav.classList.toggle("btn-active", isFav);
    }
    if (miniFav) {
      miniFav.textContent = isFav ? "❤️" : "♡";
      miniFav.classList.toggle("btn-active", isFav);
    }
  }
}

function toggleFavorite(ev, vid) {
  if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
  if (!vid) return;
  if (favoriteVids.has(vid)) favoriteVids.delete(vid);
  else favoriteVids.add(vid);
  saveFavorites();
  if (favOnly) {
    renderTable();
  } else {
    const isFav = favoriteVids.has(vid);
    document.querySelectorAll(".fav-btn").forEach(btn => {
      if (btn.getAttribute("data-vid") === vid) {
        btn.classList.toggle("is-fav", isFav);
        btn.textContent = isFav ? "❤️" : "♡";
      }
    });
    syncFavUI();
  }
}

function toggleCurrentFavorite() {
  const curSong = getActiveSong();
  if (!curSong) return;
  toggleFavorite(null, curSong.vid);
}

function toggleFavOnly() {
  favOnly = !favOnly;
  syncFavUI();
  renderTable();
}

function syncOnePerSongUI() {
  const btn = document.getElementById("onePerSongBtn");
  if (!btn) return;
  btn.classList.toggle("btn-active", onePerSongOnly);
  btn.setAttribute("aria-pressed", onePerSongOnly ? "true" : "false");
}

function toggleOnePerSong() {
  onePerSongOnly = !onePerSongOnly;
  syncOnePerSongUI();
  renderTable();
}

function syncArchAudioOnlyUI() {
  const btn = document.getElementById("archAudioOnlyBtn");
  if (!btn) return;
  btn.classList.toggle("btn-active", archAudioOnly);
  btn.setAttribute("aria-pressed", archAudioOnly ? "true" : "false");
}

function toggleArchAudioOnly() {
  archAudioOnly = !archAudioOnly;
  syncArchAudioOnlyUI();
  renderArchiveTable();
}

function toggleAdvancedFilters() {
  const drw = document.getElementById("advancedDrawer");
  const btn = document.getElementById("advFilterBtn");
  if (!drw) return;
  const isOpen = drw.classList.toggle("open");
  if (btn) btn.classList.toggle("btn-active", isOpen);
}

function updateSearchClearUI(which) {
  if (which === "arch") {
    const inp = document.getElementById("archSearchInput");
    const clr = document.getElementById("archSearchClearBtn");
    if (inp && clr) clr.style.display = inp.value.length > 0 ? "inline-flex" : "none";
  } else {
    const inp = document.getElementById("searchInput");
    const clr = document.getElementById("searchClearBtn");
    const kbd = document.getElementById("searchKbd");
    const hasVal = inp && inp.value.length > 0;
    if (clr) clr.style.display = hasVal ? "inline-flex" : "none";
    if (kbd) kbd.style.display = hasVal ? "none" : "inline";
  }
}

function onSearchInput(which) {
  updateSearchClearUI(which);
  if (which === "arch") renderArchiveTable();
  else renderTable();
}

function clearSearch(which) {
  if (which === "arch") {
    const inp = document.getElementById("archSearchInput");
    if (inp) { inp.value = ""; inp.focus(); }
    updateSearchClearUI("arch");
    renderArchiveTable();
  } else {
    const inp = document.getElementById("searchInput");
    if (inp) { inp.value = ""; inp.focus(); }
    updateSearchClearUI("yt");
    renderTable();
  }
}

function filterByExactSong(ev, rawTitle) {
  if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
  if (!rawTitle) return;
  if (exactSongTitle === rawTitle) {
    exactSongTitle = "";
  } else {
    exactSongTitle = rawTitle;
  }
  renderTable();
  if (playingSong) {
    const npVerBadge = document.querySelector("#nowPlayingRole .ver-badge");
    if (npVerBadge) npVerBadge.classList.toggle("active-ver-filter", exactSongTitle === playingSong.raw_title);
  }
}

function filterBySongTitle(ev, text) {
  if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
  const inp = document.getElementById("searchInput");
  if (!inp) return;
  exactSongTitle = "";
  if (inp.value.trim() === text) {
    inp.value = "";
  } else {
    inp.value = text;
  }
  updateSearchClearUI("yt");
  renderTable();
}

function clearSingleFilter(kind) {
  if (kind === "exact") exactSongTitle = "";
  else if (kind === "q") {
    document.getElementById("searchInput").value = "";
    updateSearchClearUI("yt");
  } else if (kind === "decade") document.getElementById("decadeFilter").value = "ALL";
  else if (kind === "tier") document.getElementById("tierFilter").value = "ALL";
  else if (kind === "role") document.getElementById("roleFilter").value = "ALL";
  else if (kind === "oneper") {
    onePerSongOnly = false;
    syncOnePerSongUI();
  } else if (kind === "fav") {
    favOnly = false;
    syncFavUI();
  }
  renderTable();
  if (playingSong) {
    const npVerBadge = document.querySelector("#nowPlayingRole .ver-badge");
    if (npVerBadge) npVerBadge.classList.toggle("active-ver-filter", exactSongTitle === playingSong.raw_title);
  }
}

function resetAllFilters() {
  exactSongTitle = "";
  document.getElementById("searchInput").value = "";
  updateSearchClearUI("yt");
  document.getElementById("sortSelect").value = "canonical";
  document.getElementById("decadeFilter").value = "ALL";
  document.getElementById("tierFilter").value = "ALL";
  document.getElementById("roleFilter").value = "ALL";
  onePerSongOnly = false;
  favOnly = false;
  syncOnePerSongUI();
  syncFavUI();
  renderTable();
  if (playingSong) {
    const npVerBadge = document.querySelector("#nowPlayingRole .ver-badge");
    if (npVerBadge) npVerBadge.classList.remove("active-ver-filter");
  }
}

function syncUrlAndStorageState() {
  try {
    const url = new URL(window.location.href);
    const s = getActiveSong();
    if (s) {
      url.searchParams.set("v", s.vid);
      url.searchParams.delete("song");
    }
    const q = document.getElementById("searchInput").value.trim();
    const sortBy = document.getElementById("sortSelect").value;
    const tf = document.getElementById("tierFilter").value;
    const rf = document.getElementById("roleFilter").value;
    const df = document.getElementById("decadeFilter").value;

    const setOrDel = (k, val, defVal) => {
      if (val && val !== defVal) url.searchParams.set(k, val);
      else url.searchParams.delete(k);
    };
    setOrDel("q", q, "");
    setOrDel("exact", exactSongTitle, "");
    setOrDel("sort", sortBy, "canonical");
    setOrDel("tier", tf, "ALL");
    setOrDel("role", rf, "ALL");
    setOrDel("decade", df, "ALL");
    setOrDel("tab", currentTab, "yt");
    setOrDel("shuffle", shuffleEnabled ? "1" : "", "");
    setOrDel("repeat", repeatOneEnabled ? "1" : "", "");
    setOrDel("oneper", onePerSongOnly ? "1" : "", "");
    setOrDel("fav", favOnly ? "1" : "", "");
    setOrDel("archaudio", archAudioOnly ? "1" : "", "");

    window.history.replaceState({}, "", url.toString());
    if (window.localStorage) {
      localStorage.setItem(STORAGE_PREFIX + "state", JSON.stringify({
        vid: s ? s.vid : "",
        song: s ? s.n : 1,
        sort: sortBy,
        tier: tf,
        role: rf,
        decade: df,
        tab: currentTab,
        shuffle: shuffleEnabled,
        repeat: repeatOneEnabled,
        oneper: onePerSongOnly,
        fav: favOnly,
        archaudio: archAudioOnly
      }));
    }
  } catch (e) {}
}

function copyShareUrl() {
  syncUrlAndStorageState();
  const s = getActiveSong();
  const shareUrlObj = new URL(window.location.href);
  if (s) {
    shareUrlObj.searchParams.set("v", s.vid);
    shareUrlObj.searchParams.delete("song");
  }
  const shareStr = shareUrlObj.toString();
  const isCoarseTouch = Boolean(window.matchMedia && window.matchMedia("(pointer: coarse)").matches);
  if (isCoarseTouch && typeof navigator !== "undefined" && typeof navigator.share === "function") {
    const shareTitle = s ? `${s.raw_title} – ${s.perf || COLLECTION_PREFIX_HE}` : document.title;
    navigator.share({
      title: shareTitle,
      url: shareStr
    }).catch(err => {
      if (err && err.name === "AbortError") return;
      copyTextWithToast(shareStr, s);
    });
    return;
  }
  copyTextWithToast(shareStr, s);
}

function copyTextWithToast(shareStr, s) {
  const showOk = () => {
    const toast = document.getElementById("shareToast");
    if (toast) {
      toast.textContent = s ? `✔ הועתק קישור ישיר ל"${s.raw_title}"!` : "✔ הקישור הישיר לשיר הועתק!";
      toast.classList.add("show");
      if (shareToastTimer) clearTimeout(shareToastTimer);
      shareToastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
    }
  };
  const fallbackCopy = () => {
    try {
      const ta = document.createElement("textarea");
      ta.value = shareStr;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      showOk();
    } catch (e) {}
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(shareStr).then(showOk).catch(fallbackCopy);
  } else {
    fallbackCopy();
  }
}

function renderArchivePills(links, stopProp = false) {
  if (!links || !links.length) return "";
  const onclickAttr = stopProp ? 'onclick="event.stopPropagation()"' : "";
  return `<div class="archive-pills">` + links.map(l => {
    let cls = "arch-pill";
    const src = String(l.source || "");
    let label = l.label || "";
    if (src === "nli_audio") {
      cls += " audio-listen";
      label = label || "🎧 האזנה להקלטה בספרייה הלאומית";
    } else if (src === "zemereshet_audio") {
      cls += " audio-listen";
      label = label || "🎧 האזנה להקלטה בזמרשת";
    } else if (src.startsWith("nli")) {
      cls += " nli";
      label = "📖 סיפור השיר בספרייה הלאומית";
    } else if (src === "shironet") {
      cls += " shironet";
    } else if (src === "zemereshet") {
      cls += " zemereshet";
    }
    return `<a class="${cls}" href="${esc(l.url)}" target="_blank" rel="noopener noreferrer" ${onclickAttr}>${esc(label)} ↗</a>`;
  }).join("") + `</div>`;
}

function updateNowPlayingCard(s) {
  document.getElementById("nowPlayingTitle").textContent = `${s.n}. ${s.raw_title}${s.year ? " (" + s.year + ")" : ""}`;
  const perfText = s.perf || s.ch || "";
  const perfEscAttr = JSON.stringify(perfText).replace(/"/g, "&quot;");
  const cleanAlb = (s.alb || "").replace(/\s*\(#\d+\)\s*$/, "").trim();
  const albEscAttr = JSON.stringify(cleanAlb).replace(/"/g, "&quot;");
  const perfSpan = perfText
    ? `<span class="clickable-meta" onclick="filterBySongTitle(event, ${perfEscAttr})" title="לחץ לסינון כל השירים של מבצע זה">${esc(perfText)}</span>`
    : "";
  const albSpan = s.alb
    ? ` · <span class="clickable-meta" onclick="filterBySongTitle(event, ${albEscAttr})" title="לחץ לסינון כל שירי האלבום">${esc(s.alb)}</span>`
    : "";
  document.getElementById("nowPlayingMeta").innerHTML = `${perfSpan}${albSpan}`;
  const isFav = favoriteVids.has(s.vid);
  const npFav = document.getElementById("npFavBtn");
  if (npFav) {
    npFav.textContent = isFav ? "❤️" : "♡";
    npFav.classList.toggle("btn-active", isFav);
  }
  const miniFav = document.getElementById("miniFavBtn");
  if (miniFav) {
    miniFav.textContent = isFav ? "❤️" : "♡";
    miniFav.classList.toggle("btn-active", isFav);
  }
  const isExactActive = (exactSongTitle && exactSongTitle === s.raw_title);
  const verBadgeHtml = s.ver_total > 1
    ? `<span class="ver-badge ${isExactActive ? "active-ver-filter" : ""}" onclick="filterByExactSong(event, ${JSON.stringify(s.raw_title).replace(/"/g, '&quot;')})" title="לחץ להצגת כל ${s.ver_total} הביצועים של שיר זה בטבלה">ביצוע ${s.ver_idx}/${s.ver_total}</span>`
    : "";
  const tierShort = s.tier_label.replace(/^[0-9]\.\s*/, "");
  document.getElementById("nowPlayingRole").innerHTML = `<span class="badge t-${esc(s.tier)}">${esc(tierShort)}</span><span class="badge r-${esc(s.role_cat)}">${esc(s.role_label)}</span>${verBadgeHtml}`;

  const verBox = document.getElementById("nowPlayingVersions");
  if (verBox) {
    const sameVers = s.ver_total > 1 ? SONGS.filter(x => x.raw_title === s.raw_title) : [];
    if (sameVers.length > 1) {
      const rawLabels = sameVers.map(v => {
        const base = (v.perf || v.ch || `ביצוע ${v.ver_idx}`).replace(/\s*\([^)]*\)\s*$/, "").trim() || (v.perf || v.ch || `ביצוע ${v.ver_idx}`);
        return `${base}${v.year ? " (" + v.year + ")" : ""}`;
      });
      const pills = sameVers.map((v, idx) => {
        const isCur = v.vid === s.vid;
        const hasDup = rawLabels.filter(x => x === rawLabels[idx]).length > 1;
        const dispBase = hasDup ? (v.perf || v.ch || `ביצוע ${v.ver_idx}`) : rawLabels[idx];
        const lbl = `${isCur ? "▶ " : ""}${dispBase}${hasDup && v.year ? " (" + v.year + ")" : ""}`;
        const tip = `${v.perf || v.ch}${v.alb ? " · " + v.alb : ""} (#${v.n})`;
        return `<button type="button" class="np-ver-pill ${isCur ? "active" : ""}" onclick="playSongByVid('${esc(v.vid)}')" title="${esc(tip)}">${esc(lbl)}</button>`;
      }).join("");
      verBox.innerHTML = `<span class="np-ver-lbl">ביצועים (${sameVers.length}):</span>${pills}`;
      verBox.style.display = "flex";
    } else {
      verBox.style.display = "none";
      verBox.innerHTML = "";
    }
  }

  const qBox = document.getElementById("nowPlayingQuote");
  const parts = [];
  if (s.opening_line) parts.push(`"${esc(s.opening_line)}"`);
  if (s.co_creators) parts.push(`<span style="color:var(--muted); font-size:11.5px;">שותפים ליצירה: ${esc(s.co_creators)}</span>`);
  if (parts.length > 0) {
    qBox.innerHTML = parts.join("<br/>");
    qBox.style.display = "block";
  } else {
    qBox.style.display = "none";
  }
  document.getElementById("nowPlayingLinks").innerHTML = renderArchivePills(s.links, false);
  document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${encodeURIComponent(s.vid)}`;
  const banner = document.getElementById("failoverBanner");
  if (banner) banner.style.display = "none";
  const bBox = document.getElementById("backupSourcesBox");
  const bSel = document.getElementById("backupSelect");
  const npSum = document.getElementById("npDetailsSummary");
  const alts = s.alts || [];
  if (npSum) {
    npSum.textContent = alts.length > 0
      ? `⚙️ מקורות גיבוי (${alts.length}) וקיצורי מקלדת`
      : `⚙️ קיצורי מקלדת`;
  }
  if (bBox && bSel) {
    if (alts.length > 0) {
      bBox.style.display = "block";
      const opts = [`<option value="${esc(s.vid)}">⭐ מקור ראשי: ${esc(s.vtitle)} (${esc(s.ch)})</option>`];
      alts.forEach((a, i) => {
        const tag = a.src === "same_song_performance" ? "ביצוע נוסף" : "עותק גיבוי";
        opts.push(`<option value="${esc(a.vid)}">🔄 גיבוי #${i + 1} (${tag}): ${esc(a.vtitle || a.vid)} (${esc(a.ch || "")})</option>`);
      });
      bSel.innerHTML = opts.join("");
      bSel.value = s.vid;
    } else {
      bBox.style.display = "none";
    }
  }
  updateMiniPlayerCard(s, s.vid);
  updateMediaSession(s, s.vid);
}

function syncBlockJumpHighlight() {
  const rawBlk = playingSong ? playingSong.blk : "";
  const activeGroup = EXTRAS_BLOCKS.has(rawBlk) ? "extras" : rawBlk;
  document.querySelectorAll("#blockJumpBar .block-jump-pill").forEach(btn => {
    btn.classList.toggle("active-blk", btn.getAttribute("data-blk") === activeGroup);
  });
}

function jumpToBlock(blkId) {
  const target = document.querySelector(`tr[data-block-header="${blkId}"]`);
  if (!target) return;
  const wrap = document.querySelector("#tabYtContent .table-wrap");
  if (wrap && wrap.scrollHeight > wrap.clientHeight + 20 && window.getComputedStyle(wrap).overflowY !== "visible") {
    const th = wrap.querySelector("thead");
    const thH = th ? th.offsetHeight : 0;
    wrap.scrollTo({ top: Math.max(0, target.offsetTop - thH), behavior: "smooth" });
  } else {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function scrollToActiveRow(smooth = true) {
  if (currentTab !== "yt") switchTab("yt", true);
  let activeRow = document.querySelector("tr.song-row.active");
  if (!activeRow && playingSong && currentIndex < 0) {
    resetAllFilters();
    activeRow = document.querySelector("tr.song-row.active");
  }
  if (activeRow) {
    activeRow.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: smooth ? "center" : "nearest" });
  }
}

function playSongByVid(vid, shouldScroll = false) {
  const nextSong = SONGS.find(x => x.vid === vid);
  if (!nextSong) return;
  hasUserStartedPlayback = true;
  if (playingSong && playingSong.vid !== nextSong.vid) {
    playHistory.push(playingSong.vid);
    if (playHistory.length > 100) playHistory.shift();
  }
  playingSong = nextSong;
  currentIndex = filteredSongs.findIndex(x => x.vid === nextSong.vid);
  currentAltIdx = -1;
  updateNowPlayingCard(nextSong);
  loadVideoByIdOrSrc(nextSong.vid, true);
  document.querySelectorAll("tr.song-row").forEach((tr, i) => {
    tr.classList.toggle("active", i === currentIndex);
  });
  if (shouldScroll && currentIndex >= 0) scrollToActiveRow(true);
  syncBlockJumpHighlight();
  syncUrlAndStorageState();
}

function playSongAt(idx, shouldScroll = true, skipHistory = false) {
  if (idx < 0 || idx >= filteredSongs.length) return;
  hasUserStartedPlayback = true;
  const nextSong = filteredSongs[idx];
  if (!skipHistory && playingSong && playingSong.vid !== nextSong.vid) {
    playHistory.push(playingSong.vid);
    if (playHistory.length > 100) playHistory.shift();
  }
  playingSong = nextSong;
  currentIndex = idx;
  currentAltIdx = -1;
  updateNowPlayingCard(nextSong);
  loadVideoByIdOrSrc(nextSong.vid, true);
  document.querySelectorAll("tr.song-row").forEach((tr, i) => {
    tr.classList.toggle("active", i === idx);
  });
  if (shouldScroll) scrollToActiveRow(true);
  syncBlockJumpHighlight();
  syncUrlAndStorageState();
}

function toggleShuffle() {
  shuffleEnabled = !shuffleEnabled;
  const btn = document.getElementById("shuffleBtn");
  if (btn) btn.classList.toggle("btn-active", shuffleEnabled);
  syncUrlAndStorageState();
}

function toggleRepeatOne() {
  repeatOneEnabled = !repeatOneEnabled;
  const btn = document.getElementById("repeatBtn");
  if (btn) {
    btn.classList.toggle("btn-active", repeatOneEnabled);
    btn.setAttribute("aria-pressed", repeatOneEnabled ? "true" : "false");
  }
  syncUrlAndStorageState();
}

function togglePlayPause() {
  hasUserStartedPlayback = true;
  if (ytApiReady && ytPlayer && typeof ytPlayer.getPlayerState === "function") {
    const st = ytPlayer.getPlayerState();
    if (st === 1) ytPlayer.pauseVideo();
    else ytPlayer.playVideo();
    if (typeof syncPlayButtonUI === "function") syncPlayButtonUI();
  } else {
    startPlaylistPlayback();
  }
}

function playNext() {
  if (!filteredSongs.length) return;
  if (shuffleEnabled && filteredSongs.length > 1) {
    let randIdx = currentIndex;
    while (randIdx === currentIndex || randIdx < 0) {
      randIdx = Math.floor(Math.random() * filteredSongs.length);
    }
    playSongAt(randIdx);
    return;
  }
  if (currentIndex < 0) {
    if (playingSong) {
      const sameTitleIdx = filteredSongs.findIndex(x => x.raw_title === playingSong.raw_title);
      if (sameTitleIdx >= 0) {
        playSongAt((sameTitleIdx + 1) % filteredSongs.length);
        return;
      }
      const afterIdx = filteredSongs.findIndex(x => x.n > playingSong.n);
      if (afterIdx >= 0) {
        playSongAt(afterIdx);
        return;
      }
    }
    playSongAt(0);
    return;
  }
  playSongAt((currentIndex + 1) % filteredSongs.length);
}

function playPrev() {
  if (!filteredSongs.length) return;
  if (shuffleEnabled && playHistory.length > 0) {
    const prevVid = playHistory.pop();
    const prevIdx = filteredSongs.findIndex(x => x.vid === prevVid);
    if (prevIdx >= 0) {
      playSongAt(prevIdx, true, true);
      return;
    }
  }
  if (currentIndex < 0) {
    if (playingSong) {
      const sameTitleIdx = filteredSongs.findIndex(x => x.raw_title === playingSong.raw_title);
      if (sameTitleIdx >= 0) {
        playSongAt((sameTitleIdx - 1 + filteredSongs.length) % filteredSongs.length, true, true);
        return;
      }
    }
    playSongAt(filteredSongs.length - 1, true, true);
    return;
  }
  playSongAt((currentIndex - 1 + filteredSongs.length) % filteredSongs.length, true, true);
}

function getSelectedOptionLabel(selId) {
  const el = document.getElementById(selId);
  if (!el || el.selectedIndex < 0) return "";
  const txt = el.options[el.selectedIndex].text || "";
  return txt.replace(/\s*\([^)]*\)\s*$/, "").trim();
}

function renderTable(skipSync = false) {
  const activeVid = playingSong ? playingSong.vid : null;
  const rawInput = document.getElementById("searchInput").value;
  const qRaw = rawInput.trim().toLowerCase();
  const qNorm = normHeb(rawInput);
  const sortBy = document.getElementById("sortSelect").value;
  const tf = document.getElementById("tierFilter").value;
  const rf = document.getElementById("roleFilter").value;
  const df = document.getElementById("decadeFilter").value;

  filteredSongs = SONGS.filter(s => {
    if (exactSongTitle && s.raw_title !== exactSongTitle) return false;
    if (favOnly && !favoriteVids.has(s.vid)) return false;
    if (!exactSongTitle && onePerSongOnly && s.ver_idx !== 1) return false;
    if (tf !== "ALL" && s.tier !== tf) return false;
    if (rf !== "ALL" && s.role_cat !== rf) return false;
    if (df !== "ALL" && s.decade !== df) return false;
    if (!qRaw) return true;
    return s._sRaw.includes(qRaw) || (qNorm.length > 0 && s._sNorm.includes(qNorm));
  });

  const TV_GRP_NAME = "תוכניות טלוויזיה ומופעים מלאים";
  const albCatRank = (ag) => {
    if (!ag || ag.startsWith("סינגל") || ag.startsWith("ביצוע ")) return 2;
    if (ag === TV_GRP_NAME) return 1;
    return 0;
  };

  filteredSongs.sort((a, b) => {
    if (sortBy === "canonical") return a.n - b.n;
    if (sortBy === "chrono_asc") return (a.chrono_n || a.n) - (b.chrono_n || b.n);
    if (sortBy === "chrono_desc") return (b.chrono_n || b.n) - (a.chrono_n || a.n);
    if (sortBy === "popularity") return (b.canon_score - a.canon_score) || (a.n - b.n);
    if (sortBy === "title_asc") return a.raw_title.localeCompare(b.raw_title, "he") || (a.n - b.n);
    if (sortBy === "perf_asc") return (a.perf || a.ch).localeCompare(b.perf || b.ch, "he") || (a.n - b.n);
    if (sortBy === "albums") {
      const aCat = albCatRank(a.alb_group);
      const bCat = albCatRank(b.alb_group);
      if (aCat !== bCat) return aCat - bCat;
      if (aCat === 0) {
        const aCreator = CREATOR_ALBUM_TIERS.has(a.tier) ? 0 : 1;
        const bCreator = CREATOR_ALBUM_TIERS.has(b.tier) ? 0 : 1;
        if (aCreator !== bCreator) return aCreator - bCreator;
        const grpCmp = (a.alb_group || "").localeCompare(b.alb_group || "", "he");
        if (grpCmp !== 0) return grpCmp;
        const trkCmp = (a.alb_trk || 999) - (b.alb_trk || 999);
        if (trkCmp !== 0) return trkCmp;
      }
      return (a.chrono_n || a.n) - (b.chrono_n || b.n);
    }
    return a.n - b.n;
  });

  currentIndex = activeVid ? filteredSongs.findIndex(x => x.vid === activeVid) : -1;

  document.getElementById("ytCountChip").textContent = filteredSongs.length === SONGS.length
    ? `${SONGS.length} ביצועים`
    : (exactSongTitle
        ? `מציג את כל ${filteredSongs.length} הביצועים של "${exactSongTitle}"`
        : (favOnly
            ? `מציג ${filteredSongs.length} מועדפים (מתוך ${SONGS.length} ביצועים)`
            : (onePerSongOnly
                ? `מציג ${filteredSongs.length} מתוך ${SONGS.length} ביצועים (ביצוע אחד לשיר)`
                : `מציג ${filteredSongs.length} מתוך ${SONGS.length} ביצועים`)));

  const activeAdvCount = [tf !== "ALL", rf !== "ALL"].filter(Boolean).length;
  const advBadge = document.getElementById("activeFiltersBadge");
  if (advBadge) {
    if (activeAdvCount > 0) {
      advBadge.textContent = activeAdvCount;
      advBadge.style.display = "inline-block";
    } else {
      advBadge.style.display = "none";
    }
  }

  const chipsBox = document.getElementById("activeFilterChips");
  if (chipsBox) {
    const chips = [];
    if (exactSongTitle) chips.push({ kind: "exact", text: `🎵 כל הביצועים של: "${exactSongTitle}"` });
    if (rawInput.trim()) chips.push({ kind: "q", text: `🔍 חיפוש: "${rawInput.trim()}"` });
    if (df !== "ALL") chips.push({ kind: "decade", text: `📅 ${getSelectedOptionLabel("decadeFilter")}` });
    if (tf !== "ALL") chips.push({ kind: "tier", text: `🎙️ ${getSelectedOptionLabel("tierFilter")}` });
    if (rf !== "ALL") chips.push({ kind: "role", text: `✍️ ${getSelectedOptionLabel("roleFilter")}` });
    if (onePerSongOnly && !exactSongTitle) chips.push({ kind: "oneper", text: "🎯 ביצוע אחד לשיר" });
    if (favOnly) chips.push({ kind: "fav", text: "❤️ מועדפים בלבד" });

    if (chips.length > 0) {
      const pillsHtml = chips.map(c =>
        `<button type="button" class="filter-chip" onclick="clearSingleFilter('${c.kind}')">${esc(c.text)} <span aria-hidden="true">✕</span></button>`
      ).join("");
      chipsBox.innerHTML = `<span class="chips-lbl">מסננים פעילים:</span>${pillsHtml}<button type="button" class="filter-chip filter-chip-reset" onclick="resetAllFilters()">↺ נקה הכול</button>`;
      chipsBox.style.display = "flex";
    } else {
      chipsBox.style.display = "none";
      chipsBox.innerHTML = "";
    }
  }

  const blockCounts = {};
  if (sortBy === "canonical") {
    filteredSongs.forEach(s => {
      const b = s.blk || "p1";
      blockCounts[b] = (blockCounts[b] || 0) + 1;
    });
  }
  const presentGroups = JUMP_GROUPS.map(g => {
    const count = g.blocks.reduce((sum, b) => sum + (blockCounts[b] || 0), 0);
    const firstBlk = g.blocks.find(b => blockCounts[b] > 0) || "";
    return { ...g, count, firstBlk };
  }).filter(g => g.count > 0);
  const jumpBar = document.getElementById("blockJumpBar");
  if (jumpBar) {
    if (sortBy === "canonical" && presentGroups.length >= 2) {
      const rawBlk = playingSong ? playingSong.blk : "";
      const activeGroup = EXTRAS_BLOCKS.has(rawBlk) ? "extras" : rawBlk;
      jumpBar.innerHTML = presentGroups.map(g => {
        const isAct = g.id === activeGroup;
        return `<button type="button" class="block-jump-pill ${isAct ? "active-blk" : ""}" data-blk="${esc(g.id)}" onclick="jumpToBlock('${esc(g.firstBlk)}')" title="${esc(g.title)} (${g.count} רצועות)">${esc(g.short)} <span style="opacity:0.7; font-weight:400;">(${g.count})</span></button>`;
      }).join("");
      jumpBar.style.display = "flex";
    } else {
      jumpBar.style.display = "none";
      jumpBar.innerHTML = "";
    }
  }

  const normalizeAlbGrp = (ag) => (!ag || ag.startsWith("סינגל") || ag.startsWith("ביצוע "))
    ? "סינגלים וביצועים בודדים"
    : ag;

  const albumCounts = {};
  if (sortBy === "albums") {
    filteredSongs.forEach(s => {
      const g = normalizeAlbGrp(s.alb_group);
      albumCounts[g] = (albumCounts[g] || 0) + 1;
    });
  }

  let lastAlbGroup = null;
  let lastBlockId = null;
  let lastSubChapter = null;
  const tbody = document.getElementById("songsBody");
  const htmlRows = [];
  if (filteredSongs.length === 0) {
    const emptyMsg = (favOnly && favoriteVids.size === 0)
      ? "עדיין לא סימנת ביצועים מועדפים — לחץ על ♡ ליד כל שיר בטבלה או בכרטיס הנגן כדי לשמור אותו ברשימה האישית שלך."
      : "לא נמצאו שירים התואמים לחיפוש או לסינון שנבחר.";
    htmlRows.push(`<tr><td colspan="4" style="text-align:center; padding:28px 16px; color:var(--muted);">${esc(emptyMsg)}</td></tr>`);
  }
  filteredSongs.forEach((s, i) => {
    if (sortBy === "canonical" && filteredSongs.length > 1) {
      const bId = s.blk || "p1";
      if (bId !== lastBlockId) {
        lastBlockId = bId;
        lastSubChapter = null;
        const bMeta = BLOCK_META[bId] || { label: bId };
        htmlRows.push(`
          <tr class="album-group-header" data-block-header="${esc(bId)}">
            <td colspan="4">${esc(bMeta.label)} <span class="album-group-count">(${blockCounts[bId]} רצועות)</span></td>
          </tr>
        `);
      }
      if (bId === "p2" && s.ch_lbl && s.ch_lbl !== lastSubChapter) {
        lastSubChapter = s.ch_lbl;
        htmlRows.push(`
          <tr class="sub-chapter-header">
            <td colspan="4">📁 ${esc(s.ch_lbl)}</td>
          </tr>
        `);
      }
    } else if (sortBy === "albums") {
      const grp = normalizeAlbGrp(s.alb_group);
      if (grp !== lastAlbGroup) {
        lastAlbGroup = grp;
        const grpIcon = grp === TV_GRP_NAME ? "📺" : (grp === "סינגלים וביצועים בודדים" ? "🎵" : "💿");
        htmlRows.push(`
          <tr class="album-group-header">
            <td colspan="4">${grpIcon} ${esc(grp)} <span class="album-group-count">(${albumCounts[grp]} רצועות)</span></td>
          </tr>
        `);
      }
    }
    const roleSub = s.role_cat !== "words_and_music" ? `<span class="badge r-${esc(s.role_cat)}">${esc(s.role_label)}</span>` : "";
    const titleAttrEsc = JSON.stringify(s.raw_title).replace(/"/g, "&quot;");
    const perfDisp = s.perf || s.ch || "";
    const perfAttrEsc = JSON.stringify(perfDisp).replace(/"/g, "&quot;");
    const cleanAlbFilter = (s.alb || "").replace(/\s*\(#\d+\)\s*$/, "").trim();
    const albAttrEsc = JSON.stringify(cleanAlbFilter).replace(/"/g, "&quot;");
    const subNumHtml = (sortBy === "albums" && s.alb_trk && s.alb_trk < 999)
      ? `<div style="font-size:10.5px; color:var(--gold-soft); opacity:0.85;">רצועה #${s.alb_trk}</div>`
      : (sortBy !== "canonical" || filteredSongs.length !== SONGS.length ? `<div style="font-size:10.5px; opacity:0.65;">#${s.n}</div>` : "");
    const isFav = favoriteVids.has(s.vid);
    const isVerFiltered = (exactSongTitle && exactSongTitle === s.raw_title);
    htmlRows.push(`
    <tr class="song-row ${i === currentIndex ? "active" : ""} ${s.ver_total > 1 ? "multi-ver-row" : ""}" onclick="playSongAt(${i}, false)">
      <td class="row-num">
        <div><span class="playing-ind">▶</span>${i + 1}</div>
        ${subNumHtml}
      </td>
      <td>
        <div class="song-main-title">
          <span>${esc(s.raw_title)}</span>
          ${s.year ? `<span class="song-year">(${esc(s.year)})</span>` : ""}
          ${s.ver_total > 1 ? `<span class="ver-badge ${isVerFiltered ? "active-ver-filter" : ""}" onclick="filterByExactSong(event, ${titleAttrEsc})" title="לחץ להצגת כל ${s.ver_total} הביצועים של שיר זה בלבד">ביצוע ${s.ver_idx}/${s.ver_total}</span>` : ""}
          ${roleSub}
        </div>
      </td>
      <td>
        <div class="perf-primary"><span class="clickable-meta" onclick="filterBySongTitle(event, ${perfAttrEsc})" title="לחץ לסינון כל השירים של מבצע זה">${esc(perfDisp)}</span></div>
        ${s.alb ? `<div class="perf-album"><span class="clickable-meta" onclick="filterBySongTitle(event, ${albAttrEsc})" title="לחץ לסינון כל שירי האלבום">${esc(s.alb)}</span></div>` : ""}
      </td>
      <td style="text-align:left;">
        <div class="dur-fav-wrap">
          <span class="dur-text">${esc(s.dur)}</span>
          <button class="fav-btn ${isFav ? "is-fav" : ""}" type="button" data-vid="${esc(s.vid)}" onclick="toggleFavorite(event, '${esc(s.vid)}')" title="הוסף / הסר מהמועדפים">${isFav ? "❤️" : "♡"}</button>
        </div>
      </td>
    </tr>`);
  });
  tbody.innerHTML = htmlRows.join("");
  syncFavUI();

  if (!skipSync) syncUrlAndStorageState();
}

function renderArchiveTable(skipSync = false) {
  const rawInput = document.getElementById("archSearchInput").value;
  const qRaw = rawInput.trim().toLowerCase();
  const qNorm = normHeb(rawInput);
  const rf = document.getElementById("archRoleFilter").value;
  const sf = document.getElementById("archSourceFilter").value;

  const filteredArch = ARCHIVE_SONGS.filter(s => {
    if (archAudioOnly && !s.has_audio) return false;
    if (rf !== "ALL" && s.role_cat !== rf) return false;
    if (sf !== "ALL") {
      const hasSource = (s.links || []).some(l => {
        const src = String(l.source || "");
        if (sf === "nli") return src.startsWith("nli");
        if (sf === "zemereshet") return src.startsWith("zemereshet");
        return src === sf;
      });
      if (!hasSource) return false;
    }
    if (!qRaw) return true;
    return s._sRaw.includes(qRaw) || (qNorm.length > 0 && s._sNorm.includes(qNorm));
  });

  document.getElementById("archCountChip").textContent = archAudioOnly
    ? `${filteredArch.length} שירים עם הקלטה להאזנה (מתוך ${ARCHIVE_SONGS.length} שירי ארכיון)`
    : `${filteredArch.length} מתוך ${ARCHIVE_SONGS.length} שירי ארכיון`;

  const tbody = document.getElementById("archiveBody");
  tbody.innerHTML = filteredArch.map((s, idx) => {
    let compactRole = s.role_label || "";
    if (s.co_creators) {
      compactRole = compactRole
        .replace(` (${s.co_creators})`, "")
        .replace(` · ${s.co_creators}`, "")
        .trim();
    }
    return `
    <tr>
      <td class="row-num">${idx + 1}</td>
      <td>
        <div class="song-main-title">
          <span>${esc(s.title)}</span>
          ${s.year && s.year !== "ללא שנה" ? `<span class="song-year">(${esc(s.year)})</span>` : ""}
          ${s.has_audio ? `<span class="badge audio-avail-badge">🎧 הקלטה להאזנה</span>` : ""}
        </div>
        ${s.alt_titles && s.alt_titles.length ? `<div class="perf-album">שמות נוספים: ${esc(s.alt_titles.join(", "))}</div>` : ""}
      </td>
      <td>
        <div class="perf-primary">${s.perfs ? esc(s.perfs) : "<span style='color:var(--muted);'>לא מתועד מבצע</span>"}</div>
        <div style="margin-top:3px;"><span class="badge r-${esc(s.role_cat)}">${esc(compactRole)}</span></div>
        ${s.co_creators ? `<div class="perf-album" style="margin-top:3px;">שותפים ליצירה: ${esc(s.co_creators)}</div>` : ""}
      </td>
      <td>
        ${s.opening_line ? `<div class="opening-line" style="-webkit-line-clamp:2;">"${esc(s.opening_line)}"</div>` : "<span style='color:var(--muted);'>—</span>"}
      </td>
      <td>${renderArchivePills(s.links, false)}</td>
    </tr>
  `;
  }).join("");

  if (!skipSync) syncUrlAndStorageState();
}

document.addEventListener("keydown", function(ev) {
  const tag = (ev.target && ev.target.tagName) ? ev.target.tagName.toLowerCase() : "";
  if (tag === "input" || tag === "textarea" || tag === "select" || (ev.target && ev.target.isContentEditable)) {
    if (ev.key === "Escape") {
      if (ev.target.id === "searchInput" && ev.target.value) {
        clearSearch("yt");
      } else if (ev.target.id === "archSearchInput" && ev.target.value) {
        clearSearch("arch");
      } else {
        ev.target.blur();
      }
    }
    return;
  }
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
  if (ev.key === "/" ) {
    ev.preventDefault();
    const inp = currentTab === "arch" ? document.getElementById("archSearchInput") : document.getElementById("searchInput");
    if (inp) { inp.focus(); inp.select(); }
  } else if (ev.key === " " || ev.key === "k" || ev.key === "K") {
    ev.preventDefault();
    togglePlayPause();
  } else if (ev.key === "n" || ev.key === "N") {
    ev.preventDefault();
    playNext();
  } else if (ev.key === "p" || ev.key === "P") {
    ev.preventDefault();
    playPrev();
  } else if (ev.key === "s" || ev.key === "S") {
    ev.preventDefault();
    toggleShuffle();
  } else if (ev.key === "r" || ev.key === "R") {
    ev.preventDefault();
    toggleRepeatOne();
  } else if (ev.key === "f" || ev.key === "F") {
    ev.preventDefault();
    toggleCurrentFavorite();
  }
});

(function initApp() {
  let saved = {};
  try {
    if (window.localStorage) {
      saved = JSON.parse(localStorage.getItem(STORAGE_PREFIX + "state") || "{}") || {};
    }
  } catch (e) {}

  const params = new URLSearchParams(window.location.search);
  const qParam = params.get("q");
  const exactParam = params.get("exact");
  const sortParam = params.get("sort") || saved.sort;
  const tierParam = params.get("tier") || saved.tier;
  const roleParam = params.get("role") || saved.role;
  const decadeParam = params.get("decade") || saved.decade;
  const tabParam = params.get("tab") || saved.tab;
  const shufParam = params.get("shuffle");
  const repParam = params.get("repeat");
  const onePerParam = params.get("oneper");
  const favParam = params.get("fav");
  const archAudioParam = params.get("archaudio");

  if (SONGS.length > 0) {
    const reqVid = params.get("v") || (!params.get("song") ? saved.vid : "");
    const reqSongNum = parseInt(params.get("song") || saved.song || "1", 10);
    if (reqVid) {
      playingSong = SONGS.find(x => x.vid === reqVid) || SONGS.find(x => x.n === reqSongNum) || SONGS[0];
    } else {
      playingSong = SONGS.find(x => x.n === reqSongNum) || SONGS[0];
    }
  }

  if (exactParam) {
    exactSongTitle = exactParam;
  }
  if (qParam !== null) {
    document.getElementById("searchInput").value = qParam;
    updateSearchClearUI("yt");
  }
  if (sortParam) document.getElementById("sortSelect").value = sortParam;
  if (tierParam) document.getElementById("tierFilter").value = tierParam;
  if (roleParam) document.getElementById("roleFilter").value = roleParam;
  if (decadeParam) document.getElementById("decadeFilter").value = decadeParam;
  if ((tierParam && tierParam !== "ALL") || (roleParam && roleParam !== "ALL")) {
    const drw = document.getElementById("advancedDrawer");
    const btn = document.getElementById("advFilterBtn");
    if (drw) drw.classList.add("open");
    if (btn) btn.classList.add("btn-active");
  }
  if (shufParam === "1" || (shufParam === null && saved.shuffle)) {
    shuffleEnabled = true;
    const btn = document.getElementById("shuffleBtn");
    if (btn) btn.classList.add("btn-active");
  }
  if (repParam === "1" || (repParam === null && saved.repeat)) {
    repeatOneEnabled = true;
    const btn = document.getElementById("repeatBtn");
    if (btn) {
      btn.classList.add("btn-active");
      btn.setAttribute("aria-pressed", "true");
    }
  }
  if (onePerParam === "1" || (onePerParam === null && saved.oneper)) {
    onePerSongOnly = true;
    syncOnePerSongUI();
  }
  if (favParam === "1" || (favParam === null && saved.fav && favoriteVids.size > 0)) {
    favOnly = true;
  }
  syncFavUI();
  if (archAudioParam === "1" || (archAudioParam === null && saved.archaudio)) {
    archAudioOnly = true;
    syncArchAudioOnlyUI();
  }
  if (tabParam === "arch") switchTab("arch", true);

  renderTable(true);
  renderArchiveTable(true);

  initMediaSessionHandlers();
  setInterval(updatePlaybackProgress, 500);
  const ytWrapEl = document.getElementById("ytFrameWrap");
  if (ytWrapEl && "IntersectionObserver" in window) {
    const obs = new IntersectionObserver((entries) => {
      if (entries && entries.length > 0) {
        isMainPlayerVisible = entries[0].isIntersecting;
        updateMiniPlayerVisibility();
      }
    }, { threshold: 0.08 });
    obs.observe(ytWrapEl);
  }
  if (SONGS.length > 0) {
    if (!playingSong) playingSong = filteredSongs[0] || SONGS[0];
    currentIndex = filteredSongs.findIndex(x => x.vid === playingSong.vid);
    currentAltIdx = -1;
    updateNowPlayingCard(playingSong);
    syncBlockJumpHighlight();
    pendingVideoLoad = { vid: playingSong.vid, autoplay: false };
    loadYouTubeIframeAPI();
    document.querySelectorAll("tr.song-row").forEach((tr, i) => {
      tr.classList.toggle("active", i === currentIndex);
    });
    if (currentIndex > 0) setTimeout(() => scrollToActiveRow(false), 150);
  }
})();
