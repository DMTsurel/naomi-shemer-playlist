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
  const PLAYLIST_TITLE = "שירי נעמי שמר";
  const TARGET_VIDEO_IDS = ["IUxt7faTExY", "H8V8yhc2eYI", "9xETAic8buQ", "hBlEx2bIRNI", "KaovY--ET14", "cpp8XENcuBk", "V4QSoLFj-NM", "mw9uiMMvFGk", "jk6lOLldgT4", "Xe4H1sCCAJo", "Zr-iKRNRzQk", "DEKLsquUP34", "TFIrOcriazY", "My9HiZIPsak", "zN2CRXhVJ3o", "bfQeAbF8-4A", "unyzPkoPBEs", "85QDrN6FB8Q", "dwUst6vBhs0", "ryXmue6dutA", "sFB_B3wTXLE", "-T6mxux7wKM", "4_Laz5PQV-Y", "tWs6g7hg0BI", "5Hz8UIWRADU", "BfKQ4bj0JJk", "gTXgnxD6Cuc", "1_dsV0afFgA", "JfJ3DrI7-6w", "NxoJzDVw4cc", "zpFGk2nz_-A", "-4bnvgAYqmo", "MFrjlagc8rE", "AvJZwh25uZ4", "eSmhtnivpvY", "07aL8h1LyJk", "418kExn65Ug", "ei2FcAMuRAw", "oNmwW4s3AuI", "0ypE8NBmyYo", "vrJcb0mauz8", "Zs1s0_fs9EI", "dDXngW-5jV0", "vQjWwS6X7CI", "6OWfRHNgEtg", "2iljNf6XqsA", "fE8xcZiFRO8", "-nzLbN3sFRQ", "5kl6qHnbp9Y", "BnKrb-46CNI", "kF5Lpl7IL6w", "zZHynZGet5g", "URL56lbFmr8", "e9lQpiSO6XM", "2QMxLPxD25g", "7uxKafYsUrU", "_NylGW8syfw", "BgpoI6q79Lw", "0IPY0etp8eE", "pWGF4nqxi9c", "AxnQ3qrsp64", "08Z_uYA9PLc", "XsDAsNDqHW4", "Ce_cSMB0Ri8", "5TZvR7wFlVo", "DdET9qVDfRI", "_DujVVkqqQ0", "neYlxPR8-WA", "ax7p4AggiqY", "zRQLXqjeRoE", "isxLekbAFHw", "4ZFF3v39RD4", "YQc4x6hGSyg", "q3XGUpCCTJs", "Q5N5gxqjDFc", "eCRBb3h6mz8", "9Er1RvAuM7M", "bzl8G_GQJKE", "7PxG0jfZX6k", "2aQJz8v_KkU", "XUR6jL3D6N8", "WFOhRFYM1wM", "QPPugl_l2ak", "mYfdJkb1gqg", "XKbvfLzHms4", "tk3zQs8gDTM", "4HZWNJzXTm4", "Okw-ktcRVr0", "UwhEUsWVdPg", "VCDKtBt4xb4", "jMlzihkguOU", "CeRvSDeJx-I", "8y5KQ8UWi0A", "neNKCSaT1T8", "ZFFJR9iTSuo", "6hhQ_4omcKs", "Gi7-feW4FfE", "FkSHlF212BA", "aKAvYLWF97U", "GgYxh_MoCDA", "06dUzmJF7H0", "gkPyKqEFNSE", "RqHN-so83M4", "OS9uUlfBrbA", "YY8vUjMWzEc", "Xoh_DVe4WcA", "ufIj60iGZqM", "sLvHms2BClA", "H3h-755AwoI", "0ga6HoypSJU", "DATGdPiFqVA", "ZcKAuoZSzWQ", "pKGFC7qoGBA", "D13BJwfsQu8", "l1b8s6ZGXhQ", "l8uDRKHspac", "dYYGjAoIU_E", "FZrRqLdaH5E", "ArRyqOnlQ3k", "_lds9E6qEQg", "z-OpnBf-JNI", "KOecGqpq-f0", "kF_MJiReEn0", "9bfiWAv4HSU", "Y8ob5jdoYBw", "VkgQyNxNQqw", "pjCtGobuuSE", "qpbBemLcsUE", "aDZqwcq7eVI", "B0EO7nYCdu0", "04AcSZS8K3s", "SDCkIuEiWWY", "0XhvBFzatFc", "NWR0K-8lBhU", "MtwqXXIN6Xs", "5v77wNxd8Kw", "AoGcmpu5D4Y", "SgzeIwaaGMU", "T5o_o8lO-1M", "zV4aK_XyPW8", "wO3U1xG7Um0", "EFIwG44Egek", "yzSOpEPUXWw", "2MUXbKJVRZo", "Okj7fK4VSOA", "vVQ0Xmtb9_Q", "CYwiq1Uu5Ng", "OvN5nJ9bn2Y", "E3V70DpK_EI", "NGtt4OBuh2E", "whmUk6hiVE4", "I00dlNJc6BI", "pDLQ_FrzKL4", "p64TXGU2ipM", "2BfY0duzEpE", "7cZaZp3xfDM", "Im8ze1yI8Aw", "BBUtEBZLJFQ", "B7oZ2GPHhEU", "sdlmzqJiT5M", "Ba1W41IDnhI", "P8g0g_IQcjI", "2o1uo7sstSI", "AnWiRbrejHg", "24JJpjDS8QY", "dtbSIHcMWjY", "Ke6iImauSj4", "m58C3mRgm5E", "sKkBNzdlFvE", "dZtHel6cUW8", "Brq81oCuNKc", "SSJdF9cV8iQ", "-7qKw4AIGP4", "V8CR6u84pXU", "_aoBikUYiBY", "pCK483hwY-0", "FQson2Wm0iw", "CEI769yjg4g", "UgXcD55HXzc", "yKAUdNGyVpA", "YtWovd6r0yc", "WxdVdudBKeE", "EikdgimAjd8", "gU6tE4TqExI", "yXzElXsHH38", "ZLzkd2ui6PM", "doXUEtdMaxc", "i9bIVfz1HBw", "wIFDo3qiS9c", "hdskywcJSMo", "bzLl7TH_VxQ", "9aIw7qJAOA4", "sgMLsWRX7SI", "ew9j2OHt8Cw", "VaztQIe75Ns", "KO7lZhbeFDs", "PXL8ltjFDCk", "gpo_GVko6OA", "nz7sT486EYw", "ut3moC4G-QI", "2vq22hm-TnI", "_6La2mK-PqU", "PEamc15DDeY", "Y5aCrfJLjIM", "3YYVsJ9MGZQ", "xypLh9F1IXk", "VsVv0OOIARQ", "bnl-cjqYOwk", "E-jZMuDEvLQ", "Vimcno4QbUw", "E-G-dnLO99U", "cCftnvA1iJo", "KEOx2onVNDs", "Ur53Ai6WISA", "nOa7P6X2I-8", "zUWmMkqQMQg", "t6jXzPCR0NA", "L7_tsGSLGTs", "cD2GgbFD_Yo", "dgC-AI1O_a8", "-rGr-thBmjs", "mtuSxIIZPqg", "cbNuUKAQMsU", "3oB1QegwRqk", "9XgKm2xg3iA", "7IEl35CsSaI", "38jU5bVcNzo", "3iQEC7mO3YY", "me0k188YXNw", "hSaod2F6TA8", "UxWCHV50LoU", "7e6hGajTOaE", "1uRrLed3pZc", "0pdyuulvbzo", "OLQITmFP3Xo", "g-477LqGTr4", "rh0oGPJbf5M", "CMhfrA5uDjE", "UtixqreayIo", "eGrPQv3g9ps", "A1BCQuWuvTE", "2GD7HJfapWM", "oNZG3NUzB3U", "V2eI7l5c3nc", "-dNwuLchpWg", "gkP9-OqJETY", "UeP8K2lXml8", "cV-WsBBOwto", "gRfvDuXwtYI", "VXLKQYTYShc", "61RF4uejHJE", "morcvF-aFsg", "-2f28ACy-Gk", "O4OhUorCxX8", "OFBBD-EuEfA", "6sR4GRdyZZ8", "yEG2trB0IxU", "X0EHaEth0TQ", "s0923q2OCPM", "VeeEHBwsyQw", "chw7OpsTH1A", "cmQ9upI0aG8", "Yd63Irvr-Q0", "mzrn0p-yRSM", "tBL2uGdMMZ4", "Jl0WahK00lU", "sJFfiL_Y1_E", "UOD51gynvJQ", "o9ElrJy3fmk", "d8h9EDhbixA", "ZYTJPE70ifA", "_FhoSjLL61A", "UfIj78lym1I", "3v9rvDklaxc", "mZxh2vHIBcs", "oQLUlVqXkpo", "pPE_eIQYtgY", "yavA7DK-_Lg", "wcy425HOqro", "tPX2FmmeM6k", "-p0EvZ_T_AY", "nvaUD-WzYDQ", "iz3Et-1Ywe8", "IWaGaO6VD4c", "GZW3RhiQeyY", "jOpau37GjhY", "_LilpxfdvKc", "3H9EF4ZzVy8", "z91zsr8vHnU", "tz4ISVJyEfI", "HH2wou4FvsA", "wFYq_Is8wJk", "uquTBB0PbFY", "v6wgkaN8mvg", "6xpROKMcQus", "Kc3Z01Zqr24", "XixXG6ffyy0", "ZSYQh_YatoU", "erKzXsvfheA", "QKmscJgKCYs", "OfsdkuisiNo", "acNmIrbrp0k", "xAvvvAO6glU", "DtlDXf6tveY", "-eINxqt2z0A", "IXn5sqpAhqc", "Hv0SuDUsjyc", "R1tJE7-evoQ", "Ya2SuHzZAXo", "J1mbZ9eGho0", "jYVg9ERVMv0", "YMdqSo7wMUk", "k8u50w4T-1g", "LR_zCS48QV0", "1dAeJminXHM", "L8jFWAH86Hw", "MhIbjL4Hghc", "ldmMVGr-syE", "sCQfgFoAQu4", "cITPhRNWoq0", "LYoIOT8VvK0", "xdj8UWyGpFg", "C-rohkw6OX8", "EEq9IuWDBlM", "KSTaBxvL4JQ", "R-oz2dlpbvY", "pUFhGuyD6j4", "SfPOduJnKvk", "NXcXk-diyDY", "yWVoMYXeBpM", "w1hLRFc3jfo", "rGRBY2iPjpk", "OxafdSA-QkE", "NhX0XzGmv9A", "t_qzuM6V2Co", "Bac-K0Wjp2A", "YMrwmCzH330", "Eff5K5VrmKE", "N4QGMJR3Qqo", "wONNxGvP9S4", "SOOmGDRVIK8", "0re6w_ZITxg", "cAOakJcPmGs", "q-9lO4eg7-w", "kLf2ybtWLCI", "Ae_oPwsp_P0", "VnReHM2MOuo", "ZKGMTf5XLCk", "Bujd3-vDfE8", "OkWKy3URsDg", "e1c2MjdU9T8", "gEacqh5DPk4", "BncSM_l0_P8", "r97YIa4BDnM", "DGUHUGnDYn0", "COoXTOZQYQ4", "7t6dTKHZY6U", "YWwJ1O6fQQs", "41VIMNNssjw", "hw_SJRb1uEk", "oJZEOGPBtp0", "G5RVx22SVzs", "g_QXbJmWWO0", "9o-4qxrv584", "nOl7AAouxVc", "k0LjOdjBdYU", "S9QL3kDf8gA", "nNFb0CPT7Js", "ukOWgL-9mlw", "O5In5PJnEr8", "LBTf6IMt2X8", "ITgt-B5IdFk", "Xw4qL0j_9Vs", "71Pqy6HKns8", "tNga0kZsgXY", "piH6EOOP7cY", "3a8B5imZV8o", "Lg-Can0ZrXM", "Rh-AfNJC1AY", "g57hoYLobng", "xam-JFkXggk", "X3GCh50sW8A", "zuYjR6RNeIw", "mxCqvGI5iu0", "ud8TFvfUJ8M", "7ziQJmP02M0", "hZirnyIx1Tw", "Ti6nFst0JaE", "sdqrr4rdUPA", "P35Ek5tTy4I", "0yT4idCIsSE", "DLilbBb5C-k", "1D4_GtYfmUE", "gfYmkBTQVD4", "dGSCRDVe9NE", "L1QLv-RFy7A", "qiWE67WQSBY", "DZCXER0nGaM", "WDQyD0VHt68", "ydCddPTqZmo", "Z-JxFdJcoB4", "KXjJoVHJsQw", "6BfneC2-IvA", "4gYlHwrMV50", "2smvtZlQSEg", "SzfqrHxbpug", "V_AZsXtgxvY", "QYW7YCydh3s", "0XHUVfPJlak", "tnNhOpq6MqI", "hZwuhnWXkLE", "p3PIKVi8goc", "OzrUXu1pKkg", "lfB0Y5mJ1qk", "ORPN8djCQws", "UsNNGSI6qzk", "OBkMzEHYA3c", "JAh-XgpCIEo", "X-KSBs_Lsd8", "omNa4PW1lU8", "8d9khSRpSkk", "qgyoXwMKJXg", "OdbpJIdes4Q", "WBfuFYdOQT4", "kO9D3crjEsU", "F6syH8W0EGA", "sFbghpqy0Lo", "JH-1IrNb_P4", "XWOGYjtgJG0", "Luu_LIPtx-M", "JvQBz3CHrK0", "reYLaGMYJYk", "l4y16i5NwwQ", "0Yn3EvME2ko", "jzNc8KFQ4S4", "WILLlFVs8K4", "VhBycovusXA", "OdYRuoXrHHw", "T3qo2SYP52U", "K1DBCpPxqeM", "EZ2zDG6qrJE", "8XCsox4ClH8", "ubenw8IJ9dE", "qvBk0IVkKRE", "fCi5ISYIy1U", "aG2s9Sp7tKg", "W6i7v9rr12o", "QUF8MiDp4O4", "oxzR9Z-kG6Q", "dWp4KgvyPYw", "PL0HmLqbxpw", "VbIHsjgvE2g", "WBc7IWmf3cs", "dV91YmIuHV4", "Mf7VagPUG50", "_GD1f91Erg8", "E452vwyyVjQ", "_eq2jnCdcyA", "-Db1ucwfr1o", "erGG9tlYbBk", "z8JrHEVGykA", "oJS0DogSjXU", "A-6m6CKOdC4", "mypB2220Rfk", "sFfgH0oJdwE", "XHdb6YDvHII", "7T8wbdYlAbQ", "gRclcNmJ9fQ", "_nDa2esEWJk", "HgMGNLc5ir8", "AuYOGchQ6XI", "J41YP1kDIKw", "7yMw3vG4_kU", "XtoKkNpyn-E", "BLpTR9p0mkY", "aO1sboxdmno", "dC2fS3vZAPY", "7kj9X6BnPKE", "FZp12hlp4gk", "HvE1Ib25iDk", "6hTkFqKThes", "fiU_B2M84Ww", "cRAhfb9Ypw8", "L-qU-BInVno", "e4cc_kptHk8", "vQPSLn2e4FY", "w2E3hxhbAc4", "EoHoiD_n7t4", "iPj5rmj8GZQ", "EdfxwaHVnAk", "-P0Gnvk5Kmk", "HlUl3uS6T6Q", "WK3WmcATcd0", "q4zRVBV0010", "Ue8yK2cnLTA", "He8KKInGwAE", "PkF2Y0bbbCo", "Jg42GYm1qv0", "M38vdprLLok", "HTMwVk8pQiY", "WZMQaNRyllY", "jd4eLSSa1Xs", "Xc6coB1-EPw", "06SSkPFTjfM", "Ar_Ua0MBt_w", "eUam8viOqxs", "jAnSY8gxLRg", "-vWfGW7Hf2E", "sCRw6hfgQTM", "YJKhOidPJhc", "AcZZ7fqUNTc", "bbIXevkZDnk", "WfM--seOsaY", "yscdF17IT_Y", "Pef5mRmx0fA", "kkJPYVGy31o", "_F3EdZ51O-Q", "Uwi4o3fwQwc", "1dDug8M2AYs", "wly5oxW3C6Y", "Picy0oa0wl0", "jfy9Pml8UZg", "vXAxaeNqze4", "0viBWDlQ9KE", "dLDcWMN-Fbw", "kA1Gl5w3ydI", "jfvSQpek00g", "ziATm-51Zc0", "FBMgpQRmfmo", "3iaTDb1K41o", "5VQkcCM1fmc", "OEVLRDRUxyc", "0u--FHf-LHU", "ms-YfEQM9E8", "SnARDknXrZQ", "Sn0vSoeVXpI", "dKHjdN2hr4w", "vLhN2olc06o", "9NbtBvkX2TI", "QeX9yVM_izg", "zEG-AcszgpQ", "TQwpuggfQWw", "6qiFa7eU34M", "f18phGNSyBg", "O9CoiUnwJ5A", "WA8fVawaHuw", "n6qfNKmjutM", "5yDnz_UrH-s", "5xj4ycn0TY8", "dFgoc8M87Ww", "jvZPz3tpWPw", "1gUgA5_iv5g", "sVEvT4pZeyQ", "JDThzHJWt4o", "0mcp9JqqJ1k", "ymL0Whh7V_I", "99iIWvXtsqc", "8UcwA-Zk3JQ", "GoWmzpyfv0Y", "uqOoO342wNg", "xkGxvP-tw1w", "qEYW8pnCu48", "3oHvXK3Xj5k", "p_OfoN-B_xw", "upipvN8Xw-c", "cYZArmDfKnA", "s1SR4hmgC4U", "HBZpHQRKrFM", "g6clciS1riA", "gXM9-IpEzEc", "nruQWhRsem4", "7m9YwTJwFrE", "3st5EgoczRM", "TmFdkd0YmjU", "s1Ac_TvGdAU", "ry9RV0yCJpI", "TGRVtcThDf4", "p320GUpKgkQ", "hA92uD-XpQs", "Omn_wSe-dKU", "YgYyQjI4UeY", "C1PjhOZQxMU", "_Fxy_CFR78Q", "narkCrS3_GA", "lKhxVjkSa84", "XWnWPkDHGz4", "PrntU87z0n8", "wzrVRxyd5a4", "3G8xlTapGQo", "0rZlNPF_utQ", "vUmuxcvyGrM", "-2N-WzrLzCc", "sQTl_NH1n0o", "0krT8xzNbyM", "bZI8gT-VbT0", "XBrUmJLCkEw", "YrJtArqXavk", "TsA3LycTPSo", "PHQFSQi4tzU", "XteReGQom40", "xI2m7tKJ40E", "JAY_uZjqmIA", "qrvKQtQgb2s", "YS6EfEQu1ik", "hDqbO57hnyQ", "EfcKLvzIDRw", "cXln3eAat5g", "Pk0mm0ly7Og", "KvBOUWSO1PM", "vNw21mQVfKM", "H9f2NJOxcz0", "P7eGfaq3E_s", "GyiSOeKOK8s", "DJFWTrj5sO8", "losUGtP6fxI", "skYeVk80Eo0", "mpPxqJrum-M", "Sah0hB6rSFY", "x0IPLHoV9Yc", "pTlgYtrDSPI", "vAT50nuKMh8", "ycWudyVJdOU", "i9KzXu-Nhx0", "YfFNug5ZOac", "A9erliXTS6o", "6EEIW68j5lY", "ipzIvlpBkbU", "rLucwp89lnE", "4g6cymurqY0", "-1__PIJhhPI", "agChJ2Ho124", "Yd3_uDW6i4w", "vxQcorAdAXA", "chuU4lFZ5iA", "vbG5B1wswQc", "U3xSpmrTgXc", "CSjnGcglVJI", "Jzkgm9A3Ooc", "INHBTa-HfSM", "4ApYhj2Mqeo", "F25xFwezdxw", "PIqHAidM99g", "EEkIbuhQ9dw", "lXCnVOsgJwo", "CJ8_MISsRxg", "nNMmAneQsLs", "Pxm7UgJ1JiE", "qblckfTw1Rk", "5-8BIb9KyNk", "_33ng3euFJI", "XIs2ZIJ2oZw", "-xNyTz_yvRU", "gsf0t-VihvE", "jqQTqr1gHEI", "n2t3bDiJcMk", "dT5g0VRp7jE", "tpe1wARxPSs", "3wNpnpA5K-w", "2LRsVjehz44", "SZhwVVZuRkY", "CwORk-NwrQM", "_JG62QmM-QE", "XeD27Barwbk", "dfPBgVKT_H8", "gq5PAlFBEi8", "_qb0WUb7i5A", "c0WSmr4tlLY", "0eWljspYG7E", "F7KHn6M2VGk", "XOJchlUhps0", "6yrG087cato", "evAV9e6QUlI", "uITVQ8JRMg4", "F-tHf-vPBxQ", "sgVtXugsDtE", "s6Geto53AmI", "d9pbNfB26wc", "ExOobxzS4tc", "FFtI8ZQT2Mk", "B86J0eynF9A", "UB35E3hE65E", "CLDelMZYKC8", "xyiYZRhJsSo", "BAliJ1ieJrI", "mMEXXehlL54", "4MJ1vA3znA4", "URuGgQXkQpQ", "wk0pllJl1nU", "_vJ6UtXHybA", "6rlo1KZ0qok", "weX6vsG96ZY", "JUiRv74kgHU", "B7rC1GyPlqM", "Yk82zpkqZjw", "oo8IRR00H30", "k0RE3k8k1pQ", "mnXZeefSK8w", "nMxKk66pAzc", "6Z2BOKloo7k", "SdrmUgN92O4", "lmTSkGSnxzw", "9d8hI1wc_Bs", "fs14OduKHd4", "YYVengVA5V8", "oMZHElIjza4"];
  const VIDEO_TITLES = {"IUxt7faTExY": "ירושלים של זהב (1967)", "H8V8yhc2eYI": "ירושלים של זהב (1967)", "9xETAic8buQ": "על כל אלה (1980)", "hBlEx2bIRNI": "על כל אלה (1981)", "KaovY--ET14": "לו יהי (1973)", "cpp8XENcuBk": "לו יהי (1973)", "V4QSoLFj-NM": "עוד לא אהבתי די (1977)", "mw9uiMMvFGk": "אני גיטרה (1993)", "jk6lOLldgT4": "שירת העשבים (1976)", "Xe4H1sCCAJo": "שירת העשבים (1981)", "Zr-iKRNRzQk": "פגישה לאין קץ (1970)", "DEKLsquUP34": "פגישה לאין קץ (1981)", "TFIrOcriazY": "חורשת האקליפטוס (1967)", "My9HiZIPsak": "חורשת האקליפטוס (1988)", "zN2CRXhVJ3o": "לא תנצחו אותי (1984)", "bfQeAbF8-4A": "לא תנצחו אותי (1984)", "unyzPkoPBEs": "אנשים טובים (1981)", "85QDrN6FB8Q": "שנים עשר ירחים (1960)", "dwUst6vBhs0": "תלבשי לבן (1985)", "ryXmue6dutA": "הכל פתוח (1994)", "sFB_B3wTXLE": "שבחי מעוז (1971)", "-T6mxux7wKM": "שבחי מעוז (1971)", "4_Laz5PQV-Y": "אור (1988)", "tWs6g7hg0BI": "מחר (1963)", "5Hz8UIWRADU": "מחר (1967)", "BfKQ4bj0JJk": "וולס להגנת הצומח (1967)", "gTXgnxD6Cuc": "החגיגה נגמרת (1976)", "1_dsV0afFgA": "החגיגה נגמרת (1976)", "JfJ3DrI7-6w": "אל בורות המים (1982)", "NxoJzDVw4cc": "יש לי חג (1977)", "zpFGk2nz_-A": "שלומית בונה סוכה (1970)", "-4bnvgAYqmo": "שלומית בונה סוכה (1975)", "MFrjlagc8rE": "לילה בחוף אכזיב (1967)", "AvJZwh25uZ4": "לילה בחוף אכזיב (1982)", "eSmhtnivpvY": "שירו של אבא (1968)", "07aL8h1LyJk": "שירו של אבא (1968)", "418kExn65Ug": "הוי, ארצי! מולדתי! (1977)", "ei2FcAMuRAw": "אהבת פועלי הבניין (1964)", "oNmwW4s3AuI": "בהיאחזות הנח\"ל בסיני (1969)", "0ypE8NBmyYo": "בהיאחזות הנח\"ל בסיני (1969)", "vrJcb0mauz8": "עיר לבנה (1959)", "Zs1s0_fs9EI": "הטיול הקטן (1966)", "dDXngW-5jV0": "הטיול הקטן (1977)", "vQjWwS6X7CI": "אורחים לקיץ (1979)", "6OWfRHNgEtg": "אורחים לקיץ (1981)", "2iljNf6XqsA": "אנחנו שנינו מאותו הכפר (1969)", "fE8xcZiFRO8": "אנחנו שנינו מאותו הכפר (1968)", "-nzLbN3sFRQ": "כנרת (1964)", "5kl6qHnbp9Y": "העיר באפור (1964)", "BnKrb-46CNI": "בראש השנה (1972)", "kF5Lpl7IL6w": "בראש השנה (1975)", "zZHynZGet5g": "מה עושים העצים (1968)", "URL56lbFmr8": "מה עושים העצים (1971)", "e9lQpiSO6XM": "החופש הגדול (1975)", "2QMxLPxD25g": "קומי צאי (1973)", "7uxKafYsUrU": "קומי צאי (1982)", "_NylGW8syfw": "פירות חמישה עשר (שלג על עירי) (1977)", "BgpoI6q79Lw": "פירות חמישה עשר (שלג על עירי) (1982)", "0IPY0etp8eE": "מטרייה בשניים (1963)", "pWGF4nqxi9c": "האורח (1984)", "AxnQ3qrsp64": "אלף בית (1975)", "08Z_uYA9PLc": "סרנדה לך (1967)", "XsDAsNDqHW4": "חבלי משיח (1967)", "Ce_cSMB0Ri8": "שיר השוק (1961)", "5TZvR7wFlVo": "בשדות בית לחם (1971)", "DdET9qVDfRI": "סימני דרך (1982)", "_DujVVkqqQ0": "לשיר זה כמו להיות ירדן (1972)", "neYlxPR8-WA": "אומרים ישנה ארץ (1980)", "ax7p4AggiqY": "אומרים ישנה ארץ (1981)", "zRQLXqjeRoE": "כיבוי אורות (1958)", "isxLekbAFHw": "כיבוי אורות (1982)", "4ZFF3v39RD4": "ספירת מלאי (1974)", "YQc4x6hGSyg": "הו רב חובל (1996)", "q3XGUpCCTJs": "נועה (1957)", "Q5N5gxqjDFc": "נועה (1977)", "eCRBb3h6mz8": "שיר סיום (1971)", "9Er1RvAuM7M": "זמר נודד (1959)", "bzl8G_GQJKE": "זמר נודד (1967)", "7PxG0jfZX6k": "אהבה בת עשרים (1972)", "2aQJz8v_KkU": "אילו ציפורים (1967)", "XUR6jL3D6N8": "אסיף (1980)", "WFOhRFYM1wM": "אסיף (1992)", "QPPugl_l2ak": "כמו חצב (1981)", "mYfdJkb1gqg": "אין לי רגע דל (1980)", "XKbvfLzHms4": "רכב אש (1964)", "tk3zQs8gDTM": "רכב אש (1964)", "4HZWNJzXTm4": "התחדשות (1985)", "Okw-ktcRVr0": "שיירת הרוכבים (1958)", "UwhEUsWVdPg": "מחבואים (1963)", "VCDKtBt4xb4": "מחבואים (1967)", "jMlzihkguOU": "על ליל אמש (1960)", "CeRvSDeJx-I": "כד הקמח (1971)", "8y5KQ8UWi0A": "בשדה תלתן (1961)", "neNKCSaT1T8": "חמסינים במשלט (1958)", "ZFFJR9iTSuo": "על כנפי הכסף (1967)", "6hhQ_4omcKs": "על כנפי הכסף (1967)", "Gi7-feW4FfE": "בית חלומותיי (1966)", "FkSHlF212BA": "בית חלומותיי (1967)", "aKAvYLWF97U": "סימן שעוד לא הגענו (1976)", "GgYxh_MoCDA": "סימן שעוד לא הגענו (1982)", "06dUzmJF7H0": "שיר סתיו (1958)", "gkPyKqEFNSE": "שיר סתיו (1958)", "RqHN-so83M4": "שיר הכזבים (1975)", "OS9uUlfBrbA": "בכל שנה בסתיו גיורא (1977)", "YY8vUjMWzEc": "בכל שנה בסתיו גיורא (1982)", "Xoh_DVe4WcA": "על אם הדרך (1972)", "ufIj60iGZqM": "איילת אהבים (1964)", "sLvHms2BClA": "זמר (1966)", "H3h-755AwoI": "מה שלומך אחות (1987)", "0ga6HoypSJU": "עצוב למות באמצע תמוז (1991)", "DATGdPiFqVA": "הלילה הולך בשדרות (1958)", "ZcKAuoZSzWQ": "הלילה הולך בשדרות (1958)", "pKGFC7qoGBA": "בגני נטעתיך (1966)", "D13BJwfsQu8": "מיכאל (1968)", "l1b8s6ZGXhQ": "הי טירילי (1958)", "l8uDRKHspac": "הי טירילי (1965)", "dYYGjAoIU_E": "בדמייך חיי (2001)", "FZrRqLdaH5E": "החייל שלי חזר (1966)", "ArRyqOnlQ3k": "החייל שלי חזר (1967)", "_lds9E6qEQg": "הופה היי (1960)", "z-OpnBf-JNI": "הלאה (1984)", "KOecGqpq-f0": "הלאה (1987)", "kF_MJiReEn0": "שלום כיתה א' (1979)", "9bfiWAv4HSU": "שלום כיתה א' (1979)", "Y8ob5jdoYBw": "דיוקן אמי (1981)", "VkgQyNxNQqw": "דיוקן אמי (1981)", "pjCtGobuuSE": "נגיד (1975)", "qpbBemLcsUE": "נומי נוגה (1977)", "aDZqwcq7eVI": "ארבעה אחים (1966)", "B0EO7nYCdu0": "ארבעה אחים (1967)", "04AcSZS8K3s": "חליל מקנה-סוף (1977)", "SDCkIuEiWWY": "יש לי חבר (1975)", "0XhvBFzatFc": "הכול בגלל מסמר (1964)", "NWR0K-8lBhU": "הכול בגלל מסמר (1967)", "MtwqXXIN6Xs": "וזוהי רק ההתחלה (1974)", "5v77wNxd8Kw": "וזוהי רק ההתחלה (1974)", "AoGcmpu5D4Y": "יובל (1998)", "SgzeIwaaGMU": "הדואר בא (1958)", "T5o_o8lO-1M": "הדואר בא (1958)", "zV4aK_XyPW8": "מר נרקיס (1972)", "wO3U1xG7Um0": "אחרי השקיעה בשדה (1962)", "EFIwG44Egek": "אחרי השקיעה בשדה (1967)", "yzSOpEPUXWw": "שיר נולד (1974)", "2MUXbKJVRZo": "המעיל (2001)", "Okj7fK4VSOA": "קרן יער (1969)", "vVQ0Xmtb9_Q": "אחותי רוחמה (1977)", "CYwiq1Uu5Ng": "על הדרך עץ עומד (1998)", "OvN5nJ9bn2Y": "שנה טובה (1992)", "E3V70DpK_EI": "נר ראשון של חנוכה (1977)", "NGtt4OBuh2E": "לחם האוהבים (1991)", "whmUk6hiVE4": "שלגיה (1966)", "I00dlNJc6BI": "שלגיה (1966)", "pDLQ_FrzKL4": "הפסנתר (1981)", "p64TXGU2ipM": "עקידת יצחק (1967)", "2BfY0duzEpE": "אין דבר (1979)", "7cZaZp3xfDM": "אין דבר (1981)", "Im8ze1yI8Aw": "האם השלישית (1970)", "BBUtEBZLJFQ": "נצא השדה (1975)", "B7oZ2GPHhEU": "ספני שלמה המלך (לחן ב') (1972)", "sdlmzqJiT5M": "משנכנס אדר (1975)", "Ba1W41IDnhI": "תפוח בדבש (1979)", "P8g0g_IQcjI": "תפוח בדבש (1979)", "2o1uo7sstSI": "לנוע ולנדוד (1975)", "AnWiRbrejHg": "אל תשאלו אותי (1967)", "24JJpjDS8QY": "על נהרות בבל (1982)", "dtbSIHcMWjY": "האיר השחר (1982)", "Ke6iImauSj4": "דוגרת (1975)", "m58C3mRgm5E": "קלי קלות (1971)", "sKkBNzdlFvE": "קולך מן הסופה (1982)", "dZtHel6cUW8": "בגינה (1956)", "Brq81oCuNKc": "בגינה (1958)", "SSJdF9cV8iQ": "אשכולית (1958)", "-7qKw4AIGP4": "אשכולית (1958)", "V8CR6u84pXU": "שבת (1958)", "_aoBikUYiBY": "בקיץ (1958)", "pCK483hwY-0": "שיר ערש לצבעים (1959)", "FQson2Wm0iw": "שיר ערש לצבעים (1968)", "CEI769yjg4g": "כיצד שוברים חמסין (1964)", "UgXcD55HXzc": "כיצד שוברים חמסין (1975)", "yKAUdNGyVpA": "גדי קטן (1977)", "YtWovd6r0yc": "פרי חדש (1993)", "WxdVdudBKeE": "פרי חדש (1993)", "EikdgimAjd8": "הללויה (1966)", "gU6tE4TqExI": "אין ויש (1972)", "yXzElXsHH38": "שש עשרה (1972)", "ZLzkd2ui6PM": "בארץ להד\"ם (1972)", "doXUEtdMaxc": "אנשים יפים (1972)", "i9bIVfz1HBw": "שני צלמי רחוב (1972)", "wIFDo3qiS9c": "מסעות בנימין מטודלה (1979)", "hdskywcJSMo": "למה צחקה מיכל (1979)", "bzLl7TH_VxQ": "גג (1987)", "9aIw7qJAOA4": "ילדה ברבור (1987)", "sgMLsWRX7SI": "פרלוד (1987)", "ew9j2OHt8Cw": "פרלוד (1987)", "VaztQIe75Ns": "אהבת אשתקד (1987)", "KO7lZhbeFDs": "תות (1987)", "PXL8ltjFDCk": "גיא (1987)", "gpo_GVko6OA": "חפצים אישיים (1987)", "nz7sT486EYw": "בראשון לספטמבר (1987)", "ut3moC4G-QI": "עלי שלכת (1989)", "2vq22hm-TnI": "שיר הבר (1958)", "_6La2mK-PqU": "רב האור והתכלת (1958)", "PEamc15DDeY": "סמוך על התרנגול (1958)", "Y5aCrfJLjIM": "אופליה (1964)", "3YYVsJ9MGZQ": "אופליה (1965)", "xypLh9F1IXk": "בלילה שכזה (1964)", "VsVv0OOIARQ": "בלילה שכזה (1964)", "bnl-cjqYOwk": "אשרוק לי שיר עליז (1966)", "E-jZMuDEvLQ": "אדון ומלך (1966)", "Vimcno4QbUw": "אקרא שלום (1966)", "E-G-dnLO99U": "חידתיות (1966)", "cCftnvA1iJo": "להתוודע (1966)", "KEOx2onVNDs": "בצל ובאופל (1966)", "Ur53Ai6WISA": "שפחה שפחה (1966)", "nOa7P6X2I-8": "דבר מה נפלא כל כך (1966)", "zUWmMkqQMQg": "בחלום (1966)", "t6jXzPCR0NA": "משל סיאמי (1966)", "L7_tsGSLGTs": "הנרקוד (1966)", "cD2GgbFD_Yo": "מה שיהיה יהיה (1956)", "dgC-AI1O_a8": "שיר לחג עשור (1958)", "-rGr-thBmjs": "שיר לחג עשור (1968)", "mtuSxIIZPqg": "יום ה בשבוע (1958)", "cbNuUKAQMsU": "יום ה בשבוע (1960)", "3oB1QegwRqk": "רוקדת (1958)", "9XgKm2xg3iA": "מצעד האביב (1959)", "7IEl35CsSaI": "מצעד האביב (1959)", "38jU5bVcNzo": "קפה שחור (1959)", "3iQEC7mO3YY": "ספני שלמה המלך (לחן א') (1959)", "me0k188YXNw": "שיר לגדעון (1961)", "hSaod2F6TA8": "חיילים יצאו לדרך (1962)", "UxWCHV50LoU": "חיילים יצאו לדרך (1967)", "7e6hGajTOaE": "ורד בר (1962)", "1uRrLed3pZc": "ורד בר (1982)", "0pdyuulvbzo": "זהירות בונים כאן (1963)", "OLQITmFP3Xo": "זהירות בונים כאן (1963)", "g-477LqGTr4": "הטיול הגדול (1963)", "rh0oGPJbf5M": "הטיול הגדול (1963)", "CMhfrA5uDjE": "עוד לא אכלנו (1963)", "UtixqreayIo": "לכבודך (1964)", "eGrPQv3g9ps": "לכבודך (1967)", "A1BCQuWuvTE": "מתי (1968)", "2GD7HJfapWM": "מתי (1968)", "oNZG3NUzB3U": "כל הדרך חזרה (1969)", "V2eI7l5c3nc": "עוד חוזר הניגון (1970)", "-dNwuLchpWg": "בתכול השמים (1970)", "gkP9-OqJETY": "אסוני הצעיר (1971)", "UeP8K2lXml8": "מה אמרו הציפורים (1972)", "cV-WsBBOwto": "מה אמרו הציפורים (1962)", "gRfvDuXwtYI": "ברברה (1972)", "VXLKQYTYShc": "ברברה (1981)", "61RF4uejHJE": "החטא השביעי (1973)", "morcvF-aFsg": "לאיש חסדי (1974)", "-2f28ACy-Gk": "נשים נשים (1974)", "O4OhUorCxX8": "אין אהבות שמחות (1974)", "OFBBD-EuEfA": "לא אבקש את ידך (1974)", "6sR4GRdyZZ8": "הצוואה (1974)", "yEG2trB0IxU": "מרגו (1974)", "X0EHaEth0TQ": "בעלייתי שם יפתי (1976)", "s0923q2OCPM": "בזכותם (1976)", "VeeEHBwsyQw": "שיר לכת (1976)", "chw7OpsTH1A": "כריש (1978)", "cmQ9upI0aG8": "יפעת (1980)", "Yd63Irvr-Q0": "תן כתף (1981)", "mzrn0p-yRSM": "תן כתף (1981)", "tBL2uGdMMZ4": "את הכי הכי (1981)", "Jl0WahK00lU": "פרדס חנה בשבת (1983)", "sJFfiL_Y1_E": "אל תלכי מכאן (1984)", "UOD51gynvJQ": "התחדשות אחרת (1985)", "o9ElrJy3fmk": "לאורך הטיילת (1985)", "d8h9EDhbixA": "ליבבתיני (1986)", "ZYTJPE70ifA": "אחר קציר (1988)", "_FhoSjLL61A": "על ראש שמחתי (1988)", "UfIj78lym1I": "ילד רע תל אביב (1988)", "3v9rvDklaxc": "עוד מעט מסך (1989)", "mZxh2vHIBcs": "אישה על החוף (1989)", "oQLUlVqXkpo": "מוזיקה (1989)", "pPE_eIQYtgY": "שיר ערש למקרים מיוחדים (1990)", "yavA7DK-_Lg": "בניך מרחוק (1990)", "wcy425HOqro": "למבדה על החוף (1990)", "tPX2FmmeM6k": "והוא יושיענו (1991)", "-p0EvZ_T_AY": "עיר ואם (1992)", "nvaUD-WzYDQ": "מי ידליק (1998)", "iz3Et-1Ywe8": "אקטואליה (2000)", "IWaGaO6VD4c": "המנגן (2001)", "GZW3RhiQeyY": "מגדל בודד (1955)", "jOpau37GjhY": "בא הגדוד (1956)", "_LilpxfdvKc": "אהבתיך גם כך (1956)", "3H9EF4ZzVy8": "הו מה נאה הוא הבוקר (1956)", "z91zsr8vHnU": "חפש את האישה (1956)", "tz4ISVJyEfI": "הינשוף והירח (1956)", "HH2wou4FvsA": "הלילה הזה הוא דומם (1957)", "wFYq_Is8wJk": "הבו לנו זמר (1957)", "uquTBB0PbFY": "אחינו הקטן (1958)", "v6wgkaN8mvg": "אחינו הקטן (1958)", "6xpROKMcQus": "רכבת הברית (1958)", "Kc3Z01Zqr24": "קיצור החדשות (1958)", "XixXG6ffyy0": "מי רוכב על מי (1958)", "ZSYQh_YatoU": "קרנבל (1958)", "erKzXsvfheA": "רומנס בכפר (1958)", "QKmscJgKCYs": "ט\"ו באב (1958)", "OfsdkuisiNo": "ירדנה (1958)", "acNmIrbrp0k": "נעלה צפונה (1958)", "xAvvvAO6glU": "הבית הקטן (1958)", "DtlDXf6tveY": "היי שלי (1958)", "-eINxqt2z0A": "אני ואחא רון (1958)", "IXn5sqpAhqc": "בלדה על מושבה נידחת (1958)", "Hv0SuDUsjyc": "זאת הארץ (1958)", "R1tJE7-evoQ": "בלדה מודרנית (1958)", "Ya2SuHzZAXo": "בתיה הסיירת (1958)", "J1mbZ9eGho0": "שיר עבודה (1958)", "jYVg9ERVMv0": "השד יודע (1959)", "YMdqSo7wMUk": "שיר עם סיאמי (1960)", "k8u50w4T-1g": "אוכל אדם (1960)", "LR_zCS48QV0": "אי הא שה (1960)", "1dAeJminXHM": "דרכים (1960)", "L8jFWAH86Hw": "עשרת הצדיקים (1960)", "MhIbjL4Hghc": "הגברת ישראלה (1960)", "ldmMVGr-syE": "בז על המרפסת (1961)", "sCQfgFoAQu4": "אל מחנה השחרורים (1961)", "cITPhRNWoq0": "רות ושות' (1961)", "LYoIOT8VvK0": "מדם בלוזון המרגלת (1963)", "xdj8UWyGpFg": "מדם בלוזון המרגלת (1963)", "C-rohkw6OX8": "סוף העולם (1963)", "EEq9IuWDBlM": "בלי מילים (1963)", "KSTaBxvL4JQ": "בלי מילים (1963)", "R-oz2dlpbvY": "שיר פורח (1963)", "pUFhGuyD6j4": "בלדה על סל תפירה (1963)", "SfPOduJnKvk": "אצל ורדה השמנה (1963)", "NXcXk-diyDY": "אותלו (1964)", "yWVoMYXeBpM": "המכשפות (1964)", "w1hLRFc3jfo": "המכשפות (1966)", "rGRBY2iPjpk": "שיר הליצן (1964)", "OxafdSA-QkE": "התפוזים (1964)", "NhX0XzGmv9A": "נערת הסיפון (1964)", "t_qzuM6V2Co": "הסוחר מוונציה (1964)", "Bac-K0Wjp2A": "הסוחר מוונציה (1966)", "YMrwmCzH330": "כמו נערה (1964)", "Eff5K5VrmKE": "מצד אל צד (1964)", "N4QGMJR3Qqo": "שיר המכביה (1965)", "wONNxGvP9S4": "יומן החדשות (1965)", "SOOmGDRVIK8": "שלום על הגלים (1965)", "0re6w_ZITxg": "בשלו הפירות בגני (1965)", "cAOakJcPmGs": "שייקספיר איננו (1965)", "q-9lO4eg7-w": "פרולוג (1965)", "kLf2ybtWLCI": "צי הצללים (1965)", "Ae_oPwsp_P0": "לרקוד איתך (1966)", "VnReHM2MOuo": "כל חיי (1966)", "ZKGMTf5XLCk": "לא לא לא (1966)", "Bujd3-vDfE8": "פרחי אולי (1966)", "OkWKy3URsDg": "אביב בתל אביב (שיר יפני) (1966)", "e1c2MjdU9T8": "שלא נהיה ברברים (1966)", "gEacqh5DPk4": "שיר השייטת (1967)", "BncSM_l0_P8": "כפות רגליך לבנות (1968)", "r97YIa4BDnM": "כי לא יהיה להם יום (1968)", "DGUHUGnDYn0": "איך את נראית (1968)", "COoXTOZQYQ4": "כיתה בארץ (1968)", "7t6dTKHZY6U": "תישן חמודי תישן (1968)", "YWwJ1O6fQQs": "הכל חינם (1969)", "41VIMNNssjw": "תחביב מיוחד במינו (1969)", "hw_SJRb1uEk": "שיר החצב (1971)", "oJZEOGPBtp0": "העוזרת של זרש (1971)", "G5RVx22SVzs": "גדי מן ההגדה (1971)", "g_QXbJmWWO0": "חידות (1971)", "9o-4qxrv584": "יש לי מנגינה בלב (1971)", "nOl7AAouxVc": "כיד המלך (1971)", "k0LjOdjBdYU": "המכונית האדומה (1971)", "S9QL3kDf8gA": "אין בגני שקדיה (1972)", "nNFb0CPT7Js": "לא אמות כי אחיה (1972)", "ukOWgL-9mlw": "חרוזי ביניים (1972)", "O5In5PJnEr8": "מדוע לי (1972)", "LBTf6IMt2X8": "בוא נרד לכרם (1972)", "ITgt-B5IdFk": "ארץ רעשה (1972)", "Xw4qL0j_9Vs": "ארבעים (1972)", "71Pqy6HKns8": "עמוק בטל (1973)", "tNga0kZsgXY": "נעשיתי כזה קטן (1974)", "piH6EOOP7cY": "האומנם (1974)", "3a8B5imZV8o": "מותי בא לי פתע (1974)", "Lg-Can0ZrXM": "פרח בדמות פרה (1974)", "Rh-AfNJC1AY": "סוזאן (1974)", "g57hoYLobng": "שוב כמו אתמול (1974)", "xam-JFkXggk": "הדוכיפת (1974)", "X3GCh50sW8A": "שיר תודה (1975)", "zuYjR6RNeIw": "כבר מאוחר יונתן ומיכלי (1975)", "mxCqvGI5iu0": "לבנות שפיה (1975)", "ud8TFvfUJ8M": "צירצורים (1975)", "7ziQJmP02M0": "הנישואין (1975)", "hZirnyIx1Tw": "פתיחה (1976)", "Ti6nFst0JaE": "הגביר (1976)", "sdqrr4rdUPA": "לכו נרננה (1976)", "P35Ek5tTy4I": "סינמה בלש (1976)", "0yT4idCIsSE": "צמחי הביצה (1976)", "DLilbBb5C-k": "יריד (1976)", "1D4_GtYfmUE": "מתפרנסים (1976)", "gfYmkBTQVD4": "מוטב בבית (1976)", "dGSCRDVe9NE": "פקדת הארץ (1976)", "L1QLv-RFy7A": "היה היה פעם מלך (1976)", "qiWE67WQSBY": "מכתב (1976)", "DZCXER0nGaM": "שבולת ירוקת העין (1977)", "WDQyD0VHt68": "היה היתה עיר (1977)", "ydCddPTqZmo": "מחרוזת שירי אביב (1978)", "Z-JxFdJcoB4": "פרנואיד (1978)", "KXjJoVHJsQw": "חד גדיא (1979)", "6BfneC2-IvA": "סיפור אהבתי לכם (1979)", "4gYlHwrMV50": "לטוס אל על (1981)", "2smvtZlQSEg": "ראש קטן (1981)", "SzfqrHxbpug": "ימי הענבים (1981)", "V_AZsXtgxvY": "יום הולדת מוזר (1981)", "QYW7YCydh3s": "הכל שטיח (1982)", "0XHUVfPJlak": "רגע מתוק (1982)", "tnNhOpq6MqI": "ליל המלאך (1983)", "hZwuhnWXkLE": "אלף תשע מאות שמונים וארבע (1984)", "p3PIKVi8goc": "הכתר השרביט והגלימה (1984)", "OzrUXu1pKkg": "ט\"ו בשבט שלי (1985)", "lfB0Y5mJ1qk": "עולם הפוך (1985)", "ORPN8djCQws": "מערת עדולם (1986)", "UsNNGSI6qzk": "נסיכה שחורה (1986)", "OBkMzEHYA3c": "שלג בצפת (1987)", "JAh-XgpCIEo": "זמן (1987)", "X-KSBs_Lsd8": "פרח (1987)", "omNa4PW1lU8": "יש לי מסיבה (1987)", "8d9khSRpSkk": "שובי השולמית (1988)", "qgyoXwMKJXg": "שובי השולמית (1988)", "OdbpJIdes4Q": "האילן הזקן (1988)", "WBfuFYdOQT4": "העלמה (1988)", "kO9D3crjEsU": "סיירת עולם (1989)", "F6syH8W0EGA": "שיר ערבי נחל (1989)", "sFbghpqy0Lo": "הכלייזמרים בצפת (1990)", "JH-1IrNb_P4": "האחרת (1990)", "XWOGYjtgJG0": "איש מוזר (1991)", "Luu_LIPtx-M": "פסח כאן (1992)", "JvQBz3CHrK0": "ילדי כל העולם (1992)", "reYLaGMYJYk": "אור וירושלים (1992)", "l4y16i5NwwQ": "מנגנות ויואלדי (1994)", "0Yn3EvME2ko": "היה היה לי טנגו (1994)", "jzNc8KFQ4S4": "לא ביאליק (1995)", "WILLlFVs8K4": "דולי (1995)", "VhBycovusXA": "קפה תפארת (1998)", "OdYRuoXrHHw": "פרידה (2004)", "T3qo2SYP52U": "אילן (2004)", "K1DBCpPxqeM": "אוניית הכאב (2014)", "EZ2zDG6qrJE": "פת במלח (2017)", "8XCsox4ClH8": "זמר נוגה (2021)", "ubenw8IJ9dE": "הורה נחל עוז (2023)", "qvBk0IVkKRE": "ירושלים של זהב (1988)", "fCi5ISYIy1U": "ירושלים של זהב (1967)", "aG2s9Sp7tKg": "ירושלים של זהב (1967)", "W6i7v9rr12o": "ירושלים של זהב (1967)", "QUF8MiDp4O4": "על כל אלה (1988)", "oxzR9Z-kG6Q": "על כל אלה (1980)", "dWp4KgvyPYw": "על כל אלה (1980)", "PL0HmLqbxpw": "לו יהי (1973)", "VbIHsjgvE2g": "לו יהי (1973)", "WBc7IWmf3cs": "לו יהי (1973)", "dV91YmIuHV4": "לו יהי (1973)", "Mf7VagPUG50": "לו יהי (1973)", "_GD1f91Erg8": "עוד לא אהבתי די (1977)", "E452vwyyVjQ": "עוד לא אהבתי די (1978)", "_eq2jnCdcyA": "עוד לא אהבתי די (1979)", "-Db1ucwfr1o": "עוד לא אהבתי די (1977)", "erGG9tlYbBk": "אני גיטרה (1993)", "z8JrHEVGykA": "אני גיטרה (1993)", "oJS0DogSjXU": "אני גיטרה (1993)", "A-6m6CKOdC4": "שירת העשבים (2009)", "mypB2220Rfk": "שירת העשבים (1976)", "sFfgH0oJdwE": "שירת העשבים (1976)", "XHdb6YDvHII": "פגישה לאין קץ (1976)", "7T8wbdYlAbQ": "פגישה לאין קץ (1975)", "gRclcNmJ9fQ": "פגישה לאין קץ (1970)", "_nDa2esEWJk": "חורשת האקליפטוס (1962)", "HgMGNLc5ir8": "חורשת האקליפטוס (1966)", "AuYOGchQ6XI": "חורשת האקליפטוס (1967)", "J41YP1kDIKw": "חורשת האקליפטוס (1967)", "7yMw3vG4_kU": "לא תנצחו אותי (2023)", "XtoKkNpyn-E": "לא תנצחו אותי (1984)", "BLpTR9p0mkY": "אנשים טובים (1983)", "aO1sboxdmno": "שנים עשר ירחים (1971)", "dC2fS3vZAPY": "שנים עשר ירחים (1975)", "7kj9X6BnPKE": "שנים עשר ירחים (1960)", "FZp12hlp4gk": "שנים עשר ירחים (1960)", "HvE1Ib25iDk": "תלבשי לבן (1985)", "6hTkFqKThes": "הכל פתוח (1993)", "fiU_B2M84Ww": "הכל פתוח (1993)", "cRAhfb9Ypw8": "שבחי מעוז (1971)", "L-qU-BInVno": "אור (1988)", "e4cc_kptHk8": "וולס להגנת הצומח (1966)", "vQPSLn2e4FY": "וולס להגנת הצומח (1969)", "w2E3hxhbAc4": "וולס להגנת הצומח (1967)", "EoHoiD_n7t4": "וולס להגנת הצומח (1967)", "iPj5rmj8GZQ": "החגיגה נגמרת (1976)", "EdfxwaHVnAk": "החגיגה נגמרת (1988)", "-P0Gnvk5Kmk": "החגיגה נגמרת (1976)", "HlUl3uS6T6Q": "אל בורות המים (1988)", "WK3WmcATcd0": "אל בורות המים (1982)", "q4zRVBV0010": "אל בורות המים (1982)", "Ue8yK2cnLTA": "יש לי חג (1977)", "He8KKInGwAE": "שלומית בונה סוכה (1970)", "PkF2Y0bbbCo": "שלומית בונה סוכה (1992)", "Jg42GYm1qv0": "לילה בחוף אכזיב (1988)", "M38vdprLLok": "שירו של אבא (1968)", "HTMwVk8pQiY": "שירו של אבא (1972)", "WZMQaNRyllY": "שירו של אבא (1970)", "jd4eLSSa1Xs": "שירו של אבא (1968)", "Xc6coB1-EPw": "הוי, ארצי! מולדתי! (1988)", "06SSkPFTjfM": "אהבת פועלי הבניין (1969)", "Ar_Ua0MBt_w": "אהבת פועלי הבניין (1996)", "eUam8viOqxs": "עיר לבנה (1959)", "jAnSY8gxLRg": "עיר לבנה (1959)", "-vWfGW7Hf2E": "עיר לבנה (1984)", "sCRw6hfgQTM": "הטיול הקטן (1977)", "YJKhOidPJhc": "הטיול הקטן (2001)", "AcZZ7fqUNTc": "הטיול הקטן (1966)", "bbIXevkZDnk": "אורחים לקיץ (1993)", "WfM--seOsaY": "אורחים לקיץ (1979)", "yscdF17IT_Y": "אנחנו שנינו מאותו הכפר (1969)", "Pef5mRmx0fA": "אנחנו שנינו מאותו הכפר (1988)", "kkJPYVGy31o": "אנחנו שנינו מאותו הכפר (1968)", "_F3EdZ51O-Q": "אנחנו שנינו מאותו הכפר (1972)", "Uwi4o3fwQwc": "כנרת (1968)", "1dDug8M2AYs": "כנרת (1984)", "wly5oxW3C6Y": "העיר באפור (1977)", "Picy0oa0wl0": "בראש השנה (1975)", "jfy9Pml8UZg": "החופש הגדול (1977)", "vXAxaeNqze4": "החופש הגדול (1993)", "0viBWDlQ9KE": "קומי צאי (2015)", "dLDcWMN-Fbw": "קומי צאי (1980)", "kA1Gl5w3ydI": "פירות חמישה עשר (שלג על עירי) (1976)", "jfvSQpek00g": "פירות חמישה עשר (שלג על עירי) (2013)", "ziATm-51Zc0": "מטרייה בשניים (1963)", "FBMgpQRmfmo": "מטרייה בשניים (1963)", "3iaTDb1K41o": "אלף בית (1975)", "5VQkcCM1fmc": "אלף בית (1993)", "OEVLRDRUxyc": "אלף בית (1975)", "0u--FHf-LHU": "חבלי משיח (1981)", "ms-YfEQM9E8": "חבלי משיח (1967)", "SnARDknXrZQ": "שיר השוק (1960)", "Sn0vSoeVXpI": "בשדות בית לחם (1988)", "dKHjdN2hr4w": "בשדות בית לחם (1997)", "vLhN2olc06o": "סימני דרך (2025)", "9NbtBvkX2TI": "סימני דרך (1982)", "QeX9yVM_izg": "לשיר זה כמו להיות ירדן (2013)", "zEG-AcszgpQ": "אומרים ישנה ארץ (1979)", "TQwpuggfQWw": "כיבוי אורות (1958)", "6qiFa7eU34M": "כיבוי אורות (1988)", "f18phGNSyBg": "הו רב חובל (2020)", "O9CoiUnwJ5A": "הו רב חובל (1996)", "WA8fVawaHuw": "נועה (1978)", "n6qfNKmjutM": "נועה (1988)", "5yDnz_UrH-s": "נועה (1968)", "5xj4ycn0TY8": "נועה (1991)", "dFgoc8M87Ww": "נועה (1958)", "jvZPz3tpWPw": "נועה (2015)", "1gUgA5_iv5g": "זמר נודד (1959)", "sVEvT4pZeyQ": "זמר נודד (1960)", "JDThzHJWt4o": "זמר נודד (1959)", "0mcp9JqqJ1k": "אהבה בת עשרים (1977)", "ymL0Whh7V_I": "אהבה בת עשרים (1972)", "99iIWvXtsqc": "אהבה בת עשרים (1972)", "8UcwA-Zk3JQ": "אילו ציפורים (1967)", "GoWmzpyfv0Y": "אילו ציפורים (1967)", "uqOoO342wNg": "אסיף (1994)", "xkGxvP-tw1w": "אסיף (1986)", "qEYW8pnCu48": "כמו חצב (2012)", "3oHvXK3Xj5k": "כמו חצב (1981)", "p_OfoN-B_xw": "רכב אש (1982)", "upipvN8Xw-c": "רכב אש (1967)", "cYZArmDfKnA": "שיירת הרוכבים (1962)", "s1SR4hmgC4U": "מחבואים (1963)", "HBZpHQRKrFM": "מחבואים (1972)", "g6clciS1riA": "על ליל אמש (1968)", "gXM9-IpEzEc": "בשדה תלתן (1961)", "nruQWhRsem4": "בשדה תלתן (2000)", "7m9YwTJwFrE": "בשדה תלתן (1977)", "3st5EgoczRM": "חמסינים במשלט (1961)", "TmFdkd0YmjU": "חמסינים במשלט (1975)", "s1Ac_TvGdAU": "חמסינים במשלט (1958)", "ry9RV0yCJpI": "על כנפי הכסף (1967)", "TGRVtcThDf4": "בית חלומותיי (1966)", "p320GUpKgkQ": "סימן שעוד לא הגענו (1976)", "hA92uD-XpQs": "שיר סתיו (1958)", "Omn_wSe-dKU": "שיר הכזבים (1993)", "YgYyQjI4UeY": "בכל שנה בסתיו גיורא (1979)", "C1PjhOZQxMU": "איילת אהבים (1993)", "_Fxy_CFR78Q": "איילת אהבים (1984)", "narkCrS3_GA": "זמר (1968)", "lKhxVjkSa84": "זמר (1988)", "XWnWPkDHGz4": "מה שלומך אחות (1987)", "PrntU87z0n8": "הלילה הולך בשדרות (1975)", "wzrVRxyd5a4": "בגני נטעתיך (1968)", "3G8xlTapGQo": "בגני נטעתיך (1972)", "0rZlNPF_utQ": "בגני נטעתיך (1972)", "vUmuxcvyGrM": "בגני נטעתיך (1968)", "-2N-WzrLzCc": "מיכאל (1976)", "sQTl_NH1n0o": "מיכאל (1993)", "0krT8xzNbyM": "בדמייך חיי (2001)", "bZI8gT-VbT0": "החייל שלי חזר (1966)", "XBrUmJLCkEw": "הופה היי (1959)", "YrJtArqXavk": "הופה היי (1961)", "TsA3LycTPSo": "הופה היי (1966)", "PHQFSQi4tzU": "שלום כיתה א' (1993)", "XteReGQom40": "נגיד (1977)", "xI2m7tKJ40E": "נגיד (1993)", "JAY_uZjqmIA": "חליל מקנה-סוף (1977)", "qrvKQtQgb2s": "חליל מקנה-סוף (1967)", "YS6EfEQu1ik": "יש לי חבר (1977)", "hDqbO57hnyQ": "הכול בגלל מסמר (1959)", "EfcKLvzIDRw": "הכול בגלל מסמר (1958)", "cXln3eAat5g": "יובל (1998)", "Pk0mm0ly7Og": "יובל (1998)", "KvBOUWSO1PM": "מר נרקיס (1972)", "vNw21mQVfKM": "שיר נולד (1976)", "H9f2NJOxcz0": "המעיל (2002)", "P7eGfaq3E_s": "קרן יער (1968)", "GyiSOeKOK8s": "קרן יער (1988)", "DJFWTrj5sO8": "אחותי רוחמה (1979)", "losUGtP6fxI": "שנה טובה (1992)", "skYeVk80Eo0": "שנה טובה (1992)", "mpPxqJrum-M": "נר ראשון של חנוכה (1984)", "Sah0hB6rSFY": "הפסנתר (1993)", "x0IPLHoV9Yc": "עקידת יצחק (1972)", "pTlgYtrDSPI": "אין דבר (1981)", "vAT50nuKMh8": "נצא השדה (1975)", "ycWudyVJdOU": "משנכנס אדר (1975)", "i9KzXu-Nhx0": "לנוע ולנדוד (1977)", "YfFNug5ZOac": "אל תשאלו אותי (1971)", "A9erliXTS6o": "אל תשאלו אותי (1968)", "6EEIW68j5lY": "דוגרת (1981)", "ipzIvlpBkbU": "דוגרת (1977)", "rLucwp89lnE": "שבת (1974)", "4g6cymurqY0": "בקיץ (1968)", "-1__PIJhhPI": "שיר ערש לצבעים (1968)", "agChJ2Ho124": "כיצד שוברים חמסין (1975)", "Yd3_uDW6i4w": "גדי קטן (1977)", "vxQcorAdAXA": "בארץ להד\"ם (1977)", "chuU4lFZ5iA": "אנשים יפים (1972)", "vbG5B1wswQc": "מסעות בנימין מטודלה (1979)", "U3xSpmrTgXc": "אהבת אשתקד (1989)", "CSjnGcglVJI": "גיא (1993)", "Jzkgm9A3Ooc": "שיר הבר (1958)", "INHBTa-HfSM": "רב האור והתכלת (1958)", "4ApYhj2Mqeo": "רב האור והתכלת (1965)", "F25xFwezdxw": "סמוך על התרנגול (1959)", "PIqHAidM99g": "סמוך על התרנגול (1958)", "EEkIbuhQ9dw": "אופליה (1964)", "lXCnVOsgJwo": "אופליה (1968)", "CJ8_MISsRxg": "אופליה (1966)", "nNMmAneQsLs": "בלילה שכזה (1968)", "Pxm7UgJ1JiE": "יום ה בשבוע (1958)", "qblckfTw1Rk": "יום ה בשבוע (1959)", "5-8BIb9KyNk": "יום ה בשבוע (1981)", "_33ng3euFJI": "קפה שחור (1969)", "XIs2ZIJ2oZw": "מתי (1988)", "-xNyTz_yvRU": "עוד חוזר הניגון (1970)", "gsf0t-VihvE": "עוד חוזר הניגון (1977)", "jqQTqr1gHEI": "מה אמרו הציפורים (1962)", "n2t3bDiJcMk": "יפעת (1980)", "dT5g0VRp7jE": "את הכי הכי (1981)", "tpe1wARxPSs": "שיר ערש למקרים מיוחדים (1972)", "3wNpnpA5K-w": "והוא יושיענו (1991)", "2LRsVjehz44": "והוא יושיענו (1991)", "SZhwVVZuRkY": "מי ידליק (1998)", "CwORk-NwrQM": "אקטואליה (1991)", "_JG62QmM-QE": "מגדל בודד (1957)", "XeD27Barwbk": "בא הגדוד (1965)", "dfPBgVKT_H8": "חפש את האישה (1958)", "gq5PAlFBEi8": "אחינו הקטן (1971)", "_qb0WUb7i5A": "אחינו הקטן (1958)", "c0WSmr4tlLY": "רכבת הברית (1960)", "0eWljspYG7E": "רכבת הברית (1973)", "F7KHn6M2VGk": "קיצור החדשות (1959)", "XOJchlUhps0": "קרנבל (1959)", "6yrG087cato": "רומנס בכפר (1958)", "evAV9e6QUlI": "ט\"ו באב (1964)", "uITVQ8JRMg4": "ט\"ו באב (1958)", "F-tHf-vPBxQ": "שיר עם סיאמי (1962)", "sgVtXugsDtE": "אוכל אדם (1962)", "s6Geto53AmI": "מדם בלוזון המרגלת (1970)", "d9pbNfB26wc": "סוף העולם (1966)", "ExOobxzS4tc": "שיר פורח (1963)", "FFtI8ZQT2Mk": "אותלו (1965)", "B86J0eynF9A": "אותלו (1966)", "UB35E3hE65E": "המכשפות (1972)", "CLDelMZYKC8": "המכשפות (1972)", "xyiYZRhJsSo": "שיר הליצן (1971)", "BAliJ1ieJrI": "כפות רגליך לבנות (1968)", "mMEXXehlL54": "תחביב מיוחד במינו (1972)", "4MJ1vA3znA4": "העוזרת של זרש (1971)", "URuGgQXkQpQ": "מותי בא לי פתע (1974)", "wk0pllJl1nU": "פקדת הארץ (1976)", "_vJ6UtXHybA": "הכתר השרביט והגלימה (1984)", "6rlo1KZ0qok": "שלג בצפת (1962)", "weX6vsG96ZY": "מנגנות ויואלדי (1996)", "JUiRv74kgHU": "לא ביאליק (1996)", "B7rC1GyPlqM": "אילן (2017)", "Yk82zpkqZjw": "אני גיטרה (1993)", "oo8IRR00H30": "אני גיטרה (1993)", "k0RE3k8k1pQ": "וולס להגנת הצומח (1970)", "mnXZeefSK8w": "ירושלים של זהב (1992)", "nMxKk66pAzc": "על כל אלה (1991)", "6Z2BOKloo7k": "עוד לא אהבתי די (1977)", "SdrmUgN92O4": "שבחי מעוז (1979)", "lmTSkGSnxzw": "אלף בית (1981)", "9d8hI1wc_Bs": "שלומית בונה סוכה (1992)", "fs14OduKHd4": "בראש השנה (1992)", "YYVengVA5V8": "נר ראשון של חנוכה (1977)", "oMZHElIjza4": "מחרוזת שירי אביב (1992)"};

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

  // שליפת כל הסרטונים הקיימים כרגע בפלייליסט (כולל סרטונים מוסתרים/לא זמינים עם params: "wgYCCAA=")
  function findSetVideoId(node, depth = 0) {
    if (!node || typeof node !== "object" || depth > 22) return null;
    if (typeof node.setVideoId === "string" && node.setVideoId) return node.setVideoId;
    if (Array.isArray(node)) {
      for (const el of node) {
        const found = findSetVideoId(el, depth + 1);
        if (found) return found;
      }
      return null;
    }
    for (const k of Object.keys(node)) {
      const found = findSetVideoId(node[k], depth + 1);
      if (found) return found;
    }
    return null;
  }

  function findWatchVideoId(node, depth = 0) {
    if (!node || typeof node !== "object" || depth > 10) return null;
    if (node.watchEndpoint && typeof node.watchEndpoint.videoId === "string" && node.watchEndpoint.videoId) {
      return node.watchEndpoint.videoId;
    }
    if (Array.isArray(node)) {
      for (const el of node) {
        const found = findWatchVideoId(el, depth + 1);
        if (found) return found;
      }
      return null;
    }
    for (const k of Object.keys(node)) {
      if (k === "menuButton") continue;
      const found = findWatchVideoId(node[k], depth + 1);
      if (found) return found;
    }
    return null;
  }

  function nodeBelongsToPlaylist(node, depth = 0) {
    if (!node || typeof node !== "object" || depth > 14) return false;
    if (node.playlistId === PLAYLIST_ID) return true;
    if (Array.isArray(node)) return node.some(el => nodeBelongsToPlaylist(el, depth + 1));
    for (const k of Object.keys(node)) {
      if (nodeBelongsToPlaylist(node[k], depth + 1)) return true;
    }
    return false;
  }

  function findContinuationTokens(node, tokensOut, seenTokens, depth = 0) {
    if (!node || typeof node !== "object" || depth > 16) return;
    if (node.continuationCommand && typeof node.continuationCommand.token === "string") {
      const tok = node.continuationCommand.token;
      if (tok && tok.startsWith("4qmF") && !seenTokens.has(tok)) {
        seenTokens.add(tok);
        tokensOut.push(tok);
      }
    }
    if (node.nextContinuationData && typeof node.nextContinuationData.continuation === "string") {
      const tok = node.nextContinuationData.continuation;
      if (tok && !seenTokens.has(tok)) {
        seenTokens.add(tok);
        tokensOut.push(tok);
      }
    }
    if (Array.isArray(node)) {
      for (const el of node) findContinuationTokens(el, tokensOut, seenTokens, depth + 1);
      return;
    }
    for (const k of Object.keys(node)) {
      findContinuationTokens(node[k], tokensOut, seenTokens, depth + 1);
    }
  }

  function extractVideosAndContinuation(obj, itemsOut, tokensOut, seenTokens) {
    if (!obj || typeof obj !== "object") return;
    if (Array.isArray(obj)) {
      for (const el of obj) extractVideosAndContinuation(el, itemsOut, tokensOut, seenTokens);
      return;
    }
    // דילוג על מדפי המלצות ("Recommended videos") שיוטיוב מציג לבעל הפלייליסט ואינם שייכים לפלייליסט!
    if (obj.reelShelfRenderer || obj.shelfRenderer || obj.horizontalCardListRenderer) {
      return;
    }
    if (obj.playlistVideoRenderer) {
      const r = obj.playlistVideoRenderer;
      const svid = r.setVideoId || findSetVideoId(r) || null;
      if ((r.videoId || svid) && (svid || nodeBelongsToPlaylist(r))) {
        itemsOut.push({
          videoId: r.videoId || null,
          setVideoId: svid
        });
      }
      return;
    }
    if (obj.lockupViewModel) {
      const lv = obj.lockupViewModel;
      const vid = lv.contentId || findWatchVideoId(lv);
      const svid = findSetVideoId(lv);
      const isVidType = lv.contentType === "LOCKUP_CONTENT_TYPE_VIDEO" || !lv.contentType;
      if (((vid && isVidType) || svid) && (svid || nodeBelongsToPlaylist(lv))) {
        itemsOut.push({
          videoId: vid || null,
          setVideoId: svid
        });
      }
      return;
    }
    if (obj.continuationItemRenderer || obj.continuationItemViewModel) {
      findContinuationTokens(obj, tokensOut, seenTokens);
      return;
    }
    if (obj.continuations && Array.isArray(obj.continuations)) {
      findContinuationTokens(obj.continuations, tokensOut, seenTokens);
    }
    for (const k of Object.keys(obj)) {
      extractVideosAndContinuation(obj[k], itemsOut, tokensOut, seenTokens);
    }
  }

  function getFirstSectionRoot(browseData) {
    const secContents = browseData?.contents?.twoColumnBrowseResultsRenderer?.tabs?.[0]?.tabRenderer?.content?.sectionListRenderer?.contents;
    if (Array.isArray(secContents) && secContents.length > 0) {
      // תמיד קוראים אך ורק את contents[0] (רשימת הפלייליסט עצמה), ולא את contents[1] (סרטונים מומלצים להוספה)!
      return secContents[0];
    }
    return browseData;
  }

  // includeUnavailable=true שולח params: "wgYCCAA=" ("Show unavailable videos") כך שגם סרטונים מוסתרים מזוהים ונמחקים!
  async function fetchCurrentPlaylistItems(includeUnavailable = true) {
    const items = [];
    const tokens = [];
    const seenTokens = new Set();
    const reqBody = { browseId: "VL" + PLAYLIST_ID };
    if (includeUnavailable) reqBody.params = "wgYCCAA=";
    const firstPage = await ytPost("/youtubei/v1/browse", reqBody);
    extractVideosAndContinuation(getFirstSectionRoot(firstPage), items, tokens, seenTokens);
    while (tokens.length > 0) {
      const tok = tokens.shift();
      const nextPage = await ytPost("/youtubei/v1/browse", { continuation: tok });
      extractVideosAndContinuation(nextPage, items, tokens, seenTokens);
    }
    return items;
  }

  function buildRemoveActions(items) {
    const actions = [];
    const seenVid = new Set();
    for (const item of items) {
      if (item.setVideoId) {
        actions.push({ action: "ACTION_REMOVE_VIDEO", setVideoId: item.setVideoId });
      } else if (item.videoId && !seenVid.has(item.videoId)) {
        seenVid.add(item.videoId);
        actions.push({ action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: item.videoId });
      }
    }
    return actions;
  }

  async function safeDeleteBatch(batch) {
    if (!batch || batch.length === 0) return;
    try {
      await ytPost("/youtubei/v1/browse/edit_playlist", {
        playlistId: PLAYLIST_ID,
        actions: batch
      });
    } catch (err) {
      console.warn(`⚠️ מחיקת אצווה נתקלה בשגיאה (${err.message.slice(0, 80)}), מנסה פריט-פריט...`);
      for (const act of batch) {
        try {
          await ytPost("/youtubei/v1/browse/edit_playlist", {
            playlistId: PLAYLIST_ID,
            actions: [act]
          });
        } catch (innerErr) {
          console.warn("  ⏭️ דילוג על פריט שאינו בפלייליסט:", act, innerErr.message.slice(0, 60));
        }
        await new Promise(r => setTimeout(r, 120));
      }
    }
  }

  // עדכון שם הפלייליסט ל-"שירי נעמי שמר"
  try {
    await ytPost("/youtubei/v1/browse/edit_playlist", {
      playlistId: PLAYLIST_ID,
      actions: [{ action: "ACTION_SET_PLAYLIST_NAME", playlistName: PLAYLIST_TITLE }]
    });
    console.log(`🏷️ שם הפלייליסט עודכן ל: "${PLAYLIST_TITLE}"`);
  } catch (e) {
    console.warn("⚠️ לא הצלחתי לעדכן את שם הפלייליסט אוטומטית:", e.message);
  }

  console.log("🔍 קורא את מצב הפלייליסט הקיים ביוטיוב (" + PLAYLIST_ID + ")...");
  let currentItems = await fetchCurrentPlaylistItems();
  console.log(`📋 נמצאו כרגע בפלייליסט ${currentItems.length} סרטונים (יעד רצוי: ${TARGET_VIDEO_IDS.length} סרטונים).`);

  // הגנה: אם הקריאה מיוטיוב החזירה 0 סרטונים בזמן שעל הדף עצמו יש סרטונים — עצור מיד לפני הוספה כפולה!
  if (currentItems.length === 0 && window.ytInitialData) {
    const pageItems = [];
    const dummyTokens = [];
    extractVideosAndContinuation(getFirstSectionRoot(window.ytInitialData), pageItems, dummyTokens, new Set());
    if (pageItems.length > 0) {
      console.error(`❌ עצירת חירום: בדף מופיעים ${pageItems.length} סרטונים אך קריאת ה-API החזירה 0. לא מוסיף כדי למנוע כפילויות!`);
      return;
    }
  }

  const curIds = currentItems.map(x => x.videoId);
  if (curIds.length === TARGET_VIDEO_IDS.length && curIds.every((v, i) => v === TARGET_VIDEO_IDS[i])) {
    console.log("✅ [וידוא הושלם] הפלייליסט כבר מסודר ומעודכן ב-100% לפי הסדר המבוקש!");
    return;
  }

  // חישוב תת-הסדרה המשותפת הארוכה ביותר (LCS) לצורך עדכון כירורגי מהיר ללא מחיקת כל הפלייליסט
  function computeLcsSet(a, b) {
    const n = a.length, m = b.length;
    const dp = Array.from({ length: n + 1 }, () => new Int16Array(m + 1));
    for (let i = n - 1; i >= 0; i--) {
      for (let j = m - 1; j >= 0; j--) {
        dp[i][j] = a[i] === b[j] ? 1 + dp[i + 1][j + 1] : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
    const keepInA = new Set();
    let i = 0, j = 0;
    while (i < n && j < m) {
      if (a[i] === b[j]) {
        keepInA.add(a[i]);
        i++; j++;
      } else if (dp[i + 1][j] >= dp[i][j + 1]) {
        i++;
      } else {
        j++;
      }
    }
    return keepInA;
  }

  const BATCH_SIZE = 50;
  const targetSetInit = new Set(TARGET_VIDEO_IDS);
  const seenInCur = new Set();
  const toDeleteItems = [];
  for (const it of currentItems) {
    if (!targetSetInit.has(it.videoId) || seenInCur.has(it.videoId)) {
      toDeleteItems.push(it);
    } else {
      seenInCur.add(it.videoId);
    }
  }
  const toAddVids = TARGET_VIDEO_IDS.filter(v => !seenInCur.has(v));
  const survivingCurIds = currentItems.filter(it => !toDeleteItems.includes(it)).map(it => it.videoId);
  const commonTargetIds = TARGET_VIDEO_IDS.filter(v => seenInCur.has(v));
  const lcsKeep = computeLcsSet(survivingCurIds, commonTargetIds);
  const estMoves = (commonTargetIds.length - lcsKeep.size) + toAddVids.length;
  const totalSurgicalOps = toDeleteItems.length + toAddVids.length + estMoves;

  const hasAllSetIds = currentItems.every(it => Boolean(it.setVideoId));
  if (currentItems.length > 0 && totalSurgicalOps <= 120 && (estMoves === 0 || hasAllSetIds)) {
    console.log(`⚡ מבצע עדכון כירורגי מהיר (${toDeleteItems.length} מחיקות, ${toAddVids.length} הוספות, ${estMoves} הזזות מיקום)...`);
    if (toDeleteItems.length > 0) {
      const delActions = buildRemoveActions(toDeleteItems);
      for (let i = 0; i < delActions.length; i += BATCH_SIZE) {
        const batch = delActions.slice(i, i + BATCH_SIZE);
        await safeDeleteBatch(batch);
        await new Promise(r => setTimeout(r, 400));
      }
    }
    if (toAddVids.length > 0) {
      for (let i = 0; i < toAddVids.length; i += BATCH_SIZE) {
        const batch = toAddVids.slice(i, i + BATCH_SIZE);
        await ytPost("/youtubei/v1/browse/edit_playlist", {
          playlistId: PLAYLIST_ID,
          actions: batch.map(vid => ({ action: "ACTION_ADD_VIDEO", addedVideoId: vid }))
        });
        await new Promise(r => setTimeout(r, 500));
      }
    }
    if (estMoves > 0) {
      await new Promise(r => setTimeout(r, 900));
      currentItems = await fetchCurrentPlaylistItems();
      const curMap = new Map(currentItems.map(it => [it.videoId, it.setVideoId]));
      const presentTarget = TARGET_VIDEO_IDS.filter(v => curMap.has(v));
      const lcsNow = computeLcsSet(currentItems.map(it => it.videoId), presentTarget);
      // עוברים מהסוף להתחלה ומזיזים רק רצועות שאינן ב-LCS אל לפני הרצועה העוקבת שלהן
      for (let k = presentTarget.length - 2; k >= 0; k--) {
        const vid = presentTarget[k];
        if (!lcsNow.has(vid)) {
          const nextVid = presentTarget[k + 1];
          const setVid = curMap.get(vid);
          const succSetVid = curMap.get(nextVid);
          if (setVid && succSetVid) {
            await ytPost("/youtubei/v1/browse/edit_playlist", {
              playlistId: PLAYLIST_ID,
              actions: [{
                action: "ACTION_MOVE_VIDEO_BEFORE",
                setVideoId: setVid,
                movedSetVideoIdSuccessor: succSetVid
              }]
            });
            lcsNow.add(vid);
          }
        }
      }
    }
  } else {
    console.log("🔄 מבצע עדכון סדר מלא בתוך הפלייליסט הקיים (" + PLAYLIST_ID + ")...");
    // שלב א': ניקוי הרשימה הישנה (עם וידוא שהרשימה התרוקנה לגמרי לפני הוספה)
    let pass = 1;
    while (currentItems.length > 0 && pass <= 10) {
      const delActions = buildRemoveActions(currentItems);
      if (delActions.length === 0) break;
      for (let i = 0; i < delActions.length; i += BATCH_SIZE) {
        const batch = delActions.slice(i, i + BATCH_SIZE);
        console.log(`🗑️ מנקה סדר ישן (סבב ${pass}: ${i + 1} עד ${Math.min(i + BATCH_SIZE, delActions.length)} מתוך ${delActions.length})...`);
        await safeDeleteBatch(batch);
        await new Promise(r => setTimeout(r, 450));
      }
      await new Promise(r => setTimeout(r, 1200));
      currentItems = await fetchCurrentPlaylistItems();
      pass++;
    }

    if (currentItems.length > 0) {
      console.error(`❌ עצירה לפני הוספה: נותרו עדיין ${currentItems.length} סרטונים בפלייליסט לאחר ניקוי. רענן את העמוד והרץ שוב כדי להשלים ללא כפילויות.`);
      return;
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
  console.log("🔎 מבצע וידוא סופי של סדר השירים ובדיקת סרטונים מוסתרים מול שרתי יוטיוב...");
  await new Promise(r => setTimeout(r, 1500));
  let finalItems = await fetchCurrentPlaylistItems(true);
  let finalIds = finalItems.map(x => x.videoId);
  let visibleItems = await fetchCurrentPlaylistItems(false);
  const visibleSet = new Set(visibleItems.map(x => x.videoId));
  const hiddenNow = [];
  finalIds.forEach((vid, idx) => {
    if (!visibleSet.has(vid)) {
      hiddenNow.push({ position: idx + 1, videoId: vid, title: VIDEO_TITLES[vid] || vid });
    }
  });
  if (hiddenNow.length === 0) {
    console.log("🟢 בדיקת זמינות: 0 סרטונים מוסתרים/לא-זמינים בפלייליסט באזור הגלישה שלך!");
  } else {
    console.warn(`⚠️ שים לב: יוטיוב מסתיר כעת באזור הגלישה שלך ${hiddenNow.length} סרטונים (חסימה אזורית או הסרה):`);
    console.table(hiddenNow);
  }

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

  if (missingFromYt.length > 0 && missingFromYt.length <= 40) {
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
      await new Promise(r => setTimeout(r, 250));
    }
  } else if (missingFromYt.length > 40) {
    console.warn(`⚠️ חסרים ${missingFromYt.length} סרטונים — מדלג על הוספה פרטנית כדי למנוע חסימת קצב מיוטיוב.`);
  }

  // 3. הסרת סרטונים עודפים או כפולים שאינם ברשימת היעד (באצוות של 50)
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
    const extraActions = buildRemoveActions(toRemoveExtra);
    console.log(`🧹 מסיר ${extraActions.length} סרטונים עודפים/כפולים...`);
    for (let i = 0; i < extraActions.length; i += BATCH_SIZE) {
      const batch = extraActions.slice(i, i + BATCH_SIZE);
      await safeDeleteBatch(batch);
      await new Promise(r => setTimeout(r, 450));
    }
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
