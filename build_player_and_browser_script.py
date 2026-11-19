#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה את קובץ הסקריפט לדפדפן (create_playlist_in_browser.js)
ואת הנגן האינטראקטיבי המלא (naomi_shemer_playlist_player.html)
מתוך naomi_shemer_youtube_playlist.json.
"""

import csv
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _parse_duration_seconds(dur_str: str) -> int:
    if not dur_str:
        return -1
    parts = [p for p in str(dur_str).strip().split(":") if p.isdigit()]
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return -1


ACUM_PERFORMER_EXACT_MAP = {
    "(דומינו (השביעייה": "השביעייה (דומינו)",
    "(הקול זורם (חברת החשמל": "הקול זורם (חברת החשמל)",
    ".תזמורת סי.בי.אס": "תזמורת סי.בי.אס.",
    "33 קפה תיאטרון-ערוץ": "קפה תיאטרון (ערוץ 33)",
    "Naomi Shemer = נעמי שמר": "נעמי שמר",
    "אביבי שי נבון דב והויברגר רמי": "שי אביבי, דב נבון ורמי הויברגר",
    "אבידן מאיה וגולן שירה": "מאיה אבידן ושירה גולן",
    "אביטל אילנה": "אילנה אביטל",
    "אבקסיס אליאל": "אליאל אבקסיס",
    "אדרי אור": "אור אדרי",
    "אהרון שלומית": "שלומית אהרון",
    "אהרוני אלינור": "אלינור אהרוני",
    "אולארצ'יק אלון": "אלון אולארצ'יק",
    "אופיר ניצן": "ניצן אופיר",
    "אופיר רונית": "רונית אופיר",
    "אופיר שייקה": "שייקה אופיר",
    "אורן דניאל": "דניאל אורן",
    "אורנשטיין דוד": "דוד אורנשטיין",
    "אזולאי גולן": "גולן אזולאי",
    "אחיות שמר": "האחיות שמר",
    "אחיות שמר והדר הדסה": "האחיות שמר והדסה הדר",
    "אחים שלם": "האחים שלם",
    "אטס רחל": "רחל אטאס",
    "אטס רחל וישראלי שמעון": "רחל אטאס ושמעון ישראלי",
    "אטס רחל ושחם אורית": "רחל אטאס ואורית שחם",
    "איינשטיין אריק": "אריק איינשטיין",
    "איינשטיין אריק ורביץ יהודית": "אריק איינשטיין ויהודית רביץ",
    "איינשטיין אריק ורובינא אילנה": "אריק איינשטיין ואילנה רובינא",
    "אילת יוני": "יוני אילת",
    "איסבין שרון": "שרון איסבין",
    "אלבו ליאור": "ליאור אלבו",
    "אלבז בני": "בני אלבז",
    "אלברשטיין חוה": "חוה אלברשטיין",
    "אלברשטיין חוה והפרברים": "חוה אלברשטיין והפרברים",
    "אלברשטיין חוה ופלטינה": "חוה אלברשטיין והפלטינה",
    "אלדמע גיל": "גיל אלדמע",
    "אלהרר דודו": "דודו אלהרר",
    "אלהרר דודו,רולנד רונית והראל רמי": "דודו אלהרר, רונית רולנד ורמי הראל",
    "אלוני מירי": "מירי אלוני",
    "אלוני מירי דברה פ. חבורת בימות": "מירי אלוני, דברה פ. וחבורת בימות",
    "אלוני מירי וחבורת בימות": "מירי אלוני וחבורת בימות",
    "אלוני מירי וליטני דני": "מירי אלוני ודני ליטני",
    "אלוני עמוס": "עמוס אלוני",
    "אלירן רן": "רן אלירן",
    "אלירן רן,חדוה ודוד": "רן אלירן, חדוה ודוד",
    "אמדורסקי בני": "בני אמדורסקי",
    "אנג'ל נריה וגיל אביעד": "נריה אנג'ל ואביעד גיל",
    "אסנר נועה": "נועה אסנר",
    "אסנר עוזי ואסנר חיים": "עוזי אסנר וחיים אסנר",
    "אקשטיין גרי": "גרי אקשטיין",
    "ארד חיה ולהקת חיל הים": "חיה ארד ולהקת חיל הים",
    "ארזי ירדנה": "ירדנה ארזי",
    "ארזי ירדנה וקירל נועה": "ירדנה ארזי ונועה קירל",
    "ארזי ירדנה כהן יזהר ומשה חיים": "ירדנה ארזי, יזהר כהן וחיים משה",
    "אריאל מתן וקפלן מיכל": "מתן אריאל ומיכל קפלן",
    "אריאל מתן קפלן מיכל ורהב תום": "מתן אריאל, מיכל קפלן ותום רהב",
    "ארמוני דפנה": "דפנה ארמוני",
    "ארמוני דפנה ובן-ישראל אפי": "דפנה ארמוני ואפי בן-ישראל",
    "ארנון ורד יעל וורד בן": "יעל ארנון ורד ובן ורד",
    "ארצי שלמה": "שלמה ארצי",
    "אשד אילן": "אילן אשד",
    "אשכנזי שמעיה ולבנת שולמית": "שמעיה אשכנזי ושולמית לבנת",
    "אשרת קובי": "קובי אשרת",
    "בדיחי יעל": "יעל בדיחי",
    "בונוס בן": "בן בונוס",
    "בורשטיין אברהם": "אברהם בורשטיין",
    "ביאליק עידו": "עידו ביאליק",
    "בירנבאום בת אלה ובנט מיכל": "בת אלה בירנבאום ומיכל בנט",
    "ביתן אורי": "אורי ביתן",
    "בלומין מארינה": "מארינה בלומין",
    "בליץ יאיר ומזור חן": "יאיר בליץ וחן מזור",
    "בלצן אסתרית": "אסתרית בלצן",
    "בן אברהם רות": "רות בן אברהם",
    "בן אברהם רות וחבורת בימות": "רות בן אברהם וחבורת בימות",
    "בן אברהם רות ומנטבר אלי": "רות בן אברהם ואלי מנטבר",
    "בן דוד יוריק": "יוריק בן דוד",
    "בן חור עודד": "עודד בן חור",
    "בן חור עודד ורז רוחמה": "עודד בן חור ורוחמה רז",
    "בן יעקב דרור": "דרור בן יעקב",
    "בן ישראל אפי": "אפי בן ישראל",
    "בן ישראל אפי וחן שולה": "אפי בן ישראל ושולה חן",
    "בן עמי אילנה": "אילנה בן עמי",
    "בנאי אהוד": "אהוד בנאי",
    "בנאי אורנה וקסמן ענת ואלימלך שרון": "אורנה בנאי, ענת וקסמן ושרון אלימלך",
    "בנאי יובל": "יובל בנאי",
    "בנאי יוסי": "יוסי בנאי",
    "בנאי יוסי ובנאי גברי": "יוסי בנאי וגברי בנאי",
    "בנאי יוסי ומיכאלי רבקה": "יוסי בנאי ורבקה מיכאלי",
    "בנאי יוסי ורביץ יהודית": "יוסי בנאי ויהודית רביץ",
    "בנאי מאיר": "מאיר בנאי",
    "בניון עמיר": "עמיר בניון",
    "בצל ירוק והנדל נחמה": "בצל ירוק ונחמה הנדל",
    "בצלאל טלי": "טלי בצלאל",
    "בקר משה": "משה בקר",
    "בר אבא שלמה ומושונוב מוני": "שלמה בראבא ומוני מושונוב",
    "בר אילן מישה ומנטבר אלי": "מישה בר אילן ואלי מנטבר",
    "בר גיורא יונתן": "יונתן בר גיורא",
    "בר נוף רוני": "רוני בר נוף",
    "בר שמעון": "שמעון בר",
    "בר שמעון ותזמורת": "שמעון בר ותזמורת",
    "ברוזה דוד": "דוד ברוזה",
    "ברונשטיין גלי": "גלי ברונשטיין",
    "ברונשטיין מלי": "מלי ברונשטיין",
    "ברזל עמוס": "עמוס ברזל",
    "ברכאן מוטי": "מוטי ברכאן",
    "ברלין גבי": "גבי ברלין",
    "ברלין גבי וטופול חיים": "גבי ברלין וחיים טופול",
    "ברלין גבי ושרון שרהלה": "גבי ברלין ושרה'לה שרון",
    "ברמן בני": "בני ברמן",
    "ברק דודו": "דודו ברק",
    "ברק פרדי": "פרדי ברק",
    "בשן יגאל": "יגאל בשן",
    "בשן יגאל דור אבי ופררה אהרון": "יגאל בשן, אבי דור ואהרון פררה",
    "ג'ונסון סנדרה": "סנדרה ג'ונסון",
    "גאון יהורם": "יהורם גאון",
    "גבאי ירון": "ירון גבאי",
    "גבאי רינת": "רינת גבאי",
    "גבני יוסי": "יוסי גבני",
    "גבעטרון": "הגבעטרון",
    "גדיר עודד": "עודד גדיר",
    "גואטה רביד": "רביד גואטה",
    "גולדבלט חנן": "חנן גולדבלט",
    "גולדבלט חנן וארמוני דפנה": "חנן גולדבלט ודפנה ארמוני",
    "גולדבלט חנן וחן שולה": "חנן גולדבלט ושולה חן",
    "גולן דינה": "דינה גולן",
    "גולן דני": "דני גולן",
    "גורביץ אמיל": "אמיל גורביץ",
    "גורדון רבקה": "רבקה גורדון",
    "גורדון רינה": "רינה גורדון",
    "גורליצקי אילי": "אילי גורליצקי",
    "גורן עדנה": "עדנה גורן",
    "גורן עדנה והראל רמי": "עדנה גורן ורמי הראל",
    "גיאת גלית אלימלך שרון ורביץ נתי": "גלית גיאת, שרון אלימלך ונתי רביץ",
    "גיל גאולה": "גאולה גיל",
    "גינת אמיר": "אמיר גינת",
    "גל נירה": "נירה גל",
    "גל נירה ולב עדנה": "נירה גל ועדנה לב",
    "גל ריקי": "ריקי גל",
    "גל ריקי ונדל לירן": "ריקי גל ולירן נדל",
    "גלוסקא אופירה": "אופירה גלוסקא",
    "גלוסקא אופירה וגולן דני": "אופירה גלוסקא ודני גולן",
    "גלוסקא אופירה ורננים": "אופירה גלוסקא וחבורת רננים",
    "גלעד איקי וגיאת גלית": "איקי גלעד וגלית גיאת",
    "גלעדי תמר": "תמר גלעדי",
    "גלרון נורית": "נורית גלרון",
    "גלרון נורית וסימפונט רעננה": "נורית גלרון וסימפונט רעננה",
    "גנוט יוני": "יוני גנוט",
    "גרוטס אתי": "אתי גרוטס",
    "גרוניך שלמה": "שלמה גרוניך",
    "גרייניק אבי ורודנר חמי": "אבי גרייניק וחמי רודנר",
    "גרינברג ענת": "ענת גרינברג",
    "גרנות דני": "דני גרנות",
    "גרנות דני וחבורת בימות": "דני גרנות וחבורת בימות",
    "גרנות רפי": "רפי גרנות",
    "דבורין דנה": "דנה דבורין",
    "דברת נתניה ותזמורת הבידור": "נתניה דברת ותזמורת הבידור",
    "דגול שמרלינג הדס": "הדס דגול שמרלינג",
    "דגן צילה": "צילה דגן",
    "דגן צילה גלוסקא אופירה ולהקת הנחל": "צילה דגן, אופירה גלוסקא ולהקת הנח\"ל",
    "דגן צילה ואמדורסקי בני": "צילה דגן ובני אמדורסקי",
    "דגן צילה ורננים": "צילה דגן וחבורת רננים",
    "דגן צילה שמר נעמי ואמדורסקי בני": "צילה דגן, נעמי שמר ובני אמדורסקי",
    "דוידוב אריק": "אריק דוידוב",
    "דורון אורן ז'נו אוסנת וילדים": "אורן דורון, אוסנת ז'נו וילדים",
    "דותן עירית": "עירית דותן",
    "דיכנה מוטי,אנקרי אתי ובר הראלה": "מוטי דיכנה, אתי אנקרי והראלה בר",
    "דירון עפרה ורויאל וויבס": "עפרה דירון ורויאל וויבס",
    "דמארי דנה": "דנה דמארי",
    "דמארי שושנה": "שושנה דמארי",
    "דמארי שושנה ותז' סימפונית": "שושנה דמארי ותזמורת סימפונית",
    "דמרי אילן": "אילן דמרי",
    "דץ משה": "משה דץ",
    "דרור שמרית": "שמרית דרור",
    "הבלין מוטי": "מוטי הבלין",
    "הגשש החיוור ושמר נעמי": "הגשש החיוור ונעמי שמר",
    "הדר קרן": "קרן הדר",
    "הולצמן רותי": "רותי הולצמן",
    "הורוביץ אריאל": "אריאל הורוביץ",
    "הורוביץ אריאל והאחיות שמר": "אריאל הורוביץ והאחיות שמר",
    "הורן חנוך": "חנוך הורן",
    "היימן נחום": "נחום היימן",
    "הלחמי רומי ונדלר בני": "רומי הלחמי ובני נדלר",
    "הנדל הלנה": "נחמה (הלנה) הנדל",
    "הראל אסנת": "אסנת הראל",
    "הראל רמי": "רמי הראל",
    "הרולד שולי": "שולי הרולד",
    "ויטלר בן ציון": "בן ציון ויטלר",
    "וייל אילן וגמליאל יסמין": "אילן וייל ויסמין גמליאל",
    "וייס דניאל": "דניאל וייס",
    "וירצר דניאלה": "דניאלה וירצר",
    "וישינסקי אסנת": "אסנת וישינסקי",
    "וישינסקי שלמה": "שלמה וישינסקי",
    "וקסמן איגי": "איגי וקסמן",
    "ורד רמי,בן זאב ערן ושוורץ ליטל": "רמי ורד, ערן בן זאב וליטל שוורץ",
    "ורדי איתן": "איתן ורדי",
    "זהבי דפנה": "דפנה זהבי",
    "זהר עוזי": "עוזי זהר",
    "זוהר ישראל": "ישראל זוהר",
    "זוהר רבקה": "רבקה זוהר",
    "זוהר רבקה ולהקת חיל הים": "רבקה זוהר ולהקת חיל הים",
    "זיטנר אורה": "אורה זיטנר",
    "זיטנר אורה קאופמן ניב וגוריון ישראל": "אורה זיטנר, ניב קאופמן וישראל גוריון",
    "זילבר אריאל": "אריאל זילבר",
    "זכאי דודו": "דודו זכאי",
    "זכאי דודו וראובני דורית": "דודו זכאי ודורית ראובני",
    "זכאי דודו ורננים": "דודו זכאי וחבורת רננים",
    "זלצמן רויטל": "רויטל זלצמן",
    "זמיר ורדה": "ורדה זמיר",
    "זמיר ורדה ובר גיורא יונתן": "ורדה זמיר ויונתן בר גיורא",
    "זראי ריקה": "ריקה זראי",
    "חבורת הזמר הדר רון והחברים ששרים": "רון הדר והחברים ששרים",
    "חדד שרית": "שרית חדד",
    "חוג הזמר גולדשטיין גורן אשד נוגה": "חוג הזמר, גורן גולדשטיין ונוגה אשד",
    "חזה עפרה": "עפרה חזה",
    "חי דוד": "דוד חי",
    "חיטמן אוהד": "אוהד חיטמן",
    "חיטמן עוזי": "עוזי חיטמן",
    "חיטמן עוזי ומשה חיים": "עוזי חיטמן וחיים משה",
    "חיים רחלי": "רחלי חיים",
    "חן שולה": "שולה חן",
    "חן שולה וחנוך שלום": "שולה חן ושלום חנוך",
    "חן שולה וייני ליאור": "שולה חן וליאור ייני",
    "חן שולה ולהקת הנחל": "שולה חן ולהקת הנח\"ל",
    "טולדנו אבי": "אבי טולדנו",
    "טופול חיים ועדי": "חיים ועדי טופול",
    "טופול חיים ושירו שיר": "חיים טופול וחבורת שירו שיר",
    "טל מיכל": "מיכל טל",
    "טלמור סיון ואלירן רן": "סיון טלמור ורן אלירן",
    "טרבלסי מיטל": "מיטל טרבלסי",
    "טרבלסי מיטל וקלינג תומר": "מיטל טרבלסי ותומר קלינג",
    "יגיל גדי": "גדי יגיל",
    "ידידיה רוני": "רוני ידידיה",
    "יובל חנן": "חנן יובל",
    "ייני ליאור": "ליאור ייני",
    "ייני ליאור ושירו שיר": "ליאור ייני וחבורת שירו שיר",
    "ינאי מיכל": "מיכל ינאי",
    "יצפאן אלי": "אלי יצפאן",
    "ישראלי חרות ועמית לוטי": "חרות ישראלי ולוטי עמית",
    "ישראלי שמעון": "שמעון ישראלי",
    "ישראלי שמעון ותז' ק\"י": "שמעון ישראלי ותזמורת קול ישראל",
    "כהן ורדינה": "ורדינה כהן",
    "כהן יזהר ורביעיית ניסן": "יזהר כהן ורביעיית ניסן",
    "כהן יזהר ורננים": "יזהר כהן וחבורת רננים",
    "כהן מזי ואלוני מירי": "מזי כהן ומירי אלוני",
    "כהן נתן": "נתן כהן",
    "כהן עדי": "עדי כהן",
    "כהן עדי ועוואד מירה": "עדי כהן ומירה עוואד",
    "כהנא דלית": "דלית כהנא",
    "כוכבא יהודית": "יהודית כוכבא",
    "כספי מתי": "מתי כספי",
    "כץ אסתי": "אסתי כץ",
    "כרמלוס יהאל": "יהאל כרמלוס",
    "לב עדנה": "עדנה לב",
    "לביא אריק": "אריק לביא",
    "לביא ראובן": "ראובן לביא",
    "לבנת שולמית": "שולמית לבנת",
    "לברי מרק": "מרק לברי",
    "להב משה": "משה להב",
    "להקות צהל": "להקות צה\"ל",
    "להקת הנחל": "להקת הנח\"ל",
    "להקת הנחל וחוה אלברשטיין": "להקת הנח\"ל וחוה אלברשטיין",
    "להקת הנחל ותזמורת קול ישראל": "להקת הנח\"ל ותזמורת קול ישראל",
    "להקת פיקוד דרום": "להקת פיקוד הדרום",
    "להקת פיקוד מרכז": "להקת פיקוד המרכז",
    "להקת פיקוד צפון": "להקת פיקוד הצפון",
    "לוגסי גל": "גל לוגסי",
    "לוי לוליק וענת עצמון": "לוליק לוי וענת עצמון",
    "לוי נעמי": "נעמי לוי",
    "לוי שייקה והשעות הקטנות": "שייקה לוי ולהקת השעות הקטנות",
    "לויכטר יהודה": "יהודה לויכטר",
    "לויכטר יהודה ולנדאו ביני": "יהודה לויכטר וביני לנדאו",
    "לופטין לאה": "לאה לופטין",
    "לופטין לאה ולוי עופר": "לאה לופטין ועופר לוי",
    "לטילה ג'ינו": "ג'ינו לטילה",
    "לידר עברי": "עברי לידר",
    "ליטני דני": "דני ליטני",
    "ליפשיץ נחמה": "נחמה ליפשיץ",
    "לסלאו חנה": "חנה לסלאו",
    "לרנר יואל": "יואל לרנר",
    "מאיירס חגית": "חגית מאיירס",
    "מאירי עוזי": "עוזי מאירי",
    "מאירי עוזי ורננים": "עוזי מאירי וחבורת רננים",
    "מואב אלינוער": "אלינוער מואב",
    "מודעי דולי": "דולי מודעי",
    "מור מירי": "מירי מור",
    "מושונוב מוני בר-אבא שלמה גוב גידי": "מוני מושונוב, שלמה בראבא וגידי גוב",
    "מזרחי שלמה": "שלמה מזרחי",
    "מיכאלי רבקה": "רבקה מיכאלי",
    "מיכאלי רבקה ואמדורסקי בני": "רבקה מיכאלי ובני אמדורסקי",
    "מיכאלי רבקה וצפיר טוביה": "רבקה מיכאלי וטוביה צפיר",
    "מיכאלי רבקה ושמר נעמי": "רבקה מיכאלי ונעמי שמר",
    "מיכאלי רבקה מושונוב מוני ובר-אבא שלמה": "רבקה מיכאלי, מוני מושונוב ושלמה בראבא",
    "מלכה שלומי": "שלומי מלכה",
    "מלמד אורי ולאה": "אורי ולאה מלמד",
    "מלקוס לילה": "לילה מלקוס",
    "מלקוס לילה אופק אורטל ורועה יוני": "לילה מלקוס, אורטל אופק ויוני רועה",
    "ממן שלמה": "שלמה ממן",
    "מן טל בן יזרעאל ומינדי טיאר": "טל מן, בן יזרעאל ומינדי טיאר",
    "מנדל יענקלה": "יענקלה מנדל",
    "מסורי איתן": "איתן מסורי",
    "מסינג דני": "דני מסינג",
    "מסנר יובל": "יובל מסנר",
    "משה חיים": "חיים משה",
    "נבון רותי": "רותי נבון",
    "נוה שלום אסף": "אסף נוה שלום",
    "נורי אילן": "אילן נורי",
    "נחמיאס חני וטופז דודו": "חני נחמיאס ודודו טופז",
    "נחמיאס חני קם מיקי ושביט ציפי": "חני נחמיאס, מיקי קם וציפי שביט",
    "ניני אחינועם ודור גיל": "אחינועם ניני וגיל דור",
    "ניצני יאיר וזוהר זאב": "יאיר ניצני וזאב זוהר",
    "נכבוש נח": "נח נכבוש",
    "נמרי יוני": "יוני נמרי",
    "נעמי שמר = Naomi Shemer": "נעמי שמר",
    "נצר אפי": "אפי נצר",
    "נצר אפי וגרייף גדעון": "אפי נצר וגדעון גרייף",
    "נרגד לירון": "לירון נרגד",
    "נשר דורון": "דורון נשר",
    "נתן שולי": "שולי נתן",
    "נתן שולי ושמר נעמי": "שולי נתן ונעמי שמר",
    "נתנאלה וזכאי דודו": "נתנאלה ודודו זכאי",
    "סבצ'וק בוריס": "בוריס סבצ'וק",
    "סדן זוהר": "זוהר סדן",
    "סוויסה מאיר ואלימלך שרון": "מאיר סוויסה ושרון אלימלך",
    "סולקין עדי ואסתר": "עדי ואסתר סולקין",
    "סונדק טל": "טל סונדק",
    "סונדק טל וקליינשטיין רמי": "טל סונדק ורמי קליינשטיין",
    "סיגלוב הדסה": "הדסה סיגלוב",
    "סיני אריק": "אריק סיני",
    "סלבר גודי": "גודי סלבר",
    "סלע טלי": "טלי סלע",
    "סמל נאוה": "נאוה סמל",
    "סנדר עירית": "עירית סנדר",
    "ספיר נירה": "נירה ספיר",
    "ספיר רות": "רות ספיר",
    "עדי סיגל": "סיגל עדי",
    "עובד לימור": "לימור עובד",
    "עופרים אסתר וישראלי שמעון": "אסתר עופרים ושמעון ישראלי",
    "עזיקרי עליזה": "עליזה עזיקרי",
    "עזיקרי עליזה וחמישיית גלבוע": "עליזה עזיקרי וחמישיית גלבוע",
    "עטרי גלי וחיטמן עוזי": "גלי עטרי ועוזי חיטמן",
    "עינב מיכאל וקייקוב ניצן": "מיכאל עינב וניצן קייקוב",
    "עינב מיקה וסנטש עודד": "מיקה עינב ועודד סנטש",
    "עמיהוד דליה": "דליה עמיהוד",
    "עמנואל יהודה": "יהודה עמנואל",
    "עמר דפנה": "דפנה עמר",
    "עמרני חדוה": "חדוה עמרני",
    "עשת דוד": "דוד עשת",
    "פולד ליאו": "ליאו פולד",
    "פוליאקוב יעל ופלד אילן": "יעל פוליאקוב ואילן פלד",
    "פז אסנת": "אסנת פז",
    "פיידמן גיורא": "גיורא פיידמן",
    "פייפר בועז": "בועז פייפר",
    "פיקוד צפון ונעמי שמר": "להקת פיקוד הצפון ונעמי שמר",
    "פישר דודו": "דודו פישר",
    "פישר דודו והדודאים": "דודו פישר והדודאים",
    "פליקס מירי": "מירי פליקס",
    "פרוסט יוסי והצעירים": "יוסי פרוסט ולהקת הצעירים",
    "פרידלנד דליה": "דליה פרידלנד",
    "פרידמן דניאל": "דניאל פרידמן",
    "פרישמן דודי וגנוט יוני": "דודי פרישמן ויוני גנוט",
    "פרנקו מונסראט": "מונסראט פרנקו",
    "פרץ אבי": "אבי פרץ",
    "פרקש דורית": "דורית פרקש",
    "פררה אברהם וחבורת אפי נצר": "אברהם פררה וחבורת אפי נצר",
    "צדר נגה": "נגה צדר",
    "צוות הווי נחל": "צוות הווי נח\"ל",
    "צוות הווי פיקוד מרכז": "צוות הווי פיקוד המרכז",
    "צילה דגן, אופירה גלוסקא ולהקת הנחל": "צילה דגן, אופירה גלוסקא ולהקת הנח\"ל",
    "צילה דגן, אופירה גלוסקא וצוות הווי של הנחל": "צילה דגן, אופירה גלוסקא וצוות הווי של הנח\"ל",
    "צינוביץ חיים": "חיים צינוביץ",
    "צנעני מרגלית": "מרגלית צנעני",
    "צפיר טוביה": "טוביה צפיר",
    "צפיר טוביה חן שולה ויובל חנן": "טוביה צפיר, שולה חן וחנן יובל",
    "קורן חיה": "חיה קורן",
    "קינן ארז": "ארז קינן",
    "קינן רונה": "רונה קינן",
    "קליין בטי": "בטי קליין",
    "קליש חגית": "חגית קליש",
    "קם מיקי": "מיקי קם",
    "קם מיקי וצינוביץ חיים": "מיקי קם וחיים צינוביץ'",
    "קניג ליא": "ליאה קניג",
    "קפסוטו תמר מנחם מיה אלדר בני": "תמר קפסוטו, מיה מנחם ובני אלדר",
    "קראוזר בועז": "בועז קראוזר",
    "קרן אור ונוי עדי": "אור קרן ועדי נוי",
    "קרן דרור וכהן איציק": "דרור קרן ואיציק כהן",
    "ראובני דורית": "דורית ראובני",
    "רביבו רבקה": "רבקה רביבו",
    "רביץ יהודית": "יהודית רביץ",
    "רואימי אבי": "אבי רואימי",
    "רובינא אילנה": "אילנה רובינא",
    "רובינא אילנה והדודאים": "אילנה רובינא והדודאים",
    "רובינא אילנה ורננים": "אילנה רובינא וחבורת רננים",
    "רוזנבלט עוזי": "עוזי רוזנבלט",
    "רוזנפלד אליעזר": "אליעזר רוזנפלד",
    "רוחמה רז וצוות הווי פיקוד מרכז": "רוחמה רז וצוות הווי פיקוד המרכז",
    "רולנד רונית": "רונית רולנד",
    "רולנד רונית ואלהרר דודו": "רונית רולנד ודודו אלהרר",
    "רולנד רונית ולהקת אלף שיר ושיר": "רונית רולנד ולהקת אלף שיר ושיר",
    "רותם שוש": "שוש רותם",
    "רז רבקה": "רבקה רז",
    "רז רוחמה": "רוחמה רז",
    "רז רוחמה  גולן דינה ורננים": "רוחמה רז, דינה גולן וחבורת רננים",
    "רז רוחמה ובירן צליל": "רוחמה רז וצליל בירן",
    "רז רוחמה ולסלאו חנה": "רוחמה רז וחנה לסלאו",
    "רז רוחמה ורננים": "רוחמה רז וחבורת רננים",
    "רז רוחמה צוות הצנחנים": "רוחמה רז וצוות הווי הצנחנים",
    "ריבלין ספי וגולן דינה": "ספי ריבלין ודינה גולן",
    "ריבלין ספי ומור אברהם": "ספי ריבלין ואברהם מור",
    "רימון מאיר ותזמורת פילהרמונית": "מאיר רימון והתזמורת הפילהרמונית",
    "רמתי לירון": "לירון רמתי",
    "שביט סיון": "סיון שביט",
    "שביט ציפי": "ציפי שביט",
    "שביט ציפי ודטנר נתן": "ציפי שביט ונתן דטנר",
    "שגרן ג'וליאן": "ג'וליאן שגרן",
    "שדה יושי": "יושי שדה",
    "שובל גיתית": "גיתית שובל",
    "שובל גיתית ודרויאן רון": "גיתית שובל ורון דרויאן",
    "שוהם יונית": "יונית שוהם",
    "שולה חן ולהקת הנחל": "שולה חן ולהקת הנח\"ל",
    "שושן גבי": "גבי שושן",
    "שי שמואל": "שמואל שי",
    "שלאנגר לאה": "לאה שלאנגר",
    "שלושרים": "השלושרים",
    "שמיר אסתר": "אסתר שמיר",
    "שמיר מיכל": "מיכל שמיר",
    "שמר נעמי": "נעמי שמר",
    "שמר נעמי ואלהרר דודו": "נעמי שמר ודודו אלהרר",
    "שני שושיק": "שושיק שני",
    "שני שושיק ולביא אריק": "שושיק שני ואריק לביא",
    "שפר אסף": "אסף שפר",
    "שרון שרה'לה": "שרה'לה שרון",
    "שרעבי בועז": "בועז שרעבי",
    "שרעבי יואל": "יואל שרעבי",
    "ששון רועי": "רועי ששון",
    "תבורי שימי": "שימי תבורי",
    "תזמורת ולהקת חיל האויר": "תזמורת ולהקת חיל האוויר",
    "תמיר גני": "גני תמיר",
    "תמיר קובי": "קובי תמיר",
}

ACUM_INLINE_PAIR_SUBS = [
    ("שמר נעמי", "נעמי שמר"),
    ("גאון יהורם", "יהורם גאון"),
    ("אלברשטיין חוה", "חוה אלברשטיין"),
    ("איינשטיין אריק", "אריק איינשטיין"),
    ("בנאי יוסי", "יוסי בנאי"),
    ("מיכאלי רבקה", "רבקה מיכאלי"),
    ("אלהרר דודו", "דודו אלהרר"),
    ("רולנד רונית", "רונית רולנד"),
    ("הורוביץ אריאל", "אריאל הורוביץ"),
    ("גלוסקא אופירה", "אופירה גלוסקא"),
    ("דגן צילה", "צילה דגן"),
    ("ירקוני יפה", "יפה ירקוני"),
    ("לוי אושיק", "אושיק לוי"),
    ("תאומי עודד", "עודד תאומי"),
    ("להקת הנחל", "להקת הנח\"ל"),
    ("צוות הווי של הנחל", "צוות הווי של הנח\"ל"),
    ("להקת פיקוד מרכז", "להקת פיקוד המרכז"),
    ("להקת פיקוד צפון", "להקת פיקוד הצפון"),
    ("להקת פיקוד דרום", "להקת פיקוד הדרום"),
    ("צוות הווי פיקוד מרכז", "צוות הווי פיקוד המרכז"),
]

def normalize_performer_name(name: str) -> str:
    s = str(name or "").strip()
    if not s:
        return ""
    if s in ACUM_PERFORMER_EXACT_MAP:
        return ACUM_PERFORMER_EXACT_MAP[s]
    if " = " in s:
        heb_parts = [p.strip() for p in s.split(" = ") if re.search(r"[\u0590-\u05FF]", p)]
        if heb_parts:
            s = heb_parts[0]
    for src_pair, dst_pair in ACUM_INLINE_PAIR_SUBS:
        if src_pair in s:
            s = s.replace(src_pair, dst_pair)
    return ACUM_PERFORMER_EXACT_MAP.get(s, s)


def normalize_performers_list(perfs: list) -> list:
    out = []
    seen = set()
    for p in perfs or []:
        np = normalize_performer_name(p)
        if np and np not in seen:
            seen.add(np)
            out.append(np)
    return out


def _clean_artist_name(item: dict, sel: dict) -> str:
    perf = sel.get("matched_performer") or item.get("matched_performer") or ""
    if not perf:
        cat_perfs = normalize_performers_list(item.get("catalog_performers") or item.get("performers") or [])
        if cat_perfs:
            perf = cat_perfs[0]
    perf = normalize_performer_name(perf)
    if not perf:
        ch = sel.get("channel", "")
        perf = re.sub(r"\s*-\s*Topic$", "", ch).strip()
    if not perf or perf.lower() in ("various artists", "release"):
        perf = "נעמי שמר"
    return perf


def _clean_display_album(item: dict, sel: dict, include_track: bool = False) -> str:
    ag = str(item.get("album_group") or "").strip()
    trk = str(item.get("album_track_number") or "").strip()
    is_single_grp = (not ag) or ag.startswith("סינגל") or ag.startswith("ביצוע ")
    if not is_single_grp:
        return f"{ag} (#{trk})" if (include_track and trk) else ag
    ma = str(sel.get("matched_album") or "").strip()
    if ma and not ma.startswith("סינגל") and not ma.startswith("ביצוע "):
        return ma
    return ""


def sync_all_secondary_exports(data: dict) -> list:
    """מייצר ומסנכרן את כל קובצי הפלט המשניים (CSV, MD, M3U8, Streaming CSV, Wayback URLs)."""
    playlist = data["playlist"]
    matched = [x for x in playlist if x.get("selected_video")]
    csv_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.csv")
    md_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.md")
    stream_csv_path = os.path.join(BASE_DIR, "naomi_shemer_streaming_import.csv")
    m3u8_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_stream.m3u8")
    wayback_path = os.path.join(BASE_DIR, "wayback_backup_urls.txt")

    # 1. naomi_shemer_youtube_playlist.csv (פרטים עובדתיים וקישור ישיר לספרייה הלאומית, ללא פסקאות מועתקות)
    fieldnames = [
        "index", "chrono_index", "canonical_layer", "canonical_score", "title",
        "year", "role_category", "role_label_heb", "co_creators_heb", "lyricist", "composer",
        "translator", "tier", "tier_label", "matched_performer", "matched_album",
        "album_group", "album_track_number", "video_id", "video_url",
        "video_title", "channel", "duration", "views", "opening_line", "nli_url"
    ]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for item in playlist:
            sel = item.get("selected_video") or {}
            nli_url = next(
                (
                    lk.get("url", "")
                    for lk in item.get("archive_links", [])
                    if str(lk.get("source", "")) == "nli" and lk.get("url")
                ),
                next(
                    (
                        lk.get("url", "")
                        for lk in item.get("archive_links", [])
                        if str(lk.get("source", "")).startswith("nli") and lk.get("url")
                    ),
                    "",
                ),
            )
            yr_raw = item.get("year", "")
            yr_csv = yr_raw if (yr_raw and str(yr_raw) != "2099") else ""
            w.writerow({
                "index": item.get("index", ""),
                "chrono_index": item.get("chrono_index", ""),
                "canonical_layer": item.get("canonical_layer", ""),
                "canonical_score": item.get("canonical_score", ""),
                "title": item.get("title", ""),
                "year": yr_csv,
                "role_category": item.get("role_category", ""),
                "role_label_heb": item.get("role_label_heb", ""),
                "co_creators_heb": item.get("co_creators_heb", ""),
                "lyricist": item.get("lyricist", ""),
                "composer": item.get("composer", ""),
                "translator": item.get("translator", ""),
                "tier": item.get("tier", ""),
                "tier_label": item.get("tier_label", ""),
                "matched_performer": sel.get("matched_performer") or item.get("matched_performer", ""),
                "matched_album": sel.get("matched_album", ""),
                "album_group": item.get("album_group", ""),
                "album_track_number": item.get("album_track_number", ""),
                "video_id": sel.get("video_id", ""),
                "video_url": f"https://www.youtube.com/watch?v={sel['video_id']}" if sel.get("video_id") else "",
                "video_title": sel.get("video_title", ""),
                "channel": sel.get("channel", ""),
                "duration": sel.get("duration", ""),
                "views": sel.get("views", ""),
                "opening_line": item.get("opening_line", ""),
                "nli_url": nli_url,
            })

    # 2. naomi_shemer_youtube_playlist.md
    md_lines = [
        f"# פלייליסט שירי נעמי שמר ביוטיוב ({len(matched)} ביצועים)",
        "",
        "| # | שנה | שם השיר | תפקיד | סיווג | מבצע / ערוץ | קישור ליוטיוב | אורך |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, item in enumerate(matched, 1):
        sel = item["selected_video"]
        vid = sel["video_id"]
        yr = item.get("year") if item.get("year") and str(item.get("year")) != "2099" else "—"
        perf = sel.get("matched_performer") or sel.get("channel", "")
        vtitle = sel.get("video_title", "").replace("|", "·")
        md_lines.append(
            f"| {i} | {yr} | **{item['title']}** | {item.get('role_label_heb','')} | "
            f"{item.get('tier_label','')} | {perf} | [{vtitle}](https://www.youtube.com/watch?v={vid}) | {sel.get('duration','')} |"
        )
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    # 3. naomi_shemer_streaming_import.csv
    with open(stream_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "playlist_order", "title", "artist", "album", "year",
                "composer_lyricist_role", "duration", "youtube_url",
                "youtube_id", "backup_youtube_urls",
            ],
        )
        writer.writeheader()
        for idx, item in enumerate(matched, 1):
            sel = item["selected_video"]
            vid = sel["video_id"]
            yr = item.get("year", "")
            yr_clean = yr if (yr and str(yr) != "2099") else ""
            alb = _clean_display_album(item, sel, include_track=False)
            artist = _clean_artist_name(item, sel)
            alts = [
                f"https://www.youtube.com/watch?v={a['video_id']}"
                for a in item.get("alternative_videos", [])[:5]
                if a.get("video_id") and a.get("video_id") != vid
            ]
            writer.writerow({
                "playlist_order": idx,
                "title": item.get("title", ""),
                "artist": artist,
                "album": alb,
                "year": yr_clean,
                "composer_lyricist_role": item.get("role_label_heb", "מילים ולחן: נעמי שמר"),
                "duration": sel.get("duration", ""),
                "youtube_url": f"https://www.youtube.com/watch?v={vid}",
                "youtube_id": vid,
                "backup_youtube_urls": " | ".join(alts),
            })

    # 4. naomi_shemer_youtube_stream.m3u8
    m3u_lines = [
        "#EXTM3U",
        f"#PLAYLIST:שירי נעמי שמר – האוסף המקיף ({len(matched)} ביצועים ביוטיוב)",
    ]
    for item in matched:
        sel = item["selected_video"]
        vid = sel["video_id"]
        sec = _parse_duration_seconds(sel.get("duration", ""))
        artist = _clean_artist_name(item, sel)
        title = item.get("title", "")
        yr = item.get("year", "")
        yr_str = f" ({yr})" if (yr and str(yr) != "2099") else ""
        m3u_lines.append(f"#EXTINF:{sec},{artist} - {title}{yr_str}")
        m3u_lines.append(f"https://www.youtube.com/watch?v={vid}")
    with open(m3u8_path, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines) + "\n")

    # 5. wayback_backup_urls.txt
    urls = ["https://www.youtube.com/playlist?list=PLFHErlX6i22g"]
    seen = set(urls)
    for item in playlist:
        sel = item.get("selected_video") or {}
        vid = sel.get("video_id")
        if vid:
            u = f"https://www.youtube.com/watch?v={vid}"
            if u not in seen:
                seen.add(u)
                urls.append(u)
        for lk in item.get("archive_links", []):
            lu = lk.get("url", "")
            if lu and ("nli.org.il/he/items/" in lu or "shironet.mako.co.il/artist?type=lyrics" in lu):
                if lu not in seen:
                    seen.add(lu)
                    urls.append(lu)
    with open(wayback_path, "w", encoding="utf-8") as f:
        f.write("\n".join(urls) + "\n")

    return [csv_path, md_path, stream_csv_path, m3u8_path, wayback_path]


def get_decade(year_str: str) -> str:
    if not year_str:
        return "unknown"
    m = re.match(r"^(\d{4})$", str(year_str).strip())
    if not m:
        return "unknown"
    yr = int(m.group(1))
    if yr >= 2099:
        return "unknown"
    if yr < 1960:
        return "1950s"
    if yr < 1970:
        return "1960s"
    if yr < 1980:
        return "1970s"
    if yr < 1990:
        return "1980s"
    return "1990s+"


def validate_and_normalize_playlist(data: dict) -> bool:
    """מנרמל ערכי tier, מחשב מחדש אינדקסים, dual_role וסטטיסטיקות, ומוודא שלמות נתונים."""
    playlist = data.get("playlist", [])
    tier_norm = {
        "1_naomi_album": ("1_album_naomi", "1. אלבום של נעמי שמר"),
        "5_cover_version": ("5_cover", "5. ביצוע מחודש / קאבר"),
        "6_no_youtube": ("6_not_found", "6. לא נמצא סרטון תואם"),
    }
    canonical_tier_labels = {
        "5_cover": "5. ביצוע מחודש / קאבר",
    }
    valid_matched_tiers = {
        "1_album_naomi",
        "2_album_original",
        "3_naomi_performance",
        "4_original_performance",
        "5_cover",
    }

    changed = False
    matched_entries = []
    unmatched_entries = []
    seen_primary_vids = {}
    by_title = {}

    for item in playlist:
        if str(item.get("year", "")) == "2099":
            item["year"] = ""
            changed = True
        ag_val = str(item.get("album_group", "") or "").strip()
        if ag_val.startswith("ביצוע נעמי שמר (אחרי האלבום:") or ag_val == "סינגל / ביצוע בודד (ביצוע נעמי שמר)":
            item["album_group"] = "סינגל / ביצוע בודד"
            changed = True
        if "catalog_performers" in item:
            norm_cp = normalize_performers_list(item.get("catalog_performers", []))
            if norm_cp != item.get("catalog_performers", []):
                item["catalog_performers"] = norm_cp
                changed = True
        t = item.get("tier", "")
        if t in tier_norm:
            item["tier"], item["tier_label"] = tier_norm[t]
            changed = True
        if item.get("tier") in canonical_tier_labels and item.get("tier_label") != canonical_tier_labels[item["tier"]]:
            item["tier_label"] = canonical_tier_labels[item["tier"]]
            changed = True
        sel = item.get("selected_video")
        if sel and sel.get("video_id"):
            st = sel.get("tier", "")
            if st in tier_norm:
                sel["tier"], sel["tier_label"] = tier_norm[st]
                changed = True
            if sel.get("tier") in canonical_tier_labels and sel.get("tier_label") != canonical_tier_labels[sel["tier"]]:
                sel["tier_label"] = canonical_tier_labels[sel["tier"]]
                changed = True
            matched_entries.append(item)
            by_title.setdefault(item["title"], []).append(item)
        else:
            if item.get("tier") != "6_not_found":
                item["tier"] = "6_not_found"
                item["tier_label"] = "6. לא נמצא סרטון תואם"
                changed = True
            unmatched_entries.append(item)

    # Recompute dual_role and version numbering per song (assigning original_performance to the true historical original)
    def _is_non_song_clip(entry: dict) -> bool:
        if entry.get("album_group") == "תוכניות טלוויזיה ומופעים מלאים":
            return True
        sv = entry.get("selected_video") or {}
        txt = f"{sv.get('matched_performer', '')} {sv.get('video_title', '')}"
        return any(w in txt for w in ("ראיון", "פרודיה", "סקיצה נדירה", "חזרה,"))

    for title, group in by_title.items():
        total_v = len(group)
        orig_idx = 0
        if total_v > 1:
            explicit_orig = [idx_g for idx_g, x in enumerate(group) if x.get("is_true_original")]
            if explicit_orig:
                orig_idx = explicit_orig[0]
            else:
                candidates = [
                    (
                        int(str(x.get("year", "")).strip()) if str(x.get("year", "")).strip().isdigit() else 9999,
                        0 if x.get("tier") != "5_cover" else 1,
                        idx_g,
                    )
                    for idx_g, x in enumerate(group)
                    if not _is_non_song_clip(x)
                ]
                if candidates:
                    orig_idx = min(candidates)[2]

        for idx_in_group, it in enumerate(group):
            it["ver_idx"] = idx_in_group + 1
            it["ver_total"] = total_v
            if total_v == 1:
                if "dual_role" in it:
                    del it["dual_role"]
                    changed = True
            else:
                if idx_in_group == orig_idx:
                    new_role = "original_performance"
                elif it.get("tier") in ("1_album_naomi", "3_naomi_performance"):
                    new_role = "naomi_performance"
                else:
                    new_role = "additional_performance"
                if it.get("dual_role") != new_role:
                    it["dual_role"] = new_role
                    changed = True

    ordered = matched_entries + unmatched_entries
    for i, it in enumerate(ordered, 1):
        if it.get("index") != i:
            it["index"] = i
            changed = True

    def _chrono_sort_key(it: dict):
        yr_s = str(it.get("year", "") or "").strip()
        yr_num = int(yr_s) if (yr_s.isdigit() and int(yr_s) < 2099) else 9999
        prev_c = it.get("chrono_index")
        prev_c_num = int(prev_c) if isinstance(prev_c, int) else 999999
        return (yr_num, prev_c_num, it["index"])

    for c_idx, it in enumerate(sorted(matched_entries, key=_chrono_sort_key), 1):
        if it.get("chrono_index") != c_idx:
            it["chrono_index"] = c_idx
            changed = True

    # Integrity validation checks
    errors = []
    for it in matched_entries:
        vid = it["selected_video"]["video_id"]
        if vid in seen_primary_vids:
            errors.append(f"Duplicate primary video_id {vid} at #{it['index']} and #{seen_primary_vids[vid]}")
        seen_primary_vids[vid] = it["index"]
        if it.get("tier") not in valid_matched_tiers:
            errors.append(f"Invalid tier '{it.get('tier')}' at #{it['index']} ({it['title']})")
        for a in it.get("alternative_videos", []):
            if a.get("video_id") == vid:
                errors.append(f"Self-referencing backup video_id {vid} at #{it['index']}")

    if errors:
        print("⚠️ אזהרות שלמות נתונים:")
        for e in errors:
            print("  -", e)
    else:
        print(f"✔ בדיקת שלמות נתונים עברה בהצלחה ({len(matched_entries)} סרטונים ייחודיים, 0 שגיאות).")

    data["playlist"] = ordered
    stats = data.setdefault("stats", {})
    matched_songs_cnt = len(by_title)
    total_songs_cnt = len({it["title"] for it in ordered})
    by_tier_map = {}
    tier_breakdown_map = {}
    for it in ordered:
        tl = it.get("tier_label", "")
        tk = it.get("tier", "")
        if tl:
            by_tier_map[tl] = by_tier_map.get(tl, 0) + 1
        if tk:
            tier_breakdown_map[tk] = tier_breakdown_map.get(tk, 0) + 1

    if (
        stats.get("matched_videos") != len(matched_entries)
        or stats.get("matched_songs") != matched_songs_cnt
        or stats.get("unmatched_songs") != len(unmatched_entries)
        or stats.get("total_songs") != total_songs_cnt
        or stats.get("total_playlist_entries") != len(ordered)
        or stats.get("by_tier") != by_tier_map
        or stats.get("tier_breakdown") != tier_breakdown_map
    ):
        changed = True
    stats["total_songs"] = total_songs_cnt
    stats["total_catalog_songs"] = total_songs_cnt
    stats["matched_songs"] = matched_songs_cnt
    stats["unmatched_songs"] = len(unmatched_entries)
    stats["total_playlist_videos"] = len(matched_entries)
    stats["total_videos"] = len(matched_entries)
    stats["matched_videos"] = len(matched_entries)
    stats["total_playlist_entries"] = len(ordered)
    stats["by_tier"] = by_tier_map
    stats["tier_breakdown"] = tier_breakdown_map
    return changed


def generate_files():
    playlist_json_path = os.path.join(BASE_DIR, "naomi_shemer_youtube_playlist.json")
    with open(playlist_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if validate_and_normalize_playlist(data):
        with open(playlist_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    playlist = data["playlist"]

    matched_entries = [item for item in playlist if item.get("selected_video")]
    unmatched_entries = [item for item in playlist if not item.get("selected_video")]

    total_videos = len(matched_entries)
    matched_songs_count = len({item["title"] for item in matched_entries})
    unmatched_songs_count = len(unmatched_entries)
    total_catalog_songs = len({item["title"] for item in playlist})

    video_ids = [item["selected_video"]["video_id"] for item in matched_entries]

    # 1. יצירת create_playlist_in_browser.js
    js_script = f"""// ============================================================================
