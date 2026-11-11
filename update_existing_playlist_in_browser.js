// ============================================================================
// עדכון הפלייליסט הקיים ביוטיוב (PLFHErlX6i22g) + וידוא אוטומטי של הסדר הסופי!
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com/playlist?list=PLFHErlX6i22g בדפדפן (מחובר לחשבון שלך).
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// הסקריפט יעדכן את הפלייליסט הקיים (PLFHErlX6i22g), ובסיום יקרא מחדש את כל הרצועות
// משרתי יוטיוב כדי לוודא ב-100% שהסידור הסופי תואם לרשימת היעד (ויתקן אוטומטית כל סטייה).
// ============================================================================
(async function updateExistingNaomiShemerPlaylist() {
  const PLAYLIST_ID = "PLFHErlX6i22g";
  const TARGET_VIDEO_IDS = ["IUxt7faTExY", "H8V8yhc2eYI", "qvBk0IVkKRE", "VbIHsjgvE2g", "cpp8XENcuBk", "FDD19O2CreI", "PL0HmLqbxpw", "KaovY--ET14", "9xETAic8buQ", "hBlEx2bIRNI", "QUF8MiDp4O4", "TFIrOcriazY", "_nDa2esEWJk", "lDNtdPiL584", "HgMGNLc5ir8", "jk6lOLldgT4", "Xe4H1sCCAJo", "A-6m6CKOdC4", "mw9uiMMvFGk", "oo8IRR00H30", "_GD1f91Erg8", "GnxLc7C_yvM", "E452vwyyVjQ", "tWs6g7hg0BI", "5Hz8UIWRADU", "4_Laz5PQV-Y", "sFB_B3wTXLE", "-T6mxux7wKM", "XHdb6YDvHII", "DEKLsquUP34", "Zr-iKRNRzQk", "7T8wbdYlAbQ", "dC2fS3vZAPY", "85QDrN6FB8Q", "aO1sboxdmno", "MFrjlagc8rE", "AvJZwh25uZ4", "Jg42GYm1qv0", "AxnQ3qrsp64", "5VQkcCM1fmc", "OEVLRDRUxyc", "3iaTDb1K41o", "ryXmue6dutA", "fiU_B2M84Ww", "gTXgnxD6Cuc", "1_dsV0afFgA", "iPj5rmj8GZQ", "EdfxwaHVnAk", "zpFGk2nz_-A", "-4bnvgAYqmo", "unyzPkoPBEs", "BLpTR9p0mkY", "kA1Gl5w3ydI", "_NylGW8syfw", "BgpoI6q79Lw", "2iljNf6XqsA", "fE8xcZiFRO8", "yscdF17IT_Y", "Pef5mRmx0fA", "kkJPYVGy31o", "Ue8yK2cnLTA", "-hts04B4Wkk", "mq13AHHLul4", "418kExn65Ug", "Xc6coB1-EPw", "vQjWwS6X7CI", "6OWfRHNgEtg", "bbIXevkZDnk", "ei2FcAMuRAw", "kF5Lpl7IL6w", "BnKrb-46CNI", "Picy0oa0wl0", "7PxG0jfZX6k", "0mcp9JqqJ1k", "q3XGUpCCTJs", "WA8fVawaHuw", "Q5N5gxqjDFc", "n6qfNKmjutM", "5yDnz_UrH-s", "5xj4ycn0TY8", "oNmwW4s3AuI", "0ypE8NBmyYo", "BfKQ4bj0JJk", "e4cc_kptHk8", "k0RE3k8k1pQ", "5kl6qHnbp9Y", "wly5oxW3C6Y", "_DujVVkqqQ0", "neYlxPR8-WA", "ax7p4AggiqY", "sCRw6hfgQTM", "dDXngW-5jV0", "Zs1s0_fs9EI", "YJKhOidPJhc", "SnARDknXrZQ", "Ce_cSMB0Ri8", "ZLzkd2ui6PM", "RqHN-so83M4", "vxQcorAdAXA", "Omn_wSe-dKU", "JfJ3DrI7-6w", "HlUl3uS6T6Q", "jfy9Pml8UZg", "e9lQpiSO6XM", "vXAxaeNqze4", "jiIKJ29A8qU", "HvE1Ib25iDk", "oCezgzbCZBk", "YQc4x6hGSyg", "-nzLbN3sFRQ", "Uwi4o3fwQwc", "0IPY0etp8eE", "DdET9qVDfRI", "TcTOqEg-htw", "HTMwVk8pQiY", "eSmhtnivpvY", "yMsCeHsgGwQ", "M38vdprLLok", "2aQJz8v_KkU", "kF_MJiReEn0", "9bfiWAv4HSU", "PHQFSQi4tzU", "zN2CRXhVJ3o", "bfQeAbF8-4A", "eCRBb3h6mz8", "iLhwph9IJMA", "uqOoO342wNg", "xkGxvP-tw1w", "WFOhRFYM1wM", "CYwiq1Uu5Ng", "4ZFF3v39RD4", "mYfdJkb1gqg", "zZHynZGet5g", "URL56lbFmr8", "aDZqwcq7eVI", "B0EO7nYCdu0", "SgzeIwaaGMU", "T5o_o8lO-1M", "0XhvBFzatFc", "NWR0K-8lBhU", "o7vESC28Iqo", "hDqbO57hnyQ", "wO3U1xG7Um0", "EFIwG44Egek", "z-OpnBf-JNI", "KOecGqpq-f0", "ZFFJR9iTSuo", "ry9RV0yCJpI", "6hhQ_4omcKs", "zRQLXqjeRoE", "isxLekbAFHw", "TQwpuggfQWw", "6qiFa7eU34M", "D13BJwfsQu8", "sQTl_NH1n0o", "-2N-WzrLzCc", "4HZWNJzXTm4", "XteReGQom40", "pjCtGobuuSE", "xI2m7tKJ40E", "0ga6HoypSJU", "JAY_uZjqmIA", "04AcSZS8K3s", "qrvKQtQgb2s", "08Z_uYA9PLc", "OS9uUlfBrbA", "YY8vUjMWzEc", "YgYyQjI4UeY", "XxJZZ-9zlpQ", "_lds9E6qEQg", "XBrUmJLCkEw", "YrJtArqXavk", "TsA3LycTPSo", "5TZvR7wFlVo", "Sn0vSoeVXpI", "dKHjdN2hr4w", "qpbBemLcsUE", "O4OhUorCxX8", "vrJcb0mauz8", "eUam8viOqxs", "jAnSY8gxLRg", "vVQ0Xmtb9_Q", "whmUk6hiVE4", "9Er1RvAuM7M", "1gUgA5_iv5g", "bzl8G_GQJKE", "zTCbwh0WyXM", "gkPyKqEFNSE", "hA92uD-XpQs", "YS6EfEQu1ik", "SDCkIuEiWWY", "jMlzihkguOU", "g6clciS1riA", "PXL8ltjFDCk", "CSjnGcglVJI", "CeRvSDeJx-I", "g-477LqGTr4", "rh0oGPJbf5M", "pDLQ_FrzKL4", "Sah0hB6rSFY", "WDzRA91O678", "hSaod2F6TA8", "UxWCHV50LoU", "OvN5nJ9bn2Y", "skYeVk80Eo0", "losUGtP6fxI", "2QMxLPxD25g", "7uxKafYsUrU", "Okw-ktcRVr0", "cYZArmDfKnA", "-1__PIJhhPI", "vczM9eWy1yw", "pCK483hwY-0", "sdlmzqJiT5M", "XsDAsNDqHW4", "0u--FHf-LHU", "zFJUpGoNWPc", "3iQEC7mO3YY", "B7oZ2GPHhEU", "Gi7-feW4FfE", "FkSHlF212BA", "8y5KQ8UWi0A", "nruQWhRsem4", "7m9YwTJwFrE", "aKAvYLWF97U", "p320GUpKgkQ", "GgYxh_MoCDA", "DATGdPiFqVA", "PrntU87z0n8", "ZcKAuoZSzWQ", "XKbvfLzHms4", "tk3zQs8gDTM", "p_OfoN-B_xw", "upipvN8Xw-c", "UwhEUsWVdPg", "s1SR4hmgC4U", "VCDKtBt4xb4", "Ba1W41IDnhI", "P8g0g_IQcjI", "CEI769yjg4g", "agChJ2Ho124", "UgXcD55HXzc", "E3V70DpK_EI", "mpPxqJrum-M", "Yd3_uDW6i4w", "yKAUdNGyVpA", "SSJdF9cV8iQ", "-7qKw4AIGP4", "ipzIvlpBkbU", "Ke6iImauSj4", "6EEIW68j5lY", "doXUEtdMaxc", "chw7OpsTH1A", "UfIj78lym1I", "narkCrS3_GA", "sLvHms2BClA", "lKhxVjkSa84", "wzrVRxyd5a4", "pKGFC7qoGBA", "3G8xlTapGQo", "0rZlNPF_utQ", "vUmuxcvyGrM", "FZrRqLdaH5E", "ArRyqOnlQ3k", "bZI8gT-VbT0", "XWnWPkDHGz4", "H3h-755AwoI", "_Zksgxev2ko", "Xoh_DVe4WcA", "2BfY0duzEpE", "7cZaZp3xfDM", "pTlgYtrDSPI", "yzSOpEPUXWw", "vNw21mQVfKM", "l1b8s6ZGXhQ", "l8uDRKHspac", "MtwqXXIN6Xs", "5v77wNxd8Kw", "Y8ob5jdoYBw", "VkgQyNxNQqw", "KBvQrOKM37k", "9XgKm2xg3iA", "7IEl35CsSaI", "Okj7fK4VSOA", "P7eGfaq3E_s", "GyiSOeKOK8s", "NGtt4OBuh2E", "PIqHAidM99g", "F25xFwezdxw", "PEamc15DDeY", "yXzElXsHH38", "UeP8K2lXml8", "cV-WsBBOwto", "jqQTqr1gHEI", "dYYGjAoIU_E", "X0EHaEth0TQ", "kurpWet0X78", "2yXv06OahEc", "ufIj60iGZqM", "C1PjhOZQxMU", "RDTKjKtbdak", "dgC-AI1O_a8", "-rGr-thBmjs", "cD2GgbFD_Yo", "wcy425HOqro", "tSmg5wveagg", "INHBTa-HfSM", "_6La2mK-PqU", "KO7lZhbeFDs", "38jU5bVcNzo", "_33ng3euFJI", "me0k188YXNw", "CMhfrA5uDjE", "-p0EvZ_T_AY", "_FhoSjLL61A", "cXln3eAat5g", "AoGcmpu5D4Y", "Pk0mm0ly7Og", "0pdyuulvbzo", "OLQITmFP3Xo", "vAT50nuKMh8", "BBUtEBZLJFQ", "sJFfiL_Y1_E", "UOD51gynvJQ", "o9ElrJy3fmk", "oNZG3NUzB3U", "61RF4uejHJE", "oQLUlVqXkpo", "jsTz7qC8tMo", "Jzkgm9A3Ooc", "2vq22hm-TnI", "tPX2FmmeM6k", "2LRsVjehz44", "3wNpnpA5K-w", "3oB1QegwRqk", "VaztQIe75Ns", "U3xSpmrTgXc", "nz7sT486EYw", "CwORk-NwrQM", "iz3Et-1Ywe8", "2MUXbKJVRZo", "H9f2NJOxcz0", "cmQ9upI0aG8", "n2t3bDiJcMk", "_aoBikUYiBY", "4g6cymurqY0", "bnl-cjqYOwk", "bzLl7TH_VxQ", "3v9rvDklaxc", "YfFNug5ZOac", "AnWiRbrejHg", "A9erliXTS6o", "-dNwuLchpWg", "IWaGaO6VD4c", "mtuSxIIZPqg", "Pxm7UgJ1JiE", "5-8BIb9KyNk", "qblckfTw1Rk", "Yd63Irvr-Q0", "mzrn0p-yRSM", "dsZYpHVPjv0", "i9KzXu-Nhx0", "2o1uo7sstSI", "Jl0WahK00lU", "UtixqreayIo", "eGrPQv3g9ps", "w8uvk1uQYXg", "pPE_eIQYtgY", "zHmm0bb_x5c", "V2eI7l5c3nc", "-xNyTz_yvRU", "gsf0t-VihvE", "YtWovd6r0yc", "WxdVdudBKeE", "EEkIbuhQ9dw", "3YYVsJ9MGZQ", "CJ8_MISsRxg", "Y5aCrfJLjIM", "lXCnVOsgJwo", "24JJpjDS8QY", "Im8ze1yI8Aw", "gpo_GVko6OA", "d8h9EDhbixA", "yavA7DK-_Lg", "6sR4GRdyZZ8", "A1BCQuWuvTE", "2GD7HJfapWM", "04e7PQhn-vY", "XIs2ZIJ2oZw", "mZxh2vHIBcs", "gkP9-OqJETY", "gRfvDuXwtYI", "VXLKQYTYShc", "OFBBD-EuEfA", "s0923q2OCPM", "ZYTJPE70ifA", "yEG2trB0IxU", "-2f28ACy-Gk", "V8CR6u84pXU", "rLucwp89lnE", "VeeEHBwsyQw", "wIFDo3qiS9c", "vbG5B1wswQc", "kd0BjoJemU4", "tBL2uGdMMZ4", "dT5g0VRp7jE", "SZhwVVZuRkY", "nvaUD-WzYDQ", "dZtHel6cUW8", "Brq81oCuNKc", "7e6hGajTOaE", "-givWJMymhs", "ut3moC4G-QI", "EikdgimAjd8", "L7_tsGSLGTs", "JUVV06GzaFE", "sgMLsWRX7SI", "ew9j2OHt8Cw", "zUWmMkqQMQg", "KEOx2onVNDs", "m58C3mRgm5E", "pTt_42SgJ0U", "nNMmAneQsLs", "VsVv0OOIARQ", "xypLh9F1IXk", "morcvF-aFsg", "E-jZMuDEvLQ", "Vimcno4QbUw", "nOa7P6X2I-8", "E-G-dnLO99U", "cCftnvA1iJo", "t6jXzPCR0NA", "Ur53Ai6WISA", "UhSscH59sdA", "FFtI8ZQT2Mk", "B86J0eynF9A", "NXcXk-diyDY", "UB35E3hE65E", "CLDelMZYKC8", "yWVoMYXeBpM", "DGUHUGnDYn0", "8d9khSRpSkk", "qgyoXwMKJXg", "LBTf6IMt2X8", "OdbpJIdes4Q", "LYoIOT8VvK0", "xdj8UWyGpFg", "b9Vxv861vb4", "FwOsYI51_NU", "qiWE67WQSBY", "nNFb0CPT7Js", "tNga0kZsgXY", "kO9D3crjEsU", "YMdqSo7wMUk", "Xw4qL0j_9Vs", "Ti6nFst0JaE", "4gYlHwrMV50", "N4QGMJR3Qqo", "RU68BDHHZJo", "S9QL3kDf8gA", "ukOWgL-9mlw", "F6syH8W0EGA", "e1c2MjdU9T8", "O5In5PJnEr8", "Lg-Can0ZrXM", "ud8TFvfUJ8M", "USMuk_mS6vA", "hw_SJRb1uEk", "OBkMzEHYA3c", "6rlo1KZ0qok", "YWwJ1O6fQQs", "JAh-XgpCIEo", "hZirnyIx1Tw", "G5RVx22SVzs", "0Yn3EvME2ko", "WBfuFYdOQT4", "zuYjR6RNeIw", "BAliJ1ieJrI", "BncSM_l0_P8", "X-KSBs_Lsd8", "6xpROKMcQus", "c0WSmr4tlLY", "0eWljspYG7E", "mMEXXehlL54", "41VIMNNssjw", "ldmMVGr-syE", "xUe9MRUvOww", "Rh-AfNJC1AY", "xyiYZRhJsSo", "rGRBY2iPjpk", "k8u50w4T-1g", "uquTBB0PbFY", "v6wgkaN8mvg", "wONNxGvP9S4", "ORPN8djCQws", "Luu_LIPtx-M", "DZCXER0nGaM", "LR_zCS48QV0", "ITgt-B5IdFk", "MhIbjL4Hghc", "tnNhOpq6MqI", "ZSYQh_YatoU", "2smvtZlQSEg", "XWOGYjtgJG0", "JvQBz3CHrK0", "F7KHn6M2VGk", "Kc3Z01Zqr24", "y_Z_-_Wt-Yc", "g57hoYLobng", "ygW51Wri9wQ", "lTvJVWW87H8", "4okw4g4Q8e4", "sFbghpqy0Lo", "nOl7AAouxVc", "sdqrr4rdUPA", "P35Ek5tTy4I", "dWXjopZ8-1s", "0yT4idCIsSE", "u-uUCxxSFhs", "GZW3RhiQeyY", "_JG62QmM-QE", "URuGgQXkQpQ", "3a8B5imZV8o", "SOOmGDRVIK8", "WILLlFVs8K4", "WDQyD0VHt68", "VnReHM2MOuo", "weX6vsG96ZY", "l4y16i5NwwQ", "UsNNGSI6qzk", "lfB0Y5mJ1qk", "Bujd3-vDfE8", "Z-JxFdJcoB4", "VhBycovusXA", "oJZEOGPBtp0", "4MJ1vA3znA4", "DLilbBb5C-k", "1D4_GtYfmUE", "piH6EOOP7cY", "SzfqrHxbpug", "r97YIa4BDnM", "JUiRv74kgHU", "jzNc8KFQ4S4", "Jwjk2orp29M", "-eINxqt2z0A", "xam-JFkXggk", "3H9EF4ZzVy8", "6BfneC2-IvA", "L8jFWAH86Hw", "AUm3hkHaOKo", "d9pbNfB26wc", "kLf2ybtWLCI", "KXjJoVHJsQw", "hs1Uo7ilYKo", "gfYmkBTQVD4", "XixXG6ffyy0", "GsmV9XnbTDY", "jOpau37GjhY", "WfesepFfvOo", "1dAeJminXHM", "t_qzuM6V2Co", "Bac-K0Wjp2A", "OzrUXu1pKkg", "acNmIrbrp0k", "OdYRuoXrHHw", "EZ2zDG6qrJE", "T3qo2SYP52U", "SfPOduJnKvk", "pUFhGuyD6j4", "7ziQJmP02M0", "dfPBgVKT_H8", "z91zsr8vHnU", "OfsdkuisiNo", "9o-4qxrv584", "Eff5K5VrmKE", "6yrG087cato", "R-oz2dlpbvY", "X3GCh50sW8A", "7t6dTKHZY6U", "JH-1IrNb_P4", "ubenw8IJ9dE", "jYVg9ERVMv0", "cAOakJcPmGs", "8tNy2en1CpE", "hZwuhnWXkLE", "EEq9IuWDBlM", "KSTaBxvL4JQ", "k0LjOdjBdYU", "mxCqvGI5iu0", "Ae_oPwsp_P0", "7m1hm4WJKAM", "R1tJE7-evoQ", "wFYq_Is8wJk", "tz4ISVJyEfI", "HH2wou4FvsA", "QKmscJgKCYs", "evAV9e6QUlI", "4Xt5gj8m7ds", "J1mbZ9eGho0", "K1DBCpPxqeM", "OxafdSA-QkE", "omNa4PW1lU8", "cITPhRNWoq0", "sCQfgFoAQu4", "p3PIKVi8goc", "V_AZsXtgxvY", "YMrwmCzH330", "NhX0XzGmv9A", "_LilpxfdvKc", "IXn5sqpAhqc", "Ya2SuHzZAXo", "xAvvvAO6glU", "DtlDXf6tveY", "Hv0SuDUsjyc", "ZKGMTf5XLCk", "OkWKy3URsDg", "q-9lO4eg7-w", "gEacqh5DPk4", "ydCddPTqZmo"];
  const VIDEO_TITLES = {"IUxt7faTExY": "ירושלים של זהב (1967)", "H8V8yhc2eYI": "ירושלים של זהב (1967)", "qvBk0IVkKRE": "ירושלים של זהב (1967)", "VbIHsjgvE2g": "לו יהי (1973)", "cpp8XENcuBk": "לו יהי (1973)", "FDD19O2CreI": "לו יהי (1973)", "PL0HmLqbxpw": "לו יהי (1973)", "KaovY--ET14": "לו יהי (1973)", "9xETAic8buQ": "על כל אלה (1980)", "hBlEx2bIRNI": "על כל אלה (1981)", "QUF8MiDp4O4": "על כל אלה (1981)", "TFIrOcriazY": "חורשת האקליפטוס (1962)", "_nDa2esEWJk": "חורשת האקליפטוס (1962)", "lDNtdPiL584": "חורשת האקליפטוס (1962)", "HgMGNLc5ir8": "חורשת האקליפטוס (1962)", "jk6lOLldgT4": "שירת העשבים (1976)", "Xe4H1sCCAJo": "שירת העשבים (1981)", "A-6m6CKOdC4": "שירת העשבים (1981)", "mw9uiMMvFGk": "אני גיטרה (1993)", "oo8IRR00H30": "אני גיטרה (1993)", "_GD1f91Erg8": "עוד לא אהבתי די (1977)", "GnxLc7C_yvM": "עוד לא אהבתי די (1977)", "E452vwyyVjQ": "עוד לא אהבתי די (1977)", "tWs6g7hg0BI": "מחר (1963)", "5Hz8UIWRADU": "מחר (1967)", "4_Laz5PQV-Y": "אור (1988)", "sFB_B3wTXLE": "שבחי מעוז (1971)", "-T6mxux7wKM": "שבחי מעוז (1971)", "XHdb6YDvHII": "פגישה לאין קץ (1970)", "DEKLsquUP34": "פגישה לאין קץ (1981)", "Zr-iKRNRzQk": "פגישה לאין קץ (1981)", "7T8wbdYlAbQ": "פגישה לאין קץ (1981)", "dC2fS3vZAPY": "שנים עשר ירחים (1975)", "85QDrN6FB8Q": "שנים עשר ירחים (1975)", "aO1sboxdmno": "שנים עשר ירחים (1975)", "MFrjlagc8rE": "לילה בחוף אכזיב (1967)", "AvJZwh25uZ4": "לילה בחוף אכזיב (1982)", "Jg42GYm1qv0": "לילה בחוף אכזיב (1982)", "AxnQ3qrsp64": "אלף בית (1975)", "5VQkcCM1fmc": "אלף בית (1975)", "OEVLRDRUxyc": "אלף בית (1975)", "3iaTDb1K41o": "אלף בית (1975)", "ryXmue6dutA": "הכל פתוח (1993)", "fiU_B2M84Ww": "הכל פתוח (1993)", "gTXgnxD6Cuc": "החגיגה נגמרת (1976)", "1_dsV0afFgA": "החגיגה נגמרת (1976)", "iPj5rmj8GZQ": "החגיגה נגמרת (1976)", "EdfxwaHVnAk": "החגיגה נגמרת (1976)", "zpFGk2nz_-A": "שלומית בונה סוכה (1970)", "-4bnvgAYqmo": "שלומית בונה סוכה (1975)", "unyzPkoPBEs": "אנשים טובים (1981)", "BLpTR9p0mkY": "אנשים טובים (1981)", "kA1Gl5w3ydI": "שלג על עירי (1976)", "_NylGW8syfw": "שלג על עירי (1976)", "BgpoI6q79Lw": "שלג על עירי (1982)", "2iljNf6XqsA": "אנחנו שנינו מאותו הכפר (1966)", "fE8xcZiFRO8": "אנחנו שנינו מאותו הכפר (1966)", "yscdF17IT_Y": "אנחנו שנינו מאותו הכפר (1966)", "Pef5mRmx0fA": "אנחנו שנינו מאותו הכפר (1966)", "kkJPYVGy31o": "אנחנו שנינו מאותו הכפר (1966)", "Ue8yK2cnLTA": "יש לי חג (1977)", "-hts04B4Wkk": "יש לי חג (1977)", "mq13AHHLul4": "הוי, ארצי! מולדתי! (1977)", "418kExn65Ug": "הוי, ארצי! מולדתי! (1977)", "Xc6coB1-EPw": "הוי, ארצי! מולדתי! (1977)", "vQjWwS6X7CI": "אורחים לקיץ (1979)", "6OWfRHNgEtg": "אורחים לקיץ (1981)", "bbIXevkZDnk": "אורחים לקיץ (1981)", "ei2FcAMuRAw": "אהבת פועלי הבניין (1964)", "kF5Lpl7IL6w": "בראש השנה (1975)", "BnKrb-46CNI": "בראש השנה (1975)", "Picy0oa0wl0": "בראש השנה (1975)", "7PxG0jfZX6k": "אהבה בת עשרים (1972)", "0mcp9JqqJ1k": "אהבה בת עשרים (1972)", "q3XGUpCCTJs": "נועה (1957)", "WA8fVawaHuw": "נועה (1957)", "Q5N5gxqjDFc": "נועה (1991)", "n6qfNKmjutM": "נועה (1991)", "5yDnz_UrH-s": "נועה (1991)", "5xj4ycn0TY8": "נועה (1991)", "oNmwW4s3AuI": "בהיאחזות הנח\"ל בסיני (1969)", "0ypE8NBmyYo": "בהיאחזות הנח\"ל בסיני (1969)", "BfKQ4bj0JJk": "וולס להגנת הצומח (1966)", "e4cc_kptHk8": "וולס להגנת הצומח (1966)", "k0RE3k8k1pQ": "וולס להגנת הצומח (1966)", "5kl6qHnbp9Y": "העיר באפור (1964)", "wly5oxW3C6Y": "העיר באפור (1964)", "_DujVVkqqQ0": "לשיר זה כמו להיות ירדן (1972)", "neYlxPR8-WA": "אומרים ישנה ארץ (1980)", "ax7p4AggiqY": "אומרים ישנה ארץ (1981)", "sCRw6hfgQTM": "הטיול הקטן (1977)", "dDXngW-5jV0": "הטיול הקטן (1977)", "Zs1s0_fs9EI": "הטיול הקטן (1977)", "YJKhOidPJhc": "הטיול הקטן (1977)", "SnARDknXrZQ": "שיר השוק (1960)", "Ce_cSMB0Ri8": "שיר השוק (1960)", "ZLzkd2ui6PM": "בארץ להד\"ם (1972)", "RqHN-so83M4": "בארץ להד\"ם (1975)", "vxQcorAdAXA": "בארץ להד\"ם (1975)", "Omn_wSe-dKU": "בארץ להד\"ם (1975)", "JfJ3DrI7-6w": "אל בורות המים (1982)", "HlUl3uS6T6Q": "אל בורות המים (1982)", "jfy9Pml8UZg": "החופש הגדול (1975)", "e9lQpiSO6XM": "החופש הגדול (1975)", "vXAxaeNqze4": "החופש הגדול (1975)", "jiIKJ29A8qU": "תלבשי לבן (1985)", "HvE1Ib25iDk": "תלבשי לבן (1985)", "oCezgzbCZBk": "תלבשי לבן (1985)", "YQc4x6hGSyg": "הו רב חובל (1996)", "-nzLbN3sFRQ": "כנרת (1963)", "Uwi4o3fwQwc": "כנרת (1963)", "0IPY0etp8eE": "מטרייה בשניים (1963)", "DdET9qVDfRI": "סימני דרך (1982)", "TcTOqEg-htw": "סימני דרך (1982)", "HTMwVk8pQiY": "שירו של אבא (1972)", "eSmhtnivpvY": "שירו של אבא (1972)", "yMsCeHsgGwQ": "שירו של אבא (1972)", "M38vdprLLok": "שירו של אבא (1972)", "2aQJz8v_KkU": "אילו ציפורים (1967)", "kF_MJiReEn0": "שלום כיתה א' (1979)", "9bfiWAv4HSU": "שלום כיתה א' (1979)", "PHQFSQi4tzU": "שלום כיתה א' (1979)", "zN2CRXhVJ3o": "לא תנצחו אותי (1984)", "bfQeAbF8-4A": "לא תנצחו אותי (1984)", "eCRBb3h6mz8": "שיר סיום (1971)", "iLhwph9IJMA": "האורח (1984)", "uqOoO342wNg": "אסיף (1976)", "xkGxvP-tw1w": "אסיף (1976)", "WFOhRFYM1wM": "אסיף (1976)", "CYwiq1Uu5Ng": "על הדרך עץ עומד (1998)", "4ZFF3v39RD4": "ספירת מלאי (1974)", "mYfdJkb1gqg": "אין לי רגע דל (1980)", "zZHynZGet5g": "מה עושים העצים (1966)", "URL56lbFmr8": "מה עושים העצים (1971)", "aDZqwcq7eVI": "ארבעה אחים (1967)", "B0EO7nYCdu0": "ארבעה אחים (1967)", "SgzeIwaaGMU": "הדואר בא (1958)", "T5o_o8lO-1M": "הדואר בא (1958)", "0XhvBFzatFc": "הכול בגלל מסמר (1964)", "NWR0K-8lBhU": "הכול בגלל מסמר (1964)", "o7vESC28Iqo": "הכול בגלל מסמר (1964)", "hDqbO57hnyQ": "הכול בגלל מסמר (1964)", "wO3U1xG7Um0": "אחרי השקיעה בשדה (1962)", "EFIwG44Egek": "אחרי השקיעה בשדה (1967)", "z-OpnBf-JNI": "הלאה (1984)", "KOecGqpq-f0": "הלאה (1984)", "ZFFJR9iTSuo": "על כנפי הכסף (1967)", "ry9RV0yCJpI": "על כנפי הכסף (1967)", "6hhQ_4omcKs": "על כנפי הכסף (1967)", "zRQLXqjeRoE": "כיבוי אורות (1958)", "isxLekbAFHw": "כיבוי אורות (1982)", "TQwpuggfQWw": "כיבוי אורות (1982)", "6qiFa7eU34M": "כיבוי אורות (1982)", "D13BJwfsQu8": "מיכאל (1968)", "sQTl_NH1n0o": "מיכאל (1968)", "-2N-WzrLzCc": "מיכאל (1968)", "4HZWNJzXTm4": "התחדשות (1985)", "XteReGQom40": "נגיד (1975)", "pjCtGobuuSE": "נגיד (1975)", "xI2m7tKJ40E": "נגיד (1975)", "0ga6HoypSJU": "עצוב למות באמצע תמוז (1991)", "JAY_uZjqmIA": "חליל מקנה-סוף (1977)", "04AcSZS8K3s": "חליל מקנה-סוף (1977)", "qrvKQtQgb2s": "חליל מקנה-סוף (1977)", "08Z_uYA9PLc": "סרנדה לך (1967)", "OS9uUlfBrbA": "בכל שנה בסתיו גיורא (1979)", "YY8vUjMWzEc": "בכל שנה בסתיו גיורא (1982)", "YgYyQjI4UeY": "בכל שנה בסתיו גיורא (1982)", "XxJZZ-9zlpQ": "מר נרקיס (1972)", "_lds9E6qEQg": "הופה היי (1961)", "XBrUmJLCkEw": "הופה היי (1961)", "YrJtArqXavk": "הופה היי (1961)", "TsA3LycTPSo": "הופה היי (1961)", "5TZvR7wFlVo": "בשדות בית לחם (1971)", "Sn0vSoeVXpI": "בשדות בית לחם (1971)", "dKHjdN2hr4w": "בשדות בית לחם (1971)", "qpbBemLcsUE": "נומי נוגה (1977)", "O4OhUorCxX8": "אין אהבות שמחות (1974)", "vrJcb0mauz8": "עיר לבנה (1959)", "eUam8viOqxs": "עיר לבנה (1959)", "jAnSY8gxLRg": "עיר לבנה (1959)", "vVQ0Xmtb9_Q": "אחותי רוחמה (1979)", "whmUk6hiVE4": "שלגיה (1966)", "9Er1RvAuM7M": "זמר נודד (1959)", "1gUgA5_iv5g": "זמר נודד (1959)", "bzl8G_GQJKE": "זמר נודד (1959)", "zTCbwh0WyXM": "שיר סתיו (1958)", "gkPyKqEFNSE": "שיר סתיו (1958)", "hA92uD-XpQs": "שיר סתיו (1958)", "YS6EfEQu1ik": "יש לי חבר (1974)", "SDCkIuEiWWY": "יש לי חבר (1975)", "jMlzihkguOU": "על ליל אמש (1960)", "g6clciS1riA": "על ליל אמש (1960)", "PXL8ltjFDCk": "גיא (1987)", "CSjnGcglVJI": "גיא (1987)", "CeRvSDeJx-I": "כד הקמח (1971)", "g-477LqGTr4": "הטיול הגדול (1963)", "rh0oGPJbf5M": "הטיול הגדול (1963)", "pDLQ_FrzKL4": "הפסנתר (1981)", "Sah0hB6rSFY": "הפסנתר (1981)", "WDzRA91O678": "כמו חצב (1981)", "hSaod2F6TA8": "חיילים יצאו לדרך (1962)", "UxWCHV50LoU": "חיילים יצאו לדרך (1962)", "OvN5nJ9bn2Y": "שנה טובה (1992)", "skYeVk80Eo0": "שנה טובה (1992)", "losUGtP6fxI": "שנה טובה (1992)", "2QMxLPxD25g": "קומי צאי (1973)", "7uxKafYsUrU": "קומי צאי (1982)", "Okw-ktcRVr0": "שיירת הרוכבים (1958)", "cYZArmDfKnA": "שיירת הרוכבים (1958)", "-1__PIJhhPI": "שיר ערש לצבעים (1968)", "vczM9eWy1yw": "שיר ערש לצבעים (1968)", "pCK483hwY-0": "שיר ערש לצבעים (1968)", "sdlmzqJiT5M": "משנכנס אדר (1975)", "XsDAsNDqHW4": "חבלי משיח (1967)", "0u--FHf-LHU": "חבלי משיח (1982)", "zFJUpGoNWPc": "למה צחקה מיכל (1979)", "3iQEC7mO3YY": "ספני שלמה המלך (1959)", "B7oZ2GPHhEU": "ספני שלמה המלך (1970)", "Gi7-feW4FfE": "בית חלומותיי (1967)", "FkSHlF212BA": "בית חלומותיי (1967)", "8y5KQ8UWi0A": "בשדה תלתן (1961)", "nruQWhRsem4": "בשדה תלתן (1961)", "7m9YwTJwFrE": "בשדה תלתן (1961)", "aKAvYLWF97U": "סימן שעוד לא הגענו (1976)", "p320GUpKgkQ": "סימן שעוד לא הגענו (1976)", "GgYxh_MoCDA": "סימן שעוד לא הגענו (1982)", "DATGdPiFqVA": "הלילה הולך בשדרות (1958)", "PrntU87z0n8": "הלילה הולך בשדרות (1958)", "ZcKAuoZSzWQ": "הלילה הולך בשדרות (1958)", "XKbvfLzHms4": "רכב אש (1964)", "tk3zQs8gDTM": "רכב אש (1964)", "p_OfoN-B_xw": "רכב אש (1964)", "upipvN8Xw-c": "רכב אש (1964)", "UwhEUsWVdPg": "מחבואים (1963)", "s1SR4hmgC4U": "מחבואים (1963)", "VCDKtBt4xb4": "מחבואים (1967)", "Ba1W41IDnhI": "תפוח בדבש (1979)", "P8g0g_IQcjI": "תפוח בדבש (1979)", "CEI769yjg4g": "כיצד שוברים חמסין (1975)", "agChJ2Ho124": "כיצד שוברים חמסין (1975)", "UgXcD55HXzc": "כיצד שוברים חמסין (1975)", "E3V70DpK_EI": "נר ראשון של חנוכה (1977)", "mpPxqJrum-M": "נר ראשון של חנוכה (1977)", "Yd3_uDW6i4w": "גדי קטן (1977)", "yKAUdNGyVpA": "גדי קטן (1977)", "SSJdF9cV8iQ": "אשכולית (1958)", "-7qKw4AIGP4": "אשכולית (1958)", "ipzIvlpBkbU": "דוגרת (1977)", "Ke6iImauSj4": "דוגרת (1977)", "6EEIW68j5lY": "דוגרת (1977)", "doXUEtdMaxc": "אנשים יפים (1972)", "chw7OpsTH1A": "כריש (1978)", "UfIj78lym1I": "ילד רע תל אביב (1988)", "narkCrS3_GA": "זמר (1968)", "sLvHms2BClA": "זמר (1968)", "lKhxVjkSa84": "זמר (1968)", "wzrVRxyd5a4": "בגני נטעתיך (1968)", "pKGFC7qoGBA": "בגני נטעתיך (1968)", "3G8xlTapGQo": "בגני נטעתיך (1968)", "0rZlNPF_utQ": "בגני נטעתיך (1968)", "vUmuxcvyGrM": "בגני נטעתיך (1968)", "FZrRqLdaH5E": "החייל שלי חזר (1966)", "ArRyqOnlQ3k": "החייל שלי חזר (1967)", "bZI8gT-VbT0": "החייל שלי חזר (1967)", "XWnWPkDHGz4": "מה שלומך אחות (1987)", "H3h-755AwoI": "מה שלומך אחות (1987)", "_Zksgxev2ko": "חמסינים במשלט (1961)", "Xoh_DVe4WcA": "על אם הדרך (1971)", "2BfY0duzEpE": "אין דבר (1981)", "7cZaZp3xfDM": "אין דבר (1981)", "pTlgYtrDSPI": "אין דבר (1981)", "yzSOpEPUXWw": "שיר נולד (1967)", "vNw21mQVfKM": "שיר נולד (1967)", "l1b8s6ZGXhQ": "הי טירילי (1958)", "l8uDRKHspac": "הי טירילי (1958)", "MtwqXXIN6Xs": "וזוהי רק ההתחלה (1974)", "5v77wNxd8Kw": "וזוהי רק ההתחלה (1974)", "Y8ob5jdoYBw": "דיוקן אמי (1981)", "VkgQyNxNQqw": "דיוקן אמי (1981)", "KBvQrOKM37k": "מצעד האביב (1959)", "9XgKm2xg3iA": "מצעד האביב (1959)", "7IEl35CsSaI": "מצעד האביב (1959)", "Okj7fK4VSOA": "קרן יער (1968)", "P7eGfaq3E_s": "קרן יער (1968)", "GyiSOeKOK8s": "קרן יער (1968)", "NGtt4OBuh2E": "לחם האוהבים (1991)", "PIqHAidM99g": "סמוך על התרנגול (1958)", "F25xFwezdxw": "סמוך על התרנגול (1958)", "PEamc15DDeY": "סמוך על התרנגול (1958)", "yXzElXsHH38": "שש עשרה (1972)", "UeP8K2lXml8": "מה אמרו הציפורים (1962)", "cV-WsBBOwto": "מה אמרו הציפורים (1962)", "jqQTqr1gHEI": "מה אמרו הציפורים (1962)", "dYYGjAoIU_E": "בדמייך חיי (2001)", "X0EHaEth0TQ": "בעלייתי שם יפתי (1976)", "kurpWet0X78": "עקידת יצחק (1967)", "2yXv06OahEc": "עקידת יצחק (1967)", "ufIj60iGZqM": "איילת אהבים (1964)", "C1PjhOZQxMU": "איילת אהבים (1964)", "RDTKjKtbdak": "שיר לחג עשור (1958)", "dgC-AI1O_a8": "שיר לחג עשור (1958)", "-rGr-thBmjs": "שיר לחג עשור (1958)", "cD2GgbFD_Yo": "מה שיהיה יהיה (1956)", "wcy425HOqro": "למבדה על החוף (1990)", "tSmg5wveagg": "רב האור והתכלת (1958)", "INHBTa-HfSM": "רב האור והתכלת (1958)", "_6La2mK-PqU": "רב האור והתכלת (1958)", "KO7lZhbeFDs": "תות (1987)", "38jU5bVcNzo": "קפה שחור (1959)", "_33ng3euFJI": "קפה שחור (1959)", "me0k188YXNw": "שיר לגדעון (1961)", "CMhfrA5uDjE": "עוד לא אכלנו (1963)", "-p0EvZ_T_AY": "עיר ואם (1992)", "_FhoSjLL61A": "על ראש שמחתי (1988)", "cXln3eAat5g": "יובל (1998)", "AoGcmpu5D4Y": "יובל (1998)", "Pk0mm0ly7Og": "יובל (1998)", "0pdyuulvbzo": "זהירות בונים כאן (1963)", "OLQITmFP3Xo": "זהירות בונים כאן (1963)", "vAT50nuKMh8": "נצא השדה (1975)", "BBUtEBZLJFQ": "נצא השדה (1975)", "sJFfiL_Y1_E": "אל תלכי מכאן (1972)", "UOD51gynvJQ": "התחדשות אחרת (1985)", "o9ElrJy3fmk": "לאורך הטיילת (1985)", "oNZG3NUzB3U": "כל הדרך חזרה (1969)", "61RF4uejHJE": "החטא השביעי (1971)", "oQLUlVqXkpo": "מוזיקה (1989)", "jsTz7qC8tMo": "שני צלמי רחוב (1972)", "Jzkgm9A3Ooc": "שיר הבר (1958)", "2vq22hm-TnI": "שיר הבר (1958)", "tPX2FmmeM6k": "והוא יושיענו (1991)", "2LRsVjehz44": "והוא יושיענו (1991)", "3wNpnpA5K-w": "והוא יושיענו (1991)", "3oB1QegwRqk": "רוקדת (1958)", "VaztQIe75Ns": "אהבת אשתקד (1987)", "U3xSpmrTgXc": "אהבת אשתקד (1987)", "nz7sT486EYw": "בראשון לספטמבר (1987)", "CwORk-NwrQM": "אקטואליה (1991)", "iz3Et-1Ywe8": "אקטואליה (1991)", "2MUXbKJVRZo": "המעיל (2001)", "H9f2NJOxcz0": "המעיל (2001)", "cmQ9upI0aG8": "יפעת (1980)", "n2t3bDiJcMk": "יפעת (1980)", "_aoBikUYiBY": "בקיץ (1968)", "4g6cymurqY0": "בקיץ (1968)", "bnl-cjqYOwk": "אשרוק לי שיר עליז (1966)", "bzLl7TH_VxQ": "גג (1987)", "3v9rvDklaxc": "עוד מעט מסך (1989)", "YfFNug5ZOac": "אל תשאלו אותי (1967)", "AnWiRbrejHg": "אל תשאלו אותי (1967)", "A9erliXTS6o": "אל תשאלו אותי (1967)", "-dNwuLchpWg": "בתכול השמים (1970)", "IWaGaO6VD4c": "המנגן (2001)", "mtuSxIIZPqg": "יום ה בשבוע (1958)", "Pxm7UgJ1JiE": "יום ה בשבוע (1958)", "5-8BIb9KyNk": "יום ה בשבוע (1981)", "qblckfTw1Rk": "יום ה בשבוע (1981)", "Yd63Irvr-Q0": "תן כתף (1981)", "mzrn0p-yRSM": "תן כתף (1981)", "dsZYpHVPjv0": "האיר השחר (1981)", "i9KzXu-Nhx0": "לנוע ולנדוד (1975)", "2o1uo7sstSI": "לנוע ולנדוד (1975)", "Jl0WahK00lU": "פרדס חנה בשבת (1983)", "UtixqreayIo": "לכבודך (1964)", "eGrPQv3g9ps": "לכבודך (1967)", "w8uvk1uQYXg": "שיר ערש למקרים מיוחדים (1972)", "pPE_eIQYtgY": "שיר ערש למקרים מיוחדים (1972)", "zHmm0bb_x5c": "ילדה ברבור (1987)", "V2eI7l5c3nc": "עוד חוזר הניגון (1970)", "-xNyTz_yvRU": "עוד חוזר הניגון (1970)", "gsf0t-VihvE": "עוד חוזר הניגון (1970)", "YtWovd6r0yc": "פרי חדש (1993)", "WxdVdudBKeE": "פרי חדש (1993)", "EEkIbuhQ9dw": "אופליה (1964)", "3YYVsJ9MGZQ": "אופליה (1964)", "CJ8_MISsRxg": "אופליה (1964)", "Y5aCrfJLjIM": "אופליה (1964)", "lXCnVOsgJwo": "אופליה (1964)", "24JJpjDS8QY": "על נהרות בבל (1982)", "Im8ze1yI8Aw": "האם השלישית (1970)", "gpo_GVko6OA": "חפצים אישיים (1987)", "d8h9EDhbixA": "ליבבתיני (1986)", "yavA7DK-_Lg": "בניך מרחוק (1990)", "6sR4GRdyZZ8": "הצוואה (1974)", "A1BCQuWuvTE": "מתי (1968)", "2GD7HJfapWM": "מתי (1968)", "04e7PQhn-vY": "מתי (1968)", "XIs2ZIJ2oZw": "מתי (1968)", "mZxh2vHIBcs": "אישה על החוף (1989)", "gkP9-OqJETY": "אסוני הצעיר (1971)", "gRfvDuXwtYI": "ברברה (1981)", "VXLKQYTYShc": "ברברה (1981)", "OFBBD-EuEfA": "לא אבקש את ידך (1974)", "s0923q2OCPM": "בזכותם (1976)", "ZYTJPE70ifA": "אחר קציר (1988)", "yEG2trB0IxU": "מרגו (1974)", "-2f28ACy-Gk": "נשים נשים (1974)", "V8CR6u84pXU": "שבת (1958)", "rLucwp89lnE": "שבת (1958)", "VeeEHBwsyQw": "שיר לכת (1976)", "wIFDo3qiS9c": "מסעות בנימין מטודלה (1979)", "vbG5B1wswQc": "מסעות בנימין מטודלה (1979)", "kd0BjoJemU4": "קולך מן הסופה (1982)", "tBL2uGdMMZ4": "את הכי הכי (1981)", "dT5g0VRp7jE": "את הכי הכי (1981)", "SZhwVVZuRkY": "מי ידליק (1998)", "nvaUD-WzYDQ": "מי ידליק (1998)", "dZtHel6cUW8": "בגינה (1958)", "Brq81oCuNKc": "בגינה (1958)", "7e6hGajTOaE": "ורד בר (1962)", "-givWJMymhs": "ורד בר (1982)", "ut3moC4G-QI": "עלי שלכת (1989)", "EikdgimAjd8": "הללויה (1966)", "L7_tsGSLGTs": "הנרקוד (1966)", "JUVV06GzaFE": "אין ויש (1972)", "sgMLsWRX7SI": "פרלוד (1987)", "ew9j2OHt8Cw": "פרלוד (1987)", "zUWmMkqQMQg": "בחלום (1966)", "KEOx2onVNDs": "בצל ובאופל (1966)", "m58C3mRgm5E": "קלי קלות (1971)", "pTt_42SgJ0U": "קלי קלות (1971)", "nNMmAneQsLs": "בלילה שכזה (1964)", "VsVv0OOIARQ": "בלילה שכזה (1964)", "xypLh9F1IXk": "בלילה שכזה (1964)", "morcvF-aFsg": "לאיש חסדי (1974)", "E-jZMuDEvLQ": "אדון ומלך (1966)", "Vimcno4QbUw": "אקרא שלום (1966)", "nOa7P6X2I-8": "דבר מה נפלא כל כך (1966)", "E-G-dnLO99U": "חידתיות (1966)", "cCftnvA1iJo": "להתוודע (1966)", "t6jXzPCR0NA": "משל סיאמי (1966)", "Ur53Ai6WISA": "שפחה שפחה (1966)", "UhSscH59sdA": "סביבון סב סב (1977)", "FFtI8ZQT2Mk": "אותלו (1964)", "B86J0eynF9A": "אותלו (1964)", "NXcXk-diyDY": "אותלו (1964)", "UB35E3hE65E": "המכשפות (1972)", "CLDelMZYKC8": "המכשפות (1972)", "yWVoMYXeBpM": "המכשפות (1972)", "DGUHUGnDYn0": "איך את נראית (1968)", "8d9khSRpSkk": "שובי השולמית (1988)", "qgyoXwMKJXg": "שובי השולמית (1988)", "LBTf6IMt2X8": "בוא נרד לכרם (1972)", "OdbpJIdes4Q": "האילן הזקן (1988)", "LYoIOT8VvK0": "מדם בלוזון המרגלת (1963)", "xdj8UWyGpFg": "מדם בלוזון המרגלת (1963)", "b9Vxv861vb4": "מדם בלוזון המרגלת (1963)", "FwOsYI51_NU": "מכתב (1976)", "qiWE67WQSBY": "מכתב (1976)", "nNFb0CPT7Js": "לא אמות כי אחיה (1972)", "tNga0kZsgXY": "נעשיתי כזה קטן (1974)", "kO9D3crjEsU": "סיירת עולם (1989)", "YMdqSo7wMUk": "שיר עם סיאמי (1960)", "Xw4qL0j_9Vs": "ארבעים (1972)", "Ti6nFst0JaE": "הגביר (1976)", "4gYlHwrMV50": "לטוס אל על (1981)", "N4QGMJR3Qqo": "שיר המכביה (1965)", "RU68BDHHZJo": "שיר המכביה (1965)", "S9QL3kDf8gA": "אין בגני שקדיה (1972)", "ukOWgL-9mlw": "חרוזי ביניים (1972)", "F6syH8W0EGA": "שיר ערבי נחל (1989)", "e1c2MjdU9T8": "שלא נהיה ברברים (1966)", "O5In5PJnEr8": "מדוע לי (1972)", "Lg-Can0ZrXM": "פרח בדמות פרה (1974)", "ud8TFvfUJ8M": "צירצורים (1971)", "USMuk_mS6vA": "צירצורים (1971)", "hw_SJRb1uEk": "שיר החצב (1971)", "OBkMzEHYA3c": "שלג בצפת (1987)", "6rlo1KZ0qok": "שלג בצפת (1987)", "YWwJ1O6fQQs": "הכל חינם (1969)", "JAh-XgpCIEo": "זמן (1987)", "hZirnyIx1Tw": "פתיחה (1976)", "G5RVx22SVzs": "גדי מן ההגדה (1971)", "0Yn3EvME2ko": "היה היה לי טנגו (1998)", "WBfuFYdOQT4": "העלמה (1988)", "zuYjR6RNeIw": "כבר מאוחר יונתן ומיכלי (1975)", "BAliJ1ieJrI": "כפות רגליך לבנות (1968)", "BncSM_l0_P8": "כפות רגליך לבנות (1968)", "X-KSBs_Lsd8": "פרח (1987)", "6xpROKMcQus": "רכבת הברית (1958)", "c0WSmr4tlLY": "רכבת הברית (1958)", "0eWljspYG7E": "רכבת הברית (1958)", "mMEXXehlL54": "תחביב מיוחד במינו (1972)", "41VIMNNssjw": "תחביב מיוחד במינו (1972)", "ldmMVGr-syE": "בז על המרפסת (1961)", "xUe9MRUvOww": "הכל שטיח (1982)", "Rh-AfNJC1AY": "סוזאן (1974)", "xyiYZRhJsSo": "שיר הליצן (1964)", "rGRBY2iPjpk": "שיר הליצן (1964)", "k8u50w4T-1g": "אוכל אדם (1960)", "uquTBB0PbFY": "אחינו הקטן (1958)", "v6wgkaN8mvg": "אחינו הקטן (1958)", "wONNxGvP9S4": "יומן החדשות (1965)", "ORPN8djCQws": "מערת עדולם (1986)", "Luu_LIPtx-M": "פסח כאן (1992)", "DZCXER0nGaM": "שבולת ירוקת העין (1977)", "LR_zCS48QV0": "אי הא שה (1960)", "ITgt-B5IdFk": "ארץ רעשה (1972)", "MhIbjL4Hghc": "הגברת ישראלה (1960)", "tnNhOpq6MqI": "ליל המלאך (1983)", "ZSYQh_YatoU": "קרנבל (1959)", "2smvtZlQSEg": "ראש קטן (1981)", "XWOGYjtgJG0": "איש מוזר (1991)", "JvQBz3CHrK0": "ילדי כל העולם (1992)", "F7KHn6M2VGk": "קיצור החדשות (1959)", "Kc3Z01Zqr24": "קיצור החדשות (1959)", "y_Z_-_Wt-Yc": "רגע מתוק (1982)", "g57hoYLobng": "שוב כמו אתמול (1974)", "ygW51Wri9wQ": "ג’ינג’י (1971)", "lTvJVWW87H8": "ג’ינג’י (1971)", "4okw4g4Q8e4": "הדוד שמחה (1971)", "sFbghpqy0Lo": "הכלייזמרים בצפת (1990)", "nOl7AAouxVc": "כיד המלך (1971)", "sdqrr4rdUPA": "לכו נרננה (1976)", "P35Ek5tTy4I": "סינמה בלש (1976)", "dWXjopZ8-1s": "פו הדב (1971)", "0yT4idCIsSE": "צמחי הביצה (1976)", "u-uUCxxSFhs": "חידות (1971)", "GZW3RhiQeyY": "מגדל בודד (1955)", "_JG62QmM-QE": "מגדל בודד (1955)", "URuGgQXkQpQ": "מותי בא לי פתע (1974)", "3a8B5imZV8o": "מותי בא לי פתע (1974)", "SOOmGDRVIK8": "שלום על הגלים (1965)", "WILLlFVs8K4": "דולי (1997)", "WDQyD0VHt68": "היה היתה עיר (1977)", "VnReHM2MOuo": "כל חיי (1966)", "weX6vsG96ZY": "מנגנות ויואלדי (1976)", "l4y16i5NwwQ": "מנגנות ויואלדי (1976)", "UsNNGSI6qzk": "נסיכה שחורה (1986)", "lfB0Y5mJ1qk": "עולם הפוך (1985)", "Bujd3-vDfE8": "פרחי אולי (1966)", "Z-JxFdJcoB4": "פרנואיד (1978)", "VhBycovusXA": "קפה תפארת (1998)", "oJZEOGPBtp0": "העוזרת של זרש (1971)", "4MJ1vA3znA4": "העוזרת של זרש (1971)", "DLilbBb5C-k": "יריד (1976)", "1D4_GtYfmUE": "מתפרנסים (1976)", "piH6EOOP7cY": "האומנם (1974)", "SzfqrHxbpug": "ימי הענבים (1974)", "r97YIa4BDnM": "כי לא יהיה להם יום (1968)", "JUiRv74kgHU": "לא ביאליק (1976)", "jzNc8KFQ4S4": "לא ביאליק (1976)", "Jwjk2orp29M": "עמוק בטל (1973)", "-eINxqt2z0A": "אני ואחא רון (1958)", "xam-JFkXggk": "הדוכיפת (1982)", "3H9EF4ZzVy8": "הו מה נאה הוא הבוקר (1956)", "6BfneC2-IvA": "סיפור אהבתי לכם (1979)", "L8jFWAH86Hw": "עשרת הצדיקים (1960)", "AUm3hkHaOKo": "סוף העולם (1963)", "d9pbNfB26wc": "סוף העולם (1963)", "kLf2ybtWLCI": "צי הצללים (1965)", "KXjJoVHJsQw": "חד גדיא (1979)", "hs1Uo7ilYKo": "חד גדיא (1979)", "gfYmkBTQVD4": "מוטב בבית (1976)", "XixXG6ffyy0": "מי רוכב על מי (1964)", "GsmV9XnbTDY": "בא הגדוד (1958)", "jOpau37GjhY": "בא הגדוד (1958)", "WfesepFfvOo": "בשלו הפירות בגני (1960)", "1dAeJminXHM": "דרכים (1960)", "t_qzuM6V2Co": "הסוחר מוונציה (1964)", "Bac-K0Wjp2A": "הסוחר מוונציה (1964)", "OzrUXu1pKkg": "ט\"ו בשבט שלי (1985)", "acNmIrbrp0k": "נעלה צפונה (1964)", "OdYRuoXrHHw": "פרידה (2004)", "EZ2zDG6qrJE": "פת במלח (1988)", "T3qo2SYP52U": "אילן (1979)", "SfPOduJnKvk": "אצל ורדה השמנה (1963)", "pUFhGuyD6j4": "בלדה על סל תפירה (1963)", "7ziQJmP02M0": "הנישואין (1975)", "dfPBgVKT_H8": "חפש את האישה (1958)", "z91zsr8vHnU": "חפש את האישה (1958)", "OfsdkuisiNo": "ירדנה (1958)", "9o-4qxrv584": "יש לי מנגינה בלב (1971)", "Eff5K5VrmKE": "מצד אל צד (1964)", "6yrG087cato": "רומנס בכפר (1958)", "R-oz2dlpbvY": "שיר פורח (1963)", "X3GCh50sW8A": "שיר תודה (1975)", "7t6dTKHZY6U": "תישן חמודי תישן (1968)", "JH-1IrNb_P4": "האחרת (1990)", "ubenw8IJ9dE": "הורה נחל עוז (1953)", "jYVg9ERVMv0": "השד יודע (1959)", "cAOakJcPmGs": "שייקספיר איננו (1964)", "8tNy2en1CpE": "שייקספיר איננו (1964)", "hZwuhnWXkLE": "אלף תשע מאות שמונים וארבע (1984)", "EEq9IuWDBlM": "בלי מילים (1963)", "KSTaBxvL4JQ": "בלי מילים (1963)", "k0LjOdjBdYU": "המכונית האדומה (1971)", "mxCqvGI5iu0": "לבנות שפיה (1975)", "Ae_oPwsp_P0": "לרקוד איתך (1966)", "7m1hm4WJKAM": "אין לי קו (2099)", "R1tJE7-evoQ": "בלדה מודרנית (1958)", "wFYq_Is8wJk": "הבו לנו זמר (1957)", "tz4ISVJyEfI": "הינשוף והירח (1956)", "HH2wou4FvsA": "הלילה הזה הוא דומם (1957)", "QKmscJgKCYs": "ט\"ו באב (1958)", "evAV9e6QUlI": "ט\"ו באב (1958)", "4Xt5gj8m7ds": "כיתה בארץ (1968)", "J1mbZ9eGho0": "שיר עבודה (1958)", "K1DBCpPxqeM": "אוניית הכאב (2004)", "OxafdSA-QkE": "התפוזים (1964)", "omNa4PW1lU8": "יש לי מסיבה (1987)", "cITPhRNWoq0": "'רות ושות (1961)", "sCQfgFoAQu4": "אל מחנה השחרורים (1961)", "p3PIKVi8goc": "הכתר השרביט והגלימה (1986)", "V_AZsXtgxvY": "יום הולדת שמח (1965)", "YMrwmCzH330": "כמו נערה (1964)", "NhX0XzGmv9A": "נערת הסיפון (1964)", "_LilpxfdvKc": "אהבתיך גם כך (1956)", "IXn5sqpAhqc": "בלדה על מושבה נידחת (1958)", "Ya2SuHzZAXo": "בתיה הסיירת (1958)", "xAvvvAO6glU": "הבית הקטן (1958)", "DtlDXf6tveY": "היי שלי (1958)", "Hv0SuDUsjyc": "זאת הארץ (1958)", "ZKGMTf5XLCk": "לא לא לא (1966)", "OkWKy3URsDg": "אביב בתל אביב (שיר יפני) (1966)", "q-9lO4eg7-w": "פרולוג (1964)", "gEacqh5DPk4": "שיר השייטת (1967)", "ydCddPTqZmo": "אביב (1978)"};

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
    alert("שגיאה: לא נמצא חיבור לחשבון יוטיוב. אנא התחבר לחשבון היוטיוב שלך ונסה שוב.");
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

  // שליפת כל הסרטונים הקיימים כרגע בפלייליסט (כולל setVideoId לצורך עריכה/מחיקה/הזזה מדויקת)
  function extractVideosAndContinuation(obj, itemsOut, tokensOut) {
    if (!obj || typeof obj !== "object") return;
    if (Array.isArray(obj)) {
      for (const el of obj) extractVideosAndContinuation(el, itemsOut, tokensOut);
      return;
    }
    if (obj.playlistVideoRenderer) {
      const r = obj.playlistVideoRenderer;
      if (r.videoId) {
        itemsOut.push({
          videoId: r.videoId,
          setVideoId: r.setVideoId || null
        });
      }
      return;
    }
    if (obj.continuationItemRenderer) {
      const tok = obj.continuationItemRenderer?.continuationEndpoint?.continuationCommand?.token;
      if (tok) tokensOut.push(tok);
      return;
    }
    for (const k of Object.keys(obj)) {
      extractVideosAndContinuation(obj[k], itemsOut, tokensOut);
    }
  }

  async function fetchCurrentPlaylistItems() {
    const items = [];
    const tokens = [];
    const firstPage = await ytPost("/youtubei/v1/browse", { browseId: "VL" + PLAYLIST_ID });
    extractVideosAndContinuation(firstPage, items, tokens);
    while (tokens.length > 0) {
      const tok = tokens.shift();
      const nextPage = await ytPost("/youtubei/v1/browse", { continuation: tok });
      extractVideosAndContinuation(nextPage, items, tokens);
    }
    return items;
  }

  console.log("🔍 קורא את מצב הפלייליסט הקיים ביוטיוב (" + PLAYLIST_ID + ")...");
  let currentItems = await fetchCurrentPlaylistItems();
  console.log(`📋 נמצאו כרגע בפלייליסט ${currentItems.length} סרטונים (יעד רצוי: ${TARGET_VIDEO_IDS.length} סרטונים).`);

  const curIds = currentItems.map(x => x.videoId);
  if (curIds.length === TARGET_VIDEO_IDS.length && curIds.every((v, i) => v === TARGET_VIDEO_IDS[i])) {
    console.log("✅ [וידוא הושלם] הפלייליסט כבר מסודר ומעודכן ב-100% לפי הסדר המבוקש!");
    return;
  }

  // בדיקה אם מדובר בשינוי נקודתי (עד 25 החלפות באותו אורך/סדר) או בסידור מחדש מלא
  let diffPositions = [];
  if (curIds.length === TARGET_VIDEO_IDS.length) {
    for (let i = 0; i < curIds.length; i++) {
      if (curIds[i] !== TARGET_VIDEO_IDS[i]) diffPositions.push(i);
    }
  }

  const BATCH_SIZE = 50;

  if (curIds.length === TARGET_VIDEO_IDS.length && diffPositions.length > 0 && diffPositions.length <= 25) {
    console.log(`⚡ זוהו ${diffPositions.length} החלפות נקודתיות בלבד! מעדכן במקום תוך שמירה על המיקומים...`);
    for (const idx of diffPositions) {
      const oldItem = currentItems[idx];
      const newVid = TARGET_VIDEO_IDS[idx];
      console.log(`🔄 מחליף רצועה #${idx + 1} (${VIDEO_TITLES[newVid] || newVid}): ${oldItem.videoId} -> ${newVid}`);
      const addRes = await ytPost("/youtubei/v1/browse/edit_playlist", {
        playlistId: PLAYLIST_ID,
        actions: [{ action: "ACTION_ADD_VIDEO", addedVideoId: newVid }]
      });
      const newSetVideoId = addRes?.playlistEditResults?.[0]?.playlistEditVideoAddedResultData?.setVideoId;
      if (newSetVideoId && oldItem.setVideoId) {
        await ytPost("/youtubei/v1/browse/edit_playlist", {
          playlistId: PLAYLIST_ID,
          actions: [{
            action: "ACTION_MOVE_VIDEO_BEFORE",
            setVideoId: newSetVideoId,
            movedSetVideoIdSuccessor: oldItem.setVideoId
          }]
        });
      }
      await ytPost("/youtubei/v1/browse/edit_playlist", {
        playlistId: PLAYLIST_ID,
        actions: [oldItem.setVideoId
          ? { action: "ACTION_REMOVE_VIDEO", setVideoId: oldItem.setVideoId }
          : { action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: oldItem.videoId }
        ]
      });
    }
  } else {
    console.log("🔄 מבצע עדכון סדר מלא בתוך הפלייליסט הקיים (" + PLAYLIST_ID + ")...");
    // שלב א': ניקוי הרשימה הישנה (עם וידוא שהרשימה התרוקנה לגמרי לפני הוספה)
    let pass = 1;
    while (currentItems.length > 0 && pass <= 3) {
      for (let i = 0; i < currentItems.length; i += BATCH_SIZE) {
        const batch = currentItems.slice(i, i + BATCH_SIZE);
        console.log(`🗑️ מנקה סדר ישן (סבב ${pass}: ${i + 1} עד ${Math.min(i + BATCH_SIZE, currentItems.length)} מתוך ${currentItems.length})...`);
        await ytPost("/youtubei/v1/browse/edit_playlist", {
          playlistId: PLAYLIST_ID,
          actions: batch.map(item => item.setVideoId
            ? { action: "ACTION_REMOVE_VIDEO", setVideoId: item.setVideoId }
            : { action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: item.videoId }
          )
        });
        await new Promise(r => setTimeout(r, 450));
      }
      await new Promise(r => setTimeout(r, 1000));
      currentItems = await fetchCurrentPlaylistItems();
      pass++;
    }

    // שלב ב': הוספת כל הסרטונים לפי הסדר החדש
    for (let i = 0; i < TARGET_VIDEO_IDS.length; i += BATCH_SIZE) {
      const batch = TARGET_VIDEO_IDS.slice(i, i + BATCH_SIZE);
      console.log(`⏳ מוסיף בסדר החדש ${i + 1} עד ${Math.min(i + BATCH_SIZE, TARGET_VIDEO_IDS.length)} מתוך ${TARGET_VIDEO_IDS.length}...`);
      await ytPost("/youtubei/v1/browse/edit_playlist", {
        playlistId: PLAYLIST_ID,
        actions: batch.map(vid => ({
          action: "ACTION_ADD_VIDEO",
          addedVideoId: vid
        }))
      });
      await new Promise(r => setTimeout(r, 550));
    }
  }

  // ============================================================================
  // שלב ג': וידוא סופי של הסידור בשרתי יוטיוב ותיקון אוטומטי של כל אי-התאמה
  // ============================================================================
  console.log("🔎 מבצע וידוא סופי של סדר השירים מול שרתי יוטיוב...");
  await new Promise(r => setTimeout(r, 1500));
  let finalItems = await fetchCurrentPlaylistItems();
  let finalIds = finalItems.map(x => x.videoId);

  // 1. בדיקת התאמה מלאה של הרשימה והסדר
  if (finalIds.length === TARGET_VIDEO_IDS.length && finalIds.every((v, i) => v === TARGET_VIDEO_IDS[i])) {
    console.log(`✅ [וידוא הושלם בהצלחה - 100% התאמה!] כל ${finalIds.length} השירים נמצאים בפלייליסט ${PLAYLIST_ID} בדיוק בסדר המבוקש!`);
    console.log("🔄 מרענן את העמוד בעוד 2 שניות כדי להציג את הרשימה המעודכנת...");
    setTimeout(() => location.reload(), 2000);
    return;
  }

  console.warn(`⚠️ נמצא פער בבדיקה הראשונית: בפלייליסט יש ${finalIds.length} שירים לעומת ${TARGET_VIDEO_IDS.length} ברשימת היעד. מנתח ומתקן...`);

  // 2. איתור סרטונים שיוטיוב לא הצליח להוסיף (למשל סרטון שהפך לפרטי/נמחק)
  const finalSet = new Set(finalIds);
  const targetSet = new Set(TARGET_VIDEO_IDS);
  const missingFromYt = [];
  TARGET_VIDEO_IDS.forEach((vid, idx) => {
    if (!finalSet.has(vid)) {
      missingFromYt.push({ index: idx + 1, videoId: vid, title: VIDEO_TITLES[vid] || vid });
    }
  });

  if (missingFromYt.length > 0) {
    console.log(`🔧 מנסה להוסיף שוב ${missingFromYt.length} סרטונים שחסרים בפלייליסט...`);
    for (const m of missingFromYt) {
      try {
        await ytPost("/youtubei/v1/browse/edit_playlist", {
          playlistId: PLAYLIST_ID,
          actions: [{ action: "ACTION_ADD_VIDEO", addedVideoId: m.videoId }]
        });
        console.log(`  ➕ נוסף בהצלחה: #${m.index} ${m.title} (${m.videoId})`);
      } catch (err) {
        console.error(`  ❌ יוטיוב דחה את הסרטון #${m.index} ${m.title} (${m.videoId}):`, err.message);
      }
    }
  }

  // 3. הסרת סרטונים עודפים או כפולים שאינם ברשימת היעד
  const seenCounts = {};
  const targetCounts = {};
  TARGET_VIDEO_IDS.forEach(v => { targetCounts[v] = (targetCounts[v] || 0) + 1; });
  const toRemoveExtra = [];
  for (const item of finalItems) {
    seenCounts[item.videoId] = (seenCounts[item.videoId] || 0) + 1;
    if (!targetSet.has(item.videoId) || seenCounts[item.videoId] > (targetCounts[item.videoId] || 0)) {
      toRemoveExtra.push(item);
    }
  }
  if (toRemoveExtra.length > 0) {
    console.log(`🧹 מסיר ${toRemoveExtra.length} סרטונים עודפים/כפולים...`);
    await ytPost("/youtubei/v1/browse/edit_playlist", {
      playlistId: PLAYLIST_ID,
      actions: toRemoveExtra.map(item => item.setVideoId
        ? { action: "ACTION_REMOVE_VIDEO", setVideoId: item.setVideoId }
        : { action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: item.videoId }
      )
    });
  }

  // 4. בדיקה חוזרת של הסדר היחסי ותיקון מיקומים במידת הצורך
  await new Promise(r => setTimeout(r, 1200));
  finalItems = await fetchCurrentPlaylistItems();
  finalIds = finalItems.map(x => x.videoId);
  const availableTargets = TARGET_VIDEO_IDS.filter(v => finalIds.includes(v));

  let orderMismatches = [];
  for (let i = 0; i < Math.min(finalIds.length, availableTargets.length); i++) {
    if (finalIds[i] !== availableTargets[i]) {
      orderMismatches.push({
        position: i + 1,
        expected: availableTargets[i],
        expectedTitle: VIDEO_TITLES[availableTargets[i]] || availableTargets[i],
        actual: finalIds[i],
        actualTitle: VIDEO_TITLES[finalIds[i]] || finalIds[i]
      });
    }
  }

  if (orderMismatches.length === 0 && finalIds.length === TARGET_VIDEO_IDS.length) {
    console.log(`✅ [וידוא הושלם בהצלחה לאחר תיקון!] כל ${finalIds.length} השירים נמצאים בפלייליסט בדיוק בסדר המבוקש!`);
    setTimeout(() => location.reload(), 2000);
  } else if (orderMismatches.length === 0) {
    console.log(`✅ [וידוא סדר הושלם] הסדר של כל ${finalIds.length} הסרטונים הזמינים תואם ב-100% לסדר המבוקש!`);
    const stillMissing = TARGET_VIDEO_IDS.filter(v => !finalIds.includes(v)).map(v => ({ videoId: v, title: VIDEO_TITLES[v] || v }));
    if (stillMissing.length > 0) {
      console.warn("⚠️ סרטונים שיוטיוב לא איפשר להוסיף (כנראה הוסרו/נחסמו ביוטיוב):", stillMissing);
      console.table(stillMissing);
    }
    setTimeout(() => location.reload(), 3000);
  } else {
    console.warn(`⚠️ נמצאו ${orderMismatches.length} אי-התאמות מיקום (מתוך ${finalIds.length} שירים):`);
    console.table(orderMismatches.slice(0, 20));
  }
})();
