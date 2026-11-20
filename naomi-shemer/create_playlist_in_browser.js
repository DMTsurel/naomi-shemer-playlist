// ============================================================================
// יצירת פלייליסט "שירי נעמי שמר - האוסף המקיף" (705 ביצועים) בחשבון היוטיוב שלך
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com בדפדפן וודא שאתה מחובר לחשבון היוטיוב שלך.
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console של הדפדפן.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// תוך כ-10 שניות הפלייליסט ייווצר וייפתח אוטומטית!
// ============================================================================
(async function createNaomiShemerPlaylist() {
  const VIDEO_IDS = ["IUxt7faTExY", "H8V8yhc2eYI", "9xETAic8buQ", "hBlEx2bIRNI", "KaovY--ET14", "cpp8XENcuBk", "V4QSoLFj-NM", "mw9uiMMvFGk", "jk6lOLldgT4", "Xe4H1sCCAJo", "Zr-iKRNRzQk", "DEKLsquUP34", "TFIrOcriazY", "My9HiZIPsak", "zN2CRXhVJ3o", "bfQeAbF8-4A", "unyzPkoPBEs", "85QDrN6FB8Q", "dwUst6vBhs0", "ryXmue6dutA", "sFB_B3wTXLE", "-T6mxux7wKM", "4_Laz5PQV-Y", "tWs6g7hg0BI", "5Hz8UIWRADU", "BfKQ4bj0JJk", "gTXgnxD6Cuc", "1_dsV0afFgA", "JfJ3DrI7-6w", "NxoJzDVw4cc", "zpFGk2nz_-A", "-4bnvgAYqmo", "MFrjlagc8rE", "AvJZwh25uZ4", "eSmhtnivpvY", "07aL8h1LyJk", "418kExn65Ug", "ei2FcAMuRAw", "oNmwW4s3AuI", "0ypE8NBmyYo", "vrJcb0mauz8", "Zs1s0_fs9EI", "dDXngW-5jV0", "vQjWwS6X7CI", "6OWfRHNgEtg", "2iljNf6XqsA", "fE8xcZiFRO8", "-nzLbN3sFRQ", "5kl6qHnbp9Y", "BnKrb-46CNI", "kF5Lpl7IL6w", "zZHynZGet5g", "URL56lbFmr8", "e9lQpiSO6XM", "2QMxLPxD25g", "7uxKafYsUrU", "_NylGW8syfw", "BgpoI6q79Lw", "0IPY0etp8eE", "pWGF4nqxi9c", "AxnQ3qrsp64", "08Z_uYA9PLc", "XsDAsNDqHW4", "Ce_cSMB0Ri8", "5TZvR7wFlVo", "DdET9qVDfRI", "_DujVVkqqQ0", "neYlxPR8-WA", "ax7p4AggiqY", "zRQLXqjeRoE", "isxLekbAFHw", "4ZFF3v39RD4", "YQc4x6hGSyg", "q3XGUpCCTJs", "Q5N5gxqjDFc", "eCRBb3h6mz8", "9Er1RvAuM7M", "bzl8G_GQJKE", "7PxG0jfZX6k", "2aQJz8v_KkU", "XUR6jL3D6N8", "WFOhRFYM1wM", "QPPugl_l2ak", "mYfdJkb1gqg", "XKbvfLzHms4", "tk3zQs8gDTM", "4HZWNJzXTm4", "Okw-ktcRVr0", "UwhEUsWVdPg", "VCDKtBt4xb4", "jMlzihkguOU", "CeRvSDeJx-I", "8y5KQ8UWi0A", "neNKCSaT1T8", "ZFFJR9iTSuo", "6hhQ_4omcKs", "Gi7-feW4FfE", "FkSHlF212BA", "aKAvYLWF97U", "GgYxh_MoCDA", "06dUzmJF7H0", "gkPyKqEFNSE", "RqHN-so83M4", "OS9uUlfBrbA", "YY8vUjMWzEc", "Xoh_DVe4WcA", "ufIj60iGZqM", "sLvHms2BClA", "H3h-755AwoI", "0ga6HoypSJU", "DATGdPiFqVA", "ZcKAuoZSzWQ", "pKGFC7qoGBA", "D13BJwfsQu8", "l1b8s6ZGXhQ", "l8uDRKHspac", "dYYGjAoIU_E", "FZrRqLdaH5E", "ArRyqOnlQ3k", "_lds9E6qEQg", "z-OpnBf-JNI", "KOecGqpq-f0", "kF_MJiReEn0", "9bfiWAv4HSU", "Y8ob5jdoYBw", "VkgQyNxNQqw", "pjCtGobuuSE", "qpbBemLcsUE", "aDZqwcq7eVI", "B0EO7nYCdu0", "04AcSZS8K3s", "SDCkIuEiWWY", "0XhvBFzatFc", "NWR0K-8lBhU", "MtwqXXIN6Xs", "5v77wNxd8Kw", "AoGcmpu5D4Y", "SgzeIwaaGMU", "T5o_o8lO-1M", "zV4aK_XyPW8", "wO3U1xG7Um0", "EFIwG44Egek", "yzSOpEPUXWw", "2MUXbKJVRZo", "Okj7fK4VSOA", "vVQ0Xmtb9_Q", "CYwiq1Uu5Ng", "OvN5nJ9bn2Y", "E3V70DpK_EI", "NGtt4OBuh2E", "whmUk6hiVE4", "I00dlNJc6BI", "pDLQ_FrzKL4", "p64TXGU2ipM", "2BfY0duzEpE", "7cZaZp3xfDM", "Im8ze1yI8Aw", "BBUtEBZLJFQ", "B7oZ2GPHhEU", "sdlmzqJiT5M", "Ba1W41IDnhI", "P8g0g_IQcjI", "2o1uo7sstSI", "AnWiRbrejHg", "24JJpjDS8QY", "dtbSIHcMWjY", "Ke6iImauSj4", "m58C3mRgm5E", "sKkBNzdlFvE", "dZtHel6cUW8", "Brq81oCuNKc", "SSJdF9cV8iQ", "-7qKw4AIGP4", "V8CR6u84pXU", "_aoBikUYiBY", "pCK483hwY-0", "FQson2Wm0iw", "CEI769yjg4g", "UgXcD55HXzc", "yKAUdNGyVpA", "YtWovd6r0yc", "WxdVdudBKeE", "EikdgimAjd8", "gU6tE4TqExI", "yXzElXsHH38", "ZLzkd2ui6PM", "doXUEtdMaxc", "i9bIVfz1HBw", "wIFDo3qiS9c", "hdskywcJSMo", "bzLl7TH_VxQ", "9aIw7qJAOA4", "sgMLsWRX7SI", "ew9j2OHt8Cw", "VaztQIe75Ns", "KO7lZhbeFDs", "PXL8ltjFDCk", "gpo_GVko6OA", "nz7sT486EYw", "ut3moC4G-QI", "2vq22hm-TnI", "_6La2mK-PqU", "PEamc15DDeY", "Y5aCrfJLjIM", "3YYVsJ9MGZQ", "xypLh9F1IXk", "VsVv0OOIARQ", "bnl-cjqYOwk", "E-jZMuDEvLQ", "Vimcno4QbUw", "E-G-dnLO99U", "cCftnvA1iJo", "KEOx2onVNDs", "Ur53Ai6WISA", "nOa7P6X2I-8", "zUWmMkqQMQg", "t6jXzPCR0NA", "L7_tsGSLGTs", "cD2GgbFD_Yo", "dgC-AI1O_a8", "-rGr-thBmjs", "mtuSxIIZPqg", "cbNuUKAQMsU", "3oB1QegwRqk", "9XgKm2xg3iA", "7IEl35CsSaI", "38jU5bVcNzo", "3iQEC7mO3YY", "me0k188YXNw", "hSaod2F6TA8", "UxWCHV50LoU", "7e6hGajTOaE", "1uRrLed3pZc", "0pdyuulvbzo", "OLQITmFP3Xo", "g-477LqGTr4", "rh0oGPJbf5M", "CMhfrA5uDjE", "UtixqreayIo", "eGrPQv3g9ps", "A1BCQuWuvTE", "2GD7HJfapWM", "oNZG3NUzB3U", "V2eI7l5c3nc", "-dNwuLchpWg", "gkP9-OqJETY", "UeP8K2lXml8", "cV-WsBBOwto", "gRfvDuXwtYI", "VXLKQYTYShc", "61RF4uejHJE", "morcvF-aFsg", "-2f28ACy-Gk", "O4OhUorCxX8", "OFBBD-EuEfA", "6sR4GRdyZZ8", "yEG2trB0IxU", "X0EHaEth0TQ", "s0923q2OCPM", "VeeEHBwsyQw", "chw7OpsTH1A", "cmQ9upI0aG8", "Yd63Irvr-Q0", "mzrn0p-yRSM", "tBL2uGdMMZ4", "Jl0WahK00lU", "sJFfiL_Y1_E", "UOD51gynvJQ", "o9ElrJy3fmk", "d8h9EDhbixA", "ZYTJPE70ifA", "_FhoSjLL61A", "UfIj78lym1I", "3v9rvDklaxc", "mZxh2vHIBcs", "oQLUlVqXkpo", "pPE_eIQYtgY", "yavA7DK-_Lg", "wcy425HOqro", "tPX2FmmeM6k", "-p0EvZ_T_AY", "nvaUD-WzYDQ", "iz3Et-1Ywe8", "IWaGaO6VD4c", "GZW3RhiQeyY", "jOpau37GjhY", "_LilpxfdvKc", "3H9EF4ZzVy8", "z91zsr8vHnU", "tz4ISVJyEfI", "HH2wou4FvsA", "wFYq_Is8wJk", "uquTBB0PbFY", "v6wgkaN8mvg", "6xpROKMcQus", "Kc3Z01Zqr24", "XixXG6ffyy0", "ZSYQh_YatoU", "erKzXsvfheA", "QKmscJgKCYs", "OfsdkuisiNo", "acNmIrbrp0k", "xAvvvAO6glU", "DtlDXf6tveY", "-eINxqt2z0A", "IXn5sqpAhqc", "Hv0SuDUsjyc", "R1tJE7-evoQ", "Ya2SuHzZAXo", "J1mbZ9eGho0", "jYVg9ERVMv0", "YMdqSo7wMUk", "k8u50w4T-1g", "LR_zCS48QV0", "1dAeJminXHM", "L8jFWAH86Hw", "MhIbjL4Hghc", "ldmMVGr-syE", "sCQfgFoAQu4", "cITPhRNWoq0", "LYoIOT8VvK0", "xdj8UWyGpFg", "C-rohkw6OX8", "EEq9IuWDBlM", "KSTaBxvL4JQ", "R-oz2dlpbvY", "pUFhGuyD6j4", "SfPOduJnKvk", "NXcXk-diyDY", "yWVoMYXeBpM", "w1hLRFc3jfo", "rGRBY2iPjpk", "OxafdSA-QkE", "NhX0XzGmv9A", "t_qzuM6V2Co", "Bac-K0Wjp2A", "YMrwmCzH330", "Eff5K5VrmKE", "N4QGMJR3Qqo", "wONNxGvP9S4", "SOOmGDRVIK8", "0re6w_ZITxg", "cAOakJcPmGs", "q-9lO4eg7-w", "kLf2ybtWLCI", "Ae_oPwsp_P0", "VnReHM2MOuo", "ZKGMTf5XLCk", "Bujd3-vDfE8", "OkWKy3URsDg", "e1c2MjdU9T8", "gEacqh5DPk4", "BncSM_l0_P8", "r97YIa4BDnM", "DGUHUGnDYn0", "COoXTOZQYQ4", "7t6dTKHZY6U", "YWwJ1O6fQQs", "41VIMNNssjw", "hw_SJRb1uEk", "oJZEOGPBtp0", "G5RVx22SVzs", "g_QXbJmWWO0", "9o-4qxrv584", "nOl7AAouxVc", "k0LjOdjBdYU", "S9QL3kDf8gA", "nNFb0CPT7Js", "ukOWgL-9mlw", "O5In5PJnEr8", "LBTf6IMt2X8", "ITgt-B5IdFk", "Xw4qL0j_9Vs", "71Pqy6HKns8", "tNga0kZsgXY", "piH6EOOP7cY", "3a8B5imZV8o", "Lg-Can0ZrXM", "Rh-AfNJC1AY", "g57hoYLobng", "xam-JFkXggk", "X3GCh50sW8A", "zuYjR6RNeIw", "mxCqvGI5iu0", "ud8TFvfUJ8M", "7ziQJmP02M0", "hZirnyIx1Tw", "Ti6nFst0JaE", "sdqrr4rdUPA", "P35Ek5tTy4I", "0yT4idCIsSE", "DLilbBb5C-k", "1D4_GtYfmUE", "gfYmkBTQVD4", "dGSCRDVe9NE", "L1QLv-RFy7A", "qiWE67WQSBY", "DZCXER0nGaM", "WDQyD0VHt68", "ydCddPTqZmo", "Z-JxFdJcoB4", "KXjJoVHJsQw", "6BfneC2-IvA", "4gYlHwrMV50", "2smvtZlQSEg", "SzfqrHxbpug", "V_AZsXtgxvY", "QYW7YCydh3s", "0XHUVfPJlak", "tnNhOpq6MqI", "hZwuhnWXkLE", "p3PIKVi8goc", "OzrUXu1pKkg", "lfB0Y5mJ1qk", "ORPN8djCQws", "UsNNGSI6qzk", "OBkMzEHYA3c", "JAh-XgpCIEo", "X-KSBs_Lsd8", "omNa4PW1lU8", "8d9khSRpSkk", "qgyoXwMKJXg", "OdbpJIdes4Q", "WBfuFYdOQT4", "kO9D3crjEsU", "F6syH8W0EGA", "sFbghpqy0Lo", "JH-1IrNb_P4", "XWOGYjtgJG0", "Luu_LIPtx-M", "JvQBz3CHrK0", "reYLaGMYJYk", "l4y16i5NwwQ", "0Yn3EvME2ko", "jzNc8KFQ4S4", "WILLlFVs8K4", "VhBycovusXA", "OdYRuoXrHHw", "T3qo2SYP52U", "K1DBCpPxqeM", "EZ2zDG6qrJE", "8XCsox4ClH8", "ubenw8IJ9dE", "qvBk0IVkKRE", "fCi5ISYIy1U", "aG2s9Sp7tKg", "W6i7v9rr12o", "QUF8MiDp4O4", "oxzR9Z-kG6Q", "dWp4KgvyPYw", "PL0HmLqbxpw", "VbIHsjgvE2g", "WBc7IWmf3cs", "dV91YmIuHV4", "Mf7VagPUG50", "_GD1f91Erg8", "E452vwyyVjQ", "_eq2jnCdcyA", "-Db1ucwfr1o", "erGG9tlYbBk", "z8JrHEVGykA", "oJS0DogSjXU", "A-6m6CKOdC4", "mypB2220Rfk", "sFfgH0oJdwE", "XHdb6YDvHII", "7T8wbdYlAbQ", "gRclcNmJ9fQ", "_nDa2esEWJk", "HgMGNLc5ir8", "AuYOGchQ6XI", "J41YP1kDIKw", "7yMw3vG4_kU", "XtoKkNpyn-E", "BLpTR9p0mkY", "aO1sboxdmno", "dC2fS3vZAPY", "7kj9X6BnPKE", "FZp12hlp4gk", "HvE1Ib25iDk", "6hTkFqKThes", "fiU_B2M84Ww", "cRAhfb9Ypw8", "L-qU-BInVno", "e4cc_kptHk8", "vQPSLn2e4FY", "w2E3hxhbAc4", "EoHoiD_n7t4", "iPj5rmj8GZQ", "EdfxwaHVnAk", "-P0Gnvk5Kmk", "HlUl3uS6T6Q", "WK3WmcATcd0", "q4zRVBV0010", "Ue8yK2cnLTA", "He8KKInGwAE", "PkF2Y0bbbCo", "Jg42GYm1qv0", "M38vdprLLok", "HTMwVk8pQiY", "WZMQaNRyllY", "jd4eLSSa1Xs", "Xc6coB1-EPw", "06SSkPFTjfM", "Ar_Ua0MBt_w", "eUam8viOqxs", "jAnSY8gxLRg", "-vWfGW7Hf2E", "sCRw6hfgQTM", "YJKhOidPJhc", "AcZZ7fqUNTc", "bbIXevkZDnk", "WfM--seOsaY", "yscdF17IT_Y", "Pef5mRmx0fA", "kkJPYVGy31o", "_F3EdZ51O-Q", "Uwi4o3fwQwc", "1dDug8M2AYs", "wly5oxW3C6Y", "Picy0oa0wl0", "jfy9Pml8UZg", "vXAxaeNqze4", "0viBWDlQ9KE", "dLDcWMN-Fbw", "kA1Gl5w3ydI", "jfvSQpek00g", "ziATm-51Zc0", "FBMgpQRmfmo", "3iaTDb1K41o", "5VQkcCM1fmc", "OEVLRDRUxyc", "0u--FHf-LHU", "ms-YfEQM9E8", "SnARDknXrZQ", "Sn0vSoeVXpI", "dKHjdN2hr4w", "vLhN2olc06o", "9NbtBvkX2TI", "QeX9yVM_izg", "zEG-AcszgpQ", "TQwpuggfQWw", "6qiFa7eU34M", "f18phGNSyBg", "O9CoiUnwJ5A", "WA8fVawaHuw", "n6qfNKmjutM", "5yDnz_UrH-s", "5xj4ycn0TY8", "dFgoc8M87Ww", "jvZPz3tpWPw", "1gUgA5_iv5g", "sVEvT4pZeyQ", "JDThzHJWt4o", "0mcp9JqqJ1k", "ymL0Whh7V_I", "99iIWvXtsqc", "8UcwA-Zk3JQ", "GoWmzpyfv0Y", "uqOoO342wNg", "xkGxvP-tw1w", "qEYW8pnCu48", "3oHvXK3Xj5k", "p_OfoN-B_xw", "upipvN8Xw-c", "cYZArmDfKnA", "s1SR4hmgC4U", "HBZpHQRKrFM", "g6clciS1riA", "gXM9-IpEzEc", "nruQWhRsem4", "7m9YwTJwFrE", "3st5EgoczRM", "TmFdkd0YmjU", "s1Ac_TvGdAU", "ry9RV0yCJpI", "TGRVtcThDf4", "p320GUpKgkQ", "hA92uD-XpQs", "Omn_wSe-dKU", "YgYyQjI4UeY", "C1PjhOZQxMU", "_Fxy_CFR78Q", "narkCrS3_GA", "lKhxVjkSa84", "XWnWPkDHGz4", "PrntU87z0n8", "wzrVRxyd5a4", "3G8xlTapGQo", "0rZlNPF_utQ", "vUmuxcvyGrM", "-2N-WzrLzCc", "sQTl_NH1n0o", "0krT8xzNbyM", "bZI8gT-VbT0", "XBrUmJLCkEw", "YrJtArqXavk", "TsA3LycTPSo", "PHQFSQi4tzU", "XteReGQom40", "xI2m7tKJ40E", "JAY_uZjqmIA", "qrvKQtQgb2s", "YS6EfEQu1ik", "hDqbO57hnyQ", "EfcKLvzIDRw", "cXln3eAat5g", "Pk0mm0ly7Og", "KvBOUWSO1PM", "vNw21mQVfKM", "H9f2NJOxcz0", "P7eGfaq3E_s", "GyiSOeKOK8s", "DJFWTrj5sO8", "losUGtP6fxI", "skYeVk80Eo0", "mpPxqJrum-M", "Sah0hB6rSFY", "x0IPLHoV9Yc", "pTlgYtrDSPI", "vAT50nuKMh8", "ycWudyVJdOU", "i9KzXu-Nhx0", "YfFNug5ZOac", "A9erliXTS6o", "6EEIW68j5lY", "ipzIvlpBkbU", "rLucwp89lnE", "4g6cymurqY0", "-1__PIJhhPI", "agChJ2Ho124", "Yd3_uDW6i4w", "vxQcorAdAXA", "chuU4lFZ5iA", "vbG5B1wswQc", "U3xSpmrTgXc", "CSjnGcglVJI", "Jzkgm9A3Ooc", "INHBTa-HfSM", "4ApYhj2Mqeo", "F25xFwezdxw", "PIqHAidM99g", "EEkIbuhQ9dw", "lXCnVOsgJwo", "CJ8_MISsRxg", "nNMmAneQsLs", "Pxm7UgJ1JiE", "qblckfTw1Rk", "5-8BIb9KyNk", "_33ng3euFJI", "XIs2ZIJ2oZw", "-xNyTz_yvRU", "gsf0t-VihvE", "jqQTqr1gHEI", "n2t3bDiJcMk", "dT5g0VRp7jE", "tpe1wARxPSs", "3wNpnpA5K-w", "2LRsVjehz44", "SZhwVVZuRkY", "CwORk-NwrQM", "_JG62QmM-QE", "XeD27Barwbk", "dfPBgVKT_H8", "gq5PAlFBEi8", "_qb0WUb7i5A", "c0WSmr4tlLY", "0eWljspYG7E", "F7KHn6M2VGk", "XOJchlUhps0", "6yrG087cato", "evAV9e6QUlI", "uITVQ8JRMg4", "F-tHf-vPBxQ", "sgVtXugsDtE", "s6Geto53AmI", "d9pbNfB26wc", "ExOobxzS4tc", "FFtI8ZQT2Mk", "B86J0eynF9A", "UB35E3hE65E", "CLDelMZYKC8", "xyiYZRhJsSo", "BAliJ1ieJrI", "mMEXXehlL54", "4MJ1vA3znA4", "URuGgQXkQpQ", "wk0pllJl1nU", "_vJ6UtXHybA", "6rlo1KZ0qok", "weX6vsG96ZY", "JUiRv74kgHU", "B7rC1GyPlqM", "Yk82zpkqZjw", "oo8IRR00H30", "k0RE3k8k1pQ", "mnXZeefSK8w", "nMxKk66pAzc", "6Z2BOKloo7k", "SdrmUgN92O4", "lmTSkGSnxzw", "9d8hI1wc_Bs", "fs14OduKHd4", "YYVengVA5V8", "oMZHElIjza4"];
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
