// ============================================================================
// יצירת פלייליסט "שירי נעמי שמר - האוסף המקיף" (619 ביצועים) בחשבון היוטיוב שלך
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com בדפדפן וודא שאתה מחובר לחשבון היוטיוב שלך.
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console של הדפדפן.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// תוך כ-10 שניות הפלייליסט ייווצר וייפתח אוטומטית!
// ============================================================================
(async function createNaomiShemerPlaylist() {
  const VIDEO_IDS = ["IUxt7faTExY", "H8V8yhc2eYI", "qvBk0IVkKRE", "VbIHsjgvE2g", "cpp8XENcuBk", "FDD19O2CreI", "PL0HmLqbxpw", "KaovY--ET14", "9xETAic8buQ", "hBlEx2bIRNI", "QUF8MiDp4O4", "TFIrOcriazY", "_nDa2esEWJk", "lDNtdPiL584", "HgMGNLc5ir8", "jk6lOLldgT4", "Xe4H1sCCAJo", "A-6m6CKOdC4", "mw9uiMMvFGk", "oo8IRR00H30", "_GD1f91Erg8", "GnxLc7C_yvM", "E452vwyyVjQ", "tWs6g7hg0BI", "5Hz8UIWRADU", "4_Laz5PQV-Y", "sFB_B3wTXLE", "-T6mxux7wKM", "XHdb6YDvHII", "DEKLsquUP34", "Zr-iKRNRzQk", "7T8wbdYlAbQ", "dC2fS3vZAPY", "85QDrN6FB8Q", "aO1sboxdmno", "MFrjlagc8rE", "AvJZwh25uZ4", "Jg42GYm1qv0", "AxnQ3qrsp64", "5VQkcCM1fmc", "OEVLRDRUxyc", "3iaTDb1K41o", "ryXmue6dutA", "fiU_B2M84Ww", "gTXgnxD6Cuc", "1_dsV0afFgA", "iPj5rmj8GZQ", "EdfxwaHVnAk", "zpFGk2nz_-A", "-4bnvgAYqmo", "unyzPkoPBEs", "BLpTR9p0mkY", "kA1Gl5w3ydI", "_NylGW8syfw", "BgpoI6q79Lw", "2iljNf6XqsA", "fE8xcZiFRO8", "yscdF17IT_Y", "Pef5mRmx0fA", "kkJPYVGy31o", "Ue8yK2cnLTA", "-hts04B4Wkk", "mq13AHHLul4", "418kExn65Ug", "Xc6coB1-EPw", "vQjWwS6X7CI", "6OWfRHNgEtg", "bbIXevkZDnk", "ei2FcAMuRAw", "kF5Lpl7IL6w", "BnKrb-46CNI", "Picy0oa0wl0", "7PxG0jfZX6k", "0mcp9JqqJ1k", "q3XGUpCCTJs", "WA8fVawaHuw", "Q5N5gxqjDFc", "n6qfNKmjutM", "5yDnz_UrH-s", "5xj4ycn0TY8", "oNmwW4s3AuI", "0ypE8NBmyYo", "BfKQ4bj0JJk", "e4cc_kptHk8", "k0RE3k8k1pQ", "5kl6qHnbp9Y", "wly5oxW3C6Y", "_DujVVkqqQ0", "neYlxPR8-WA", "ax7p4AggiqY", "sCRw6hfgQTM", "dDXngW-5jV0", "Zs1s0_fs9EI", "YJKhOidPJhc", "SnARDknXrZQ", "Ce_cSMB0Ri8", "ZLzkd2ui6PM", "RqHN-so83M4", "vxQcorAdAXA", "Omn_wSe-dKU", "JfJ3DrI7-6w", "HlUl3uS6T6Q", "jfy9Pml8UZg", "e9lQpiSO6XM", "vXAxaeNqze4", "jiIKJ29A8qU", "HvE1Ib25iDk", "oCezgzbCZBk", "YQc4x6hGSyg", "-nzLbN3sFRQ", "Uwi4o3fwQwc", "0IPY0etp8eE", "DdET9qVDfRI", "TcTOqEg-htw", "HTMwVk8pQiY", "eSmhtnivpvY", "yMsCeHsgGwQ", "M38vdprLLok", "2aQJz8v_KkU", "kF_MJiReEn0", "9bfiWAv4HSU", "PHQFSQi4tzU", "zN2CRXhVJ3o", "bfQeAbF8-4A", "eCRBb3h6mz8", "iLhwph9IJMA", "uqOoO342wNg", "xkGxvP-tw1w", "WFOhRFYM1wM", "CYwiq1Uu5Ng", "4ZFF3v39RD4", "mYfdJkb1gqg", "zZHynZGet5g", "URL56lbFmr8", "aDZqwcq7eVI", "B0EO7nYCdu0", "SgzeIwaaGMU", "T5o_o8lO-1M", "0XhvBFzatFc", "NWR0K-8lBhU", "o7vESC28Iqo", "hDqbO57hnyQ", "wO3U1xG7Um0", "EFIwG44Egek", "z-OpnBf-JNI", "KOecGqpq-f0", "ZFFJR9iTSuo", "ry9RV0yCJpI", "6hhQ_4omcKs", "zRQLXqjeRoE", "isxLekbAFHw", "TQwpuggfQWw", "6qiFa7eU34M", "D13BJwfsQu8", "sQTl_NH1n0o", "-2N-WzrLzCc", "4HZWNJzXTm4", "XteReGQom40", "pjCtGobuuSE", "xI2m7tKJ40E", "0ga6HoypSJU", "JAY_uZjqmIA", "04AcSZS8K3s", "qrvKQtQgb2s", "08Z_uYA9PLc", "OS9uUlfBrbA", "YY8vUjMWzEc", "YgYyQjI4UeY", "XxJZZ-9zlpQ", "_lds9E6qEQg", "XBrUmJLCkEw", "YrJtArqXavk", "TsA3LycTPSo", "5TZvR7wFlVo", "Sn0vSoeVXpI", "dKHjdN2hr4w", "qpbBemLcsUE", "O4OhUorCxX8", "vrJcb0mauz8", "eUam8viOqxs", "jAnSY8gxLRg", "vVQ0Xmtb9_Q", "whmUk6hiVE4", "9Er1RvAuM7M", "1gUgA5_iv5g", "bzl8G_GQJKE", "zTCbwh0WyXM", "gkPyKqEFNSE", "hA92uD-XpQs", "YS6EfEQu1ik", "SDCkIuEiWWY", "jMlzihkguOU", "g6clciS1riA", "PXL8ltjFDCk", "CSjnGcglVJI", "CeRvSDeJx-I", "g-477LqGTr4", "rh0oGPJbf5M", "pDLQ_FrzKL4", "Sah0hB6rSFY", "WDzRA91O678", "hSaod2F6TA8", "UxWCHV50LoU", "OvN5nJ9bn2Y", "skYeVk80Eo0", "losUGtP6fxI", "2QMxLPxD25g", "7uxKafYsUrU", "Okw-ktcRVr0", "cYZArmDfKnA", "-1__PIJhhPI", "vczM9eWy1yw", "pCK483hwY-0", "sdlmzqJiT5M", "XsDAsNDqHW4", "0u--FHf-LHU", "zFJUpGoNWPc", "3iQEC7mO3YY", "B7oZ2GPHhEU", "Gi7-feW4FfE", "FkSHlF212BA", "8y5KQ8UWi0A", "nruQWhRsem4", "7m9YwTJwFrE", "aKAvYLWF97U", "p320GUpKgkQ", "GgYxh_MoCDA", "DATGdPiFqVA", "PrntU87z0n8", "ZcKAuoZSzWQ", "XKbvfLzHms4", "tk3zQs8gDTM", "p_OfoN-B_xw", "upipvN8Xw-c", "UwhEUsWVdPg", "s1SR4hmgC4U", "VCDKtBt4xb4", "Ba1W41IDnhI", "P8g0g_IQcjI", "CEI769yjg4g", "agChJ2Ho124", "UgXcD55HXzc", "E3V70DpK_EI", "mpPxqJrum-M", "Yd3_uDW6i4w", "yKAUdNGyVpA", "SSJdF9cV8iQ", "-7qKw4AIGP4", "ipzIvlpBkbU", "Ke6iImauSj4", "6EEIW68j5lY", "doXUEtdMaxc", "chw7OpsTH1A", "UfIj78lym1I", "narkCrS3_GA", "sLvHms2BClA", "lKhxVjkSa84", "wzrVRxyd5a4", "pKGFC7qoGBA", "3G8xlTapGQo", "0rZlNPF_utQ", "vUmuxcvyGrM", "FZrRqLdaH5E", "ArRyqOnlQ3k", "bZI8gT-VbT0", "XWnWPkDHGz4", "H3h-755AwoI", "_Zksgxev2ko", "Xoh_DVe4WcA", "2BfY0duzEpE", "7cZaZp3xfDM", "pTlgYtrDSPI", "yzSOpEPUXWw", "vNw21mQVfKM", "l1b8s6ZGXhQ", "l8uDRKHspac", "MtwqXXIN6Xs", "5v77wNxd8Kw", "Y8ob5jdoYBw", "VkgQyNxNQqw", "KBvQrOKM37k", "9XgKm2xg3iA", "7IEl35CsSaI", "Okj7fK4VSOA", "P7eGfaq3E_s", "GyiSOeKOK8s", "NGtt4OBuh2E", "PIqHAidM99g", "F25xFwezdxw", "PEamc15DDeY", "yXzElXsHH38", "UeP8K2lXml8", "cV-WsBBOwto", "jqQTqr1gHEI", "dYYGjAoIU_E", "X0EHaEth0TQ", "kurpWet0X78", "2yXv06OahEc", "ufIj60iGZqM", "C1PjhOZQxMU", "RDTKjKtbdak", "dgC-AI1O_a8", "-rGr-thBmjs", "cD2GgbFD_Yo", "wcy425HOqro", "tSmg5wveagg", "INHBTa-HfSM", "_6La2mK-PqU", "KO7lZhbeFDs", "38jU5bVcNzo", "_33ng3euFJI", "me0k188YXNw", "CMhfrA5uDjE", "-p0EvZ_T_AY", "_FhoSjLL61A", "cXln3eAat5g", "AoGcmpu5D4Y", "Pk0mm0ly7Og", "0pdyuulvbzo", "OLQITmFP3Xo", "vAT50nuKMh8", "BBUtEBZLJFQ", "sJFfiL_Y1_E", "UOD51gynvJQ", "o9ElrJy3fmk", "oNZG3NUzB3U", "61RF4uejHJE", "oQLUlVqXkpo", "jsTz7qC8tMo", "Jzkgm9A3Ooc", "2vq22hm-TnI", "tPX2FmmeM6k", "2LRsVjehz44", "3wNpnpA5K-w", "3oB1QegwRqk", "VaztQIe75Ns", "U3xSpmrTgXc", "nz7sT486EYw", "CwORk-NwrQM", "iz3Et-1Ywe8", "2MUXbKJVRZo", "H9f2NJOxcz0", "cmQ9upI0aG8", "n2t3bDiJcMk", "_aoBikUYiBY", "4g6cymurqY0", "bnl-cjqYOwk", "bzLl7TH_VxQ", "3v9rvDklaxc", "YfFNug5ZOac", "AnWiRbrejHg", "A9erliXTS6o", "-dNwuLchpWg", "IWaGaO6VD4c", "mtuSxIIZPqg", "Pxm7UgJ1JiE", "5-8BIb9KyNk", "qblckfTw1Rk", "Yd63Irvr-Q0", "mzrn0p-yRSM", "dsZYpHVPjv0", "i9KzXu-Nhx0", "2o1uo7sstSI", "Jl0WahK00lU", "UtixqreayIo", "eGrPQv3g9ps", "w8uvk1uQYXg", "pPE_eIQYtgY", "zHmm0bb_x5c", "V2eI7l5c3nc", "-xNyTz_yvRU", "gsf0t-VihvE", "YtWovd6r0yc", "WxdVdudBKeE", "EEkIbuhQ9dw", "3YYVsJ9MGZQ", "CJ8_MISsRxg", "Y5aCrfJLjIM", "lXCnVOsgJwo", "24JJpjDS8QY", "Im8ze1yI8Aw", "gpo_GVko6OA", "d8h9EDhbixA", "yavA7DK-_Lg", "6sR4GRdyZZ8", "A1BCQuWuvTE", "2GD7HJfapWM", "04e7PQhn-vY", "XIs2ZIJ2oZw", "mZxh2vHIBcs", "gkP9-OqJETY", "gRfvDuXwtYI", "VXLKQYTYShc", "OFBBD-EuEfA", "s0923q2OCPM", "ZYTJPE70ifA", "yEG2trB0IxU", "-2f28ACy-Gk", "V8CR6u84pXU", "rLucwp89lnE", "VeeEHBwsyQw", "wIFDo3qiS9c", "vbG5B1wswQc", "kd0BjoJemU4", "tBL2uGdMMZ4", "dT5g0VRp7jE", "SZhwVVZuRkY", "nvaUD-WzYDQ", "dZtHel6cUW8", "Brq81oCuNKc", "7e6hGajTOaE", "-givWJMymhs", "ut3moC4G-QI", "EikdgimAjd8", "L7_tsGSLGTs", "JUVV06GzaFE", "sgMLsWRX7SI", "ew9j2OHt8Cw", "zUWmMkqQMQg", "KEOx2onVNDs", "m58C3mRgm5E", "pTt_42SgJ0U", "nNMmAneQsLs", "VsVv0OOIARQ", "xypLh9F1IXk", "morcvF-aFsg", "E-jZMuDEvLQ", "Vimcno4QbUw", "nOa7P6X2I-8", "E-G-dnLO99U", "cCftnvA1iJo", "t6jXzPCR0NA", "Ur53Ai6WISA", "UhSscH59sdA", "FFtI8ZQT2Mk", "B86J0eynF9A", "NXcXk-diyDY", "UB35E3hE65E", "CLDelMZYKC8", "yWVoMYXeBpM", "DGUHUGnDYn0", "8d9khSRpSkk", "qgyoXwMKJXg", "LBTf6IMt2X8", "OdbpJIdes4Q", "LYoIOT8VvK0", "xdj8UWyGpFg", "b9Vxv861vb4", "FwOsYI51_NU", "qiWE67WQSBY", "nNFb0CPT7Js", "tNga0kZsgXY", "kO9D3crjEsU", "YMdqSo7wMUk", "Xw4qL0j_9Vs", "Ti6nFst0JaE", "4gYlHwrMV50", "N4QGMJR3Qqo", "RU68BDHHZJo", "S9QL3kDf8gA", "ukOWgL-9mlw", "F6syH8W0EGA", "e1c2MjdU9T8", "O5In5PJnEr8", "Lg-Can0ZrXM", "ud8TFvfUJ8M", "USMuk_mS6vA", "hw_SJRb1uEk", "OBkMzEHYA3c", "6rlo1KZ0qok", "YWwJ1O6fQQs", "JAh-XgpCIEo", "hZirnyIx1Tw", "G5RVx22SVzs", "0Yn3EvME2ko", "WBfuFYdOQT4", "zuYjR6RNeIw", "BAliJ1ieJrI", "BncSM_l0_P8", "X-KSBs_Lsd8", "6xpROKMcQus", "c0WSmr4tlLY", "0eWljspYG7E", "mMEXXehlL54", "41VIMNNssjw", "ldmMVGr-syE", "xUe9MRUvOww", "Rh-AfNJC1AY", "xyiYZRhJsSo", "rGRBY2iPjpk", "k8u50w4T-1g", "uquTBB0PbFY", "v6wgkaN8mvg", "wONNxGvP9S4", "ORPN8djCQws", "Luu_LIPtx-M", "DZCXER0nGaM", "LR_zCS48QV0", "ITgt-B5IdFk", "MhIbjL4Hghc", "tnNhOpq6MqI", "ZSYQh_YatoU", "2smvtZlQSEg", "XWOGYjtgJG0", "JvQBz3CHrK0", "F7KHn6M2VGk", "Kc3Z01Zqr24", "y_Z_-_Wt-Yc", "g57hoYLobng", "ygW51Wri9wQ", "lTvJVWW87H8", "4okw4g4Q8e4", "sFbghpqy0Lo", "nOl7AAouxVc", "sdqrr4rdUPA", "P35Ek5tTy4I", "dWXjopZ8-1s", "0yT4idCIsSE", "u-uUCxxSFhs", "GZW3RhiQeyY", "_JG62QmM-QE", "URuGgQXkQpQ", "3a8B5imZV8o", "SOOmGDRVIK8", "WILLlFVs8K4", "WDQyD0VHt68", "VnReHM2MOuo", "weX6vsG96ZY", "l4y16i5NwwQ", "UsNNGSI6qzk", "lfB0Y5mJ1qk", "Bujd3-vDfE8", "Z-JxFdJcoB4", "VhBycovusXA", "oJZEOGPBtp0", "4MJ1vA3znA4", "DLilbBb5C-k", "1D4_GtYfmUE", "piH6EOOP7cY", "SzfqrHxbpug", "r97YIa4BDnM", "JUiRv74kgHU", "jzNc8KFQ4S4", "Jwjk2orp29M", "-eINxqt2z0A", "xam-JFkXggk", "3H9EF4ZzVy8", "6BfneC2-IvA", "L8jFWAH86Hw", "AUm3hkHaOKo", "d9pbNfB26wc", "kLf2ybtWLCI", "KXjJoVHJsQw", "hs1Uo7ilYKo", "gfYmkBTQVD4", "XixXG6ffyy0", "GsmV9XnbTDY", "jOpau37GjhY", "WfesepFfvOo", "1dAeJminXHM", "t_qzuM6V2Co", "Bac-K0Wjp2A", "OzrUXu1pKkg", "acNmIrbrp0k", "OdYRuoXrHHw", "EZ2zDG6qrJE", "T3qo2SYP52U", "SfPOduJnKvk", "pUFhGuyD6j4", "7ziQJmP02M0", "dfPBgVKT_H8", "z91zsr8vHnU", "OfsdkuisiNo", "9o-4qxrv584", "Eff5K5VrmKE", "6yrG087cato", "R-oz2dlpbvY", "X3GCh50sW8A", "7t6dTKHZY6U", "JH-1IrNb_P4", "ubenw8IJ9dE", "jYVg9ERVMv0", "cAOakJcPmGs", "8tNy2en1CpE", "hZwuhnWXkLE", "EEq9IuWDBlM", "KSTaBxvL4JQ", "k0LjOdjBdYU", "mxCqvGI5iu0", "Ae_oPwsp_P0", "7m1hm4WJKAM", "R1tJE7-evoQ", "wFYq_Is8wJk", "tz4ISVJyEfI", "HH2wou4FvsA", "QKmscJgKCYs", "evAV9e6QUlI", "4Xt5gj8m7ds", "J1mbZ9eGho0", "K1DBCpPxqeM", "OxafdSA-QkE", "omNa4PW1lU8", "cITPhRNWoq0", "sCQfgFoAQu4", "p3PIKVi8goc", "V_AZsXtgxvY", "YMrwmCzH330", "NhX0XzGmv9A", "_LilpxfdvKc", "IXn5sqpAhqc", "Ya2SuHzZAXo", "xAvvvAO6glU", "DtlDXf6tveY", "Hv0SuDUsjyc", "ZKGMTf5XLCk", "OkWKy3URsDg", "q-9lO4eg7-w", "gEacqh5DPk4", "ydCddPTqZmo"];
  const PLAYLIST_TITLE = "שירי נעמי שמר - האוסף המקיף (619 ביצועים, 369 שירים)";
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