// יצירת פלייליסט "שירי נעמי שמר - האוסף המקיף" ({total_videos} ביצועים) בחשבון היוטיוב שלך
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com בדפדפן וודא שאתה מחובר לחשבון היוטיוב שלך.
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console של הדפדפן.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// תוך כ-10 שניות הפלייליסט ייווצר וייפתח אוטומטית!
// ============================================================================
(async function createNaomiShemerPlaylist() {{
  const VIDEO_IDS = {json.dumps(video_ids, ensure_ascii=False)};
  const PLAYLIST_TITLE = "שירי נעמי שמר";
  const PLAYLIST_DESC = "אוסף מקיף של שירי נעמי שמר (אלבומיה של נעמי שמר, ביצועים מקוריים מתוך אלבומים, הקלטות ארכיון וקאברים נבחרים). נוצר מתוך איחוד 9 מאגרים (אקו\\"ם, הספרייה הלאומית, שירונט, ויקיפדיה, סטריאו ומונו, פזמונט, זמרשת, Discogs ו-MusicBrainz).";

  if (!window.ytcfg || typeof window.ytcfg.get !== "function") {{
    alert("שגיאה: יש להריץ את הסקריפט מתוך לשונית פתוחה של https://www.youtube.com");
    return;
  }}

  function getCookie(name) {{
    const m = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([.$?*|{{}}()\\[\\]\\\\/+^])/g, "\\\\$1") + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : null;
  }}

  const sapisid = getCookie("SAPISID") || getCookie("__Secure-3PAPISID");
  if (!sapisid) {{
    alert("שגיאה: לא נמצא חיבור לחשבון יוטיוב. אנא התחבר לחשבון היוטיוב שלך ב-https://www.youtube.com ונסה שוב.");
    return;
  }}

  async function makeSapisidHash(origin) {{
    const ts = Math.floor(Date.now() / 1000);
    const input = ts + " " + sapisid + " " + origin;
    const buf = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(input));
    const hex = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    return "SAPISIDHASH " + ts + "_" + hex;
  }}

  async function ytPost(endpoint, bodyObj) {{
    const origin = window.location.origin;
    const auth = await makeSapisidHash(origin);
    const headers = {{
      "Content-Type": "application/json",
      "Authorization": auth,
      "X-Origin": origin,
      "X-Goog-AuthUser": String(window.ytcfg.get("SESSION_INDEX") ?? "0"),
    }};
    const visitor = window.ytcfg.get("VISITOR_DATA");
    if (visitor) headers["X-Goog-Visitor-Id"] = visitor;

    const resp = await fetch(origin + endpoint + "?prettyPrint=false", {{
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({{
        context: window.ytcfg.get("INNERTUBE_CONTEXT"),
        ...bodyObj
      }})
    }});
    if (!resp.ok) {{
      const txt = await resp.text();
      throw new Error("HTTP " + resp.status + ": " + txt.slice(0, 300));
    }}
    return resp.json();
  }}

  console.log("🚀 יוצר פלייליסט חדש ביוטיוב:", PLAYLIST_TITLE);
  const createRes = await ytPost("/youtubei/v1/playlist/create", {{
    title: PLAYLIST_TITLE,
    description: PLAYLIST_DESC,
    privacyStatus: "UNLISTED"
  }});

  const playlistId = createRes.playlistId;
  if (!playlistId) {{
    console.error("תגובת שרת:", createRes);
    throw new Error("לא התקבל playlistId מיוטיוב.");
  }}
  console.log("✅ הפלייליסט נוצר בהצלחה! מזהה:", playlistId);

  const BATCH_SIZE = 50;
  for (let i = 0; i < VIDEO_IDS.length; i += BATCH_SIZE) {{
    const batch = VIDEO_IDS.slice(i, i + BATCH_SIZE);
    console.log(`⏳ מוסיף שירים ${{i + 1}} עד ${{Math.min(i + BATCH_SIZE, VIDEO_IDS.length)}} מתוך ${{VIDEO_IDS.length}}...`);
    await ytPost("/youtubei/v1/browse/edit_playlist", {{
      playlistId: playlistId,
      actions: batch.map(vid => ({{
        action: "ACTION_ADD_VIDEO",
        addedVideoId: vid
      }}))
    }});
    await new Promise(r => setTimeout(r, 600));
  }}

  const url = "https://www.youtube.com/playlist?list=" + playlistId;
  console.log("🎉 סיימנו! כל " + VIDEO_IDS.length + " השירים נוספו לפלייליסט:");
  console.log(url);
  window.open(url, "_blank");
}})();
"""

    js_path = os.path.join(BASE_DIR, "create_playlist_in_browser.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_script)

    # 1b. יצירת update_existing_playlist_in_browser.js (עדכון הפלייליסט הקיים PLFHErlX6i22g + וידוא מלא מול שרתי יוטיוב)
    vid_to_title = {item["selected_video"]["video_id"]: f"{item['title']} ({item.get('year','')})" for item in matched_entries}
    update_js_script = f"""// ============================================================================
