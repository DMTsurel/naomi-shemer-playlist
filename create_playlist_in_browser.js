// ============================================================================
// יצירת פלייליסט "שירי נעמי שמר - האוסף המקיף" (648 ביצועים) בחשבון היוטיוב שלך
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com בדפדפן וודא שאתה מחובר לחשבון היוטיוב שלך.
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console של הדפדפן.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// תוך כ-10 שניות הפלייליסט ייווצר וייפתח אוטומטית!
// ============================================================================
(async function createNaomiShemerPlaylist() {
  const VIDEO_IDS = ["IUxt7faTExY", "H8V8yhc2eYI", "VbIHsjgvE2g", "cpp8XENcuBk", "9xETAic8buQ", "hBlEx2bIRNI", "TFIrOcriazY", "lDNtdPiL584", "jk6lOLldgT4", "Xe4H1sCCAJo", "mw9uiMMvFGk", "GnxLc7C_yvM", "tWs6g7hg0BI", "5Hz8UIWRADU", "4_Laz5PQV-Y", "sFB_B3wTXLE", "-T6mxux7wKM", "Zr-iKRNRzQk", "DEKLsquUP34", "85QDrN6FB8Q", "dC2fS3vZAPY", "MFrjlagc8rE", "AvJZwh25uZ4", "AxnQ3qrsp64", "OEVLRDRUxyc", "ryXmue6dutA", "fiU_B2M84Ww", "gTXgnxD6Cuc", "1_dsV0afFgA", "zpFGk2nz_-A", "-4bnvgAYqmo", "BLpTR9p0mkY", "unyzPkoPBEs", "kA1Gl5w3ydI", "BgpoI6q79Lw", "2iljNf6XqsA", "fE8xcZiFRO8", "Ue8yK2cnLTA", "-hts04B4Wkk", "418kExn65Ug", "VS1Bu7hsvi8", "vQjWwS6X7CI", "6OWfRHNgEtg", "ei2FcAMuRAw", "BnKrb-46CNI", "kF5Lpl7IL6w", "7PxG0jfZX6k", "0mcp9JqqJ1k", "q3XGUpCCTJs", "Q5N5gxqjDFc", "oNmwW4s3AuI", "0ypE8NBmyYo", "BfKQ4bj0JJk", "k0RE3k8k1pQ", "5kl6qHnbp9Y", "wly5oxW3C6Y", "_DujVVkqqQ0", "neYlxPR8-WA", "ax7p4AggiqY", "Zs1s0_fs9EI", "dDXngW-5jV0", "Ce_cSMB0Ri8", "SnARDknXrZQ", "ZLzkd2ui6PM", "RqHN-so83M4", "JfJ3DrI7-6w", "HlUl3uS6T6Q", "jfy9Pml8UZg", "e9lQpiSO6XM", "oCezgzbCZBk", "HvE1Ib25iDk", "YQc4x6hGSyg", "-nzLbN3sFRQ", "Uwi4o3fwQwc", "0IPY0etp8eE", "DdET9qVDfRI", "eSmhtnivpvY", "07aL8h1LyJk", "2aQJz8v_KkU", "kF_MJiReEn0", "9bfiWAv4HSU", "zN2CRXhVJ3o", "bfQeAbF8-4A", "eCRBb3h6mz8", "iLhwph9IJMA", "uqOoO342wNg", "WFOhRFYM1wM", "CYwiq1Uu5Ng", "4ZFF3v39RD4", "mYfdJkb1gqg", "zZHynZGet5g", "URL56lbFmr8", "aDZqwcq7eVI", "B0EO7nYCdu0", "SgzeIwaaGMU", "T5o_o8lO-1M", "0XhvBFzatFc", "NWR0K-8lBhU", "wO3U1xG7Um0", "EFIwG44Egek", "z-OpnBf-JNI", "KOecGqpq-f0", "ZFFJR9iTSuo", "6hhQ_4omcKs", "zRQLXqjeRoE", "isxLekbAFHw", "D13BJwfsQu8", "-2N-WzrLzCc", "4HZWNJzXTm4", "XteReGQom40", "pjCtGobuuSE", "0ga6HoypSJU", "JAY_uZjqmIA", "04AcSZS8K3s", "08Z_uYA9PLc", "OS9uUlfBrbA", "YY8vUjMWzEc", "zV4aK_XyPW8", "KvBOUWSO1PM", "_lds9E6qEQg", "XBrUmJLCkEw", "5TZvR7wFlVo", "Sn0vSoeVXpI", "qpbBemLcsUE", "O4OhUorCxX8", "vrJcb0mauz8", "eUam8viOqxs", "vVQ0Xmtb9_Q", "whmUk6hiVE4", "I00dlNJc6BI", "9Er1RvAuM7M", "bzl8G_GQJKE", "zTCbwh0WyXM", "gkPyKqEFNSE", "YS6EfEQu1ik", "SDCkIuEiWWY", "jMlzihkguOU", "g6clciS1riA", "PXL8ltjFDCk", "CSjnGcglVJI", "CeRvSDeJx-I", "g-477LqGTr4", "rh0oGPJbf5M", "pDLQ_FrzKL4", "Sah0hB6rSFY", "WDzRA91O678", "hSaod2F6TA8", "UxWCHV50LoU", "OvN5nJ9bn2Y", "skYeVk80Eo0", "2QMxLPxD25g", "7uxKafYsUrU", "Okw-ktcRVr0", "cYZArmDfKnA", "pCK483hwY-0", "vczM9eWy1yw", "sdlmzqJiT5M", "XsDAsNDqHW4", "0u--FHf-LHU", "zFJUpGoNWPc", "3iQEC7mO3YY", "B7oZ2GPHhEU", "Gi7-feW4FfE", "FkSHlF212BA", "8y5KQ8UWi0A", "gXM9-IpEzEc", "aKAvYLWF97U", "GgYxh_MoCDA", "DATGdPiFqVA", "ZcKAuoZSzWQ", "XKbvfLzHms4", "tk3zQs8gDTM", "UwhEUsWVdPg", "VCDKtBt4xb4", "Ba1W41IDnhI", "P8g0g_IQcjI", "CEI769yjg4g", "UgXcD55HXzc", "E3V70DpK_EI", "mpPxqJrum-M", "Yd3_uDW6i4w", "yKAUdNGyVpA", "SSJdF9cV8iQ", "-7qKw4AIGP4", "Ke6iImauSj4", "6EEIW68j5lY", "doXUEtdMaxc", "chuU4lFZ5iA", "chw7OpsTH1A", "UfIj78lym1I", "qvBk0IVkKRE", "PL0HmLqbxpw", "KaovY--ET14", "WBc7IWmf3cs", "QUF8MiDp4O4", "_nDa2esEWJk", "HgMGNLc5ir8", "A-6m6CKOdC4", "E452vwyyVjQ", "XHdb6YDvHII", "7T8wbdYlAbQ", "aO1sboxdmno", "Jg42GYm1qv0", "3iaTDb1K41o", "5VQkcCM1fmc", "iPj5rmj8GZQ", "EdfxwaHVnAk", "He8KKInGwAE", "PkF2Y0bbbCo", "_NylGW8syfw", "yscdF17IT_Y", "Pef5mRmx0fA", "kkJPYVGy31o", "_F3EdZ51O-Q", "Xc6coB1-EPw", "bbIXevkZDnk", "Picy0oa0wl0", "WA8fVawaHuw", "n6qfNKmjutM", "5yDnz_UrH-s", "5xj4ycn0TY8", "dFgoc8M87Ww", "jvZPz3tpWPw", "e4cc_kptHk8", "vQPSLn2e4FY", "zEG-AcszgpQ", "sCRw6hfgQTM", "YJKhOidPJhc", "vxQcorAdAXA", "Omn_wSe-dKU", "vXAxaeNqze4", "M38vdprLLok", "HTMwVk8pQiY", "WZMQaNRyllY", "PHQFSQi4tzU", "xkGxvP-tw1w", "hDqbO57hnyQ", "EfcKLvzIDRw", "ry9RV0yCJpI", "TQwpuggfQWw", "6qiFa7eU34M", "sQTl_NH1n0o", "xI2m7tKJ40E", "qrvKQtQgb2s", "YgYyQjI4UeY", "YrJtArqXavk", "TsA3LycTPSo", "dKHjdN2hr4w", "jAnSY8gxLRg", "1gUgA5_iv5g", "sVEvT4pZeyQ", "JDThzHJWt4o", "hA92uD-XpQs", "losUGtP6fxI", "0viBWDlQ9KE", "dLDcWMN-Fbw", "-1__PIJhhPI", "nruQWhRsem4", "7m9YwTJwFrE", "p320GUpKgkQ", "PrntU87z0n8", "p_OfoN-B_xw", "upipvN8Xw-c", "s1SR4hmgC4U", "HBZpHQRKrFM", "agChJ2Ho124", "ipzIvlpBkbU", "sLvHms2BClA", "narkCrS3_GA", "lKhxVjkSa84", "pKGFC7qoGBA", "wzrVRxyd5a4", "3G8xlTapGQo", "0rZlNPF_utQ", "vUmuxcvyGrM", "FZrRqLdaH5E", "ArRyqOnlQ3k", "bZI8gT-VbT0", "H3h-755AwoI", "XWnWPkDHGz4", "_Zksgxev2ko", "r-eS75zZ76k", "Xoh_DVe4WcA", "2BfY0duzEpE", "7cZaZp3xfDM", "pTlgYtrDSPI", "yzSOpEPUXWw", "vNw21mQVfKM", "l1b8s6ZGXhQ", "l8uDRKHspac", "MtwqXXIN6Xs", "5v77wNxd8Kw", "Y8ob5jdoYBw", "VkgQyNxNQqw", "9XgKm2xg3iA", "7IEl35CsSaI", "Okj7fK4VSOA", "P7eGfaq3E_s", "GyiSOeKOK8s", "NGtt4OBuh2E", "PEamc15DDeY", "F25xFwezdxw", "PIqHAidM99g", "yXzElXsHH38", "UeP8K2lXml8", "cV-WsBBOwto", "jqQTqr1gHEI", "dYYGjAoIU_E", "X0EHaEth0TQ", "x0IPLHoV9Yc", "p64TXGU2ipM", "ufIj60iGZqM", "C1PjhOZQxMU", "dgC-AI1O_a8", "-rGr-thBmjs", "cD2GgbFD_Yo", "wcy425HOqro", "_6La2mK-PqU", "INHBTa-HfSM", "4ApYhj2Mqeo", "KO7lZhbeFDs", "38jU5bVcNzo", "_33ng3euFJI", "me0k188YXNw", "CMhfrA5uDjE", "-p0EvZ_T_AY", "_FhoSjLL61A", "cXln3eAat5g", "AoGcmpu5D4Y", "Pk0mm0ly7Og", "0pdyuulvbzo", "OLQITmFP3Xo", "vAT50nuKMh8", "BBUtEBZLJFQ", "sJFfiL_Y1_E", "UOD51gynvJQ", "o9ElrJy3fmk", "oNZG3NUzB3U", "61RF4uejHJE", "oQLUlVqXkpo", "i9bIVfz1HBw", "2vq22hm-TnI", "Jzkgm9A3Ooc", "tPX2FmmeM6k", "3wNpnpA5K-w", "2LRsVjehz44", "3oB1QegwRqk", "VaztQIe75Ns", "U3xSpmrTgXc", "nz7sT486EYw", "iz3Et-1Ywe8", "CwORk-NwrQM", "2MUXbKJVRZo", "H9f2NJOxcz0", "cmQ9upI0aG8", "n2t3bDiJcMk", "_aoBikUYiBY", "4g6cymurqY0", "bnl-cjqYOwk", "bzLl7TH_VxQ", "3v9rvDklaxc", "YfFNug5ZOac", "AnWiRbrejHg", "A9erliXTS6o", "-dNwuLchpWg", "IWaGaO6VD4c", "mtuSxIIZPqg", "Pxm7UgJ1JiE", "qblckfTw1Rk", "cbNuUKAQMsU", "5-8BIb9KyNk", "Yd63Irvr-Q0", "mzrn0p-yRSM", "dtbSIHcMWjY", "i9KzXu-Nhx0", "2o1uo7sstSI", "Jl0WahK00lU", "UtixqreayIo", "eGrPQv3g9ps", "pPE_eIQYtgY", "tpe1wARxPSs", "9aIw7qJAOA4", "V2eI7l5c3nc", "-xNyTz_yvRU", "gsf0t-VihvE", "YtWovd6r0yc", "WxdVdudBKeE", "Y5aCrfJLjIM", "3YYVsJ9MGZQ", "CJ8_MISsRxg", "EEkIbuhQ9dw", "lXCnVOsgJwo", "24JJpjDS8QY", "Im8ze1yI8Aw", "gpo_GVko6OA", "d8h9EDhbixA", "yavA7DK-_Lg", "6sR4GRdyZZ8", "A1BCQuWuvTE", "2GD7HJfapWM", "XIs2ZIJ2oZw", "mZxh2vHIBcs", "gkP9-OqJETY", "gRfvDuXwtYI", "VXLKQYTYShc", "OFBBD-EuEfA", "s0923q2OCPM", "ZYTJPE70ifA", "yEG2trB0IxU", "-2f28ACy-Gk", "V8CR6u84pXU", "rLucwp89lnE", "VeeEHBwsyQw", "wIFDo3qiS9c", "vbG5B1wswQc", "sKkBNzdlFvE", "tBL2uGdMMZ4", "dT5g0VRp7jE", "SZhwVVZuRkY", "nvaUD-WzYDQ", "dZtHel6cUW8", "Brq81oCuNKc", "7e6hGajTOaE", "1uRrLed3pZc", "ut3moC4G-QI", "EikdgimAjd8", "L7_tsGSLGTs", "gU6tE4TqExI", "sgMLsWRX7SI", "ew9j2OHt8Cw", "zUWmMkqQMQg", "KEOx2onVNDs", "pTt_42SgJ0U", "xypLh9F1IXk", "VsVv0OOIARQ", "nNMmAneQsLs", "morcvF-aFsg", "E-jZMuDEvLQ", "Vimcno4QbUw", "nOa7P6X2I-8", "E-G-dnLO99U", "cCftnvA1iJo", "t6jXzPCR0NA", "Ur53Ai6WISA", "UhSscH59sdA", "NXcXk-diyDY", "FFtI8ZQT2Mk", "B86J0eynF9A", "yWVoMYXeBpM", "w1hLRFc3jfo", "UB35E3hE65E", "CLDelMZYKC8", "DGUHUGnDYn0", "8d9khSRpSkk", "qgyoXwMKJXg", "LBTf6IMt2X8", "OdbpJIdes4Q", "LYoIOT8VvK0", "xdj8UWyGpFg", "s6Geto53AmI", "qiWE67WQSBY", "nNFb0CPT7Js", "tNga0kZsgXY", "kO9D3crjEsU", "YMdqSo7wMUk", "F-tHf-vPBxQ", "Xw4qL0j_9Vs", "Ti6nFst0JaE", "4gYlHwrMV50", "N4QGMJR3Qqo", "S9QL3kDf8gA", "ukOWgL-9mlw", "F6syH8W0EGA", "e1c2MjdU9T8", "O5In5PJnEr8", "Lg-Can0ZrXM", "ud8TFvfUJ8M", "hw_SJRb1uEk", "OBkMzEHYA3c", "6rlo1KZ0qok", "YWwJ1O6fQQs", "JAh-XgpCIEo", "hZirnyIx1Tw", "G5RVx22SVzs", "0Yn3EvME2ko", "WBfuFYdOQT4", "zuYjR6RNeIw", "BncSM_l0_P8", "BAliJ1ieJrI", "X-KSBs_Lsd8", "6xpROKMcQus", "c0WSmr4tlLY", "0eWljspYG7E", "41VIMNNssjw", "mMEXXehlL54", "ldmMVGr-syE", "QYW7YCydh3s", "Rh-AfNJC1AY", "rGRBY2iPjpk", "xyiYZRhJsSo", "k8u50w4T-1g", "sgVtXugsDtE", "uquTBB0PbFY", "v6wgkaN8mvg", "gq5PAlFBEi8", "_qb0WUb7i5A", "wONNxGvP9S4", "ORPN8djCQws", "Luu_LIPtx-M", "DZCXER0nGaM", "LR_zCS48QV0", "ITgt-B5IdFk", "MhIbjL4Hghc", "tnNhOpq6MqI", "ZSYQh_YatoU", "XOJchlUhps0", "2smvtZlQSEg", "XWOGYjtgJG0", "JvQBz3CHrK0", "Kc3Z01Zqr24", "F7KHn6M2VGk", "0XHUVfPJlak", "g57hoYLobng", "ygW51Wri9wQ", "4okw4g4Q8e4", "sFbghpqy0Lo", "nOl7AAouxVc", "sdqrr4rdUPA", "P35Ek5tTy4I", "dWXjopZ8-1s", "0yT4idCIsSE", "g_QXbJmWWO0", "GZW3RhiQeyY", "_JG62QmM-QE", "3a8B5imZV8o", "URuGgQXkQpQ", "SOOmGDRVIK8", "WILLlFVs8K4", "WDQyD0VHt68", "VnReHM2MOuo", "l4y16i5NwwQ", "weX6vsG96ZY", "UsNNGSI6qzk", "lfB0Y5mJ1qk", "Bujd3-vDfE8", "Z-JxFdJcoB4", "VhBycovusXA", "oJZEOGPBtp0", "4MJ1vA3znA4", "DLilbBb5C-k", "1D4_GtYfmUE", "piH6EOOP7cY", "SzfqrHxbpug", "r97YIa4BDnM", "jzNc8KFQ4S4", "JUiRv74kgHU", "71Pqy6HKns8", "-eINxqt2z0A", "xam-JFkXggk", "3H9EF4ZzVy8", "6BfneC2-IvA", "L8jFWAH86Hw", "C-rohkw6OX8", "d9pbNfB26wc", "kLf2ybtWLCI", "KXjJoVHJsQw", "gfYmkBTQVD4", "XixXG6ffyy0", "jOpau37GjhY", "XeD27Barwbk", "0re6w_ZITxg", "1dAeJminXHM", "t_qzuM6V2Co", "Bac-K0Wjp2A", "OzrUXu1pKkg", "acNmIrbrp0k", "OdYRuoXrHHw", "EZ2zDG6qrJE", "T3qo2SYP52U", "B7rC1GyPlqM", "SfPOduJnKvk", "pUFhGuyD6j4", "7ziQJmP02M0", "z91zsr8vHnU", "dfPBgVKT_H8", "OfsdkuisiNo", "9o-4qxrv584", "Eff5K5VrmKE", "erKzXsvfheA", "6yrG087cato", "R-oz2dlpbvY", "ExOobxzS4tc", "X3GCh50sW8A", "7t6dTKHZY6U", "JH-1IrNb_P4", "ubenw8IJ9dE", "jYVg9ERVMv0", "cAOakJcPmGs", "hZwuhnWXkLE", "EEq9IuWDBlM", "KSTaBxvL4JQ", "k0LjOdjBdYU", "mxCqvGI5iu0", "Ae_oPwsp_P0", "R1tJE7-evoQ", "wFYq_Is8wJk", "tz4ISVJyEfI", "HH2wou4FvsA", "QKmscJgKCYs", "evAV9e6QUlI", "uITVQ8JRMg4", "COoXTOZQYQ4", "J1mbZ9eGho0", "K1DBCpPxqeM", "OxafdSA-QkE", "omNa4PW1lU8", "cITPhRNWoq0", "sCQfgFoAQu4", "p3PIKVi8goc", "_vJ6UtXHybA", "V_AZsXtgxvY", "YMrwmCzH330", "NhX0XzGmv9A", "_LilpxfdvKc", "IXn5sqpAhqc", "Ya2SuHzZAXo", "xAvvvAO6glU", "DtlDXf6tveY", "Hv0SuDUsjyc", "ZKGMTf5XLCk", "OkWKy3URsDg", "q-9lO4eg7-w", "gEacqh5DPk4", "ydCddPTqZmo", "L1QLv-RFy7A", "dGSCRDVe9NE", "wk0pllJl1nU", "Yk82zpkqZjw", "oo8IRR00H30", "mnXZeefSK8w", "nMxKk66pAzc", "6Z2BOKloo7k", "SdrmUgN92O4", "lmTSkGSnxzw", "9d8hI1wc_Bs", "fs14OduKHd4", "YYVengVA5V8", "oMZHElIjza4"];
  const PLAYLIST_TITLE = "שירי נעמי שמר";
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
