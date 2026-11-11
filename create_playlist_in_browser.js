// ============================================================================
// יצירת פלייליסט "שירי נעמי שמר - האוסף המקיף" (426 ביצועים) בחשבון היוטיוב שלך
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com בדפדפן וודא שאתה מחובר לחשבון היוטיוב שלך.
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console של הדפדפן.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// תוך כ-10 שניות הפלייליסט ייווצר וייפתח אוטומטית!
// ============================================================================
(async function createNaomiShemerPlaylist() {
  const VIDEO_IDS = ["ubenw8IJ9dE", "GZW3RhiQeyY", "_LilpxfdvKc", "3H9EF4ZzVy8", "tz4ISVJyEfI", "cD2GgbFD_Yo", "wFYq_Is8wJk", "HH2wou4FvsA", "q3XGUpCCTJs", "RJd_8iW_4AQ", "SSJdF9cV8iQ", "SgzeIwaaGMU", "dZtHel6cUW8", "zTCbwh0WyXM", "LHpYM8gdGu4", "A6RoASKhCNU", "-7qKw4AIGP4", "T5o_o8lO-1M", "Brq81oCuNKc", "gkPyKqEFNSE", "tSmg5wveagg", "GsmV9XnbTDY", "6yrG087cato", "Jzkgm9A3Ooc", "PIqHAidM99g", "dfPBgVKT_H8", "J1mbZ9eGho0", "Okw-ktcRVr0", "dgC-AI1O_a8", "7UR3J49MP3o", "R1tJE7-evoQ", "IXn5sqpAhqc", "Ya2SuHzZAXo", "xAvvvAO6glU", "l1b8s6ZGXhQ", "DtlDXf6tveY", "DATGdPiFqVA", "Hv0SuDUsjyc", "QKmscJgKCYs", "mtuSxIIZPqg", "DIqPZvt0krA", "zRQLXqjeRoE", "3oB1QegwRqk", "AQSyWY542DU", "38jU5bVcNzo", "vrJcb0mauz8", "F7KHn6M2VGk", "9Er1RvAuM7M", "9XgKm2xg3iA", "ZSYQh_YatoU", "jYVg9ERVMv0", "k8u50w4T-1g", "L8jFWAH86Hw", "jMlzihkguOU", "SnARDknXrZQ", "LR_zCS48QV0", "WfesepFfvOo", "1dAeJminXHM", "MhIbjL4Hghc", "YMdqSo7wMUk", "_lds9E6qEQg", "8y5KQ8UWi0A", "me0k188YXNw", "neNKCSaT1T8", "cITPhRNWoq0", "sCQfgFoAQu4", "ldmMVGr-syE", "qS_vPd2O1no", "7e6hGajTOaE", "TFIrOcriazY", "lDNtdPiL584", "hSaod2F6TA8", "UeP8K2lXml8", "jqQTqr1gHEI", "tWs6g7hg0BI", "AUm3hkHaOKo", "EEq9IuWDBlM", "pUFhGuyD6j4", "LYoIOT8VvK0", "CMhfrA5uDjE", "g-477LqGTr4", "0IPY0etp8eE", "UwhEUsWVdPg", "SfPOduJnKvk", "xdj8UWyGpFg", "0pdyuulvbzo", "OLQITmFP3Xo", "-nzLbN3sFRQ", "R-oz2dlpbvY", "0XhvBFzatFc", "MqgKFE4UrC4", "NE6QdM4g7bc", "NWR0K-8lBhU", "ei2FcAMuRAw", "EEkIbuhQ9dw", "CJ8_MISsRxg", "FFtI8ZQT2Mk", "ufIj60iGZqM", "nNMmAneQsLs", "VsVv0OOIARQ", "Bac-K0Wjp2A", "5kl6qHnbp9Y", "qAY-hA0QveY", "OxafdSA-QkE", "YMrwmCzH330", "UtixqreayIo", "Eff5K5VrmKE", "NhX0XzGmv9A", "q-9lO4eg7-w", "XKbvfLzHms4", "cAOakJcPmGs", "xyiYZRhJsSo", "V_AZsXtgxvY", "wONNxGvP9S4", "kLf2ybtWLCI", "RU68BDHHZJo", "SOOmGDRVIK8", "Bujd3-vDfE8", "Ae_oPwsp_P0", "EikdgimAjd8", "ZKGMTf5XLCk", "Jln9XtBu2Pc", "E-jZMuDEvLQ", "Uz5FS8p8KdI", "u5LMWBjWfgQ", "CCZMQwHwkNk", "KEOx2onVNDs", "FX7fnWOOg6g", "nOa7P6X2I-8", "e1c2MjdU9T8", "zUWmMkqQMQg", "jd_FU5morhQ", "9HZVUKehx1M", "2iljNf6XqsA", "fE8xcZiFRO8", "FZrRqLdaH5E", "BfKQ4bj0JJk", "VnReHM2MOuo", "zZHynZGet5g", "whmUk6hiVE4", "IUxt7faTExY", "ZFFJR9iTSuo", "B0EO7nYCdu0", "AnWiRbrejHg", "5Hz8UIWRADU", "ArRyqOnlQ3k", "6hhQ_4omcKs", "2yXv06OahEc", "FkSHlF212BA", "eGrPQv3g9ps", "VCDKtBt4xb4", "EFIwG44Egek", "H8V8yhc2eYI", "zRZ9XNdVKL8", "atlO4ofBSJc", "MFrjlagc8rE", "08Z_uYA9PLc", "gEacqh5DPk4", "Hg77f-xalbc", "-1__PIJhhPI", "narkCrS3_GA", "4g6cymurqY0", "P7eGfaq3E_s", "BAliJ1ieJrI", "wzrVRxyd5a4", "r97YIa4BDnM", "A1BCQuWuvTE", "2GD7HJfapWM", "DGUHUGnDYn0", "4Xt5gj8m7ds", "D13BJwfsQu8", "7t6dTKHZY6U", "oNmwW4s3AuI", "0ypE8NBmyYo", "YWwJ1O6fQQs", "Cp6JWRyIiHI", "-dNwuLchpWg", "Im8ze1yI8Aw", "_lQMNHjzBi4", "V2eI7l5c3nc", "XHdb6YDvHII", "zpFGk2nz_-A", "sFB_B3wTXLE", "URL56lbFmr8", "ygW51Wri9wQ", "uknSL-k0Mk4", "ud8TFvfUJ8M", "hw_SJRb1uEk", "4okw4g4Q8e4", "3KL06zK4_gM", "dWXjopZ8-1s", "-T6mxux7wKM", "gkP9-OqJETY", "5TZvR7wFlVo", "G5RVx22SVzs", "61RF4uejHJE", "k0LjOdjBdYU", "oJZEOGPBtp0", "u-uUCxxSFhs", "9o-4qxrv584", "COwJ3lgcT1w", "nOl7AAouxVc", "Xoh_DVe4WcA", "kQzNA4IiaNs", "_DujVVkqqQ0", "JUVV06GzaFE", "LBTf6IMt2X8", "yXzElXsHH38", "ukOWgL-9mlw", "ZLzkd2ui6PM", "nNFb0CPT7Js", "HTMwVk8pQiY", "doXUEtdMaxc", "XxJZZ-9zlpQ", "mMEXXehlL54", "w8uvk1uQYXg", "Xw4qL0j_9Vs", "UB35E3hE65E", "jsTz7qC8tMo", "yMsCeHsgGwQ", "CLDelMZYKC8", "cMnTruKBW9c", "S9QL3kDf8gA", "sJFfiL_Y1_E", "ITgt-B5IdFk", "O5In5PJnEr8", "VbIHsjgvE2g", "cpp8XENcuBk", "Jwjk2orp29M", "2QMxLPxD25g", "O4OhUorCxX8", "OFBBD-EuEfA", "6sR4GRdyZZ8", "Lg-Can0ZrXM", "g57hoYLobng", "tNga0kZsgXY", "yEG2trB0IxU", "-2f28ACy-Gk", "morcvF-aFsg", "piH6EOOP7cY", "MtwqXXIN6Xs", "5v77wNxd8Kw", "SzfqrHxbpug", "YS6EfEQu1ik", "URuGgQXkQpQ", "Rh-AfNJC1AY", "4ZFF3v39RD4", "sdlmzqJiT5M", "pjCtGobuuSE", "BBUtEBZLJFQ", "e9lQpiSO6XM", "2o1uo7sstSI", "UgXcD55HXzc", "SDCkIuEiWWY", "RqHN-so83M4", "-4bnvgAYqmo", "dC2fS3vZAPY", "kF5Lpl7IL6w", "AxnQ3qrsp64", "7ziQJmP02M0", "zuYjR6RNeIw", "mxCqvGI5iu0", "X3GCh50sW8A", "hZirnyIx1Tw", "VeeEHBwsyQw", "kA1Gl5w3ydI", "Ti6nFst0JaE", "P35Ek5tTy4I", "DLilbBb5C-k", "sdqrr4rdUPA", "jk6lOLldgT4", "0yT4idCIsSE", "FwOsYI51_NU", "1D4_GtYfmUE", "gfYmkBTQVD4", "aKAvYLWF97U", "uqOoO342wNg", "WFOhRFYM1wM", "s0923q2OCPM", "7ML3C4GTeus", "fcRd2ZTQiPA", "jzNc8KFQ4S4", "l4y16i5NwwQ", "sCRw6hfgQTM", "Ue8yK2cnLTA", "E3V70DpK_EI", "qpbBemLcsUE", "JAY_uZjqmIA", "6EEIW68j5lY", "Yd3_uDW6i4w", "yKAUdNGyVpA", "mq13AHHLul4", "WDQyD0VHt68", "UhSscH59sdA", "V4QSoLFj-NM", "DZCXER0nGaM", "ydCddPTqZmo", "3o8DcLvv3tQ", "Z-JxFdJcoB4", "zFJUpGoNWPc", "vVQ0Xmtb9_Q", "Ba1W41IDnhI", "kF_MJiReEn0", "wIFDo3qiS9c", "P8g0g_IQcjI", "9bfiWAv4HSU", "vQjWwS6X7CI", "T3qo2SYP52U", "OS9uUlfBrbA", "KXjJoVHJsQw", "6BfneC2-IvA", "zEG-AcszgpQ", "mYfdJkb1gqg", "cmQ9upI0aG8", "9xETAic8buQ", "hBlEx2bIRNI", "ax7p4AggiqY", "6OWfRHNgEtg", "DEKLsquUP34", "VXLKQYTYShc", "Xe4H1sCCAJo", "0u--FHf-LHU", "dsZYpHVPjv0", "7cZaZp3xfDM", "5-8BIb9KyNk", "pDLQ_FrzKL4", "unyzPkoPBEs", "WDzRA91O678", "Y8ob5jdoYBw", "tBL2uGdMMZ4", "2smvtZlQSEg", "4gYlHwrMV50", "Yd63Irvr-Q0", "JfJ3DrI7-6w", "GgYxh_MoCDA", "AvJZwh25uZ4", "y_Z_-_Wt-Yc", "isxLekbAFHw", "7uxKafYsUrU", "xUe9MRUvOww", "kd0BjoJemU4", "BgpoI6q79Lw", "YY8vUjMWzEc", "24JJpjDS8QY", "-givWJMymhs", "xam-JFkXggk", "BwFspz55-xs", "Jl0WahK00lU", "tnNhOpq6MqI", "hZwuhnWXkLE", "LsjkI8D1zYQ", "z-OpnBf-JNI", "KOecGqpq-f0", "zN2CRXhVJ3o", "bfQeAbF8-4A", "4HZWNJzXTm4", "UOD51gynvJQ", "OzrUXu1pKkg", "o9ElrJy3fmk", "jiIKJ29A8qU", "UsNNGSI6qzk", "UIWqYA98hzI", "p3PIKVi8goc", "ORPN8djCQws", "6Z46a9WwmDY", "bzLl7TH_VxQ", "zHmm0bb_x5c", "sgMLsWRX7SI", "VaztQIe75Ns", "KO7lZhbeFDs", "JAh-XgpCIEo", "X-KSBs_Lsd8", "XWnWPkDHGz4", "PXL8ltjFDCk", "gpo_GVko6OA", "nz7sT486EYw", "omNa4PW1lU8", "OBkMzEHYA3c", "ZYTJPE70ifA", "OdbpJIdes4Q", "4_Laz5PQV-Y", "WBfuFYdOQT4", "H1uKLGSdCFU", "_FhoSjLL61A", "EZ2zDG6qrJE", "8d9khSRpSkk", "oQLUlVqXkpo", "mZxh2vHIBcs", "F6syH8W0EGA", "rQkXmnBSc70", "3v9rvDklaxc", "EW511LnOUJg", "iDL9k25rJLk", "yavA7DK-_Lg", "JH-1IrNb_P4", "sFbghpqy0Lo", "wcy425HOqro", "iz3Et-1Ywe8", "tPX2FmmeM6k", "NGtt4OBuh2E", "AwFSUc4g-2U", "JvQBz3CHrK0", "-p0EvZ_T_AY", "Luu_LIPtx-M", "skYeVk80Eo0", "YtWovd6r0yc", "ryXmue6dutA", "WxdVdudBKeE", "fiU_B2M84Ww", "mw9uiMMvFGk", "oo8IRR00H30", "K45gjCVyUbo", "WILLlFVs8K4", "SZhwVVZuRkY", "VhBycovusXA", "0Yn3EvME2ko", "AoGcmpu5D4Y", "CYwiq1Uu5Ng", "3Kf4rRQEpW0", "dYYGjAoIU_E", "IWaGaO6VD4c", "2MUXbKJVRZo", "K1DBCpPxqeM", "OdYRuoXrHHw", "7m1hm4WJKAM", "WkG7H2prm7Y"];
  const PLAYLIST_TITLE = "שירי נעמי שמר - האוסף המקיף (426 ביצועים, 371 שירים)";
  const PLAYLIST_DESC = "אוסף מקיף של שירי נעמי שמר (אלבומיה של נעמי שמר, ביצועים מקוריים מתוך אלבומים, הקלטות ארכיון וקאברים נבחרים). נוצר מתוך איחוד 9 מאגרים (אקו\"ם, הספרייה הלאומית, שירונט, ויקיפדיה, סטריאו ומונו, פזמונט, זמרשת, Discogs ו-MusicBrainz).";

  if (!window.ytcfg || typeof window.ytcfg.get !== "function") {
    alert("שגיאה: יש להריץ את הסקריפט מתוך לשונית פתוחה של https://www.youtube.com");
    return;
  }

  function getCookie(name) {
    const m = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()\[\]\\/+^])/g, "\\$1") + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : null;
  }

  const sapisid = getCookie("SAPISID") || getCookie("__Secure-3PAPISID");
  if (!sapisid) {
    alert("שגיאה: לא נמצא חיבור לחשבון יוטיוב. אנא התחבר לחשבון היוטיוב שלך ב-https://www.youtube.com ונסה שוב.");
    return;
  }

  async function makeSapisidHash(origin) {
    const ts = Math.floor(Date.now() / 1000);
    const input = ts + " " + sapisid + " " + origin;
    const buf = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(input));
    const hex = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    return "SAPISIDHASH " + ts + "_" + hex;
  }

  async function ytPost(endpoint, bodyObj) {
    const origin = window.location.origin;
    const auth = await makeSapisidHash(origin);
    const headers = {
      "Content-Type": "application/json",
      "Authorization": auth,
      "X-Origin": origin,
      "X-Goog-AuthUser": String(window.ytcfg.get("SESSION_INDEX") ?? "0"),
    };
    const visitor = window.ytcfg.get("VISITOR_DATA");
    if (visitor) headers["X-Goog-Visitor-Id"] = visitor;

    const resp = await fetch(origin + endpoint + "?prettyPrint=false", {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({
        context: window.ytcfg.get("INNERTUBE_CONTEXT"),
        ...bodyObj
      })
    });
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error("HTTP " + resp.status + ": " + txt.slice(0, 300));
    }
    return resp.json();
  }

  console.log("🚀 יוצר פלייליסט חדש ביוטיוב:", PLAYLIST_TITLE);
  const createRes = await ytPost("/youtubei/v1/playlist/create", {
    title: PLAYLIST_TITLE,
    description: PLAYLIST_DESC,
    privacyStatus: "UNLISTED"
  });

  const playlistId = createRes.playlistId;
  if (!playlistId) {
    console.error("תגובת שרת:", createRes);
    throw new Error("לא התקבל playlistId מיוטיוב.");
  }
  console.log("✅ הפלייליסט נוצר בהצלחה! מזהה:", playlistId);

  const BATCH_SIZE = 50;
  for (let i = 0; i < VIDEO_IDS.length; i += BATCH_SIZE) {
    const batch = VIDEO_IDS.slice(i, i + BATCH_SIZE);
    console.log(`⏳ מוסיף שירים ${i + 1} עד ${Math.min(i + BATCH_SIZE, VIDEO_IDS.length)} מתוך ${VIDEO_IDS.length}...`);
    await ytPost("/youtubei/v1/browse/edit_playlist", {
      playlistId: playlistId,
      actions: batch.map(vid => ({
        action: "ACTION_ADD_VIDEO",
        addedVideoId: vid
      }))
    });
    await new Promise(r => setTimeout(r, 600));
  }

  const url = "https://www.youtube.com/playlist?list=" + playlistId;
  console.log("🎉 סיימנו! כל " + VIDEO_IDS.length + " השירים נוספו לפלייליסט:");
  console.log(url);
  window.open(url, "_blank");
})();