// עדכון הפלייליסט הקיים ביוטיוב (PLFHErlX6i22g) + וידוא אוטומטי של הסדר הסופי!
// הוראות הפעלה:
// 1. פתח את https://www.youtube.com/playlist?list=PLFHErlX6i22g בדפדפן (מחובר לחשבון שלך).
// 2. לחץ Cmd+Option+J (במק) או F12 כדי לפתוח את ה-Console.
// 3. הדבק את כל הקוד הזה ב-Console ולחץ Enter.
// הסקריפט יעדכן את הפלייליסט הקיים (PLFHErlX6i22g), ובסיום יקרא מחדש את כל הרצועות
// משרתי יוטיוב כדי לוודא ב-100% שהסידור הסופי תואם לרשימת היעד (ויתקן אוטומטית כל סטייה).
// ============================================================================
(async function updateExistingNaomiShemerPlaylist() {{
  const PLAYLIST_ID = "PLFHErlX6i22g";
  const PLAYLIST_TITLE = "שירי נעמי שמר";
  const TARGET_VIDEO_IDS = {json.dumps(video_ids, ensure_ascii=False)};
  const VIDEO_TITLES = {json.dumps(vid_to_title, ensure_ascii=False)};

  if (!window.ytcfg || typeof window.ytcfg.get !== "function") {{
    alert("שגיאה: יש להריץ את הסקריפט מתוך לשונית פתוחה של https://www.youtube.com");
    return;
  }}

  function getCookie(name) {{
    const m = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([.$?*|{{}}()\\[\\]\\\\/+^])/g, "\\\\$1") + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : null;
  }}

  const sapisid = getCookie("SAPISID") || getCookie("__Secure-3PAPISID");
  if (!sapisid) {{
    alert("שגיאה: לא נמצא חיבור לחשבון יוטיוב. אנא התחבר לחשבון היוטיוב שלך ונסה שוב.");
    return;
  }}

  async function makeSapisidHash(origin) {{
    const ts = Math.floor(Date.now() / 1000);
    const input = ts + " " + sapisid + " " + origin;
    const buf = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(input));
    const hex = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    return "SAPISIDHASH " + ts + "_" + hex;
  }}

  async function ytPost(endpoint, bodyObj) {{
    const origin = window.location.origin;
    const auth = await makeSapisidHash(origin);
    const headers = {{
      "Content-Type": "application/json",
      "Authorization": auth,
      "X-Origin": origin,
      "X-Goog-AuthUser": String(window.ytcfg.get("SESSION_INDEX") ?? "0"),
    }};
    const visitor = window.ytcfg.get("VISITOR_DATA");
    if (visitor) headers["X-Goog-Visitor-Id"] = visitor;

    const resp = await fetch(origin + endpoint + "?prettyPrint=false", {{
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({{
        context: window.ytcfg.get("INNERTUBE_CONTEXT"),
        ...bodyObj
      }})
    }});
    if (!resp.ok) {{
      const txt = await resp.text();
      throw new Error("HTTP " + resp.status + ": " + txt.slice(0, 300));
    }}
    return resp.json();
  }}

  // שליפת כל הסרטונים הקיימים כרגע בפלייליסט (כולל סרטונים מוסתרים/לא זמינים עם params: "wgYCCAA=")
  function findSetVideoId(node, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 22) return null;
    if (typeof node.setVideoId === "string" && node.setVideoId) return node.setVideoId;
    if (Array.isArray(node)) {{
      for (const el of node) {{
        const found = findSetVideoId(el, depth + 1);
        if (found) return found;
      }}
      return null;
    }}
    for (const k of Object.keys(node)) {{
      const found = findSetVideoId(node[k], depth + 1);
      if (found) return found;
    }}
    return null;
  }}

  function findWatchVideoId(node, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 10) return null;
    if (node.watchEndpoint && typeof node.watchEndpoint.videoId === "string" && node.watchEndpoint.videoId) {{
      return node.watchEndpoint.videoId;
    }}
    if (Array.isArray(node)) {{
      for (const el of node) {{
        const found = findWatchVideoId(el, depth + 1);
        if (found) return found;
      }}
      return null;
    }}
    for (const k of Object.keys(node)) {{
      if (k === "menuButton") continue;
      const found = findWatchVideoId(node[k], depth + 1);
      if (found) return found;
    }}
    return null;
  }}

  function nodeBelongsToPlaylist(node, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 14) return false;
    if (node.playlistId === PLAYLIST_ID) return true;
    if (Array.isArray(node)) return node.some(el => nodeBelongsToPlaylist(el, depth + 1));
    for (const k of Object.keys(node)) {{
      if (nodeBelongsToPlaylist(node[k], depth + 1)) return true;
    }}
    return false;
  }}

  function findContinuationTokens(node, tokensOut, seenTokens, depth = 0) {{
    if (!node || typeof node !== "object" || depth > 16) return;
    if (node.continuationCommand && typeof node.continuationCommand.token === "string") {{
      const tok = node.continuationCommand.token;
      if (tok && tok.startsWith("4qmF") && !seenTokens.has(tok)) {{
        seenTokens.add(tok);
        tokensOut.push(tok);
      }}
    }}
    if (node.nextContinuationData && typeof node.nextContinuationData.continuation === "string") {{
      const tok = node.nextContinuationData.continuation;
      if (tok && !seenTokens.has(tok)) {{
        seenTokens.add(tok);
        tokensOut.push(tok);
      }}
    }}
    if (Array.isArray(node)) {{
      for (const el of node) findContinuationTokens(el, tokensOut, seenTokens, depth + 1);
      return;
    }}
    for (const k of Object.keys(node)) {{
      findContinuationTokens(node[k], tokensOut, seenTokens, depth + 1);
    }}
  }}

  function extractVideosAndContinuation(obj, itemsOut, tokensOut, seenTokens) {{
    if (!obj || typeof obj !== "object") return;
    if (Array.isArray(obj)) {{
      for (const el of obj) extractVideosAndContinuation(el, itemsOut, tokensOut, seenTokens);
      return;
    }}
    // דילוג על מדפי המלצות ("Recommended videos") שיוטיוב מציג לבעל הפלייליסט ואינם שייכים לפלייליסט!
    if (obj.reelShelfRenderer || obj.shelfRenderer || obj.horizontalCardListRenderer) {{
      return;
    }}
    if (obj.playlistVideoRenderer) {{
      const r = obj.playlistVideoRenderer;
      const svid = r.setVideoId || findSetVideoId(r) || null;
      if ((r.videoId || svid) && (svid || nodeBelongsToPlaylist(r))) {{
        itemsOut.push({{
          videoId: r.videoId || null,
          setVideoId: svid
        }});
      }}
      return;
    }}
    if (obj.lockupViewModel) {{
      const lv = obj.lockupViewModel;
      const vid = lv.contentId || findWatchVideoId(lv);
      const svid = findSetVideoId(lv);
      const isVidType = lv.contentType === "LOCKUP_CONTENT_TYPE_VIDEO" || !lv.contentType;
      if (((vid && isVidType) || svid) && (svid || nodeBelongsToPlaylist(lv))) {{
        itemsOut.push({{
          videoId: vid || null,
          setVideoId: svid
        }});
      }}
      return;
    }}
    if (obj.continuationItemRenderer || obj.continuationItemViewModel) {{
      findContinuationTokens(obj, tokensOut, seenTokens);
      return;
    }}
    if (obj.continuations && Array.isArray(obj.continuations)) {{
      findContinuationTokens(obj.continuations, tokensOut, seenTokens);
    }}
    for (const k of Object.keys(obj)) {{
      extractVideosAndContinuation(obj[k], itemsOut, tokensOut, seenTokens);
    }}
  }}

  function getFirstSectionRoot(browseData) {{
    const secContents = browseData?.contents?.twoColumnBrowseResultsRenderer?.tabs?.[0]?.tabRenderer?.content?.sectionListRenderer?.contents;
    if (Array.isArray(secContents) && secContents.length > 0) {{
      // תמיד קוראים אך ורק את contents[0] (רשימת הפלייליסט עצמה), ולא את contents[1] (סרטונים מומלצים להוספה)!
      return secContents[0];
    }}
    return browseData;
  }}

  // includeUnavailable=true שולח params: "wgYCCAA=" ("Show unavailable videos") כך שגם סרטונים מוסתרים מזוהים ונמחקים!
  async function fetchCurrentPlaylistItems(includeUnavailable = true) {{
    const items = [];
    const tokens = [];
    const seenTokens = new Set();
    const reqBody = {{ browseId: "VL" + PLAYLIST_ID }};
    if (includeUnavailable) reqBody.params = "wgYCCAA=";
    const firstPage = await ytPost("/youtubei/v1/browse", reqBody);
    extractVideosAndContinuation(getFirstSectionRoot(firstPage), items, tokens, seenTokens);
    while (tokens.length > 0) {{
      const tok = tokens.shift();
      const nextPage = await ytPost("/youtubei/v1/browse", {{ continuation: tok }});
      extractVideosAndContinuation(nextPage, items, tokens, seenTokens);
    }}
    return items;
  }}

  function buildRemoveActions(items) {{
    const actions = [];
    const seenVid = new Set();
    for (const item of items) {{
      if (item.setVideoId) {{
        actions.push({{ action: "ACTION_REMOVE_VIDEO", setVideoId: item.setVideoId }});
      }} else if (item.videoId && !seenVid.has(item.videoId)) {{
        seenVid.add(item.videoId);
        actions.push({{ action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID", removedVideoId: item.videoId }});
      }}
    }}
    return actions;
  }}

  async function safeDeleteBatch(batch) {{
    if (!batch || batch.length === 0) return;
    try {{
      await ytPost("/youtubei/v1/browse/edit_playlist", {{
        playlistId: PLAYLIST_ID,
        actions: batch
      }});
    }} catch (err) {{
      console.warn(`⚠️ מחיקת אצווה נתקלה בשגיאה (${{err.message.slice(0, 80)}}), מנסה פריט-פריט...`);
      for (const act of batch) {{
        try {{
          await ytPost("/youtubei/v1/browse/edit_playlist", {{
            playlistId: PLAYLIST_ID,
            actions: [act]
          }});
        }} catch (innerErr) {{
          console.warn("  ⏭️ דילוג על פריט שאינו בפלייליסט:", act, innerErr.message.slice(0, 60));
        }}
        await new Promise(r => setTimeout(r, 120));
      }}
    }}
  }}

  // עדכון שם הפלייליסט ל-"שירי נעמי שמר"
  try {{
    await ytPost("/youtubei/v1/browse/edit_playlist", {{
      playlistId: PLAYLIST_ID,
      actions: [{{ action: "ACTION_SET_PLAYLIST_NAME", playlistName: PLAYLIST_TITLE }}]
    }});
    console.log(`🏷️ שם הפלייליסט עודכן ל: "${{PLAYLIST_TITLE}}"`);
  }} catch (e) {{
    console.warn("⚠️ לא הצלחתי לעדכן את שם הפלייליסט אוטומטית:", e.message);
  }}

  console.log("🔍 קורא את מצב הפלייליסט הקיים ביוטיוב (" + PLAYLIST_ID + ")...");
  let currentItems = await fetchCurrentPlaylistItems();
  console.log(`📋 נמצאו כרגע בפלייליסט ${{currentItems.length}} סרטונים (יעד רצוי: ${{TARGET_VIDEO_IDS.length}} סרטונים).`);

  // הגנה: אם הקריאה מיוטיוב החזירה 0 סרטונים בזמן שעל הדף עצמו יש סרטונים — עצור מיד לפני הוספה כפולה!
  if (currentItems.length === 0 && window.ytInitialData) {{
    const pageItems = [];
    const dummyTokens = [];
    extractVideosAndContinuation(getFirstSectionRoot(window.ytInitialData), pageItems, dummyTokens, new Set());
    if (pageItems.length > 0) {{
      console.error(`❌ עצירת חירום: בדף מופיעים ${{pageItems.length}} סרטונים אך קריאת ה-API החזירה 0. לא מוסיף כדי למנוע כפילויות!`);
      return;
    }}
  }}

  const curIds = currentItems.map(x => x.videoId);
  if (curIds.length === TARGET_VIDEO_IDS.length && curIds.every((v, i) => v === TARGET_VIDEO_IDS[i])) {{
    console.log("✅ [וידוא הושלם] הפלייליסט כבר מסודר ומעודכן ב-100% לפי הסדר המבוקש!");
    return;
  }}

  // חישוב תת-הסדרה המשותפת הארוכה ביותר (LCS) לצורך עדכון כירורגי מהיר ללא מחיקת כל הפלייליסט
  function computeLcsSet(a, b) {{
    const n = a.length, m = b.length;
    const dp = Array.from({{ length: n + 1 }}, () => new Int16Array(m + 1));
    for (let i = n - 1; i >= 0; i--) {{
      for (let j = m - 1; j >= 0; j--) {{
        dp[i][j] = a[i] === b[j] ? 1 + dp[i + 1][j + 1] : Math.max(dp[i + 1][j], dp[i][j + 1]);
      }}
    }}
    const keepInA = new Set();
    let i = 0, j = 0;
    while (i < n && j < m) {{
      if (a[i] === b[j]) {{
        keepInA.add(a[i]);
        i++; j++;
      }} else if (dp[i + 1][j] >= dp[i][j + 1]) {{
        i++;
      }} else {{
        j++;
      }}
    }}
    return keepInA;
  }}

  const BATCH_SIZE = 50;
  const targetSetInit = new Set(TARGET_VIDEO_IDS);
  const seenInCur = new Set();
  const toDeleteItems = [];
  for (const it of currentItems) {{
    if (!targetSetInit.has(it.videoId) || seenInCur.has(it.videoId)) {{
      toDeleteItems.push(it);
    }} else {{
      seenInCur.add(it.videoId);
    }}
  }}
  const toAddVids = TARGET_VIDEO_IDS.filter(v => !seenInCur.has(v));
  const survivingCurIds = currentItems.filter(it => !toDeleteItems.includes(it)).map(it => it.videoId);
  const commonTargetIds = TARGET_VIDEO_IDS.filter(v => seenInCur.has(v));
  const lcsKeep = computeLcsSet(survivingCurIds, commonTargetIds);
  const estMoves = (commonTargetIds.length - lcsKeep.size) + toAddVids.length;
  const totalSurgicalOps = toDeleteItems.length + toAddVids.length + estMoves;

  const hasAllSetIds = currentItems.every(it => Boolean(it.setVideoId));
  if (currentItems.length > 0 && totalSurgicalOps <= 120 && (estMoves === 0 || hasAllSetIds)) {{
    console.log(`⚡ מבצע עדכון כירורגי מהיר (${{toDeleteItems.length}} מחיקות, ${{toAddVids.length}} הוספות, ${{estMoves}} הזזות מיקום)...`);
    if (toDeleteItems.length > 0) {{
      const delActions = buildRemoveActions(toDeleteItems);
      for (let i = 0; i < delActions.length; i += BATCH_SIZE) {{
        const batch = delActions.slice(i, i + BATCH_SIZE);
        await safeDeleteBatch(batch);
        await new Promise(r => setTimeout(r, 400));
      }}
    }}
    if (toAddVids.length > 0) {{
      for (let i = 0; i < toAddVids.length; i += BATCH_SIZE) {{
        const batch = toAddVids.slice(i, i + BATCH_SIZE);
        await ytPost("/youtubei/v1/browse/edit_playlist", {{
          playlistId: PLAYLIST_ID,
          actions: batch.map(vid => ({{ action: "ACTION_ADD_VIDEO", addedVideoId: vid }}))
        }});
        await new Promise(r => setTimeout(r, 500));
      }}
    }}
    if (estMoves > 0) {{
      await new Promise(r => setTimeout(r, 900));
      currentItems = await fetchCurrentPlaylistItems();
      const curMap = new Map(currentItems.map(it => [it.videoId, it.setVideoId]));
      const presentTarget = TARGET_VIDEO_IDS.filter(v => curMap.has(v));
      const lcsNow = computeLcsSet(currentItems.map(it => it.videoId), presentTarget);
      // עוברים מהסוף להתחלה ומזיזים רק רצועות שאינן ב-LCS אל לפני הרצועה העוקבת שלהן
      for (let k = presentTarget.length - 2; k >= 0; k--) {{
        const vid = presentTarget[k];
        if (!lcsNow.has(vid)) {{
          const nextVid = presentTarget[k + 1];
          const setVid = curMap.get(vid);
          const succSetVid = curMap.get(nextVid);
          if (setVid && succSetVid) {{
            await ytPost("/youtubei/v1/browse/edit_playlist", {{
              playlistId: PLAYLIST_ID,
              actions: [{{
                action: "ACTION_MOVE_VIDEO_BEFORE",
                setVideoId: setVid,
                movedSetVideoIdSuccessor: succSetVid
              }}]
            }});
            lcsNow.add(vid);
          }}
        }}
      }}
    }}
  }} else {{
    console.log("🔄 מבצע עדכון סדר מלא בתוך הפלייליסט הקיים (" + PLAYLIST_ID + ")...");
    // שלב א': ניקוי הרשימה הישנה (עם וידוא שהרשימה התרוקנה לגמרי לפני הוספה)
    let pass = 1;
    while (currentItems.length > 0 && pass <= 10) {{
      const delActions = buildRemoveActions(currentItems);
      if (delActions.length === 0) break;
      for (let i = 0; i < delActions.length; i += BATCH_SIZE) {{
        const batch = delActions.slice(i, i + BATCH_SIZE);
        console.log(`🗑️ מנקה סדר ישן (סבב ${{pass}}: ${{i + 1}} עד ${{Math.min(i + BATCH_SIZE, delActions.length)}} מתוך ${{delActions.length}})...`);
        await safeDeleteBatch(batch);
        await new Promise(r => setTimeout(r, 450));
      }}
      await new Promise(r => setTimeout(r, 1200));
      currentItems = await fetchCurrentPlaylistItems();
      pass++;
    }}

    if (currentItems.length > 0) {{
      console.error(`❌ עצירה לפני הוספה: נותרו עדיין ${{currentItems.length}} סרטונים בפלייליסט לאחר ניקוי. רענן את העמוד והרץ שוב כדי להשלים ללא כפילויות.`);
      return;
    }}

    // שלב ב': הוספת כל הסרטונים לפי הסדר החדש
    for (let i = 0; i < TARGET_VIDEO_IDS.length; i += BATCH_SIZE) {{
      const batch = TARGET_VIDEO_IDS.slice(i, i + BATCH_SIZE);
      console.log(`⏳ מוסיף בסדר החדש ${{i + 1}} עד ${{Math.min(i + BATCH_SIZE, TARGET_VIDEO_IDS.length)}} מתוך ${{TARGET_VIDEO_IDS.length}}...`);
      await ytPost("/youtubei/v1/browse/edit_playlist", {{
        playlistId: PLAYLIST_ID,
        actions: batch.map(vid => ({{
          action: "ACTION_ADD_VIDEO",
          addedVideoId: vid
        }}))
      }});
      await new Promise(r => setTimeout(r, 550));
    }}
  }}

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
  finalIds.forEach((vid, idx) => {{
    if (!visibleSet.has(vid)) {{
      hiddenNow.push({{ position: idx + 1, videoId: vid, title: VIDEO_TITLES[vid] || vid }});
    }}
  }});
  if (hiddenNow.length === 0) {{
    console.log("🟢 בדיקת זמינות: 0 סרטונים מוסתרים/לא-זמינים בפלייליסט באזור הגלישה שלך!");
  }} else {{
    console.warn(`⚠️ שים לב: יוטיוב מסתיר כעת באזור הגלישה שלך ${{hiddenNow.length}} סרטונים (חסימה אזורית או הסרה):`);
    console.table(hiddenNow);
  }}

  // 1. בדיקת התאמה מלאה של הרשימה והסדר
  if (finalIds.length === TARGET_VIDEO_IDS.length && finalIds.every((v, i) => v === TARGET_VIDEO_IDS[i])) {{
    console.log(`✅ [וידוא הושלם בהצלחה - 100% התאמה!] כל ${{finalIds.length}} השירים נמצאים בפלייליסט ${{PLAYLIST_ID}} בדיוק בסדר המבוקש!`);
    console.log("🔄 מרענן את העמוד בעוד 2 שניות כדי להציג את הרשימה המעודכנת...");
    setTimeout(() => location.reload(), 2000);
    return;
  }}

  console.warn(`⚠️ נמצא פער בבדיקה הראשונית: בפלייליסט יש ${{finalIds.length}} שירים לעומת ${{TARGET_VIDEO_IDS.length}} ברשימת היעד. מנתח ומתקן...`);

  // 2. איתור סרטונים שיוטיוב לא הצליח להוסיף (למשל סרטון שהפך לפרטי/נמחק)
  const finalSet = new Set(finalIds);
  const targetSet = new Set(TARGET_VIDEO_IDS);
  const missingFromYt = [];
  TARGET_VIDEO_IDS.forEach((vid, idx) => {{
    if (!finalSet.has(vid)) {{
      missingFromYt.push({{ index: idx + 1, videoId: vid, title: VIDEO_TITLES[vid] || vid }});
    }}
  }});

  if (missingFromYt.length > 0 && missingFromYt.length <= 40) {{
    console.log(`🔧 מנסה להוסיף שוב ${{missingFromYt.length}} סרטונים שחסרים בפלייליסט...`);
    for (const m of missingFromYt) {{
      try {{
        await ytPost("/youtubei/v1/browse/edit_playlist", {{
          playlistId: PLAYLIST_ID,
          actions: [{{ action: "ACTION_ADD_VIDEO", addedVideoId: m.videoId }}]
        }});
        console.log(`  ➕ נוסף בהצלחה: #${{m.index}} ${{m.title}} (${{m.videoId}})`);
      }} catch (err) {{
        console.error(`  ❌ יוטיוב דחה את הסרטון #${{m.index}} ${{m.title}} (${{m.videoId}}):`, err.message);
      }}
      await new Promise(r => setTimeout(r, 250));
    }}
  }} else if (missingFromYt.length > 40) {{
    console.warn(`⚠️ חסרים ${{missingFromYt.length}} סרטונים — מדלג על הוספה פרטנית כדי למנוע חסימת קצב מיוטיוב.`);
  }}

  // 3. הסרת סרטונים עודפים או כפולים שאינם ברשימת היעד (באצוות של 50)
  const seenCounts = {{}};
  const targetCounts = {{}};
  TARGET_VIDEO_IDS.forEach(v => {{ targetCounts[v] = (targetCounts[v] || 0) + 1; }});
  const toRemoveExtra = [];
  for (const item of finalItems) {{
    seenCounts[item.videoId] = (seenCounts[item.videoId] || 0) + 1;
    if (!targetSet.has(item.videoId) || seenCounts[item.videoId] > (targetCounts[item.videoId] || 0)) {{
      toRemoveExtra.push(item);
    }}
  }}
  if (toRemoveExtra.length > 0) {{
    const extraActions = buildRemoveActions(toRemoveExtra);
    console.log(`🧹 מסיר ${{extraActions.length}} סרטונים עודפים/כפולים...`);
    for (let i = 0; i < extraActions.length; i += BATCH_SIZE) {{
      const batch = extraActions.slice(i, i + BATCH_SIZE);
      await safeDeleteBatch(batch);
      await new Promise(r => setTimeout(r, 450));
    }}
  }}

  // 4. בדיקה חוזרת של הסדר היחסי ותיקון מיקומים במידת הצורך
  await new Promise(r => setTimeout(r, 1200));
  finalItems = await fetchCurrentPlaylistItems();
  finalIds = finalItems.map(x => x.videoId);
  const availableTargets = TARGET_VIDEO_IDS.filter(v => finalIds.includes(v));

  let orderMismatches = [];
  for (let i = 0; i < Math.min(finalIds.length, availableTargets.length); i++) {{
    if (finalIds[i] !== availableTargets[i]) {{
      orderMismatches.push({{
        position: i + 1,
        expected: availableTargets[i],
        expectedTitle: VIDEO_TITLES[availableTargets[i]] || availableTargets[i],
        actual: finalIds[i],
        actualTitle: VIDEO_TITLES[finalIds[i]] || finalIds[i]
      }});
    }}
  }}

  if (orderMismatches.length === 0 && finalIds.length === TARGET_VIDEO_IDS.length) {{
    console.log(`✅ [וידוא הושלם בהצלחה לאחר תיקון!] כל ${{finalIds.length}} השירים נמצאים בפלייליסט בדיוק בסדר המבוקש!`);
    setTimeout(() => location.reload(), 2000);
  }} else if (orderMismatches.length === 0) {{
    console.log(`✅ [וידוא סדר הושלם] הסדר של כל ${{finalIds.length}} הסרטונים הזמינים תואם ב-100% לסדר המבוקש!`);
    const stillMissing = TARGET_VIDEO_IDS.filter(v => !finalIds.includes(v)).map(v => ({{ videoId: v, title: VIDEO_TITLES[v] || v }}));
    if (stillMissing.length > 0) {{
      console.warn("⚠️ סרטונים שיוטיוב לא איפשר להוסיף (כנראה הוסרו/נחסמו ביוטיוב):", stillMissing);
      console.table(stillMissing);
    }}
    setTimeout(() => location.reload(), 3000);
  }} else {{
    console.warn(`⚠️ נמצאו ${{orderMismatches.length}} אי-התאמות מיקום (מתוך ${{finalIds.length}} שירים):`);
    console.table(orderMismatches.slice(0, 20));
  }}
}})();
"""
    update_js_path = os.path.join(BASE_DIR, "update_existing_playlist_in_browser.js")
    with open(update_js_path, "w", encoding="utf-8") as f:
        f.write(update_js_script)

    # 2. בניית נתוני SONGS ו-ARCHIVE_SONGS עבור ה-HTML (ללא פסקאות notes מועתקות; פרטים עובדתיים + קישור לספרייה הלאומית)
    songs_js = []
    tier_counts = {}
    role_counts = {}
    decade_counts = {}
    layer_counts = {1: 0, 2: 0, 3: 0}
    in_extras_section = False
    seen_primary_titles = set()
    prev_primary_lyr = 1

    for idx_item, item in enumerate(matched_entries):
        sel = item["selected_video"]
        yr = item.get("year", "")
        yr_display = yr if (yr and str(yr) != "2099") else ""
        dual_role = item.get("dual_role", "")
        if dual_role == "original_performance":
            role_suffix = " [ביצוע מקורי]"
        elif dual_role == "naomi_performance":
            role_suffix = " [ביצוע נעמי שמר]"
        elif dual_role == "additional_performance":
            perf_lbl = sel.get("matched_performer", "").strip()
            role_suffix = f" [ביצוע: {perf_lbl}]" if perf_lbl else " [ביצוע נוסף]"
        else:
            role_suffix = ""

        display_title = f"{item['title']}{role_suffix}" + (f" ({yr_display})" if yr_display else "")
        tier = item["tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        rcat = item.get("role_category", "words_and_music")
        role_counts[rcat] = role_counts.get(rcat, 0) + 1

        dec = get_decade(yr_display)
        decade_counts[dec] = decade_counts.get(dec, 0) + 1

        lyr = int(item.get("canonical_layer", 2))
        layer_counts[lyr] = layer_counts.get(lyr, 0) + 1
        lyr_label = item.get("canonical_layer_label", "")

        ag = item.get("album_group", "")
        trk = item.get("album_track_number", "")
        alb_str = _clean_display_album(item, sel, include_track=True)

        perf_raw_blk = sel.get("matched_performer", "")
        is_tv_blk = (ag == "תוכניות טלוויזיה ומופעים מלאים")
        is_tail_blk = (not is_tv_blk) and (
            sel["video_id"] == "k0RE3k8k1pQ" or "סקיצה נדירה" in perf_raw_blk
        )
        if not in_extras_section:
            if (
                is_tv_blk
                or is_tail_blk
                or lyr < prev_primary_lyr
                or (
                    item["title"] in seen_primary_titles
                    and (idx_item == 0 or matched_entries[idx_item - 1]["title"] != item["title"])
                )
            ):
                in_extras_section = True
            else:
                seen_primary_titles.add(item["title"])
                prev_primary_lyr = lyr

        if is_tv_blk:
            blk_id = "tv"
        elif is_tail_blk:
            blk_id = "tail"
        elif not in_extras_section:
            blk_id = f"p{lyr}"
        else:
            blk_id = f"e{lyr}"

        alts_list = []
        seen_alt_vids = {sel["video_id"]}
        for a in item.get("alternative_videos", []):
            avid = a.get("video_id", "")
            if avid and avid not in seen_alt_vids:
                seen_alt_vids.add(avid)
                alts_list.append({
                    "vid": avid,
                    "vtitle": a.get("video_title", ""),
                    "ch": a.get("channel", ""),
                    "dur": a.get("duration", ""),
                    "src": a.get("source", "direct_alternative"),
                })
                if len(alts_list) >= 6:
                    break

        songs_js.append({
            "n": item["index"],
            "chrono_n": item.get("chrono_index", item["index"]),
            "canon_score": item.get("canonical_score", 0),
            "acum_v": item.get("acum_versions_count", 0),
            "layer": lyr,
            "layer_label": lyr_label,
            "blk": blk_id,
            "ch_lbl": item.get("layer2_chapter", "") if blk_id == "p2" else "",
            "title": display_title,
            "raw_title": item["title"],
            "alt_titles": item.get("alt_titles", []),
            "ver_idx": item.get("ver_idx", 1),
            "ver_total": item.get("ver_total", 1),
            "year": yr_display,
            "decade": dec,
            "vid": sel["video_id"],
            "vtitle": sel["video_title"],
            "ch": sel["channel"],
            "dur": sel.get("duration", ""),
            "tier": tier,
            "tier_label": item["tier_label"],
            "perf": sel.get("matched_performer") or (", ".join(item.get("catalog_performers", [])[:2])),
            "alb": alb_str,
            "alb_group": ag,
            "alb_trk": int(trk) if str(trk).isdigit() else 999,
            "role_cat": rcat,
            "role_label": item.get("role_label_heb", "מילים ולחן: נעמי שמר"),
            "co_creators": item.get("co_creators_heb", ""),
            "opening_line": item.get("opening_line", ""),
            "links": item.get("archive_links", []),
            "alts": alts_list,
        })

    archive_songs_js = []
    arch_role_counts = {}
    arch_src_counts = {}
    as_audio = 0
    for item in unmatched_entries:
        yr = item.get("year", "")
        yr_display = yr if (yr and str(yr) != "2099") else "ללא שנה"
        rcat = item.get("role_category", "words_and_music")
        arch_role_counts[rcat] = arch_role_counts.get(rcat, 0) + 1
        links_list = item.get("archive_links", [])
        has_audio = any(lk.get("source") in ("nli_audio", "zemereshet_audio") for lk in links_list)
        if has_audio:
            as_audio += 1
        seen_src_groups = set()
        for lk in links_list:
            src_key = str(lk.get("source", ""))
            if src_key.startswith("nli"):
                seen_src_groups.add("nli")
            elif src_key.startswith("zemereshet"):
                seen_src_groups.add("zemereshet")
            elif src_key:
                seen_src_groups.add(src_key)
        for sg in seen_src_groups:
            arch_src_counts[sg] = arch_src_counts.get(sg, 0) + 1
        archive_songs_js.append({
            "n": item["index"],
            "title": item["title"],
            "alt_titles": item.get("alt_titles", []),
            "year": yr_display,
            "role_cat": rcat,
            "role_label": item.get("role_label_heb", "מילים ולחן: נעמי שמר"),
            "co_creators": item.get("co_creators_heb", ""),
            "perfs": ", ".join(item.get("catalog_performers", [])[:5]),
            "albums": ", ".join(item.get("catalog_albums", [])[:3]),
            "opening_line": item.get("opening_line", ""),
            "sources": item.get("sources", []),
            "has_audio": has_audio,
            "links": links_list,
        })

    ar_wm = arch_role_counts.get("words_and_music", 0)
    ar_m = arch_role_counts.get("music_only", 0)
    ar_w = arch_role_counts.get("words_only", 0)
    ar_t = arch_role_counts.get("translation", 0)
    ar_p = arch_role_counts.get("performance_only", 0)

    as_nli = arch_src_counts.get("nli", 0)
    as_acum = arch_src_counts.get("acum", 0)
    as_shir = arch_src_counts.get("shironet", 0)
    as_zem = arch_src_counts.get("zemereshet", 0)

    t1 = tier_counts.get("1_album_naomi", 0)
    t2 = tier_counts.get("2_album_original", 0)
    t3 = tier_counts.get("3_naomi_performance", 0)
    t4 = tier_counts.get("4_original_performance", 0)
    t5 = tier_counts.get("5_cover", 0)

    r_wm = role_counts.get("words_and_music", 0)
    r_m = role_counts.get("music_only", 0)
    r_w = role_counts.get("words_only", 0)
    r_t = role_counts.get("translation", 0)
    r_p = role_counts.get("performance_only", 0)

    d_50 = decade_counts.get("1950s", 0)
    d_60 = decade_counts.get("1960s", 0)
    d_70 = decade_counts.get("1970s", 0)
    d_80 = decade_counts.get("1980s", 0)
    d_90 = decade_counts.get("1990s+", 0)
    d_unk = decade_counts.get("unknown", 0)

    l1 = layer_counts.get(1, 0)
    l2 = layer_counts.get(2, 0)
    l3 = layer_counts.get(3, 0)
    unique_songs_count = sum(1 for item in songs_js if item.get("ver_idx") == 1)
    first_vid = songs_js[0]["vid"] if songs_js else ""

    html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>שירי נעמי שמר – האוסף המקיף ({total_videos} ביצועים ביוטיוב + {unmatched_songs_count} שירי ארכיון)</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%230b1120' stroke='%23f59e0b' stroke-width='3'/%3E%3Ctext x='32' y='45' font-size='36' text-anchor='middle' fill='%23fbbf24'%3E%E2%99%AB%3C/text%3E%3C/svg%3E" />
  <meta name="description" content="האוסף הכרונולוגי המקיף של שירי נעמי שמר ({total_catalog_songs} שירים מאוחדים מ-9 מאגרים): {total_videos} ביצועים מקוריים ביוטיוב ו-{unmatched_songs_count} שירי ארכיון נדירים עם קישורים לספרייה הלאומית, שירונט, זמרשת ואקו&quot;ם." />
  <meta property="og:title" content="שירי נעמי שמר – האוסף המקיף ({total_videos} ביצועים + {unmatched_songs_count} שירי ארכיון)" />
  <meta property="og:description" content="נגן אינטראקטיבי וקטלוג כרונולוגי מלא של כל {total_catalog_songs} שירי נעמי שמר: אלבומים מקוריים, ביצועי נעמי שמר, תרגומים וארכיון הספרייה הלאומית." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://dmtsurel.github.io/naomi-shemer-playlist/" />
  <meta property="og:image" content="https://i.ytimg.com/vi/{first_vid}/hqdefault.jpg" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="שירי נעמי שמר – האוסף המקיף ({total_videos} ביצועים + {unmatched_songs_count} שירי ארכיון)" />
  <meta name="twitter:image" content="https://i.ytimg.com/vi/{first_vid}/hqdefault.jpg" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@600;700;800&family=Heebo:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b1120;
      --bg-grad: radial-gradient(1200px 600px at 85% -10%, rgba(245, 158, 11, 0.10), transparent 60%),
                 radial-gradient(1000px 500px at 10% 0%, rgba(56, 189, 248, 0.08), transparent 55%),
                 #0b1120;
      --card: rgba(22, 32, 51, 0.85);
      --card-solid: #162033;
      --card-hover: rgba(38, 53, 77, 0.55);
      --border: rgba(148, 163, 184, 0.14);
      --border-strong: rgba(148, 163, 184, 0.25);
      --text: #f8fafc;
      --text-secondary: #cbd5e1;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --gold: #f59e0b;
      --gold-soft: #fbbf24;
      --green: #10b981;
      --purple: #c084fc;
      --rose: #fb7185;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Heebo", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg-grad);
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 20px 24px 86px;
      min-height: 100vh;
    }}
    .container {{ max-width: 1420px; margin: 0 auto; }}

    /* Top Header */
    .top-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 18px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border);
    }}
    .brand-title {{
      font-family: "Frank Ruhl Libre", Georgia, serif;
      margin: 0 0 4px;
      font-size: 32px;
      font-weight: 800;
      letter-spacing: -0.3px;
      color: #fff;
      display: flex;
      align-items: baseline;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .brand-count {{
      font-family: "Heebo", sans-serif;
      font-size: 14px;
      font-weight: 500;
      color: var(--gold-soft);
      background: rgba(245, 158, 11, 0.12);
      border: 1px solid rgba(245, 158, 11, 0.28);
      padding: 2px 10px;
      border-radius: 999px;
    }}
    .subtitle {{
      color: var(--muted);
      margin: 0;
      font-size: 14px;
      max-width: 780px;
    }}
    .header-actions {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}

    /* Cards */
    .card {{
      background: var(--card);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 12px 32px -8px rgba(0, 0, 0, 0.35);
    }}

    /* Buttons */
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      padding: 9px 15px;
      border-radius: 10px;
      border: 1px solid transparent;
      font-family: inherit;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease;
      white-space: nowrap;
    }}
    .btn:hover {{ transform: translateY(-1px); }}
    .btn-gold {{
      background: linear-gradient(135deg, #f59e0b, #fbbf24);
      color: #0f172a;
      font-weight: 700;
      box-shadow: 0 4px 14px rgba(245, 158, 11, 0.25);
    }}
    .btn-gold:hover {{ box-shadow: 0 6px 18px rgba(245, 158, 11, 0.35); }}
    .btn-outline {{
      background: rgba(15, 23, 42, 0.55);
      color: var(--text-secondary);
      border-color: var(--border-strong);
    }}
    .btn-outline:hover {{
      color: #fff;
      border-color: var(--accent);
      background: rgba(56, 189, 248, 0.10);
    }}
    .btn-outline.btn-active {{
      background: rgba(245, 158, 11, 0.2);
      color: var(--gold-soft);
      border-color: var(--gold);
    }}
    .btn-sm {{ padding: 6px 11px; font-size: 12.5px; border-radius: 8px; }}
    .btn-icon {{ padding: 8px 12px; font-size: 14px; }}
    .btn-hero-play {{
      padding: 11px 22px;
      font-size: 15px;
      border-radius: 12px;
      box-shadow: 0 6px 20px rgba(245, 158, 11, 0.32);
    }}

    /* Top Bar: Tabs + Search + Quick Filters */
    .nav-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .tabs-bar {{
      display: inline-flex;
      background: rgba(15, 23, 42, 0.75);
      padding: 4px;
      border-radius: 12px;
      border: 1px solid var(--border);
      gap: 4px;
    }}
    .tab-btn {{
      background: transparent;
      color: var(--muted);
      border: none;
      padding: 8px 16px;
      border-radius: 9px;
      font-family: inherit;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .tab-btn:hover {{ color: var(--text); }}
    .tab-btn.active {{
      background: var(--card-solid);
      color: var(--gold-soft);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }}

    /* Layout */
    .player-layout {{
      display: grid;
      grid-template-columns: 390px 1fr;
      gap: 20px;
      align-items: start;
    }}
    @media (max-width: 1080px) {{
      .player-layout {{ grid-template-columns: 1fr; }}
      .sticky-player {{ position: static; }}
    }}
    @media (min-width: 1081px) {{
      .sticky-player {{ position: sticky; top: 16px; }}
    }}
    .yt-frame-wrap {{
      width: 100%;
      aspect-ratio: 16/9;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid var(--border);
      background: #000;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }}
    .yt-frame-wrap iframe, #ytFrame {{
      width: 100%;
      height: 100%;
      border: none;
      display: block;
    }}
    @media (max-width: 768px) {{
      body {{ padding: 12px 10px 88px; }}
      .container {{ padding: 0; }}
      .sticky-player {{
        padding: 12px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.55);
      }}
      #nowPlayingTitle {{ font-size: 18px !important; }}
      #nowPlayingMeta {{ font-size: 12.5px !important; margin-bottom: 5px !important; }}
      .arch-toggle-btn {{ white-space: normal; text-align: center; }}
      .table-wrap {{ max-height: none !important; overflow-y: visible !important; }}
      th {{ box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35); z-index: 5; }}
      th, td {{ padding: 8px 7px; font-size: 12.5px; }}
      .song-main-title {{ font-size: 13.5px; }}
    }}

    /* Now Playing Card */
    .np-header {{ margin-top: 12px; }}
    .np-title-row {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 4px;
    }}
    .np-title-actions {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      flex-shrink: 0;
    }}
    #nowPlayingTitle {{
      font-family: "Frank Ruhl Libre", Georgia, serif;
      font-weight: 700;
      font-size: 21px;
      color: #fff;
      line-height: 1.25;
    }}
    #nowPlayingMeta {{
      color: var(--text-secondary);
      font-size: 13.5px;
      font-weight: 500;
      margin-bottom: 8px;
    }}
    .np-badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      margin-bottom: 10px;
    }}
    .np-versions {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 5px;
      margin-bottom: 10px;
      padding: 7px 9px;
      background: rgba(11, 17, 32, 0.55);
      border: 1px solid var(--border);
      border-radius: 9px;
    }}
    .np-ver-lbl {{
      font-size: 11.5px;
      color: var(--muted);
      font-weight: 600;
      margin-left: 3px;
    }}
    .np-ver-pill {{
      background: rgba(30, 41, 59, 0.75);
      color: var(--text-secondary);
      border: 1px solid var(--border-strong);
      border-radius: 999px;
      padding: 2px 9px;
      font-family: inherit;
      font-size: 11.5px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.14s ease;
      max-width: 220px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .np-ver-pill:hover {{
      border-color: var(--accent);
      color: #fff;
      background: rgba(56, 189, 248, 0.14);
    }}
    .np-ver-pill.active {{
      background: rgba(245, 158, 11, 0.22);
      border-color: var(--gold);
      color: var(--gold-soft);
      font-weight: 700;
    }}
    .transport-bar {{
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 6px;
      margin-top: 12px;
    }}
    .clickable-meta {{
      cursor: pointer;
      transition: color 0.14s ease;
    }}
    .clickable-meta:hover {{
      color: var(--gold-soft);
      text-decoration: underline;
      text-underline-offset: 3px;
    }}
    .np-details {{
      margin-top: 10px;
      border-top: 1px solid var(--border);
      padding-top: 8px;
      font-size: 12.5px;
      color: var(--muted);
    }}
    .np-details summary {{
      cursor: pointer;
      user-select: none;
      font-weight: 500;
      color: var(--muted);
      padding: 3px 0;
    }}
    .np-details summary:hover {{ color: var(--text-secondary); }}

    /* Filter Toolbar */
    .toolbar {{
      display: flex;
      gap: 10px;
      margin-bottom: 12px;
      flex-wrap: wrap;
      align-items: center;
    }}
    .search-wrap {{
      position: relative;
      flex: 1;
      min-width: 240px;
    }}
    .search-wrap input {{
      width: 100%;
      padding-left: 34px;
    }}
    .search-kbd {{
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      pointer-events: none;
      font-size: 11px;
      color: var(--muted);
      border: 1px solid var(--border-strong);
      border-radius: 5px;
      padding: 0 5px;
      background: rgba(15, 23, 42, 0.7);
    }}
    .search-clear {{
      position: absolute;
      left: 8px;
      top: 50%;
      transform: translateY(-50%);
      background: rgba(148, 163, 184, 0.18);
      color: var(--text);
      border: none;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      font-size: 11px;
      line-height: 1;
      cursor: pointer;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 0;
    }}
    .search-clear:hover {{ background: rgba(245, 158, 11, 0.35); color: #fff; }}
    input, select {{
      background: rgba(11, 17, 32, 0.75);
      color: var(--text);
      border: 1px solid var(--border-strong);
      padding: 8px 12px;
      border-radius: 10px;
      font-family: inherit;
      font-size: 13.5px;
      transition: border-color 0.15s;
    }}
    input:focus, select:focus {{
      outline: none;
      border-color: var(--accent);
    }}
    .advanced-drawer {{
      display: none;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      padding: 10px 12px;
      margin-bottom: 12px;
      background: rgba(11, 17, 32, 0.55);
      border: 1px solid var(--border);
      border-radius: 12px;
    }}
    .advanced-drawer.open {{ display: flex; }}

    .active-chips-bar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
      margin-bottom: 10px;
      padding: 7px 10px;
      background: rgba(245, 158, 11, 0.07);
      border: 1px solid rgba(245, 158, 11, 0.22);
      border-radius: 10px;
    }}
    .chips-lbl {{
      font-size: 12px;
      color: var(--muted);
      font-weight: 600;
      margin-left: 2px;
    }}
    .filter-chip {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: rgba(15, 23, 42, 0.8);
      color: var(--gold-soft);
      border: 1px solid rgba(245, 158, 11, 0.35);
      border-radius: 999px;
      padding: 3px 10px;
      font-family: inherit;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.14s ease;
    }}
    .filter-chip:hover {{
      background: rgba(245, 158, 11, 0.22);
      color: #fff;
    }}
    .filter-chip-reset {{
      background: transparent;
      color: var(--text-secondary);
      border-color: var(--border-strong);
      margin-right: auto;
    }}
    .filter-chip-reset:hover {{
      border-color: var(--rose);
      color: var(--rose);
      background: rgba(251, 113, 133, 0.10);
    }}

    .block-jump-bar {{
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 10px;
      overflow-x: auto;
      padding-bottom: 3px;
      scrollbar-width: thin;
    }}
    .block-jump-bar::-webkit-scrollbar {{ height: 4px; }}
    .block-jump-bar::-webkit-scrollbar-thumb {{ background: rgba(148, 163, 184, 0.22); border-radius: 999px; }}
    .block-jump-pill {{
      background: rgba(15, 23, 42, 0.65);
      color: var(--text-secondary);
      border: 1px solid var(--border-strong);
      border-radius: 999px;
      padding: 4px 10px;
      font-family: inherit;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.14s ease;
    }}
    .block-jump-pill:hover {{
      color: var(--gold-soft);
      border-color: var(--gold);
      background: rgba(245, 158, 11, 0.12);
    }}
    .block-jump-pill.active-blk {{
      color: var(--gold-soft);
      border-color: rgba(245, 158, 11, 0.55);
      background: rgba(245, 158, 11, 0.16);
    }}

    /* Clean 4-Column Song List Table */
    .table-wrap {{
      max-height: 700px;
      overflow-y: auto;
      border-radius: 10px;
    }}
    .table-wrap::-webkit-scrollbar {{ width: 7px; }}
    .table-wrap::-webkit-scrollbar-track {{ background: transparent; }}
    .table-wrap::-webkit-scrollbar-thumb {{ background: rgba(148, 163, 184, 0.22); border-radius: 999px; }}
    .table-wrap::-webkit-scrollbar-thumb:hover {{ background: rgba(148, 163, 184, 0.38); }}

    table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: right;
      vertical-align: middle;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
      font-size: 12px;
      letter-spacing: 0.2px;
      position: sticky;
      top: 0;
      background: var(--card-solid);
      z-index: 2;
    }}
    tr.song-row {{ cursor: pointer; transition: background 0.12s; }}
    tr.song-row:hover {{ background: var(--card-hover); }}
    tr.song-row.active {{
      background: rgba(245, 158, 11, 0.13);
    }}
    tr.song-row.active td:first-child {{
      border-right: 3px solid var(--gold);
    }}
    tr.song-row.multi-ver-row:not(.active) td:first-child {{
      border-right: 3px solid rgba(56, 189, 248, 0.38);
    }}
    tr.album-group-header td {{
      background: rgba(15, 23, 42, 0.92);
      color: var(--gold-soft);
      font-weight: 700;
      font-size: 13px;
      padding: 8px 14px;
      border-bottom: 1px solid rgba(245, 158, 11, 0.25);
      border-top: 1px solid rgba(245, 158, 11, 0.18);
    }}
    tr.sub-chapter-header td {{
      background: rgba(15, 23, 42, 0.58);
      color: var(--accent);
      font-weight: 600;
      font-size: 12px;
      padding: 6px 18px;
      border-bottom: 1px solid rgba(56, 189, 248, 0.18);
      border-top: 1px solid rgba(56, 189, 248, 0.12);
    }}
    .album-group-count {{
      color: var(--muted);
      font-weight: 400;
      font-size: 12px;
      margin-right: 6px;
    }}

    .row-num {{
      font-weight: 600;
      color: var(--muted);
      font-variant-numeric: tabular-nums;
      width: 44px;
      text-align: center;
    }}
    tr.song-row.active .row-num {{ color: var(--gold-soft); font-weight: 700; }}
    .playing-ind {{
      display: none;
      color: var(--gold);
      font-size: 11px;
      margin-left: 2px;
    }}
    tr.song-row.active .playing-ind {{ display: inline; }}

    .song-main-title {{
      font-weight: 600;
      font-size: 14.5px;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .song-year {{
      color: var(--muted);
      font-weight: 400;
      font-size: 12.5px;
    }}
    .opening-line {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
      display: -webkit-box;
      -webkit-line-clamp: 1;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .perf-primary {{
      font-weight: 500;
      color: var(--text-secondary);
      font-size: 13.5px;
    }}
    .perf-album {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 1px;
    }}
    .meta-col {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
      white-space: nowrap;
    }}
    .dur-text {{
      color: var(--muted);
      font-size: 12.5px;
      font-variant-numeric: tabular-nums;
    }}
    .dur-fav-wrap {{
      display: inline-flex;
      align-items: center;
      justify-content: flex-end;
      gap: 6px;
    }}
    .fav-btn {{
      background: transparent;
      border: none;
      cursor: pointer;
      font-size: 15px;
      line-height: 1;
      padding: 3px 5px;
      border-radius: 6px;
      color: var(--muted);
      opacity: 0.55;
      transition: all 0.14s ease;
      flex-shrink: 0;
    }}
    tr.song-row:hover .fav-btn, .fav-btn.is-fav {{
      opacity: 1;
    }}
    .fav-btn:hover {{
      transform: scale(1.18);
      color: var(--rose);
      background: rgba(251, 113, 133, 0.12);
    }}
    .fav-btn.is-fav {{
      color: var(--rose);
    }}
    .tab-offscreen {{
      position: fixed !important;
      left: -9999px !important;
      top: 0 !important;
      width: 380px !important;
      height: 220px !important;
      opacity: 0 !important;
      pointer-events: none !important;
      overflow: hidden !important;
      z-index: -1 !important;
    }}

    /* Subtle Badges */
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .ver-badge {{
      display: inline-block;
      padding: 1px 6px;
      border-radius: 6px;
      font-size: 10.5px;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.13);
      color: var(--accent);
      cursor: pointer;
      transition: all 0.14s;
    }}
    .ver-badge:hover {{
      background: var(--accent);
      color: #0f172a;
    }}
    .ver-badge.active-ver-filter {{
      background: var(--gold);
      color: #0f172a;
      box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.45);
    }}
    .t-1_album_naomi {{ background: rgba(245, 158, 11, 0.16); color: #fbbf24; }}
    .t-2_album_original {{ background: rgba(16, 185, 129, 0.16); color: #34d399; }}
    .t-3_naomi_performance {{ background: rgba(56, 189, 248, 0.16); color: #38bdf8; }}
    .t-4_original_performance {{ background: rgba(168, 85, 247, 0.16); color: #c084fc; }}
    .t-5_cover {{ background: rgba(148, 163, 184, 0.14); color: #cbd5e1; }}

    .r-words_and_music {{ background: rgba(245, 158, 11, 0.12); color: #fcd34d; }}
    .r-music_only {{ background: rgba(56, 189, 248, 0.12); color: #7dd3fc; }}
    .r-words_only {{ background: rgba(192, 132, 252, 0.12); color: #d8b4fe; }}
    .r-translation {{ background: rgba(16, 185, 129, 0.12); color: #6ee7b7; }}
    .r-performance_only {{ background: rgba(251, 113, 133, 0.12); color: #fda4af; }}

    .quote-box {{
      background: rgba(11, 17, 32, 0.6);
      border-right: 3px solid var(--gold);
      padding: 7px 11px;
      border-radius: 6px;
      font-size: 12.5px;
      line-height: 1.55;
      color: var(--text-secondary);
      margin-bottom: 10px;
      max-height: 155px;
      overflow-y: auto;
    }}
    .quote-box::-webkit-scrollbar {{ width: 5px; }}
    .quote-box::-webkit-scrollbar-track {{ background: transparent; }}
    .quote-box::-webkit-scrollbar-thumb {{ background: rgba(148, 163, 184, 0.25); border-radius: 999px; }}
    .archive-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }}
    .arch-pill {{
      display: inline-flex;
      align-items: center;
      gap: 3px;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      text-decoration: none;
      background: rgba(56, 189, 248, 0.10);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.22);
      transition: all 0.15s;
    }}
    .arch-pill:hover {{ background: var(--accent); color: #0f172a; }}
    .arch-pill.nli {{
      background: rgba(245, 158, 11, 0.12);
      color: #fbbf24;
      border-color: rgba(245, 158, 11, 0.28);
    }}
    .arch-pill.nli:hover {{ background: #fbbf24; color: #0f172a; }}
    .arch-pill.shironet {{
      background: rgba(16, 185, 129, 0.12);
      color: #34d399;
      border-color: rgba(16, 185, 129, 0.28);
    }}
    .arch-pill.shironet:hover {{ background: #34d399; color: #0f172a; }}
    .arch-pill.zemereshet {{
      background: rgba(168, 85, 247, 0.13);
      color: #d8b4fe;
      border-color: rgba(168, 85, 247, 0.30);
    }}
    .arch-pill.zemereshet:hover {{ background: #c084fc; color: #0f172a; }}
    .arch-pill.audio-listen {{
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.24), rgba(20, 184, 166, 0.20));
      color: #6ee7b7;
      border: 1px solid rgba(52, 211, 153, 0.55);
      padding: 4px 10px;
      font-size: 11.5px;
      font-weight: 700;
      box-shadow: 0 1px 6px rgba(16, 185, 129, 0.16);
    }}
    .arch-pill.audio-listen:hover {{
      background: #10b981;
      color: #022c22;
      border-color: #34d399;
    }}
    .audio-avail-badge {{
      background: rgba(16, 185, 129, 0.16);
      color: #6ee7b7;
      border: 1px solid rgba(52, 211, 153, 0.32);
      font-size: 10.5px;
      padding: 1px 7px;
    }}
    .count-chip {{
      color: var(--muted);
      font-size: 12.5px;
      margin-right: auto;
      white-space: nowrap;
    }}
    kbd {{
      background: #0f172a;
      border: 1px solid var(--border-strong);
      border-radius: 4px;
      padding: 1px 5px;
      font-size: 11px;
      color: #cbd5e1;
    }}
    .mini-player-bar {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      z-index: 95;
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border-top: 1px solid rgba(245, 158, 11, 0.32);
      box-shadow: 0 -8px 28px rgba(0, 0, 0, 0.55);
      padding: 10px 16px 8px;
      transform: translateY(115%);
      transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1);
    }}
    .mini-progress-wrap {{
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: rgba(148, 163, 184, 0.18);
      cursor: pointer;
      direction: ltr;
      transition: height 0.12s ease;
    }}
    .mini-player-bar:hover .mini-progress-wrap {{
      height: 6px;
    }}
    .mini-progress-fill {{
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #f59e0b, #fbbf24);
      border-radius: 0 2px 2px 0;
      transition: width 0.25s linear;
      pointer-events: none;
    }}
    .mini-time-text {{
      font-size: 11.5px;
      color: var(--gold-soft);
      font-variant-numeric: tabular-nums;
      direction: ltr;
      display: inline-block;
      margin-right: 6px;
      opacity: 0.9;
    }}
    .mini-player-bar.visible {{
      transform: translateY(0);
    }}
    .mini-player-inner {{
      max-width: 1420px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .mini-song-info {{
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      flex: 1;
      cursor: pointer;
    }}
    .mini-thumb {{
      width: 48px;
      height: 36px;
      border-radius: 6px;
      object-fit: cover;
      border: 1px solid var(--border-strong);
      background: #000;
      flex-shrink: 0;
    }}
    .mini-text {{
      min-width: 0;
      overflow: hidden;
    }}
    .mini-title {{
      font-weight: 700;
      font-size: 13.5px;
      color: #fff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .mini-perf {{
      font-size: 12px;
      color: var(--text-secondary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .mini-controls {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }}
    .share-toast {{
      position: fixed;
      bottom: 74px;
      left: 50%;
      transform: translateX(-50%) translateY(12px);
      background: #065f46;
      color: #ecfdf5;
      border: 1px solid #34d399;
      padding: 8px 16px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
      z-index: 120;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease, transform 0.2s ease;
      white-space: nowrap;
    }}
    .share-toast.show {{
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }}
    @media (max-width: 560px) {{
      .transport-bar {{ gap: 6px; }}
      .transport-bar .btn-icon {{ min-height: 42px; padding: 8px 4px; font-size: 14.5px; }}
      #openOnYt {{ font-size: 12px; }}
      .mini-player-bar {{ padding: 10px 10px 7px; }}
      .mini-thumb {{ width: 40px; height: 30px; }}
      .mini-controls .btn-icon {{ padding: 6px 8px; font-size: 13px; min-height: 34px; }}
      .mini-back-lbl {{ display: none; }}
      .mini-hide-xs {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- כותרת עליונה אלגנטית ומאוחדת -->
    <header class="top-header">
      <div>
        <h1 class="brand-title">
          שירי נעמי שמר
          <span class="brand-count">{total_videos} ביצועים · {total_catalog_songs} שירים בקטלוג</span>
        </h1>
        <p class="subtitle">
          האוסף המקיף מאוחד מ-9 מאגרים (אקו"ם, הספרייה הלאומית, שירונט, זמרשת ועוד) — מסודר מהקלאסיקות הגדולות אל הפנינים הנדירות.
        </p>
      </div>
      <div class="header-actions">
        <button id="playPlaylistBtn" class="btn btn-gold btn-hero-play" onclick="startPlaylistPlayback()">▶ נגן פלייליסט</button>
        <a class="btn btn-outline" href="https://www.youtube.com/playlist?list=PLFHErlX6i22g" target="_blank" rel="noopener">פתח ב-YouTube ↗</a>
      </div>
    </header>

    <!-- סרגל עליון למעבר מהיר לארכיון ומונה -->
    <div id="topStatusRow" class="nav-bar" style="margin-bottom: 10px;">
      <button id="topArchToggleBtn" class="btn btn-outline btn-sm arch-toggle-btn" onclick="switchTab('arch')">
        🏛️ הצג גם {unmatched_songs_count} שירים נדירים מהארכיון שאינם ביוטיוב
      </button>
      <button id="backToPlayerBtn" class="btn btn-outline btn-sm" style="display:none;" onclick="switchTab('yt')">← חזרה לנגן הפלייליסט ({total_videos} ביצועים)</button>
      <span id="ytCountChip" class="count-chip"></span>
    </div>

    <!-- לשונית 1: פלייליסט יוטיוב -->
    <div id="tabYtContent">
      <div class="player-layout">
        <!-- כרטיס הנגן הדביק -->
        <div class="card sticky-player">
          <div id="failoverBanner" style="display:none; background:rgba(245,158,11,0.18); border:1px solid var(--gold); color:#fcd34d; padding:7px 10px; border-radius:8px; font-size:12.5px; margin-bottom:8px;"></div>
          <div id="ytFrameWrap" class="yt-frame-wrap">
            <div id="ytFrame"></div>
          </div>

          <div class="np-header">
            <div class="np-title-row">
              <div id="nowPlayingTitle">בחר שיר מהרשימה</div>
              <div class="np-title-actions">
                <button class="btn btn-outline btn-sm" type="button" onclick="scrollToActiveRow()" title="גלול לשיר המתנגן בטבלה">🎯</button>
                <button id="npFavBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleCurrentFavorite()" title="הוסף / הסר מהמועדפים (F)">♡</button>
              </div>
            </div>
            <div id="nowPlayingMeta"></div>
            <div id="nowPlayingRole" class="np-badges"></div>
            <div id="nowPlayingVersions" class="np-versions" style="display:none;"></div>
            <div id="nowPlayingQuote" class="quote-box" style="display:none;"></div>
            <div id="nowPlayingLinks" class="archive-pills" style="margin-bottom:6px;"></div>
          </div>

          <div class="transport-bar">
            <button class="btn btn-outline btn-icon" type="button" onclick="playPrev()" title="השיר הקודם (P)">⏮</button>
            <button id="mainPlayPauseBtn" class="btn btn-outline btn-icon" type="button" onclick="togglePlayPause()" title="ניגון / השהיה (Space / K)">⏯</button>
            <button class="btn btn-outline btn-icon" type="button" onclick="playNext()" title="השיר הבא (N)">⏭</button>
            <button id="shuffleBtn" class="btn btn-outline btn-icon" type="button" onclick="toggleShuffle()" title="ניגון אקראי (S)">🔀</button>
            <button id="repeatBtn" class="btn btn-outline btn-icon" type="button" onclick="toggleRepeatOne()" aria-pressed="false" title="ניגון חוזר לשיר הנוכחי (R)">🔂</button>
            <button id="npShareBtn" class="btn btn-outline btn-icon" type="button" onclick="copyShareUrl()" title="שתף או העתק קישור ישיר לשיר זה">🔗</button>
            <a id="openOnYt" class="btn btn-outline btn-icon" href="#" target="_blank" rel="noopener" title="פתח ביוטיוב">↗ YT</a>
          </div>

          <!-- פרטים משניים מוסתרים במגירה נקייה -->
          <details id="npDetails" class="np-details">
            <summary id="npDetailsSummary">⚙️ מקורות גיבוי וקיצורי מקלדת</summary>
            <div style="margin-top:8px; display:flex; flex-direction:column; gap:8px;">
              <div id="backupSourcesBox" style="display:none;">
                <label style="display:block; margin-bottom:4px; color:var(--text-secondary);">🛡️ החלף למקור גיבוי / ביצוע חלופי:</label>
                <select id="backupSelect" onchange="switchVideoSource(this.value)" style="width:100%; padding:6px 8px; font-size:12px;"></select>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                <button class="btn btn-outline btn-sm" onclick="scrollToActiveRow()">🎯 גלול לשיר המתנגן בטבלה</button>
                <span>קיצורים: <kbd>Space</kbd> השהיה · <kbd>N</kbd>/<kbd>P</kbd> מעבר · <kbd>S</kbd> אקראי · <kbd>R</kbd> חוזר · <kbd>F</kbd> מועדף · <kbd>/</kbd> חיפוש</span>
              </div>
            </div>
          </details>
        </div>

        <!-- כרטיס רשימת השירים -->
        <div class="card" style="padding: 16px;">
          <!-- שורת חיפוש ומיון נקייה -->
          <div class="toolbar">
            <div class="search-wrap">
              <input type="text" id="searchInput" placeholder="חיפוש שיר, שורת פתיחה, מבצע או אלבום..." oninput="onSearchInput('yt')" />
              <span id="searchKbd" class="search-kbd">/</span>
              <button id="searchClearBtn" class="search-clear" type="button" onclick="clearSearch('yt')" title="נקה חיפוש (Esc)">✕</button>
            </div>
            <select id="sortSelect" onchange="renderTable()">
              <option value="canonical">🌟 מיון: קלאסיקות תחילה</option>
              <option value="chrono_asc">📅 כרונולוגי (לפי שנת הקלטה)</option>
              <option value="chrono_desc">⏪ כרונולוגי הפוך</option>
              <option value="albums">💿 לפי אלבומים מקוריים</option>
              <option value="popularity">🔥 לפי תפוצה באקו"ם</option>
              <option value="title_asc">🔤 שם השיר (א'–ת')</option>
              <option value="perf_asc">🎤 שם המבצע (א'–ת')</option>
            </select>
            <select id="decadeFilter" onchange="renderTable()">
              <option value="ALL">כל העשורים ({total_videos})</option>
              <option value="1950s">שנות ה-50 ({d_50})</option>
              <option value="1960s">שנות ה-60 ({d_60})</option>
              <option value="1970s">שנות ה-70 ({d_70})</option>
              <option value="1980s">שנות ה-80 ({d_80})</option>
              <option value="1990s+">שנות ה-90+ ({d_90})</option>
              <option value="unknown">ללא שנה ({d_unk})</option>
            </select>
            <button id="onePerSongBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleOnePerSong()" aria-pressed="false" title="סנן לביצוע מוביל אחד לכל שיר (מדלג על גרסאות כפולות בלי למחוק אותן)">
              🎯 ביצוע אחד לכל שיר ({unique_songs_count})
            </button>
            <button id="favOnlyBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleFavOnly()" aria-pressed="false" title="הצג רק ביצועים שסימנת כמועדפים">
              ❤️ מועדפים (<span id="favCountSpan">0</span>)
            </button>
            <button id="advFilterBtn" class="btn btn-outline btn-sm" onclick="toggleAdvancedFilters()">
              ⚙️ סינון מתקדם <span id="activeFiltersBadge" style="display:none; background:var(--gold); color:#000; padding:0 6px; border-radius:999px; font-size:11px;"></span>
            </button>
          </div>

          <!-- מגירת סינון מתקדם (מוסתרת כברירת מחדל) -->
          <div id="advancedDrawer" class="advanced-drawer">
            <select id="tierFilter" onchange="renderTable()">
              <option value="ALL">כל סוגי הביצועים ({total_videos})</option>
              <option value="1_album_naomi">אלבום של נעמי שמר ({t1})</option>
              <option value="2_album_original">אלבום מבצע מקורי ({t2})</option>
              <option value="3_naomi_performance">ביצוע נעמי שמר ({t3})</option>
              <option value="4_original_performance">ביצוע מקורי ({t4})</option>
              <option value="5_cover">ביצוע נוסף / קאבר ({t5})</option>
            </select>
            <select id="roleFilter" onchange="renderTable()">
              <option value="ALL">כל תפקידי היצירה ({total_videos})</option>
              <option value="words_and_music">מילים ולחן: נעמי שמר ({r_wm})</option>
              <option value="music_only">לחן בלבד ({r_m})</option>
              <option value="words_only">מילים בלבד ({r_w})</option>
              <option value="translation">תרגום ({r_t})</option>
              <option value="performance_only">ביצוע בלבד ({r_p})</option>
            </select>
            <button class="btn btn-outline btn-sm" onclick="resetAllFilters()" title="אפס את כל המסננים">↺ איפוס</button>
          </div>

          <!-- שורת תגיות מסננים פעילים -->
          <div id="activeFilterChips" class="active-chips-bar" style="display:none;"></div>

          <!-- ניווט מהיר בין בלוקים במיון קלאסיקות -->
          <div id="blockJumpBar" class="block-jump-bar" style="display:none;"></div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th style="width:44px; text-align:center;">#</th>
                  <th>שיר</th>
                  <th>מבצע ואלבום</th>
                  <th style="width:84px; text-align:left;">אורך</th>
                </tr>
              </thead>
              <tbody id="songsBody"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- לשונית 2: ארכיון שירים נדירים שלא ביוטיוב -->
    <div id="tabArchContent" style="display:none;">
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
          <div>
            <h3 style="margin:0 0 4px; font-size:18px; color:#fff;">🏛️ ארכיון משלים: {unmatched_songs_count} שירים נדירים שאינם ביוטיוב</h3>
            <p style="margin:0; color:var(--muted); font-size:13.5px;">
              שירים שאותרו בספרייה הלאומית, אקו"ם, שירונט וזמרשת (הקלטות רדיו, שירי הצגות מוקדמים או כתבי יד) עם קישורים ישירים למילים ולהאזנה בארכיון.
            </p>
          </div>
          <span id="archCountChip" class="count-chip"></span>
        </div>
        <div class="toolbar">
          <div class="search-wrap">
            <input type="text" id="archSearchInput" placeholder="חיפוש בארכיון לפי שם שיר, שורת פתיחה או מבצע..." oninput="onSearchInput('arch')" />
            <button id="archSearchClearBtn" class="search-clear" type="button" onclick="clearSearch('arch')" title="נקה חיפוש (Esc)">✕</button>
          </div>
          <button id="archAudioOnlyBtn" class="btn btn-outline btn-sm" type="button" onclick="toggleArchAudioOnly()" aria-pressed="false" title="סנן לשירים שקיימת עבורם הקלטת שמע פתוחה להאזנה חופשית באתר הספרייה הלאומית או בזמרשת">
            🎧 קיימת הקלטה להאזנה ({as_audio})
          </button>
          <select id="archRoleFilter" onchange="renderArchiveTable()">
            <option value="ALL">כל התפקידים ({unmatched_songs_count})</option>
            <option value="words_and_music">מילים ולחן ({ar_wm})</option>
            <option value="music_only">לחן בלבד ({ar_m})</option>
            <option value="words_only">מילים בלבד ({ar_w})</option>
            <option value="translation">תרגום ({ar_t})</option>
            <option value="performance_only">ביצוע בלבד ({ar_p})</option>
          </select>
          <select id="archSourceFilter" onchange="renderArchiveTable()">
            <option value="ALL">כל המאגרים ({unmatched_songs_count})</option>
            <option value="nli">הספרייה הלאומית ({as_nli})</option>
            <option value="acum">אקו"ם ({as_acum})</option>
            <option value="shironet">שירונט ({as_shir})</option>
            <option value="zemereshet">זמרשת ({as_zem})</option>
          </select>
        </div>
        <div class="table-wrap" style="max-height: 720px;">
          <table>
            <thead>
              <tr>
                <th style="width:44px;">#</th>
                <th>שיר ושנה</th>
                <th>מבצעים ותפקיד</th>
                <th>שורת פתיחה</th>
                <th>קישורים לארכיון</th>
              </tr>
            </thead>
            <tbody id="archiveBody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- פוטר שקט בתחתית העמוד למעבר לארכיון המשלים -->
    <footer style="margin-top: 24px; padding-top: 14px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; color: var(--muted); font-size: 13px;">
      <span>קטלוג שירי נעמי שמר · {total_videos} ביצועים ביוטיוב</span>
      <button id="footerArchToggleBtn" class="btn btn-outline btn-sm arch-toggle-btn" onclick="switchTab(currentTab === 'yt' ? 'arch' : 'yt')">
        🏛️ הצג גם {unmatched_songs_count} שירים נדירים מהארכיון שאינם ביוטיוב
      </button>
    </footer>
  </div>

  <div id="miniPlayerBar" class="mini-player-bar" role="region" aria-label="נגן מוקטן">
    <div id="miniProgressWrap" class="mini-progress-wrap" onclick="seekFromMiniBar(event)" title="לחץ לדילוג לנקודה בשיר">
      <div id="miniProgressFill" class="mini-progress-fill"></div>
    </div>
    <div class="mini-player-inner">
      <div class="mini-song-info" onclick="scrollToTopPlayer()" title="חזרה לנגן הווידאו בראש העמוד">
        <img id="miniThumb" class="mini-thumb" src="" alt="" loading="lazy" />
        <div class="mini-text">
          <div id="miniTitle" class="mini-title">בחר שיר מהרשימה</div>
          <div class="mini-perf"><span id="miniTimeText" class="mini-time-text"></span><span id="miniPerf"></span></div>
        </div>
      </div>
      <div class="mini-controls">
        <button class="btn btn-outline btn-icon" type="button" onclick="playPrev()" title="השיר הקודם (P)">⏮</button>
        <button id="miniPlayBtn" class="btn btn-gold btn-icon" type="button" onclick="togglePlayPause()" title="ניגון / השהיה (Space / K)">▶</button>
        <button class="btn btn-outline btn-icon" type="button" onclick="playNext()" title="השיר הבא (N)">⏭</button>
        <button class="btn btn-outline btn-icon" type="button" onclick="scrollToActiveRow(true)" title="גלול לשיר המתנגן בטבלה">🎯</button>
        <button id="miniFavBtn" class="btn btn-outline btn-icon" type="button" onclick="toggleCurrentFavorite()" title="הוסף / הסר מהמועדפים (F)">♡</button>
        <button class="btn btn-outline btn-icon mini-hide-xs" type="button" onclick="copyShareUrl()" title="שתף או העתק קישור ישיר לשיר זה">🔗</button>
        <button class="btn btn-outline btn-sm" type="button" onclick="scrollToTopPlayer()" title="חזרה לנגן הווידאו">⬆ <span class="mini-back-lbl">לנגן</span></button>
      </div>
    </div>
  </div>
  <div id="shareToast" class="share-toast" role="status" aria-live="polite">✔ הקישור הישיר לשיר הועתק!</div>

  <script>
    function esc(s) {{
      if (s === null || s === undefined) return "";
      const d = document.createElement("div");
      d.textContent = String(s);
      return d.innerHTML;
    }}
    const SONGS = {json.dumps(songs_js, ensure_ascii=False, indent=2)};
    const ARCHIVE_SONGS = {json.dumps(archive_songs_js, ensure_ascii=False, indent=2)};
    const BLOCK_ORDER = ["p1", "p2", "p3", "e1", "e2", "e3", "tail", "tv"];
    const BLOCK_META = {{
      p1:   {{ label: "🌟 שכבה א' — קלאסיקות ושירי ילדים קאנוניים", short: "🌟 קלאסיקות" }},
      p2:   {{ label: "💿 שכבה ב' — אלבומים וביצועים מוכרים", short: "💿 שכבה ב'" }},
      p3:   {{ label: "💎 שכבה ג' — פנינים נדירות וארכיון", short: "💎 נדירים" }},
      e1:   {{ label: "➕ ביצועים נוספים — שכבה א'", short: "➕ נוספים א'" }},
      e2:   {{ label: "➕ ביצועים נוספים — שכבה ב'", short: "➕ נוספים ב'" }},
      e3:   {{ label: "➕ ביצועים נוספים — שכבה ג'", short: "➕ נוספים ג'" }},
      tail: {{ label: "🎙️ סקיצות אולפן וראיונות ארכיוניים", short: "🎙️ סקיצות" }},
      tv:   {{ label: "📺 תוכניות טלוויזיה ומופעים מלאים", short: "📺 תוכניות מלאות" }}
    }};

    function normHeb(str) {{
      if (!str) return "";
      return String(str)
        .toLowerCase()
        .replace(/[\\u0591-\\u05C7]/g, "")
        .replace(/["'״׳”’‘“]/g, "")
        .replace(/[־\\-–—,.!:;?()\\[\\]\\/\\\\]/g, " ")
        .replace(/וו+/g, "ו")
        .replace(/יי+/g, "י")
        .replace(/\\s+/g, " ")
        .trim();
    }}

    SONGS.forEach(s => {{
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
    }});

    ARCHIVE_SONGS.forEach(s => {{
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
    }});

    let favoriteVids = new Set();
    try {{
      if (window.localStorage) {{
        const rawFavs = JSON.parse(localStorage.getItem("naomi_playlist_favorites") || "[]");
        if (Array.isArray(rawFavs)) {{
          rawFavs.forEach(v => {{ if (typeof v === "string" && v) favoriteVids.add(v); }});
        }}
      }}
    }} catch (e) {{}}

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

    function getActiveSong() {{
      return playingSong || filteredSongs[0] || SONGS[0] || null;
    }}

    function formatSec(sec) {{
      if (!Number.isFinite(sec) || sec < 0) return "0:00";
      const total = Math.floor(sec);
      const hrs = Math.floor(total / 3600);
      const mins = Math.floor((total % 3600) / 60);
      const s = total % 60;
      if (hrs > 0) {{
        return `${{hrs}}:${{String(mins).padStart(2, "0")}}:${{String(s).padStart(2, "0")}}`;
      }}
      return `${{mins}}:${{String(s).padStart(2, "0")}}`;
    }}

    function updatePlaybackProgress() {{
      const fill = document.getElementById("miniProgressFill");
      const timeEl = document.getElementById("miniTimeText");
      if (!fill && !timeEl) return;
      if (!ytApiReady || !ytPlayer || typeof ytPlayer.getCurrentTime !== "function" || typeof ytPlayer.getDuration !== "function") return;
      const st = typeof ytPlayer.getPlayerState === "function" ? ytPlayer.getPlayerState() : -1;
      if (st !== 1 && st !== 2) return;
      const dur = ytPlayer.getDuration();
      const cur = ytPlayer.getCurrentTime();
      if (dur > 0 && Number.isFinite(dur)) {{
        const pct = Math.max(0, Math.min(100, (cur / dur) * 100));
        if (fill) fill.style.width = pct.toFixed(2) + "%";
        if (timeEl) timeEl.textContent = `${{formatSec(cur)}} / ${{formatSec(dur)}}`;
      }}
    }}

    function seekFromMiniBar(ev) {{
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
      if (timeEl) timeEl.textContent = `${{formatSec(targetSec)}} / ${{formatSec(dur)}}`;
    }}

    function updateMiniPlayerVisibility() {{
      const bar = document.getElementById("miniPlayerBar");
      if (!bar) return;
      const st = (ytApiReady && ytPlayer && typeof ytPlayer.getPlayerState === "function") ? ytPlayer.getPlayerState() : -1;
      const isActivePlayback = (st === 1 || st === 2 || st === 3 || hasUserStartedPlayback);
      const shouldShow = (currentTab === "yt" && !isMainPlayerVisible) || (currentTab === "arch" && isActivePlayback);
      bar.classList.toggle("visible", Boolean(shouldShow));
    }}

    function scrollToTopPlayer() {{
      if (currentTab !== "yt") switchTab("yt");
      const el = document.querySelector(".sticky-player") || document.getElementById("ytFrameWrap");
      if (el) el.scrollIntoView({{ behavior: "smooth", block: "start" }});
      else window.scrollTo({{ top: 0, behavior: "smooth" }});
    }}

    function updateMiniPlayerCard(s, vidOverride) {{
      if (!s) return;
      const activeVid = vidOverride || s.vid;
      const thumb = document.getElementById("miniThumb");
      const titleEl = document.getElementById("miniTitle");
      const perfEl = document.getElementById("miniPerf");
      if (thumb) thumb.src = `https://i.ytimg.com/vi/${{encodeURIComponent(activeVid)}}/mqdefault.jpg`;
      if (titleEl) titleEl.textContent = `${{s.n}}. ${{s.raw_title}}${{s.year ? " (" + s.year + ")" : ""}}`;
      if (perfEl) perfEl.textContent = `${{s.perf || s.ch}}${{s.alb ? " · " + s.alb : ""}}`;
      if (activeVid !== lastMiniVid) {{
        lastMiniVid = activeVid;
        const fill = document.getElementById("miniProgressFill");
        const timeEl = document.getElementById("miniTimeText");
        if (fill) fill.style.width = "0%";
        if (timeEl) timeEl.textContent = s.dur ? `0:00 / ${{s.dur}}` : "";
      }}
    }}

    function updateMediaSession(s, vidOverride) {{
      if (!s || typeof navigator === "undefined" || !("mediaSession" in navigator) || typeof MediaMetadata === "undefined") return;
      try {{
        const activeVid = vidOverride || s.vid;
        const artistParts = [s.perf || s.ch || "נעמי שמר"];
        if (s.year) artistParts.push(`(${{s.year}})`);
        const albTitle = (s.alb && !s.alb.startsWith("סינגל")) ? s.alb : "משירי נעמי שמר";
        navigator.mediaSession.metadata = new MediaMetadata({{
          title: s.raw_title || s.title,
          artist: artistParts.join(" "),
          album: albTitle,
          artwork: [
            {{ src: `https://i.ytimg.com/vi/${{encodeURIComponent(activeVid)}}/mqdefault.jpg`, sizes: "320x180", type: "image/jpeg" }},
            {{ src: `https://i.ytimg.com/vi/${{encodeURIComponent(activeVid)}}/hqdefault.jpg`, sizes: "480x360", type: "image/jpeg" }}
          ]
        }});
      }} catch (e) {{}}
    }}

    function initMediaSessionHandlers() {{
      if (typeof navigator === "undefined" || !("mediaSession" in navigator)) return;
      const handlers = [
        ["play", () => {{ if (ytApiReady && ytPlayer && typeof ytPlayer.playVideo === "function") ytPlayer.playVideo(); else startPlaylistPlayback(); }}],
        ["pause", () => {{ if (ytApiReady && ytPlayer && typeof ytPlayer.pauseVideo === "function") ytPlayer.pauseVideo(); }}],
        ["previoustrack", () => playPrev()],
        ["nexttrack", () => playNext()]
      ];
      handlers.forEach(([action, fn]) => {{
        try {{
          navigator.mediaSession.setActionHandler(action, fn);
        }} catch (e) {{}}
      }});
    }}

    function syncPlayButtonUI() {{
      const btn = document.getElementById("playPlaylistBtn");
      const miniBtn = document.getElementById("miniPlayBtn");
      const mainBtn = document.getElementById("mainPlayPauseBtn");
      if (!ytApiReady || !ytPlayer || typeof ytPlayer.getPlayerState !== "function") {{
        if (btn) btn.textContent = "▶ נגן פלייליסט";
        if (miniBtn) miniBtn.textContent = "▶";
        if (mainBtn) mainBtn.textContent = "⏯";
        updateMiniPlayerVisibility();
        return;
      }}
      const st = ytPlayer.getPlayerState();
      if (st === 1) {{
        if (btn) btn.textContent = "⏸ השהה פלייליסט";
        if (miniBtn) miniBtn.textContent = "⏸";
        if (mainBtn) mainBtn.textContent = "⏸";
        if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "playing";
      }} else if (st === 2) {{
        if (btn) btn.textContent = "▶ המשך פלייליסט";
        if (miniBtn) miniBtn.textContent = "▶";
        if (mainBtn) mainBtn.textContent = "▶";
        if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "paused";
      }} else {{
        if (btn) btn.textContent = "▶ נגן פלייליסט";
        if (miniBtn) miniBtn.textContent = "▶";
        if (mainBtn) mainBtn.textContent = "⏯";
      }}
      updateMiniPlayerVisibility();
    }}

    function startPlaylistPlayback() {{
      if (currentTab !== "yt") switchTab("yt");
      if (!filteredSongs.length) return;
      hasUserStartedPlayback = true;
      if (ytApiReady && ytPlayer && typeof ytPlayer.getPlayerState === "function") {{
        const st = ytPlayer.getPlayerState();
        if (st === 1) {{
          ytPlayer.pauseVideo();
        }} else {{
          ytPlayer.playVideo();
        }}
        syncPlayButtonUI();
        return;
      }}
      playSongAt(currentIndex >= 0 ? currentIndex : 0, true, true);
    }}

    function loadYouTubeIframeAPI() {{
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      tag.onerror = function() {{
        ytApiFailed = true;
        if (pendingVideoLoad) {{
          const req = pendingVideoLoad;
          pendingVideoLoad = null;
          loadVideoByIdOrSrc(req.vid, req.autoplay);
        }}
      }};
      document.head.appendChild(tag);
      setTimeout(() => {{
        if (!ytApiReady && !ytApiFailed) {{
          ytApiFailed = true;
          if (pendingVideoLoad) {{
            const req = pendingVideoLoad;
            pendingVideoLoad = null;
            loadVideoByIdOrSrc(req.vid, req.autoplay);
          }}
        }}
      }}, 6000);
    }}

    window.onYouTubeIframeAPIReady = function() {{
      try {{
        const activeInit = getActiveSong();
        const initReq = pendingVideoLoad || {{ vid: activeInit ? activeInit.vid : "", autoplay: false }};
        pendingVideoLoad = null;
        ytPlayer = new YT.Player("ytFrame", {{
          width: "100%",
          height: "100%",
          videoId: initReq.vid,
          playerVars: {{
            rel: 0,
            enablejsapi: 1,
            playsinline: 1,
            autoplay: initReq.autoplay ? 1 : 0
          }},
          events: {{
            onReady: function() {{
              ytApiReady = true;
              const req = pendingVideoLoad || initReq;
              pendingVideoLoad = null;
              if (req && req.autoplay) {{
                if (req.vid !== initReq.vid) ytPlayer.loadVideoById(req.vid);
                else ytPlayer.playVideo();
              }} else if (req && req.vid !== initReq.vid) {{
                ytPlayer.cueVideoById(req.vid);
              }}
              syncPlayButtonUI();
            }},
            onStateChange: function(ev) {{
              if (ev.data === 1) {{
                hasUserStartedPlayback = true;
              }} else if (ev.data === 0) {{ // YT.PlayerState.ENDED
                if (repeatOneEnabled && ytPlayer && typeof ytPlayer.seekTo === "function") {{
                  ytPlayer.seekTo(0, true);
                  ytPlayer.playVideo();
                }} else {{
                  playNext();
                }}
              }}
              syncPlayButtonUI();
            }},
            onError: function(ev) {{
              handleVideoPlaybackError(ev.data);
            }}
          }}
        }});
      }} catch (e) {{
        ytApiFailed = true;
        if (pendingVideoLoad) {{
          const req = pendingVideoLoad;
          pendingVideoLoad = null;
          loadVideoByIdOrSrc(req.vid, req.autoplay);
        }}
      }}
    }};

    function handleVideoPlaybackError(errCode) {{
      const s = getActiveSong();
      if (!s) return;
      const alts = s.alts || [];
      const nextAltIdx = currentAltIdx + 1;
      const banner = document.getElementById("failoverBanner");
      const npDet = document.getElementById("npDetails");
      if (nextAltIdx < alts.length) {{
        currentAltIdx = nextAltIdx;
        const alt = alts[currentAltIdx];
        if (banner) {{
          banner.style.display = "block";
          banner.innerHTML = `⚠️ הסרטון הראשי אינו זמין כעת (קוד ${{esc(errCode)}}). הנגן עבר אוטומטית למקור גיבוי #${{currentAltIdx + 1}}: <strong>${{esc(alt.vtitle || alt.vid)}}</strong>`;
        }}
        if (npDet) npDet.open = true;
        const sel = document.getElementById("backupSelect");
        if (sel) sel.value = alt.vid;
        loadVideoByIdOrSrc(alt.vid, true);
        updateMiniPlayerCard(s, alt.vid);
        updateMediaSession(s, alt.vid);
        document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{encodeURIComponent(alt.vid)}}`;
      }} else {{
        if (banner) {{
          banner.style.display = "block";
          banner.innerHTML = `⚠️ הסרטון אינו זמין (קוד ${{esc(errCode)}}) ולא נמצאו מקורות גיבוי נוספים. עובר לשיר הבא...`;
        }}
        setTimeout(() => playNext(), 1800);
      }}
    }}

    function loadVideoByIdOrSrc(vid, autoplay) {{
      if (ytApiReady && ytPlayer && typeof ytPlayer.loadVideoById === "function") {{
        if (autoplay) {{
          ytPlayer.loadVideoById(vid);
        }} else {{
          ytPlayer.cueVideoById(vid);
        }}
        if (typeof syncPlayButtonUI === "function") syncPlayButtonUI();
        return;
      }}
      if (!ytApiFailed) {{
        pendingVideoLoad = {{ vid, autoplay }};
        return;
      }}
      const wrap = document.getElementById("ytFrameWrap");
      const originParam = window.location.origin && window.location.origin !== "null" ? `&origin=${{encodeURIComponent(window.location.origin)}}` : "";
      const srcUrl = `https://www.youtube.com/embed/${{encodeURIComponent(vid)}}?enablejsapi=1&rel=0${{autoplay ? "&autoplay=1" : ""}}${{originParam}}`;
      let frame = document.getElementById("ytFrame");
      if (!frame || frame.tagName.toLowerCase() !== "iframe") {{
        if (wrap) {{
          wrap.innerHTML = `<iframe id="ytFrame" src="${{srcUrl}}" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
        }}
      }} else {{
        frame.src = srcUrl;
      }}
    }}

    function switchVideoSource(vid) {{
      const s = getActiveSong();
      if (!s) return;
      hasUserStartedPlayback = true;
      const banner = document.getElementById("failoverBanner");
      if (vid === s.vid) {{
        currentAltIdx = -1;
        if (banner) banner.style.display = "none";
      }} else {{
        const alts = s.alts || [];
        currentAltIdx = alts.findIndex(a => a.vid === vid);
        const alt = alts[currentAltIdx];
        if (banner && alt) {{
          banner.style.display = "block";
          banner.innerHTML = `🛡️ מנגן מקור גיבוי #${{currentAltIdx + 1}}: <strong>${{esc(alt.vtitle || alt.vid)}}</strong> (${{esc(alt.ch || "")}})`;
        }}
      }}
      loadVideoByIdOrSrc(vid, true);
      updateMiniPlayerCard(s, vid);
      updateMediaSession(s, vid);
      document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{encodeURIComponent(vid)}}`;
    }}

    function switchTab(tab, skipSync = false) {{
      currentTab = tab === "arch" ? "arch" : "yt";
      const isYt = currentTab === "yt";
      const ytTabEl = document.getElementById("tabYtContent");
      if (ytTabEl) {{
        ytTabEl.style.display = "block";
        ytTabEl.classList.toggle("tab-offscreen", !isYt);
      }}
      document.getElementById("tabArchContent").style.display = isYt ? "none" : "block";
      const topArchBtn = document.getElementById("topArchToggleBtn");
      if (topArchBtn) topArchBtn.style.display = isYt ? "inline-flex" : "none";
      const backBtn = document.getElementById("backToPlayerBtn");
      if (backBtn) backBtn.style.display = isYt ? "none" : "inline-flex";
      const ytChip = document.getElementById("ytCountChip");
      if (ytChip) ytChip.style.display = isYt ? "" : "none";
      const footerBtn = document.getElementById("footerArchToggleBtn");
      if (footerBtn) {{
        footerBtn.textContent = isYt
          ? `🏛️ הצג גם ${{ARCHIVE_SONGS.length}} שירים נדירים מהארכיון שאינם ביוטיוב`
          : `🎵 חזרה לנגן הפלייליסט הראשי (${{SONGS.length}} ביצועים)`;
      }}
      updateMiniPlayerVisibility();
      if (!skipSync) {{
        syncUrlAndStorageState();
        window.scrollTo({{ top: 0, behavior: "smooth" }});
      }}
    }}

    function saveFavorites() {{
      try {{
        if (window.localStorage) {{
          localStorage.setItem("naomi_playlist_favorites", JSON.stringify(Array.from(favoriteVids)));
        }}
      }} catch (e) {{}}
    }}

    function syncFavUI() {{
      const cntEl = document.getElementById("favCountSpan");
      if (cntEl) cntEl.textContent = String(favoriteVids.size);
      const favFilterBtn = document.getElementById("favOnlyBtn");
      if (favFilterBtn) {{
        favFilterBtn.classList.toggle("btn-active", favOnly);
        favFilterBtn.setAttribute("aria-pressed", favOnly ? "true" : "false");
      }}
      const curSong = getActiveSong();
      const npFav = document.getElementById("npFavBtn");
      const miniFav = document.getElementById("miniFavBtn");
      if (curSong) {{
        const isFav = favoriteVids.has(curSong.vid);
        if (npFav) {{
          npFav.textContent = isFav ? "❤️" : "♡";
          npFav.classList.toggle("btn-active", isFav);
        }}
        if (miniFav) {{
          miniFav.textContent = isFav ? "❤️" : "♡";
          miniFav.classList.toggle("btn-active", isFav);
        }}
      }}
    }}

    function toggleFavorite(ev, vid) {{
      if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
      if (!vid) return;
      if (favoriteVids.has(vid)) favoriteVids.delete(vid);
      else favoriteVids.add(vid);
      saveFavorites();
      if (favOnly) {{
        renderTable();
      }} else {{
        const isFav = favoriteVids.has(vid);
        document.querySelectorAll(".fav-btn").forEach(btn => {{
          if (btn.getAttribute("data-vid") === vid) {{
            btn.classList.toggle("is-fav", isFav);
            btn.textContent = isFav ? "❤️" : "♡";
          }}
        }});
        syncFavUI();
      }}
    }}

    function toggleCurrentFavorite() {{
      const curSong = getActiveSong();
      if (!curSong) return;
      toggleFavorite(null, curSong.vid);
    }}

    function toggleFavOnly() {{
      favOnly = !favOnly;
      syncFavUI();
      renderTable();
    }}

    function syncOnePerSongUI() {{
      const btn = document.getElementById("onePerSongBtn");
      if (!btn) return;
      btn.classList.toggle("btn-active", onePerSongOnly);
      btn.setAttribute("aria-pressed", onePerSongOnly ? "true" : "false");
    }}

    function toggleOnePerSong() {{
      onePerSongOnly = !onePerSongOnly;
      syncOnePerSongUI();
      renderTable();
    }}

    function syncArchAudioOnlyUI() {{
      const btn = document.getElementById("archAudioOnlyBtn");
      if (!btn) return;
      btn.classList.toggle("btn-active", archAudioOnly);
      btn.setAttribute("aria-pressed", archAudioOnly ? "true" : "false");
    }}

    function toggleArchAudioOnly() {{
      archAudioOnly = !archAudioOnly;
      syncArchAudioOnlyUI();
      renderArchiveTable();
    }}

    function toggleAdvancedFilters() {{
      const drw = document.getElementById("advancedDrawer");
      const btn = document.getElementById("advFilterBtn");
      if (!drw) return;
      const isOpen = drw.classList.toggle("open");
      if (btn) btn.classList.toggle("btn-active", isOpen);
    }}

    function updateSearchClearUI(which) {{
      if (which === "arch") {{
        const inp = document.getElementById("archSearchInput");
        const clr = document.getElementById("archSearchClearBtn");
        if (inp && clr) clr.style.display = inp.value.length > 0 ? "inline-flex" : "none";
      }} else {{
        const inp = document.getElementById("searchInput");
        const clr = document.getElementById("searchClearBtn");
        const kbd = document.getElementById("searchKbd");
        const hasVal = inp && inp.value.length > 0;
        if (clr) clr.style.display = hasVal ? "inline-flex" : "none";
        if (kbd) kbd.style.display = hasVal ? "none" : "inline";
      }}
    }}

    function onSearchInput(which) {{
      updateSearchClearUI(which);
      if (which === "arch") renderArchiveTable();
      else renderTable();
    }}

    function clearSearch(which) {{
      if (which === "arch") {{
        const inp = document.getElementById("archSearchInput");
        if (inp) {{ inp.value = ""; inp.focus(); }}
        updateSearchClearUI("arch");
        renderArchiveTable();
      }} else {{
        const inp = document.getElementById("searchInput");
        if (inp) {{ inp.value = ""; inp.focus(); }}
        updateSearchClearUI("yt");
        renderTable();
      }}
    }}

    function filterByExactSong(ev, rawTitle) {{
      if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
      if (!rawTitle) return;
      if (exactSongTitle === rawTitle) {{
        exactSongTitle = "";
      }} else {{
        exactSongTitle = rawTitle;
      }}
      renderTable();
      if (playingSong) {{
        const npVerBadge = document.querySelector("#nowPlayingRole .ver-badge");
        if (npVerBadge) npVerBadge.classList.toggle("active-ver-filter", exactSongTitle === playingSong.raw_title);
      }}
    }}

    function filterBySongTitle(ev, text) {{
      if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
      const inp = document.getElementById("searchInput");
      if (!inp) return;
      exactSongTitle = "";
      if (inp.value.trim() === text) {{
        inp.value = "";
      }} else {{
        inp.value = text;
      }}
      updateSearchClearUI("yt");
      renderTable();
    }}

    function clearSingleFilter(kind) {{
      if (kind === "exact") exactSongTitle = "";
      else if (kind === "q") {{
        document.getElementById("searchInput").value = "";
        updateSearchClearUI("yt");
      }} else if (kind === "decade") document.getElementById("decadeFilter").value = "ALL";
      else if (kind === "tier") document.getElementById("tierFilter").value = "ALL";
      else if (kind === "role") document.getElementById("roleFilter").value = "ALL";
      else if (kind === "oneper") {{
        onePerSongOnly = false;
        syncOnePerSongUI();
      }} else if (kind === "fav") {{
        favOnly = false;
        syncFavUI();
      }}
      renderTable();
      if (playingSong) {{
        const npVerBadge = document.querySelector("#nowPlayingRole .ver-badge");
        if (npVerBadge) npVerBadge.classList.toggle("active-ver-filter", exactSongTitle === playingSong.raw_title);
      }}
    }}

    function resetAllFilters() {{
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
      if (playingSong) {{
        const npVerBadge = document.querySelector("#nowPlayingRole .ver-badge");
        if (npVerBadge) npVerBadge.classList.remove("active-ver-filter");
      }}
    }}

    function syncUrlAndStorageState() {{
      try {{
        const url = new URL(window.location.href);
        const s = getActiveSong();
        if (s) {{
          url.searchParams.set("v", s.vid);
          url.searchParams.delete("song");
        }}
        const q = document.getElementById("searchInput").value.trim();
        const sortBy = document.getElementById("sortSelect").value;
        const tf = document.getElementById("tierFilter").value;
        const rf = document.getElementById("roleFilter").value;
        const df = document.getElementById("decadeFilter").value;

        const setOrDel = (k, val, defVal) => {{
          if (val && val !== defVal) url.searchParams.set(k, val);
          else url.searchParams.delete(k);
        }};
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

        window.history.replaceState({{}}, "", url.toString());
        if (window.localStorage) {{
          localStorage.setItem("naomi_playlist_state", JSON.stringify({{
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
          }}));
        }}
      }} catch (e) {{}}
    }}

    function copyShareUrl() {{
      syncUrlAndStorageState();
      const s = getActiveSong();
      const shareUrlObj = new URL(window.location.href);
      if (s) {{
        shareUrlObj.searchParams.set("v", s.vid);
        shareUrlObj.searchParams.delete("song");
      }}
      const shareStr = shareUrlObj.toString();
      const isCoarseTouch = Boolean(window.matchMedia && window.matchMedia("(pointer: coarse)").matches);
      if (isCoarseTouch && typeof navigator !== "undefined" && typeof navigator.share === "function") {{
        const shareTitle = s ? `${{s.raw_title}} – ${{s.perf || "משירי נעמי שמר"}}` : document.title;
        navigator.share({{
          title: shareTitle,
          url: shareStr
        }}).catch(err => {{
          if (err && err.name === "AbortError") return;
          copyTextWithToast(shareStr, s);
        }});
        return;
      }}
      copyTextWithToast(shareStr, s);
    }}

    function copyTextWithToast(shareStr, s) {{
      const showOk = () => {{
        const toast = document.getElementById("shareToast");
        if (toast) {{
          toast.textContent = s ? `✔ הועתק קישור ישיר ל"${{s.raw_title}}"!` : "✔ הקישור הישיר לשיר הועתק!";
          toast.classList.add("show");
          if (shareToastTimer) clearTimeout(shareToastTimer);
          shareToastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
        }}
      }};
      const fallbackCopy = () => {{
        try {{
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
        }} catch (e) {{}}
      }};
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(shareStr).then(showOk).catch(fallbackCopy);
      }} else {{
        fallbackCopy();
      }}
    }}

    function renderArchivePills(links, stopProp = false) {{
      if (!links || !links.length) return "";
      const onclickAttr = stopProp ? 'onclick="event.stopPropagation()"' : "";
      return `<div class="archive-pills">` + links.map(l => {{
        let cls = "arch-pill";
        const src = String(l.source || "");
        let label = l.label || "";
        if (src === "nli_audio") {{
          cls += " audio-listen";
          label = label || "🎧 האזנה להקלטה בספרייה הלאומית";
        }} else if (src === "zemereshet_audio") {{
          cls += " audio-listen";
          label = label || "🎧 האזנה להקלטה בזמרשת";
        }} else if (src.startsWith("nli")) {{
          cls += " nli";
          label = "📖 סיפור השיר בספרייה הלאומית";
        }} else if (src === "shironet") {{
          cls += " shironet";
        }} else if (src === "zemereshet") {{
          cls += " zemereshet";
        }}
        return `<a class="${{cls}}" href="${{esc(l.url)}}" target="_blank" rel="noopener noreferrer" ${{onclickAttr}}>${{esc(label)}} ↗</a>`;
      }}).join("") + `</div>`;
    }}

    function updateNowPlayingCard(s) {{
      document.getElementById("nowPlayingTitle").textContent = `${{s.n}}. ${{s.raw_title}}${{s.year ? " (" + s.year + ")" : ""}}`;
      const perfText = s.perf || s.ch || "";
      const perfEscAttr = JSON.stringify(perfText).replace(/"/g, "&quot;");
      const cleanAlb = (s.alb || "").replace(/\\s*\\(#\\d+\\)\\s*$/, "").trim();
      const albEscAttr = JSON.stringify(cleanAlb).replace(/"/g, "&quot;");
      const perfSpan = perfText
        ? `<span class="clickable-meta" onclick="filterBySongTitle(event, ${{perfEscAttr}})" title="לחץ לסינון כל השירים של מבצע זה">${{esc(perfText)}}</span>`
        : "";
      const albSpan = s.alb
        ? ` · <span class="clickable-meta" onclick="filterBySongTitle(event, ${{albEscAttr}})" title="לחץ לסינון כל שירי האלבום">${{esc(s.alb)}}</span>`
        : "";
      document.getElementById("nowPlayingMeta").innerHTML = `${{perfSpan}}${{albSpan}}`;
      const isFav = favoriteVids.has(s.vid);
      const npFav = document.getElementById("npFavBtn");
      if (npFav) {{
        npFav.textContent = isFav ? "❤️" : "♡";
        npFav.classList.toggle("btn-active", isFav);
      }}
      const miniFav = document.getElementById("miniFavBtn");
      if (miniFav) {{
        miniFav.textContent = isFav ? "❤️" : "♡";
        miniFav.classList.toggle("btn-active", isFav);
      }}
      const isExactActive = (exactSongTitle && exactSongTitle === s.raw_title);
      const verBadgeHtml = s.ver_total > 1
        ? `<span class="ver-badge ${{isExactActive ? "active-ver-filter" : ""}}" onclick="filterByExactSong(event, ${{JSON.stringify(s.raw_title).replace(/"/g, '&quot;')}})" title="לחץ להצגת כל ${{s.ver_total}} הביצועים של שיר זה בטבלה">ביצוע ${{s.ver_idx}}/${{s.ver_total}}</span>`
        : "";
      const tierShort = s.tier_label.replace(/^[0-9]\\.\\s*/, "");
      document.getElementById("nowPlayingRole").innerHTML = `<span class="badge t-${{esc(s.tier)}}">${{esc(tierShort)}}</span><span class="badge r-${{esc(s.role_cat)}}">${{esc(s.role_label)}}</span>${{verBadgeHtml}}`;

      const verBox = document.getElementById("nowPlayingVersions");
      if (verBox) {{
        const sameVers = s.ver_total > 1 ? SONGS.filter(x => x.raw_title === s.raw_title) : [];
        if (sameVers.length > 1) {{
          const rawLabels = sameVers.map(v => {{
            const base = (v.perf || v.ch || `ביצוע ${{v.ver_idx}}`).replace(/\\s*\\([^)]*\\)\\s*$/, "").trim() || (v.perf || v.ch || `ביצוע ${{v.ver_idx}}`);
            return `${{base}}${{v.year ? " (" + v.year + ")" : ""}}`;
          }});
          const pills = sameVers.map((v, idx) => {{
            const isCur = v.vid === s.vid;
            const hasDup = rawLabels.filter(x => x === rawLabels[idx]).length > 1;
            const dispBase = hasDup ? (v.perf || v.ch || `ביצוע ${{v.ver_idx}}`) : rawLabels[idx];
            const lbl = `${{isCur ? "▶ " : ""}}${{dispBase}}${{hasDup && v.year ? " (" + v.year + ")" : ""}}`;
            const tip = `${{v.perf || v.ch}}${{v.alb ? " · " + v.alb : ""}} (#${{v.n}})`;
            return `<button type="button" class="np-ver-pill ${{isCur ? "active" : ""}}" onclick="playSongByVid('${{esc(v.vid)}}')" title="${{esc(tip)}}">${{esc(lbl)}}</button>`;
          }}).join("");
          verBox.innerHTML = `<span class="np-ver-lbl">ביצועים (${{sameVers.length}}):</span>${{pills}}`;
          verBox.style.display = "flex";
        }} else {{
          verBox.style.display = "none";
          verBox.innerHTML = "";
        }}
      }}

      const qBox = document.getElementById("nowPlayingQuote");
      const parts = [];
      if (s.opening_line) parts.push(`"${{esc(s.opening_line)}}"`);
      if (s.co_creators) parts.push(`<span style="color:var(--muted); font-size:11.5px;">שותפים ליצירה: ${{esc(s.co_creators)}}</span>`);
      if (parts.length > 0) {{
        qBox.innerHTML = parts.join("<br/>");
        qBox.style.display = "block";
      }} else {{
        qBox.style.display = "none";
      }}
      document.getElementById("nowPlayingLinks").innerHTML = renderArchivePills(s.links, false);
      document.getElementById("openOnYt").href = `https://www.youtube.com/watch?v=${{encodeURIComponent(s.vid)}}`;
      const banner = document.getElementById("failoverBanner");
      if (banner) banner.style.display = "none";
      const bBox = document.getElementById("backupSourcesBox");
      const bSel = document.getElementById("backupSelect");
      const npSum = document.getElementById("npDetailsSummary");
      const alts = s.alts || [];
      if (npSum) {{
        npSum.textContent = alts.length > 0
          ? `⚙️ מקורות גיבוי (${{alts.length}}) וקיצורי מקלדת`
          : `⚙️ קיצורי מקלדת`;
      }}
      if (bBox && bSel) {{
        if (alts.length > 0) {{
          bBox.style.display = "block";
          const opts = [`<option value="${{esc(s.vid)}}">⭐ מקור ראשי: ${{esc(s.vtitle)}} (${{esc(s.ch)}})</option>`];
          alts.forEach((a, i) => {{
            const tag = a.src === "same_song_performance" ? "ביצוע נוסף" : "עותק גיבוי";
            opts.push(`<option value="${{esc(a.vid)}}">🔄 גיבוי #${{i + 1}} (${{tag}}): ${{esc(a.vtitle || a.vid)}} (${{esc(a.ch || "")}})</option>`);
          }});
          bSel.innerHTML = opts.join("");
          bSel.value = s.vid;
        }} else {{
          bBox.style.display = "none";
        }}
      }}
      updateMiniPlayerCard(s, s.vid);
      updateMediaSession(s, s.vid);
    }}

    function syncBlockJumpHighlight() {{
      const activeBlk = playingSong ? playingSong.blk : "";
      document.querySelectorAll("#blockJumpBar .block-jump-pill").forEach(btn => {{
        btn.classList.toggle("active-blk", btn.getAttribute("data-blk") === activeBlk);
      }});
    }}

    function jumpToBlock(blkId) {{
      const target = document.querySelector(`tr[data-block-header="${{blkId}}"]`);
      if (!target) return;
      const wrap = document.querySelector("#tabYtContent .table-wrap");
      if (wrap && wrap.scrollHeight > wrap.clientHeight + 20 && window.getComputedStyle(wrap).overflowY !== "visible") {{
        const th = wrap.querySelector("thead");
        const thH = th ? th.offsetHeight : 0;
        wrap.scrollTo({{ top: Math.max(0, target.offsetTop - thH), behavior: "smooth" }});
      }} else {{
        target.scrollIntoView({{ behavior: "smooth", block: "start" }});
      }}
    }}

    function scrollToActiveRow(smooth = true) {{
      if (currentTab !== "yt") switchTab("yt", true);
      let activeRow = document.querySelector("tr.song-row.active");
      if (!activeRow && playingSong && currentIndex < 0) {{
        resetAllFilters();
        activeRow = document.querySelector("tr.song-row.active");
      }}
      if (activeRow) {{
        activeRow.scrollIntoView({{ behavior: smooth ? "smooth" : "auto", block: smooth ? "center" : "nearest" }});
      }}
    }}

    function playSongByVid(vid, shouldScroll = false) {{
      const nextSong = SONGS.find(x => x.vid === vid);
      if (!nextSong) return;
      hasUserStartedPlayback = true;
      if (playingSong && playingSong.vid !== nextSong.vid) {{
        playHistory.push(playingSong.vid);
        if (playHistory.length > 100) playHistory.shift();
      }}
      playingSong = nextSong;
      currentIndex = filteredSongs.findIndex(x => x.vid === nextSong.vid);
      currentAltIdx = -1;
      updateNowPlayingCard(nextSong);
      loadVideoByIdOrSrc(nextSong.vid, true);
      document.querySelectorAll("tr.song-row").forEach((tr, i) => {{
        tr.classList.toggle("active", i === currentIndex);
      }});
      if (shouldScroll && currentIndex >= 0) scrollToActiveRow(true);
      syncBlockJumpHighlight();
      syncUrlAndStorageState();
    }}

    function playSongAt(idx, shouldScroll = true, skipHistory = false) {{
      if (idx < 0 || idx >= filteredSongs.length) return;
      hasUserStartedPlayback = true;
      const nextSong = filteredSongs[idx];
      if (!skipHistory && playingSong && playingSong.vid !== nextSong.vid) {{
        playHistory.push(playingSong.vid);
        if (playHistory.length > 100) playHistory.shift();
      }}
      playingSong = nextSong;
      currentIndex = idx;
      currentAltIdx = -1;
      updateNowPlayingCard(nextSong);
      loadVideoByIdOrSrc(nextSong.vid, true);
      document.querySelectorAll("tr.song-row").forEach((tr, i) => {{
        tr.classList.toggle("active", i === idx);
      }});
      if (shouldScroll) scrollToActiveRow(true);
      syncBlockJumpHighlight();
      syncUrlAndStorageState();
    }}

    function toggleShuffle() {{
      shuffleEnabled = !shuffleEnabled;
      const btn = document.getElementById("shuffleBtn");
      if (btn) btn.classList.toggle("btn-active", shuffleEnabled);
      syncUrlAndStorageState();
    }}

    function toggleRepeatOne() {{
      repeatOneEnabled = !repeatOneEnabled;
      const btn = document.getElementById("repeatBtn");
      if (btn) {{
        btn.classList.toggle("btn-active", repeatOneEnabled);
        btn.setAttribute("aria-pressed", repeatOneEnabled ? "true" : "false");
      }}
      syncUrlAndStorageState();
    }}

    function togglePlayPause() {{
      hasUserStartedPlayback = true;
      if (ytApiReady && ytPlayer && typeof ytPlayer.getPlayerState === "function") {{
        const st = ytPlayer.getPlayerState();
        if (st === 1) ytPlayer.pauseVideo();
        else ytPlayer.playVideo();
        if (typeof syncPlayButtonUI === "function") syncPlayButtonUI();
      }} else {{
        startPlaylistPlayback();
      }}
    }}

    function playNext() {{
      if (!filteredSongs.length) return;
      if (shuffleEnabled && filteredSongs.length > 1) {{
        let randIdx = currentIndex;
        while (randIdx === currentIndex || randIdx < 0) {{
          randIdx = Math.floor(Math.random() * filteredSongs.length);
        }}
        playSongAt(randIdx);
        return;
      }}
      if (currentIndex < 0) {{
        if (playingSong) {{
          const sameTitleIdx = filteredSongs.findIndex(x => x.raw_title === playingSong.raw_title);
          if (sameTitleIdx >= 0) {{
            playSongAt((sameTitleIdx + 1) % filteredSongs.length);
            return;
          }}
          const afterIdx = filteredSongs.findIndex(x => x.n > playingSong.n);
          if (afterIdx >= 0) {{
            playSongAt(afterIdx);
            return;
          }}
        }}
        playSongAt(0);
        return;
      }}
      playSongAt((currentIndex + 1) % filteredSongs.length);
    }}

    function playPrev() {{
      if (!filteredSongs.length) return;
      if (shuffleEnabled && playHistory.length > 0) {{
        const prevVid = playHistory.pop();
        const prevIdx = filteredSongs.findIndex(x => x.vid === prevVid);
        if (prevIdx >= 0) {{
          playSongAt(prevIdx, true, true);
          return;
        }}
      }}
      if (currentIndex < 0) {{
        if (playingSong) {{
          const sameTitleIdx = filteredSongs.findIndex(x => x.raw_title === playingSong.raw_title);
          if (sameTitleIdx >= 0) {{
            playSongAt((sameTitleIdx - 1 + filteredSongs.length) % filteredSongs.length, true, true);
            return;
          }}
        }}
        playSongAt(filteredSongs.length - 1, true, true);
        return;
      }}
      playSongAt((currentIndex - 1 + filteredSongs.length) % filteredSongs.length, true, true);
    }}

    function getSelectedOptionLabel(selId) {{
      const el = document.getElementById(selId);
      if (!el || el.selectedIndex < 0) return "";
      const txt = el.options[el.selectedIndex].text || "";
      return txt.replace(/\\s*\\([^)]*\\)\\s*$/, "").trim();
    }}

    function renderTable(skipSync = false) {{
      const activeVid = playingSong ? playingSong.vid : null;
      const rawInput = document.getElementById("searchInput").value;
      const qRaw = rawInput.trim().toLowerCase();
      const qNorm = normHeb(rawInput);
      const sortBy = document.getElementById("sortSelect").value;
      const tf = document.getElementById("tierFilter").value;
      const rf = document.getElementById("roleFilter").value;
      const df = document.getElementById("decadeFilter").value;

      filteredSongs = SONGS.filter(s => {{
        if (exactSongTitle && s.raw_title !== exactSongTitle) return false;
        if (favOnly && !favoriteVids.has(s.vid)) return false;
        if (!exactSongTitle && onePerSongOnly && s.ver_idx !== 1) return false;
        if (tf !== "ALL" && s.tier !== tf) return false;
        if (rf !== "ALL" && s.role_cat !== rf) return false;
        if (df !== "ALL" && s.decade !== df) return false;
        if (!qRaw) return true;
        return s._sRaw.includes(qRaw) || (qNorm.length > 0 && s._sNorm.includes(qNorm));
      }});

      const TV_GRP_NAME = "תוכניות טלוויזיה ומופעים מלאים";
      const albCatRank = (ag) => {{
        if (!ag || ag.startsWith("סינגל") || ag.startsWith("ביצוע ")) return 2;
        if (ag === TV_GRP_NAME) return 1;
        return 0;
      }};

      filteredSongs.sort((a, b) => {{
        if (sortBy === "canonical") return a.n - b.n;
        if (sortBy === "chrono_asc") return (a.chrono_n || a.n) - (b.chrono_n || b.n);
        if (sortBy === "chrono_desc") return (b.chrono_n || b.n) - (a.chrono_n || a.n);
        if (sortBy === "popularity") return (b.canon_score - a.canon_score) || (a.n - b.n);
        if (sortBy === "title_asc") return a.raw_title.localeCompare(b.raw_title, "he") || (a.n - b.n);
        if (sortBy === "perf_asc") return (a.perf || a.ch).localeCompare(b.perf || b.ch, "he") || (a.n - b.n);
        if (sortBy === "albums") {{
          const aCat = albCatRank(a.alb_group);
          const bCat = albCatRank(b.alb_group);
          if (aCat !== bCat) return aCat - bCat;
          if (aCat === 0) {{
            const aNaomi = a.tier === "1_album_naomi" ? 0 : 1;
            const bNaomi = b.tier === "1_album_naomi" ? 0 : 1;
            if (aNaomi !== bNaomi) return aNaomi - bNaomi;
            const grpCmp = (a.alb_group || "").localeCompare(b.alb_group || "", "he");
            if (grpCmp !== 0) return grpCmp;
            const trkCmp = (a.alb_trk || 999) - (b.alb_trk || 999);
            if (trkCmp !== 0) return trkCmp;
          }}
          return (a.chrono_n || a.n) - (b.chrono_n || b.n);
        }}
        return a.n - b.n;
      }});

      currentIndex = activeVid ? filteredSongs.findIndex(x => x.vid === activeVid) : -1;

      document.getElementById("ytCountChip").textContent = filteredSongs.length === SONGS.length
        ? `${{SONGS.length}} ביצועים`
        : (exactSongTitle
            ? `מציג את כל ${{filteredSongs.length}} הביצועים של "${{exactSongTitle}}"`
            : (favOnly
                ? `מציג ${{filteredSongs.length}} מועדפים (מתוך ${{SONGS.length}} ביצועים)`
                : (onePerSongOnly
                    ? `מציג ${{filteredSongs.length}} מתוך ${{SONGS.length}} ביצועים (ביצוע אחד לשיר)`
                    : `מציג ${{filteredSongs.length}} מתוך ${{SONGS.length}} ביצועים`)));

      const activeAdvCount = [tf !== "ALL", rf !== "ALL"].filter(Boolean).length;
      const advBadge = document.getElementById("activeFiltersBadge");
      if (advBadge) {{
        if (activeAdvCount > 0) {{
          advBadge.textContent = activeAdvCount;
          advBadge.style.display = "inline-block";
        }} else {{
          advBadge.style.display = "none";
        }}
      }}

      const chipsBox = document.getElementById("activeFilterChips");
      if (chipsBox) {{
        const chips = [];
        if (exactSongTitle) chips.push({{ kind: "exact", text: `🎵 כל הביצועים של: "${{exactSongTitle}}"` }});
        if (rawInput.trim()) chips.push({{ kind: "q", text: `🔍 חיפוש: "${{rawInput.trim()}}"` }});
        if (df !== "ALL") chips.push({{ kind: "decade", text: `📅 ${{getSelectedOptionLabel("decadeFilter")}}` }});
        if (tf !== "ALL") chips.push({{ kind: "tier", text: `🎙️ ${{getSelectedOptionLabel("tierFilter")}}` }});
        if (rf !== "ALL") chips.push({{ kind: "role", text: `✍️ ${{getSelectedOptionLabel("roleFilter")}}` }});
        if (onePerSongOnly && !exactSongTitle) chips.push({{ kind: "oneper", text: "🎯 ביצוע אחד לשיר" }});
        if (favOnly) chips.push({{ kind: "fav", text: "❤️ מועדפים בלבד" }});

        if (chips.length > 0) {{
          const pillsHtml = chips.map(c =>
            `<button type="button" class="filter-chip" onclick="clearSingleFilter('${{c.kind}}')">${{esc(c.text)}} <span aria-hidden="true">✕</span></button>`
          ).join("");
          chipsBox.innerHTML = `<span class="chips-lbl">מסננים פעילים:</span>${{pillsHtml}}<button type="button" class="filter-chip filter-chip-reset" onclick="resetAllFilters()">↺ נקה הכול</button>`;
          chipsBox.style.display = "flex";
        }} else {{
          chipsBox.style.display = "none";
          chipsBox.innerHTML = "";
        }}
      }}

      const blockCounts = {{}};
      if (sortBy === "canonical") {{
        filteredSongs.forEach(s => {{
          const b = s.blk || "p1";
          blockCounts[b] = (blockCounts[b] || 0) + 1;
        }});
      }}
      const presentBlocks = BLOCK_ORDER.filter(b => blockCounts[b] > 0);
      const jumpBar = document.getElementById("blockJumpBar");
      if (jumpBar) {{
        if (sortBy === "canonical" && presentBlocks.length >= 2) {{
          const activeBlk = playingSong ? playingSong.blk : "";
          jumpBar.innerHTML = presentBlocks.map(b => {{
            const meta = BLOCK_META[b] || {{ short: b, label: b }};
            const isAct = b === activeBlk;
            return `<button type="button" class="block-jump-pill ${{isAct ? "active-blk" : ""}}" data-blk="${{esc(b)}}" onclick="jumpToBlock('${{esc(b)}}')" title="${{esc(meta.label)}} (${{blockCounts[b]}} רצועות)">${{esc(meta.short)}} <span style="opacity:0.7; font-weight:400;">(${{blockCounts[b]}})</span></button>`;
          }}).join("");
          jumpBar.style.display = "flex";
        }} else {{
          jumpBar.style.display = "none";
          jumpBar.innerHTML = "";
        }}
      }}

      const normalizeAlbGrp = (ag) => (!ag || ag.startsWith("סינגל") || ag.startsWith("ביצוע "))
        ? "סינגלים וביצועים בודדים"
        : ag;

      const albumCounts = {{}};
      if (sortBy === "albums") {{
        filteredSongs.forEach(s => {{
          const g = normalizeAlbGrp(s.alb_group);
          albumCounts[g] = (albumCounts[g] || 0) + 1;
        }});
      }}

      let lastAlbGroup = null;
      let lastBlockId = null;
      let lastSubChapter = null;
      const tbody = document.getElementById("songsBody");
      const htmlRows = [];
      if (filteredSongs.length === 0) {{
        const emptyMsg = (favOnly && favoriteVids.size === 0)
          ? "עדיין לא סימנת ביצועים מועדפים — לחץ על ♡ ליד כל שיר בטבלה או בכרטיס הנגן כדי לשמור אותו ברשימה האישית שלך."
          : "לא נמצאו שירים התואמים לחיפוש או לסינון שנבחר.";
        htmlRows.push(`<tr><td colspan="4" style="text-align:center; padding:28px 16px; color:var(--muted);">${{esc(emptyMsg)}}</td></tr>`);
      }}
      filteredSongs.forEach((s, i) => {{
        if (sortBy === "canonical" && filteredSongs.length > 1) {{
          const bId = s.blk || "p1";
          if (bId !== lastBlockId) {{
            lastBlockId = bId;
            lastSubChapter = null;
            const bMeta = BLOCK_META[bId] || {{ label: bId }};
            htmlRows.push(`
              <tr class="album-group-header" data-block-header="${{esc(bId)}}">
                <td colspan="4">${{esc(bMeta.label)}} <span class="album-group-count">(${{blockCounts[bId]}} רצועות)</span></td>
              </tr>
            `);
          }}
          if (bId === "p2" && s.ch_lbl && s.ch_lbl !== lastSubChapter) {{
            lastSubChapter = s.ch_lbl;
            htmlRows.push(`
              <tr class="sub-chapter-header">
                <td colspan="4">📁 ${{esc(s.ch_lbl)}}</td>
              </tr>
            `);
          }}
        }} else if (sortBy === "albums") {{
          const grp = normalizeAlbGrp(s.alb_group);
          if (grp !== lastAlbGroup) {{
            lastAlbGroup = grp;
            const grpIcon = grp === TV_GRP_NAME ? "📺" : (grp === "סינגלים וביצועים בודדים" ? "🎵" : "💿");
            htmlRows.push(`
              <tr class="album-group-header">
                <td colspan="4">${{grpIcon}} ${{esc(grp)}} <span class="album-group-count">(${{albumCounts[grp]}} רצועות)</span></td>
              </tr>
            `);
          }}
        }}
        const roleSub = s.role_cat !== "words_and_music" ? `<span class="badge r-${{esc(s.role_cat)}}">${{esc(s.role_label)}}</span>` : "";
        const titleAttrEsc = JSON.stringify(s.raw_title).replace(/"/g, "&quot;");
        const perfDisp = s.perf || s.ch || "";
        const perfAttrEsc = JSON.stringify(perfDisp).replace(/"/g, "&quot;");
        const cleanAlbFilter = (s.alb || "").replace(/\\s*\\(#\\d+\\)\\s*$/, "").trim();
        const albAttrEsc = JSON.stringify(cleanAlbFilter).replace(/"/g, "&quot;");
        const subNumHtml = (sortBy === "albums" && s.alb_trk && s.alb_trk < 999)
          ? `<div style="font-size:10.5px; color:var(--gold-soft); opacity:0.85;">רצועה #${{s.alb_trk}}</div>`
          : (sortBy !== "canonical" || filteredSongs.length !== SONGS.length ? `<div style="font-size:10.5px; opacity:0.65;">#${{s.n}}</div>` : "");
        const isFav = favoriteVids.has(s.vid);
        const isVerFiltered = (exactSongTitle && exactSongTitle === s.raw_title);
        htmlRows.push(`
        <tr class="song-row ${{i === currentIndex ? "active" : ""}} ${{s.ver_total > 1 ? "multi-ver-row" : ""}}" onclick="playSongAt(${{i}}, false)">
          <td class="row-num">
            <div><span class="playing-ind">▶</span>${{i + 1}}</div>
            ${{subNumHtml}}
          </td>
          <td>
            <div class="song-main-title">
              <span>${{esc(s.raw_title)}}</span>
              ${{s.year ? `<span class="song-year">(${{esc(s.year)}})</span>` : ""}}
              ${{s.ver_total > 1 ? `<span class="ver-badge ${{isVerFiltered ? "active-ver-filter" : ""}}" onclick="filterByExactSong(event, ${{titleAttrEsc}})" title="לחץ להצגת כל ${{s.ver_total}} הביצועים של שיר זה בלבד">ביצוע ${{s.ver_idx}}/${{s.ver_total}}</span>` : ""}}
              ${{roleSub}}
            </div>
          </td>
          <td>
            <div class="perf-primary"><span class="clickable-meta" onclick="filterBySongTitle(event, ${{perfAttrEsc}})" title="לחץ לסינון כל השירים של מבצע זה">${{esc(perfDisp)}}</span></div>
            ${{s.alb ? `<div class="perf-album"><span class="clickable-meta" onclick="filterBySongTitle(event, ${{albAttrEsc}})" title="לחץ לסינון כל שירי האלבום">${{esc(s.alb)}}</span></div>` : ""}}
          </td>
          <td style="text-align:left;">
            <div class="dur-fav-wrap">
              <span class="dur-text">${{esc(s.dur)}}</span>
              <button class="fav-btn ${{isFav ? "is-fav" : ""}}" type="button" data-vid="${{esc(s.vid)}}" onclick="toggleFavorite(event, '${{esc(s.vid)}}')" title="הוסף / הסר מהמועדפים">${{isFav ? "❤️" : "♡"}}</button>
            </div>
          </td>
        </tr>`);
      }});
      tbody.innerHTML = htmlRows.join("");
      syncFavUI();

      if (!skipSync) syncUrlAndStorageState();
    }}

    function renderArchiveTable(skipSync = false) {{
      const rawInput = document.getElementById("archSearchInput").value;
      const qRaw = rawInput.trim().toLowerCase();
      const qNorm = normHeb(rawInput);
      const rf = document.getElementById("archRoleFilter").value;
      const sf = document.getElementById("archSourceFilter").value;

      const filteredArch = ARCHIVE_SONGS.filter(s => {{
        if (archAudioOnly && !s.has_audio) return false;
        if (rf !== "ALL" && s.role_cat !== rf) return false;
        if (sf !== "ALL") {{
          const hasSource = (s.links || []).some(l => {{
            const src = String(l.source || "");
            if (sf === "nli") return src.startsWith("nli");
            if (sf === "zemereshet") return src.startsWith("zemereshet");
            return src === sf;
          }});
          if (!hasSource) return false;
        }}
        if (!qRaw) return true;
        return s._sRaw.includes(qRaw) || (qNorm.length > 0 && s._sNorm.includes(qNorm));
      }});

      document.getElementById("archCountChip").textContent = archAudioOnly
        ? `${{filteredArch.length}} שירים עם הקלטה להאזנה (מתוך ${{ARCHIVE_SONGS.length}} שירי ארכיון)`
        : `${{filteredArch.length}} מתוך ${{ARCHIVE_SONGS.length}} שירי ארכיון`;

      const tbody = document.getElementById("archiveBody");
      tbody.innerHTML = filteredArch.map((s, idx) => {{
        let compactRole = s.role_label || "";
        if (s.co_creators) {{
          compactRole = compactRole
            .replace(` (${{s.co_creators}})`, "")
            .replace(` · ${{s.co_creators}}`, "")
            .trim();
        }}
        return `
        <tr>
          <td class="row-num">${{idx + 1}}</td>
          <td>
            <div class="song-main-title">
              <span>${{esc(s.title)}}</span>
              ${{s.year && s.year !== "ללא שנה" ? `<span class="song-year">(${{esc(s.year)}})</span>` : ""}}
              ${{s.has_audio ? `<span class="badge audio-avail-badge">🎧 הקלטה להאזנה</span>` : ""}}
            </div>
            ${{s.alt_titles && s.alt_titles.length ? `<div class="perf-album">שמות נוספים: ${{esc(s.alt_titles.join(", "))}}</div>` : ""}}
          </td>
          <td>
            <div class="perf-primary">${{s.perfs ? esc(s.perfs) : "<span style='color:var(--muted);'>לא מתועד מבצע</span>"}}</div>
            <div style="margin-top:3px;"><span class="badge r-${{esc(s.role_cat)}}">${{esc(compactRole)}}</span></div>
            ${{s.co_creators ? `<div class="perf-album" style="margin-top:3px;">שותפים ליצירה: ${{esc(s.co_creators)}}</div>` : ""}}
          </td>
          <td>
            ${{s.opening_line ? `<div class="opening-line" style="-webkit-line-clamp:2;">"${{esc(s.opening_line)}}"</div>` : "<span style='color:var(--muted);'>—</span>"}}
          </td>
          <td>${{renderArchivePills(s.links, false)}}</td>
        </tr>
      `;
      }}).join("");

      if (!skipSync) syncUrlAndStorageState();
    }}

    document.addEventListener("keydown", function(ev) {{
      const tag = (ev.target && ev.target.tagName) ? ev.target.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "textarea" || tag === "select" || (ev.target && ev.target.isContentEditable)) {{
        if (ev.key === "Escape") {{
          if (ev.target.id === "searchInput" && ev.target.value) {{
            clearSearch("yt");
          }} else if (ev.target.id === "archSearchInput" && ev.target.value) {{
            clearSearch("arch");
          }} else {{
            ev.target.blur();
          }}
        }}
        return;
      }}
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      if (ev.key === "/" ) {{
        ev.preventDefault();
        const inp = currentTab === "arch" ? document.getElementById("archSearchInput") : document.getElementById("searchInput");
        if (inp) {{ inp.focus(); inp.select(); }}
      }} else if (ev.key === " " || ev.key === "k" || ev.key === "K") {{
        ev.preventDefault();
        togglePlayPause();
      }} else if (ev.key === "n" || ev.key === "N") {{
        ev.preventDefault();
        playNext();
      }} else if (ev.key === "p" || ev.key === "P") {{
        ev.preventDefault();
        playPrev();
      }} else if (ev.key === "s" || ev.key === "S") {{
        ev.preventDefault();
        toggleShuffle();
      }} else if (ev.key === "r" || ev.key === "R") {{
        ev.preventDefault();
        toggleRepeatOne();
      }} else if (ev.key === "f" || ev.key === "F") {{
        ev.preventDefault();
        toggleCurrentFavorite();
      }}
    }});

    (function initApp() {{
      let saved = {{}};
      try {{
        if (window.localStorage) {{
          saved = JSON.parse(localStorage.getItem("naomi_playlist_state") || "{{}}") || {{}};
        }}
      }} catch (e) {{}}

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

      if (SONGS.length > 0) {{
        const reqVid = params.get("v") || (!params.get("song") ? saved.vid : "");
        const reqSongNum = parseInt(params.get("song") || saved.song || "1", 10);
        if (reqVid) {{
          playingSong = SONGS.find(x => x.vid === reqVid) || SONGS.find(x => x.n === reqSongNum) || SONGS[0];
        }} else {{
          playingSong = SONGS.find(x => x.n === reqSongNum) || SONGS[0];
        }}
      }}

      if (exactParam) {{
        exactSongTitle = exactParam;
      }}
      if (qParam !== null) {{
        document.getElementById("searchInput").value = qParam;
        updateSearchClearUI("yt");
      }}
      if (sortParam) document.getElementById("sortSelect").value = sortParam;
      if (tierParam) document.getElementById("tierFilter").value = tierParam;
      if (roleParam) document.getElementById("roleFilter").value = roleParam;
      if (decadeParam) document.getElementById("decadeFilter").value = decadeParam;
      if ((tierParam && tierParam !== "ALL") || (roleParam && roleParam !== "ALL")) {{
        const drw = document.getElementById("advancedDrawer");
        const btn = document.getElementById("advFilterBtn");
        if (drw) drw.classList.add("open");
        if (btn) btn.classList.add("btn-active");
      }}
      if (shufParam === "1" || (shufParam === null && saved.shuffle)) {{
        shuffleEnabled = true;
        const btn = document.getElementById("shuffleBtn");
        if (btn) btn.classList.add("btn-active");
      }}
      if (repParam === "1" || (repParam === null && saved.repeat)) {{
        repeatOneEnabled = true;
        const btn = document.getElementById("repeatBtn");
        if (btn) {{
          btn.classList.add("btn-active");
          btn.setAttribute("aria-pressed", "true");
        }}
      }}
      if (onePerParam === "1" || (onePerParam === null && saved.oneper)) {{
        onePerSongOnly = true;
        syncOnePerSongUI();
      }}
      if (favParam === "1" || (favParam === null && saved.fav && favoriteVids.size > 0)) {{
        favOnly = true;
      }}
      syncFavUI();
      if (archAudioParam === "1" || (archAudioParam === null && saved.archaudio)) {{
        archAudioOnly = true;
        syncArchAudioOnlyUI();
      }}
      if (tabParam === "arch") switchTab("arch", true);

      renderTable(true);
      renderArchiveTable(true);

      initMediaSessionHandlers();
      setInterval(updatePlaybackProgress, 500);
      const ytWrapEl = document.getElementById("ytFrameWrap");
      if (ytWrapEl && "IntersectionObserver" in window) {{
        const obs = new IntersectionObserver((entries) => {{
          if (entries && entries.length > 0) {{
            isMainPlayerVisible = entries[0].isIntersecting;
            updateMiniPlayerVisibility();
          }}
        }}, {{ threshold: 0.08 }});
        obs.observe(ytWrapEl);
      }}
      if (SONGS.length > 0) {{
        if (!playingSong) playingSong = filteredSongs[0] || SONGS[0];
        currentIndex = filteredSongs.findIndex(x => x.vid === playingSong.vid);
        currentAltIdx = -1;
        updateNowPlayingCard(playingSong);
        syncBlockJumpHighlight();
        pendingVideoLoad = {{ vid: playingSong.vid, autoplay: false }};
        loadYouTubeIframeAPI();
        document.querySelectorAll("tr.song-row").forEach((tr, i) => {{
          tr.classList.toggle("active", i === currentIndex);
        }});
        if (currentIndex > 0) setTimeout(() => scrollToActiveRow(false), 150);
      }}
    }})();
  </script>
</body>
</html>
"""

    html_path = os.path.join(BASE_DIR, "naomi_shemer_playlist_player.html")
    index_path = os.path.join(BASE_DIR, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    secondary_paths = sync_all_secondary_exports(data)
    all_out = [js_path, update_js_path, html_path, index_path] + secondary_paths
    print("עודכנו בהצלחה כל קובצי הפרויקט:")
    for idx_p, p in enumerate(all_out, 1):
        print(f"  {idx_p}. {p}")


if __name__ == "__main__":
    generate_files()
