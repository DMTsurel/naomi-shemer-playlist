#!/usr/bin/env python3
"""
סקריפט לאיסוף ואיחוד מקיף של אלבומי ושירי נעמי שמר מ-8 מקורות:
1. ויקיפדיה העברית (הערך "נעמי שמר" תחת "יצירותיה", תבנית:נעמי שמר, קטגוריות שיריה וערכי האלבומים/ספרים המקושרים)
2. שירונט (כל קטגוריות היצירה: מילים, לחן, תרגום, ביצוע + דיסקוגרפיה עבור prfid=738)
3. אקו"ם מורחב (creatorId=I-000202452-2 + performerId=1267/101393/15697 + getalbuminfo ל-44 אלבומים + getworkinfo לכל היצירות)
4. סטריאו ומונו (דיסקוגרפיה מלאה של 31 דפי אלבומים והקלטות, כולל רשימות רצועות וקישורי יוטיוב)
5. פזמונט (דף האמן, קטגוריית שירי נעמי שמר, מבצעים מקוריים, מצעדים ומזהי יוטיוב)
6. זמרשת (דף האמן ושיריה המוקדמים של נעמי שמר)
7. Discogs API (דיסקוגרפיה ורשימות שירים של אלבומים ראשיים עבור artist=800979)
8. MusicBrainz API (אלבומים, הקלטות ויצירות עבור נעמי שמר)
"""

import concurrent.futures
import csv
import html
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Set, Tuple

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CACHE_DIR = os.path.join(OUTPUT_DIR, "raw_cache")
os.makedirs(RAW_CACHE_DIR, exist_ok=True)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
}


# ---------------------------------------------------------------------------
# עזרי נרמול טקסט ושמות שירים
# ---------------------------------------------------------------------------

NIKUD_RE = re.compile(r"[\u0591-\u05C7]")


def clean_wiki_markup(text: str) -> str:
    """מסיר תגיות ויקיפדיה, קישורים פנימיים והערות שוליים."""
    if not text:
        return ""
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/>]*/\s*>", "", text)
    text = re.sub(r"\{\{הערה\|.*?\}\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def clean_wiki_song_title(title: str) -> str:
    """מסיר סיומות של ויקיפדיה/פזמונט כמו '(שיר)' או '(שושנה דמארי)'."""
    title = clean_wiki_markup(title)
    title = re.sub(r"\s*\((?:שיר|אלבום|מחזמר|סרט|תוכנית)[^)]*\)\s*$", "", title)
    return title.strip()


SYNONYM_MAP = {
    "אהבה בת 20": "אהבה בת עשרים",
    "שניים עשר ירחים": "שנים עשר ירחים",
    "שנים-עשר ירחים": "שנים עשר ירחים",
    "12 ירחים": "שנים עשר ירחים",
    "ירחים 12": "שנים עשר ירחים",
    "א ב": "אלף בית",
    "בהאחזות הנחל בסיני": "בהיאחזות הנחל בסיני",
    "בהיאחזות הנח\"ל בסיני": "בהיאחזות הנחל בסיני",
    "בהאחזות הנח\"ל בסיני": "בהיאחזות הנחל בסיני",
    "אהבת פועלי בנין": "אהבת פועלי הבניין",
    "אהבת פועלי בניין": "אהבת פועלי הבניין",
    "אהבת פועלי הבנין": "אהבת פועלי הבניין",
    "בית חלומותי": "בית חלומותיי",
    "הכל בגלל מסמר": "הכול בגלל מסמר",
    "בגלל מסמר": "הכול בגלל מסמר",
    "alla fiera dell est": "הכול בגלל מסמר",
    "alla fiera dell'est": "הכול בגלל מסמר",
    "הכול פתוח": "הכל פתוח",
    "ואלס להגנת הצומח": "וולס להגנת הצומח",
    "ולס להגנת הצומח": "וולס להגנת הצומח",
    "אורחים לקיץ (אצלנו בחצר)": "אורחים לקיץ",
    "אורחים לקיץ אצלנו בחצר": "אורחים לקיץ",
    "אצלנו בחצר (אורחים לקיץ)": "אורחים לקיץ",
    "אצלנו בחצר אורחים לקיץ": "אורחים לקיץ",
    "אצלנו בחצר": "אורחים לקיץ",
    "פגשתיך בשדה תלתן": "בשדה תלתן",
    "אלף אוהל": "אלף בית",
    "אלף - אוהל": "אלף בית",
    "אלו ציפורים": "אילו ציפורים",
    "אנחנו מאותו הכפר": "אנחנו שנינו מאותו הכפר",
    "שנינו מאותו הכפר": "אנחנו שנינו מאותו הכפר",
    "בנייך מרחוק": "בניך מרחוק",
    "בתכול השמיים": "בתכול השמים",
    "דיוקן אימי": "דיוקן אמי",
    "האמנם": "האומנם",
    "הכלייזמרים מצפת": "הכלייזמרים בצפת",
    "הליצן": "שיר הליצן",
    "המכתב": "מכתב",
    "העיר הלבנה": "עיר לבנה",
    "זהירות בונים": "זהירות בונים כאן",
    "זוהי רק ההתחלה": "וזוהי רק ההתחלה",
    "כבוי אורות": "כיבוי אורות",
    "כמו להיות ירדן": "לשיר זה כמו להיות ירדן",
    "כשנכנס אדר": "משנכנס אדר",
    "לא אהבתי די": "עוד לא אהבתי די",
    "לא כדאי אופליה": "אופליה",
    "זה לא כדאי אופליה": "אופליה",
    "לבבתיני": "ליבבתיני",
    "לילה שכזה": "בלילה שכזה",
    "מארגו": "מרגו",
    "מדאם בלוזון המרגלת": "מדם בלוזון המרגלת",
    "מה אמרו הצפרים": "מה אמרו הציפורים",
    "מוסיקה": "מוזיקה",
    "מטריה בשניים": "מטרייה בשניים",
    "מרש המכביה": "שיר המכביה",
    "נומי נגה": "נומי נוגה",
    "נצאה השדה": "נצא השדה",
    "ספור אהבתי לכם": "סיפור אהבתי לכם",
    "סרנדה": "סרנדה לך",
    "עמוק בטל (טנא מלא כוכבים)": "עמוק בטל",
    "טנא מלא כוכבים": "עמוק בטל",
    "אמצע התמוז": "עצוב למות באמצע תמוז",
    "עקדת יצחק": "עקידת יצחק",
    "פירות חמישה עשר": "שלג על עירי",
    "פת ומלח": "פת במלח",
    "שלומית בונה סוכת שלום": "שלומית בונה סוכה",
    "שירם של האוהבים הזקנים": "הזקנים",
    "חורשת האיקליפטוס": "חורשת האקליפטוס",
    "הوي ארצי מולדתי": "הוי ארצי מולדתי",
    "ליל אמש": "על ליל אמש",
    "חדשי השנה": "שנים עשר ירחים",
    "חודשי השנה": "שנים עשר ירחים",
    "ילדה של שבת": "שבת",
    "זמר לגדעון": "שיר לגדעון",
    "מר נרקיס (אם אדוני חושש)": "מר נרקיס",
    "מר נרקיס אם אדוני חושש": "מר נרקיס",
    "זמר אהבה לים": "שיר אהבה לים",
    "הלילה הלך בשדרות": "הלילה הולך בשדרות",
    "שיר הכזבים להדם": "בארץ להדם",
    "שיר הכזבים": "בארץ להדם",
    "צמחי הבצה": "צמחי הביצה",
    "שיר הנודד": "זמר נודד",
    "שירי זמר נודד": "זמר נודד",
    "מחבואים חפש אותי": "מחבואים",
    "על כל אלה על הדבש ועל העוקץ": "על כל אלה",
    "שיירת רוכבים": "שיירת הרוכבים",
    "שנים עשר הירחים": "שנים עשר ירחים",
    "היאחזות הנחל בסיני": "בהיאחזות הנחל בסיני",
    "האחזות הנחל בסיני": "בהיאחזות הנחל בסיני",
    "יום ח בשבוע": "יום ה בשבוע",
    "בגנה": "בגינה",
    "בגני": "בגני נטעתיך",
    "בית חלמותיי": "בית חלומותיי",
    "חורשת האקפליפטוס": "חורשת האקליפטוס",
    "לוי יהי": "לו יהי",
    "לכה נרננה": "לכו נרננה",
    "נגיד ש": "נגיד",
    "נעה": "נועה",
    "עצוב למות באמצע התמוז": "עצוב למות באמצע תמוז",
    "שלג על עירי פירות חמשה עשר": "שלג על עירי",
    "החגיגה נגמר": "החגיגה נגמרת",
    "הלילה הולך בשדות": "הלילה הולך בשדרות",
    "ירחים": "שנים עשר ירחים",
    "לילה בשדות בית לחם": "בשדות בית לחם",
    "שיירת העשבים": "שירת העשבים",
    "שיר המטריה": "מטרייה בשניים",
    "chanson pour l auvergnat": "לאיש חסדי",
    "chanson pour l'auvergnat": "לאיש חסדי",
    "i whistle a happy tune": "אשרוק לי שיר עליז",
    "que sera sera": "מה שיהיה יהיה",
    "western people funn": "שלא נהיה ברברים",
    "western people funny": "שלא נהיה ברברים",
    "llorando se fue": "למבדה על החוף",
    "dedication": "שיר סיום",
    "king and i": "המלך ואני",
    "oifen weg shteit a boym": "על הדרך עץ עומד",
    "oifen weg shtet a boim": "על הדרך עץ עומד",
    "אילו צפורים": "אילו ציפורים",
    "אילת אהבים": "איילת אהבים",
    "אקרא לשלום": "אקרא שלום",
    "שיר לאוהבים הצעירים": "אקרא שלום",
    "בהאחזות הנחל": "בהיאחזות הנחל בסיני",
    "בכל שנה בסתו גיורא": "בכל שנה בסתיו גיורא",
    "בשלו הפרות בגני": "בשלו הפירות בגני",
    "בתכל השמים": "בתכול השמים",
    "בתכל השמים בגובה כי רב כבר שטו": "בתכול השמים",
    "הדאר בא": "הדואר בא היום",
    "דאר נע": "הדואר בא היום",
    "הדוגרת": "דוגרת לנו לבנה",
    "הורה נחל עז": "הורה נחל עוז",
    "חפש את האשה": "חפש את האישה",
    "החפש הגדול": "החופש הגדול",
    "חרוזי בינים": "חרוזי ביניים",
    "יהי כאשר יהי": "מה שיהיה יהיה",
    "קה סרה סרה": "מה שיהיה יהיה",
    "הילדה אילת": "הילדה איילת",
    "כאן בצפת": "שלג בצפת",
    "חורף בצפת": "שלג בצפת",
    "חרף בצפת": "שלג בצפת",
    "שירה של דסדמונה": "שיר ערבי נחל",
    "שיר ערבי הנחל": "שיר ערבי נחל",
    "שנה שנה טובה לכל חי על פני האדמה": "שנה טובה",
    "אומרים ישנה ארץ ארץ שכורת שמש": "אומרים ישנה ארץ",
    "אין לי רגע דל או סקנדל או פסטיבל": "אין לי רגע דל",
    "אנשים טובים באמצע הדרך": "אנשים טובים",
    "אצלנו בחצר בצל עצי הזית": "אורחים לקיץ",
    "את תלכי בשדה": "האומנם",
    "בגני נטעתיך בגני המצנע בלבי": "בגני נטעתיך",
    "בז על המרפסת בונה לו קן מעלה מעשב": "בז על המרפסת",
    "ארץ להדם": "בארץ להדם",
    "הבה נשירה": "חמסינים במשלט",
    "הוי ארצי מולדתי הר טרשים קרח": "הוי ארצי מולדתי",
    "הי טירליי": "הי טירלי",
    "היה היה רועה ואפילו עז לא היתה לו": "שיר הרועה",
    "ידידי עשה חליל לי מקנה ירק של סוף": "חליל מקנה סוף",
    "על הדרך עץ עומד צמרתו תשוח": "על הדרך עץ עומד",
    "שירו של אמנון": "בשדות בית לחם",
    "שמותיהם של מקומות": "שמות המקומות",
    "ינשוף וירח": "הינשוף והירח",
    "הכליזמרים": "הכלייזמרים בצפת",
    "כליזמרים חוזרים הכליזמרים בצפת": "הכלייזמרים בצפת",
    "לאורך הטילת": "לאורך הטיילת",
    "מי ידליק נר עתיק מי ישמיע שיר": "מי ידליק",
    "מעוז צור ישועתי": "מעוז צור",
    "נצא השדה נלינה בכפרים": "נצא השדה",
    "על שפת ים כנרת": "אגדה",
    "פרות חמישה עשר": "שלג על עירי",
    "פרות חמשה עשר": "שלג על עירי",
    "שלומית בונה סכת שלום": "שלומית בונה סוכה",
    "ירושלים אי דיהבא": "ירושלים של זהב",
    "ירושלים ביסט פון גאלד": "ירושלים של זהב",
    "ירושלים שטאט פון גאלד": "ירושלים של זהב",
    "אדון אופה": "האדון אופה",
    "בניין מרחוק": "בניך מרחוק",
    "דוכיפת": "הדוכיפת",
    "איזה בוקר יפה": "הו מה נאה הוא הבוקר",
    "חצב": "שיר החצב",
    "יום זה יולד בו שיר": "יום זה יום יולד בו שיר",
    "כל דבר נותן פריו": "כל דבר פריו נותן",
    "נייר מה לבן הוא ודיו מה שחורה": "ניר מה לבן",
    "ניר מה לבן הוא ודיו מה שחורה": "ניר מה לבן",
    "שיר אהבה סיאמי": "שיר עם סיאמי",
    "באה הדבורה": "שיר עם סיאמי",
    "בזכותם קיים": "בזכותם",
    "עיר באפור": "העיר באפור",
    "אנא אל תלכי": "אל תלכי מכאן",
    "אל תלך מכאן": "אל תלכי מכאן",
    "כאן מכביה": "שיר המכביה",
    "גדי אחד": "גדי מן ההגדה",
    "בבית חלומותי": "בית חלומותיי",
    "בית חלומותי": "בית חלומותיי",
    "פו הדוב": "פו הדב",
    "אחותי": "בשלו הפירות בגני",
    "איזו שמש מבורכת": "שיר לכת",
    "איש בבקר קם": "ראש קטן",
    "איש בבוקר קם": "ראש קטן",
    "אני מגדלת בעל": "תחביב מיוחד במינו",
    "בקיץ הזה תלבשי לבן": "תלבשי לבן",
    "גורגיה אלבמה מיסיסיפי": "אותלו",
    "גביר": "הגביר",
    "מה יש לגביר": "הגביר",
    "הגדי": "גדי קטן",
    "יללת הרוח": "בעלייתי שם יפתי",
    "כבר לך סיפרתי סיפרתי סיפרתי שאין לי אין לי": "אין לי קו",
    "לא היו דברים מעולם": "בארץ להדם",
    "שיר הפירות": "פרי חדש",
    "הזקנים": "אהבה בת עשרים",
    "שירם של האוהבים הזקנים": "אהבה בת עשרים",
    "המנון": "המנגן",
    "טלפונדו": "יש לי מנגינה בלב",
    "ילד של אמא": "למבדה על החוף",
    "ארץ זו": "זאת הארץ",
    "ימי החנוכה": "סביבון סב סב",
    "כד קטן": "סביבון סב סב",
    "באנו חושך לגרש": "סביבון סב סב",
    "הופה הי": "הופה היי",
    "הי טירלי": "הי טירילי",
    "היי טירילי": "הי טירילי",
    "הי טיריליי": "הי טירילי",
    "הי טירליי": "הי טירילי",
    "הם בלבד": "מתי",
    "והוא יושיעני": "והוא יושיענו",
    "והיה כנגן המנגן": "המנגן",
    "עלמה חיוורת": "ורד בר",
    "עלמה חוורת": "ורד בר",
    "חפש אותי": "מחבואים",
    "נירה אזדרכת": "יש לי חבר",
    "לטיול יצאנו": "הטיול הקטן",
    "לך ועליך": "זמר",
    "למגדול ועד קטן": "כיד המלך",
    "מה אמרו": "מה אמרו הציפורים",
    "אני שואל": "מה עושים העצים",
    "מעוז צור": "שבחי מעוז",
    "משירי זמר נודד": "זמר נודד",
    "סוזן": "סוזאן",
    "על הסכין": "שיר השוק",
    "קומי אורי": "בניך מרחוק",
    "קצור החדשות": "קיצור החדשות",
    "קרן סהר": "קרן יער",
    "שיר האוכל": "עוד לא אכלנו",
    "שיר העונות": "שנים עשר ירחים",
    "שיר על עץ": "על הדרך עץ עומד",
    "שמש שקעה": "שבת",
    "תרנגול בן גבר": "סמוך על התרנגול",
    "דבר מה נפלא": "דבר מה נפלא כל כך",
    "הסוחר מונציה": "הסוחר מוונציה",
    "ילדי העולם": "ילדי כל העולם",
    "ימי ענבים": "ימי הענבים",
    "ירושלים שלי": "ירושלים של זהב",
    "לרקוד אתך": "לרקוד איתך",
    "נצא השדה מתוך שיר השירים": "נצא השדה",
    "שיר הסתיו": "שיר סתיו",
    "שיר ערש": "שיר ערש למקרים מיוחדים",
    "נומי בת": "שיר ערש למקרים מיוחדים",
    "הרי את מקודשת לי": "הנישואין",
    "כבר מאוחר יונתן": "כבר מאוחר יונתן ומיכלי",
    "יונתן ומיכלי": "כבר מאוחר יונתן ומיכלי",
    "צי הצלילים": "צי הצללים",
    "להתחיל מבראשית": "החגיגה נגמרת",
    "שיר כפות רגלייך": "כפות רגליך לבנות",
    "שיר כפות רגליך": "כפות רגליך לבנות",
    "קוארטט": "רביעייה",
    "כנרת שם הרי גולן": "כנרת",
    "עמוק בטל טנא מלא כוכבים": "עמוק בטל",
    "ירוק הוא הברוש": "שיר ערש לצבעים",
    "ניגון מיוחד משלו": "שירת העשבים",
    "שיר שבת": "שבת",
    "טו בשבט": "טו בשבט שלי",
    "שוב יורד מסך": "עוד מעט מסך",
    "די יודלך פון אלף בית": "אלף בית",
    "אוניית כאב": "אוניית הכאב",
    "אל מחנה שחרורים": "אל מחנה השחרורים",
    "שקספיר איננו": "שייקספיר איננו",
}

EXCLUDED_NORMALIZED_SONGS = {
    # כתבת חדשות על תביעה משפטית (2023), לא שיר של נעמי שמר
    "נונו הכלבלב",
    # שירים מודרניים שדגמו/ציטטו משפט של נעמי שמר (היפ-הופ/פופ/מאשאפ)
    "האור והצל",
    "עיר האלוהים",
    "ספורט",
    "יום חדש",
    "ירושלים",
    "ירושלים נערת גבעות",
    "משקפופר",
    "שלומית",
    "שינויים",
    "צחוק מהחוק",
    "מזמור לתודה אל בורות המים",
    "ירושלים של זהב האמיני יום יבוא",
    "יומן מלחמה",
    # כותרות אלבומים / מחרוזות / קטעי מעבר שאינם שירים בודדים
    "זמר בוקר וערב",
    "מחרוזת יוסי בנאי",
    "מחרוזת שירי לכת",
    "מחרוזת שירי נעמי שמר",
    "מחרוזת שירי שמר",
    "המלך ואני",
    "הצגת ילדי המלך",
    "גיטרה",
    "שירים",
    "אגדה",
    "על שפת ים כנרת",
    "יום הולדת מתיה",
    "זמרת השנה",
    # יצירות של יוצרים אחרים (לא של נעמי שמר) שהשתרבבו מאלבומים/אוספים משותפים
    "אין לי קו",
    "גינגי",
    "הדוד שמחה",
    "פו הדב",
}


def normalize_song_title(title: str) -> str:
    """מנרמל שם שיר לצורך איחוד כפילויות בין כלל המאגרים."""
    if not title:
        return ""
    t = html.unescape(title).strip()
    t = NIKUD_RE.sub("", t)
    # הסרת תווים בלתי נראים (כגון RTL/LTR marks)
    t = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", t)
    # הסרת סיומות ויקיפדיה/פזמונט
    t = re.sub(r"\s*\((?:שיר|אלבום|מחזמר|סרט|תוכנית)[^)]*\)\s*$", "", t)
    # תיקון היפוך מספרים של אקו"ם (למשל "20 אהבה בת" -> "אהבה בת 20")
    m_num = re.match(r"^(\d+)\s+([\u0590-\u05FF].*)$", t)
    if m_num:
        t = f"{m_num.group(2)} {m_num.group(1)}"
    # הסרת גרשיים בתוך ראשי תיבות בעברית (למשל נח"ל -> נחל, להד"ם / להד''ם -> להדם)
    t = re.sub(r'(?<=[\u0590-\u05FF])["״׳\'\u2018\u2019\u201c\u201d]+(?=[\u0590-\u05FF])', "", t)
    # החלפת מקפים וסימני פיסוק ברווחים
    t_clean = re.sub(r"[\"'״׳`\u2018\u2019\u201c\u201d־\-–—,.!:?()\[\]/\\]", " ", t)
    t_clean = re.sub(r"\s+", " ", t_clean).strip().lower()
    while t_clean in SYNONYM_MAP:
        nxt = SYNONYM_MAP[t_clean]
        nxt = re.sub(r'(?<=[\u0590-\u05FF])["״׳\'\u2018\u2019\u201c\u201d]+(?=[\u0590-\u05FF])', "", nxt)
        nxt = re.sub(r"[\"'״׳`\u2018\u2019\u201c\u201d־\-–—,.!:?()\[\]/\\]", " ", nxt)
        nxt = re.sub(r"\s+", " ", nxt).strip().lower()
        if nxt == t_clean:
            break
        t_clean = nxt
    return t_clean


# ---------------------------------------------------------------------------
# 1. איסוף מוויקיפדיה
# ---------------------------------------------------------------------------

def fetch_wikipedia_json(params: Dict[str, str]) -> Dict[str, Any]:
    params = dict(params, format="json")
    url = "https://he.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def scrape_wikipedia() -> Dict[str, Any]:
    print("[1/8] קורא נתונים מוויקיפדיה...")
    cache_path = os.path.join(RAW_CACHE_DIR, "wikipedia_raw.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            print(
                f"  -> נטען מהמטמון: {len(cached['albums'])} אלבומים, "
                f"{len(cached['compilations'])} אוספים, "
                f"{len(cached['books'])} ספרים, "
                f"{len(cached['songs'])} שירים."
            )
            return cached

    sections_data = fetch_wikipedia_json({
        "action": "parse",
        "page": "נעמי שמר",
        "prop": "sections",
    })
    works_section_idx = None
    for sec in sections_data["parse"]["sections"]:
        if sec["line"].strip() == "יצירותיה":
            works_section_idx = sec["index"]
            break

    wikitext = ""
    if works_section_idx:
        sec_data = fetch_wikipedia_json({
            "action": "parse",
            "page": "נעמי שמר",
            "section": works_section_idx,
            "prop": "wikitext",
        })
        wikitext = sec_data["parse"]["wikitext"]["*"]

    albums: List[Dict[str, Any]] = []
    compilations: List[Dict[str, Any]] = []
    translated_songs: List[Dict[str, Any]] = []
    books: List[Dict[str, Any]] = []
    tribute_songs: List[Dict[str, Any]] = []

    sub_sections = re.split(r"===\s*([^=]+?)\s*===", wikitext)
    for i in range(1, len(sub_sections), 2):
        sec_title = sub_sections[i].strip()
        sec_body = sub_sections[i + 1]

        if sec_title == "אלבומים":
            for line in sec_body.splitlines():
                line = line.strip()
                if line.startswith("*"):
                    raw_item = clean_wiki_markup(line.lstrip("*").strip())
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", raw_item)
                    year = year_match.group(1) if year_match else ""
                    albums.append({
                        "raw": raw_item,
                        "year": year,
                        "category": "album",
                        "source": "wikipedia",
                    })

        elif sec_title == "אוספים":
            for line in sec_body.splitlines():
                line = line.strip()
                if line.startswith("*"):
                    raw_item = clean_wiki_markup(line.lstrip("*").strip())
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", raw_item)
                    year = year_match.group(1) if year_match else ""
                    compilations.append({
                        "raw": raw_item,
                        "year": year,
                        "category": "compilation",
                        "source": "wikipedia",
                    })

        elif sec_title == "תרגומי שירים":
            rows = sec_body.split("|-")
            for row in rows[1:]:
                if "|}" in row:
                    row = row.split("|}")[0]
                cells = [clean_wiki_markup(c) for c in row.split("||")]
                if len(cells) >= 2:
                    first_cell = re.sub(r"^\s*\|\s*", "", cells[0].strip())
                    orig_title = cells[1].strip() if len(cells) > 1 else ""
                    performer = cells[2].strip() if len(cells) > 2 else ""
                    album_year = cells[3].strip() if len(cells) > 3 else ""
                    if first_cell and "שם השיר" not in first_cell:
                        translated_songs.append({
                            "title": clean_wiki_song_title(first_cell),
                            "original_title": orig_title,
                            "performer": performer,
                            "album_info": album_year,
                            "roles": ["translator"],
                            "source": "wikipedia_translations_table",
                        })

        elif sec_title == "ספרים":
            for line in sec_body.splitlines():
                line = line.strip()
                if line.startswith("*"):
                    raw_item = clean_wiki_markup(line.lstrip("*").strip())
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", raw_item)
                    year = year_match.group(1) if year_match else ""
                    books.append({
                        "raw": raw_item,
                        "year": year,
                        "category": "book",
                        "source": "wikipedia",
                    })

        elif "שירים שנכתבו על" in sec_title:
            for line in sec_body.splitlines():
                line = line.strip()
                if line.startswith("*"):
                    raw_item = clean_wiki_markup(line.lstrip("*").strip())
                    tribute_songs.append(raw_item)

    songs_dict: Dict[str, Dict[str, Any]] = {}

    def add_wiki_song(
        title: str,
        role: str,
        source_detail: str,
        original_title: str = "",
        performer: str = "",
        album: str = "",
        lyricist: str = "",
    ):
        clean_t = clean_wiki_song_title(title)
        if not clean_t:
            return
        norm = normalize_song_title(clean_t)
        if not norm:
            return
        entry = songs_dict.setdefault(norm, {
            "title": clean_t,
            "roles": [],
            "wiki_sources": [],
            "original_title": "",
            "performers": [],
            "albums": [],
            "lyricist": "",
        })
        if role and role not in entry["roles"]:
            entry["roles"].append(role)
        if source_detail and source_detail not in entry["wiki_sources"]:
            entry["wiki_sources"].append(source_detail)
        if original_title and not entry["original_title"]:
            entry["original_title"] = original_title
        if performer and performer not in entry["performers"]:
            entry["performers"].append(performer)
        if album and album not in entry["albums"]:
            entry["albums"].append(album)
        if lyricist and not entry["lyricist"]:
            entry["lyricist"] = lyricist

    for ts in translated_songs:
        add_wiki_song(
            title=ts["title"],
            role="translator",
            source_detail="יצירותיה: תרגומי שירים",
            original_title=ts["original_title"],
            performer=ts["performer"],
            album=ts["album_info"],
        )

    tpl_data = fetch_wikipedia_json({
        "action": "parse",
        "page": "תבנית:נעמי שמר",
        "prop": "wikitext",
    })
    tpl_wt = tpl_data["parse"]["wikitext"]["*"]
    for m in re.finditer(r"\|רשימה(\d)\s*=\s*(.*)", tpl_wt):
        grp_num = m.group(1)
        items_str = m.group(2)
        links = re.findall(r"\[\[(?:([^|\]]+)\|)?([^\]]+)\]\]", items_str)
        for target, label in links:
            song_name = label or target
            if grp_num == "2":
                add_wiki_song(song_name, "author", "תבנית:נעמי שמר (כתבה ותרגמה)")
            elif grp_num == "3":
                add_wiki_song(song_name, "composer", "תבנית:נעמי שמר (הלחינה)")

    for cat_name, role in [
        ("קטגוריה:שירים שנכתבו על ידי נעמי שמר", "author"),
        ("קטגוריה:שירים שהולחנו על ידי נעמי שמר", "composer"),
    ]:
        cat_data = fetch_wikipedia_json({
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cat_name,
            "cmlimit": "500",
        })
        for member in cat_data["query"]["categorymembers"]:
            if member["ns"] == 0:
                add_wiki_song(member["title"], role, cat_name)

    honey_data = fetch_wikipedia_json({
        "action": "parse",
        "page": "על הדבש ועל העוקץ (אלבום)",
        "prop": "wikitext",
    })
    honey_wt = honey_data["parse"]["wikitext"]["*"]
    for idx in range(1, 20):
        m_name = re.search(rf"\|\s*שם{idx}\s*=\s*(.*)", honey_wt)
        m_lyrics = re.search(rf"\|\s*מילים{idx}\s*=\s*(.*)", honey_wt)
        if m_name:
            s_name = clean_wiki_song_title(m_name.group(1))
            lyr = clean_wiki_markup(m_lyrics.group(1)) if m_lyrics else ""
            role = "author" if "נעמי שמר" in lyr else "composer"
            add_wiki_song(
                s_name,
                role=role,
                source_detail="אלבום: על הדבש ועל העוקץ (1981)",
                performer="נעמי שמר",
                album="על הדבש ועל העוקץ, 1981",
                lyricist=lyr,
            )

    kol_data = fetch_wikipedia_json({
        "action": "parse",
        "page": "כל השירים",
        "prop": "wikitext",
    })
    kol_wt = kol_data["parse"]["wikitext"]["*"]
    if "== השירים ==" in kol_wt:
        songs_part = kol_wt.split("== השירים ==")[1].split("==")[0]
        for line in songs_part.splitlines():
            line = line.strip()
            if line.startswith("*"):
                s_name = clean_wiki_song_title(line.lstrip("*").strip())
                add_wiki_song(
                    s_name,
                    role="author",
                    source_detail="ספר: כל השירים (1967)",
                    album="כל השירים (ספר), 1967",
                )
                add_wiki_song(
                    s_name,
                    role="composer",
                    source_detail="ספר: כל השירים (1967)",
                    album="כל השירים (ספר), 1967",
                )

    piano_data = fetch_wikipedia_json({
        "action": "parse",
        "page": "אצלנו בפסנתר",
        "prop": "wikitext",
    })
    piano_wt = piano_data["parse"]["wikitext"]["*"]
    if "== השירים בקלטת ==" in piano_wt:
        p_part = piano_wt.split("== השירים בקלטת ==")[1].split("==")[0]
        for line in p_part.splitlines():
            line = line.strip()
            if line.startswith("#"):
                s_name = clean_wiki_song_title(line.lstrip("#").strip())
                if s_name and s_name != "שיר פתיחה":
                    add_wiki_song(
                        s_name,
                        role="composer",
                        source_detail="אלבום/קלטת: אצלנו בפסנתר (1993)",
                        album="אצלנו בפסנתר, 1993",
                    )

    result = {
        "albums": albums,
        "compilations": compilations,
        "books": books,
        "tribute_songs": tribute_songs,
        "translated_songs": translated_songs,
        "songs": list(songs_dict.values()),
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        f"  -> הסתיים איסוף מוויקיפדיה: {len(albums)} אלבומים, "
        f"{len(compilations)} אוספים, {len(books)} ספרים, "
        f"{len(result['songs'])} שירים ייחודיים."
    )
    return result


# ---------------------------------------------------------------------------
# 2. איסוף משירונט
# ---------------------------------------------------------------------------

SHIRONET_CLASSES = {
    1: ("author", "שירים שנכתבו ע\"י נעמי שמר"),
    2: ("composer", "שירים שהולחנו ע\"י נעמי שמר"),
    3: ("translator", "שירים שתורגמו ע\"י נעמי שמר"),
    4: ("performer", "שירים שבוצעו ע\"י נעמי שמר"),
}


def scrape_shironet() -> Dict[str, Any]:
    print("[2/8] קורא נתונים משירונט...")
    cache_path = os.path.join(RAW_CACHE_DIR, "shironet_raw.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            print(
                f"  -> נטען מהמטמון: {len(cached['songs'])} שירים ייחודיים, "
                f"{len(cached['work_entries'])} דפי שיר (wrkid), "
                f"{len(cached['albums'])} אלבומים."
            )
            return cached

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    headers = dict(BROWSER_HEADERS)
    headers["Referer"] = "https://shironet.mako.co.il/artist?type=works&lang=1&prfid=738"

    def fetch_html(url: str) -> str:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                with opener.open(req, timeout=20) as resp:
                    text = resp.read().decode("utf-8", errors="replace")
                    if "Radware Block Page" not in text:
                        return text
            except Exception as e:
                if attempt == 2:
                    print(f"  [!] שגיאה בטעינת {url}: {e}", file=sys.stderr)
            time.sleep(1.0 + attempt)
        return ""

    fetch_html("https://shironet.mako.co.il/artist?type=works&lang=1&prfid=738")
    time.sleep(0.4)

    work_entries: Dict[str, Dict[str, Any]] = {}

    for cls_id, (role_key, role_label) in SHIRONET_CLASSES.items():
        page = 1
        max_page = 1
        while page <= max_page:
            url = (
                f"https://shironet.mako.co.il/artist?type=works&lang=1"
                f"&prfid=738&class={cls_id}&sort=alpha&page={page}"
            )
            page_html = fetch_html(url)
            if not page_html:
                break

            matches = re.findall(
                r'<a\s+href="(/artist\?type=lyrics&lang=1&prfid=738&wrkid=(\d+))"\s+'
                r'class="artist_player_songlist">\s*(.*?)\s*</a>',
                page_html,
                flags=re.DOTALL,
            )
            for href, wrkid, raw_title in matches:
                title = html.unescape(re.sub(r"\s+", " ", raw_title)).strip()
                entry = work_entries.setdefault(wrkid, {
                    "wrkid": wrkid,
                    "title": title,
                    "url": f"https://shironet.mako.co.il{href}",
                    "roles": [],
                    "albums": [],
                })
                if role_key not in entry["roles"]:
                    entry["roles"].append(role_key)

            page_nums = [int(p) for p in re.findall(r"page=(\d+)", page_html)]
            if page_nums:
                max_page = max(max_page, max(page_nums))

            print(
                f"  -> שירונט class={cls_id} ({role_label}) עמוד {page}/{max_page}: "
                f"נמצאו {len(matches)} רשומות"
            )
            page += 1
            time.sleep(0.35)

    disco_url = "https://shironet.mako.co.il/artist?type=discography&lang=1&prfid=738"
    disco_html = fetch_html(disco_url)
    disc_matches = re.findall(
        r'<a\s+href="(/artist\?type=disc&lang=1&prfid=738&discid=(\d+))"[^>]*>\s*'
        r'([^<]+?)\s*</a>',
        disco_html,
    )
    seen_discs: Set[str] = set()
    shironet_albums: List[Dict[str, Any]] = []
    for href, discid, raw_album_title in disc_matches:
        if discid in seen_discs:
            continue
        seen_discs.add(discid)
        album_title = html.unescape(raw_album_title).strip()
        time.sleep(0.35)
        disc_page_html = fetch_html(f"https://shironet.mako.co.il{href}")
        track_matches = re.findall(
            r'<a\s+href="(/artist\?type=lyrics&lang=1&prfid=738&wrkid=(\d+))"\s+'
            r'class="artist_player_songlist">\s*(.*?)\s*</a>',
            disc_page_html,
            flags=re.DOTALL,
        )
        tracks = []
        for t_href, wrkid, raw_t_title in track_matches:
            t_title = html.unescape(re.sub(r"\s+", " ", raw_t_title)).strip()
            tracks.append({"wrkid": wrkid, "title": t_title})
            if wrkid in work_entries and album_title not in work_entries[wrkid]["albums"]:
                work_entries[wrkid]["albums"].append(album_title)

        shironet_albums.append({
            "discid": discid,
            "title": album_title,
            "url": f"https://shironet.mako.co.il{href}",
            "tracks": tracks,
            "source": "shironet",
        })

    songs_by_norm: Dict[str, Dict[str, Any]] = {}
    for wrkid, w in work_entries.items():
        norm = normalize_song_title(w["title"])
        if not norm:
            continue
        s = songs_by_norm.setdefault(norm, {
            "title": w["title"],
            "roles": [],
            "wrkids": [],
            "urls": [],
            "albums": [],
        })
        if wrkid not in s["wrkids"]:
            s["wrkids"].append(wrkid)
        if w["url"] not in s["urls"]:
            s["urls"].append(w["url"])
        for r in w["roles"]:
            if r not in s["roles"]:
                s["roles"].append(r)
        for a in w["albums"]:
            if a not in s["albums"]:
                s["albums"].append(a)

    result = {
        "songs": list(songs_by_norm.values()),
        "work_entries": list(work_entries.values()),
        "albums": shironet_albums,
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        f"  -> הסתיים איסוף משירונט: {len(result['songs'])} שירים ייחודיים "
        f"({len(work_entries)} דפי שיר), {len(shironet_albums)} אלבומים."
    )
    return result


# ---------------------------------------------------------------------------
# 3. איסוף מאקו"ם (כולל הרחבת אלבומים, מבצעים ופרטי יצירות)
# ---------------------------------------------------------------------------

ACUM_CREATOR_ID = "I-000202452-2"
ACUM_PERFORMER_IDS = [
    ("1267", "נעמי שמר"),
    ("101393", "אנסמבל נעמי שמר"),
    ("15697", "משתתפי מופע הצדעה לנעמי שמר"),
]
ACUM_BASE_URL = "https://nocs.acum.org.il/acumsitesearchdb"


def fetch_acum_json(endpoint_and_query: str) -> Dict[str, Any]:
    url = f"{ACUM_BASE_URL}/{endpoint_and_query}"
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers=BROWSER_HEADERS)
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_sec = 5.0 * (attempt + 1)
                time.sleep(wait_sec)
                continue
            if attempt == 7:
                raise RuntimeError(f"Failed fetching ACUM {url}: {e}") from e
            time.sleep(1.5 * (attempt + 1))
        except Exception as e:
            if attempt == 7:
                raise RuntimeError(f"Failed fetching ACUM {url}: {e}") from e
            time.sleep(1.5 * (attempt + 1))
    return {}


def scrape_acum() -> Dict[str, Any]:
    print("[3/8] קורא נתונים מאקו\"ם (כולל הרחבת אלבומים, מבצעים וגרסאות שירים)...")
    cache_path = os.path.join(RAW_CACHE_DIR, "acum_raw.json")
    all_beans: List[Dict[str, Any]] = []
    albums_list: List[Dict[str, Any]] = []

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            all_beans = cached.get("raw_beans", [])
            albums_list = cached.get("albums", [])

    if not all_beans:
        pages_cache_path = os.path.join(RAW_CACHE_DIR, "acum_pages_partial.json")
        fetched_pages: Dict[str, List[Dict[str, Any]]] = {}
        if os.path.exists(pages_cache_path):
            with open(pages_cache_path, "r", encoding="utf-8") as f:
                fetched_pages = json.load(f)

        init_data = fetch_acum_json(f"searchdb?creatorId={ACUM_CREATOR_ID}")
        result_type_infos = init_data.get("data", {}).get("resultTypeInfos", [])

        tasks: List[Tuple[str, int]] = []

        for rti in result_type_infos:
            rt_key = rti["resultTypeKey"]
            count = int(rti.get("count", 0))
            page_results = rti.get("pageResults") or []
            fetched_pages[f"{rt_key}:1"] = page_results
            total_pages = (count + 9) // 10
            print(f"  -> אקו\"ם קטגוריה '{rt_key}': סה\"כ {count} רשומות ({total_pages} עמודים)")
            for p in range(2, total_pages + 1):
                if f"{rt_key}:{p}" not in fetched_pages:
                    tasks.append((rt_key, p))

        def fetch_page(task: Tuple[str, int]) -> Tuple[str, List[Dict[str, Any]]]:
            rt_key, page_num = task
            time.sleep(0.25)
            data = fetch_acum_json(
                f"searchdb?creatorId={ACUM_CREATOR_ID}&resultTypeKey={rt_key}&pageNumber={page_num}"
            )
            for info in data.get("data", {}).get("resultTypeInfos", []):
                if info.get("resultTypeKey") == rt_key:
                    return f"{rt_key}:{page_num}", (info.get("pageResults") or [])
            return f"{rt_key}:{page_num}", []

        completed = 0
        if tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_task = {executor.submit(fetch_page, t): t for t in tasks}
                for future in concurrent.futures.as_completed(future_to_task):
                    key, beans = future.result()
                    fetched_pages[key] = beans
                    completed += 1
                    if completed % 25 == 0 or completed == len(tasks):
                        print(f"  -> התקדמות אקו\"ם (יצירות וביצועים): {completed}/{len(tasks)} עמודים...")
                        with open(pages_cache_path, "w", encoding="utf-8") as f:
                            json.dump(fetched_pages, f, ensure_ascii=False)

        for key in sorted(fetched_pages.keys(), key=lambda k: (k.split(":")[0], int(k.split(":")[1]))):
            all_beans.extend(fetched_pages[key])

        term_encoded = urllib.parse.quote("נעמי שמר")
        album_init = fetch_acum_json(f"searchdb?term={term_encoded}&resultTypeKey=album&pageNumber=1")
        album_total_pages = 1
        for info in album_init.get("data", {}).get("resultTypeInfos", []):
            if info.get("resultTypeKey") == "album":
                count = int(info.get("count", 0))
                albums_list.extend(info.get("pageResults") or [])
                album_total_pages = (count + 6) // 7

        for p in range(2, album_total_pages + 1):
            adata = fetch_acum_json(f"searchdb?term={term_encoded}&resultTypeKey=album&pageNumber={p}")
            for info in adata.get("data", {}).get("resultTypeInfos", []):
                if info.get("resultTypeKey") == "album":
                    albums_list.extend(info.get("pageResults") or [])

    # 3א. שליפת הקלטות לפי מזהי מבצע (performerId=1267, 101393, 15697)
    perf_cache_path = os.path.join(RAW_CACHE_DIR, "acum_performer_beans.json")
    perf_beans: List[Dict[str, Any]] = []
    if os.path.exists(perf_cache_path):
        with open(perf_cache_path, "r", encoding="utf-8") as f:
            perf_beans = json.load(f)
        print(f"  -> נטענו מהמטמון {len(perf_beans)} רשומות ביצוע (performerId).")
    else:
        print("  -> שולף רשומות ביצוע מאקו\"ם עבור נעמי שמר כמבצעת (performerId=1267, 101393, 15697)...")
        for perf_id, perf_label in ACUM_PERFORMER_IDS:
            init_p = fetch_acum_json(f"searchdb?performerId={perf_id}")
            for rti in init_p.get("data", {}).get("resultTypeInfos", []):
                rt_key = rti["resultTypeKey"]
                count = int(rti.get("count", 0))
                if count == 0:
                    continue
                perf_beans.extend(rti.get("pageResults") or [])
                total_p = (count + 9) // 10
                for p in range(2, total_p + 1):
                    time.sleep(0.22)
                    pdata = fetch_acum_json(
                        f"searchdb?performerId={perf_id}&resultTypeKey={rt_key}&pageNumber={p}"
                    )
                    for info in pdata.get("data", {}).get("resultTypeInfos", []):
                        if info.get("resultTypeKey") == rt_key:
                            perf_beans.extend(info.get("pageResults") or [])
        with open(perf_cache_path, "w", encoding="utf-8") as f:
            json.dump(perf_beans, f, ensure_ascii=False, indent=2)
        print(f"  -> נשלפו {len(perf_beans)} רשומות ביצוע (performerId).")

    # 3ב. שליפת פירוט הרצועות המלא (getalbuminfo) לכל 44 האלבומים באקו"ם
    albums_details_cache_path = os.path.join(RAW_CACHE_DIR, "acum_albums_details.json")
    albums_details: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(albums_details_cache_path):
        with open(albums_details_cache_path, "r", encoding="utf-8") as f:
            albums_details = json.load(f)
        print(f"  -> נטענו מהמטמון פרטי רצועות של {len(albums_details)} אלבומי אקו\"ם.")
    else:
        print(f"  -> שולף רשימות רצועות מלאות (getalbuminfo) עבור {len(albums_list)} אלבומים באקו\"ם...")
        for idx, alb in enumerate(albums_list, 1):
            alb_num = str(alb.get("number", "")).strip()
            if not alb_num or alb_num in albums_details:
                continue
            time.sleep(0.22)
            ainfo = fetch_acum_json(f"getalbuminfo?albumId={alb_num}")
            ab = ainfo.get("data", {}).get("albumBean") or {}
            if ab:
                albums_details[alb_num] = ab
            if idx % 10 == 0 or idx == len(albums_list):
                print(f"  -> התקדמות אלבומי אקו\"ם: {idx}/{len(albums_list)} אלבומים...")
        with open(albums_details_cache_path, "w", encoding="utf-8") as f:
            json.dump(albums_details, f, ensure_ascii=False, indent=2)

    # העשרת רשימת האלבומים בפרטי שנה/מו"ל ורשימת שירים מתוך albums_details
    work_to_acum_albums: Dict[str, List[str]] = {}
    album_track_beans: List[Dict[str, Any]] = []
    for alb in albums_list:
        alb_num = str(alb.get("number", "")).strip()
        ab = albums_details.get(alb_num, {})
        alb_title = (ab.get("title") or alb.get("title") or "").strip()
        versions = ab.get("versions") or []
        release_dates = [v.get("release_date", "") for v in versions if v.get("release_date")]
        publishers = [
            v.get("publisherHebName") or v.get("publisherEngName") or ""
            for v in versions
            if v.get("publisherHebName") or v.get("publisherEngName")
        ]
        alb["release_date"] = release_dates[0] if release_dates else ""
        alb["publisher"] = publishers[0] if publishers else ""
        tracks = ab.get("tracks") or []
        alb["tracks_names"] = [
            (t.get("workHebName") or t.get("workEngName") or "").strip()
            for t in tracks
        ]
        for t in tracks:
            wid = str(t.get("workId") or t.get("workNumber") or "")
            # הוספת הרצועה רק אם נעמי שמר קשורה ליצירה או המבצעת שלה
            creators = (
                (t.get("authors") or [])
                + (t.get("composers") or [])
                + (t.get("translators") or [])
                + (t.get("arrangers") or [])
                + (t.get("creators") or [])
            )
            perf_num = str((t.get("performer") or {}).get("number", ""))
            is_shemer = any(
                c.get("creatorIpBaseNumber") == ACUM_CREATOR_ID or "נעמי שמר" in (c.get("creatorHebName") or "")
                for c in creators
            ) or perf_num in {"1267", "101393"}
            if is_shemer:
                album_track_beans.append(t)
                if wid and alb_title:
                    work_to_acum_albums.setdefault(wid, [])
                    if alb_title not in work_to_acum_albums[wid]:
                        work_to_acum_albums[wid].append(alb_title)

    # איחוד כל הרשומות ליצירות (לפי workId / workTranslatedId)
    works_by_id: Dict[str, Dict[str, Any]] = {}

    def extract_names(beans_list: Optional[List[Dict[str, Any]]]) -> List[str]:
        if not beans_list:
            return []
        names = []
        for b in beans_list:
            n = (b.get("creatorHebName") or b.get("creatorEngName") or "").strip()
            if n and n not in names:
                names.append(n)
        return names

    def has_naomi_shemer(beans_list: Optional[List[Dict[str, Any]]]) -> bool:
        if not beans_list:
            return False
        for b in beans_list:
            if b.get("creatorIpBaseNumber") == ACUM_CREATOR_ID:
                return True
            if "נעמי שמר" in (b.get("creatorHebName") or ""):
                return True
        return False

    combined_beans = all_beans + perf_beans + album_track_beans

    for bean in combined_beans:
        heb_name = (bean.get("workTranslatedHebName") or bean.get("workHebName") or "").strip()
        eng_name = (bean.get("workTranslatedEngName") or bean.get("workEngName") or "").strip()
        orig_name = ""
        if bean.get("original"):
            orig_name = (
                bean["original"].get("workHebName")
                or bean["original"].get("workEngName")
                or ""
            ).strip()
        elif bean.get("workTranslatedHebName") and bean.get("workHebName") != bean.get("workTranslatedHebName"):
            orig_name = (bean.get("workHebName") or "").strip()

        m_num = re.match(r"^(\d+)\s+([\u0590-\u05FF].*)$", heb_name)
        if m_num:
            heb_name = f"{m_num.group(2)} {m_num.group(1)}"

        work_id = str(bean.get("workTranslatedId") or bean.get("workId") or bean.get("workNumber") or "")
        if not work_id:
            continue

        w = works_by_id.setdefault(work_id, {
            "work_id": work_id,
            "work_number": bean.get("workNumber", ""),
            "title_heb": heb_name,
            "title_eng": eng_name,
            "original_title": orig_name,
            "work_type": bean.get("workType", ""),
            "roles": [],
            "authors": [],
            "composers": [],
            "translators": [],
            "arrangers": [],
            "performers": [],
            "albums": [],
            "youtube_ids": [],
            "versions_count": 0,
            "registration_date": bean.get("registration_date", ""),
            "publication_date": bean.get("publication_date", ""),
        })

        if heb_name and (not w["title_heb"] or w["title_heb"].isascii()):
            w["title_heb"] = heb_name
        if eng_name and not w["title_eng"]:
            w["title_eng"] = eng_name
        if orig_name and not w["original_title"]:
            w["original_title"] = orig_name

        authors_beans = (bean.get("authors") or []) + (bean.get("composersAndAuthors") or [])
        composers_beans = (bean.get("composers") or []) + (bean.get("composersAndAuthors") or [])
        translators_beans = bean.get("translators") or []
        arrangers_beans = bean.get("arrangers") or []

        # בדיקה גם ב-creators (מופיע ב-getalbuminfo וב-getworkinfo)
        for cr in bean.get("creators") or []:
            rc = cr.get("roleCode", "")
            if rc in ("A", "CA"):
                authors_beans.append(cr)
            if rc in ("C", "CA"):
                composers_beans.append(cr)
            if rc in ("SA", "TR"):
                translators_beans.append(cr)
            if rc == "AR":
                arrangers_beans.append(cr)

        if has_naomi_shemer(authors_beans) and "author" not in w["roles"]:
            w["roles"].append("author")
        if has_naomi_shemer(composers_beans) and "composer" not in w["roles"]:
            w["roles"].append("composer")
        if has_naomi_shemer(translators_beans) and "translator" not in w["roles"]:
            w["roles"].append("translator")
        if has_naomi_shemer(arrangers_beans) and "arranger" not in w["roles"]:
            w["roles"].append("arranger")

        for a in extract_names(authors_beans):
            if a not in w["authors"]:
                w["authors"].append(a)
        for c in extract_names(composers_beans):
            if c not in w["composers"]:
                w["composers"].append(c)
        for tr in extract_names(translators_beans):
            if tr not in w["translators"]:
                w["translators"].append(tr)
        for ar in extract_names(arrangers_beans):
            if ar not in w["arrangers"]:
                w["arrangers"].append(ar)

        perf = bean.get("performer")
        if perf:
            p_name = (perf.get("performerHebName") or perf.get("performerEngName") or "").strip()
            if p_name and p_name not in w["performers"]:
                w["performers"].append(p_name)
            if str(perf.get("number", "")) in {"1267", "101393"} and "performer" not in w["roles"]:
                w["roles"].append("performer")

        yt_id = (bean.get("youtubeId") or "").strip()
        if yt_id and yt_id not in w["youtube_ids"]:
            w["youtube_ids"].append(yt_id)

        if bean.get("isVersion") == "1":
            w["versions_count"] = max(w["versions_count"], 1)
        elif bean.get("workVersions") and bean["workVersions"].get("total"):
            try:
                wv_total = int(bean["workVersions"]["total"])
                if wv_total > w["versions_count"]:
                    w["versions_count"] = wv_total
            except ValueError:
                pass

    # שיוך אלבומים מתוך getalbuminfo
    for wid, alb_titles in work_to_acum_albums.items():
        if wid in works_by_id:
            for at in alb_titles:
                if at not in works_by_id[wid]["albums"]:
                    works_by_id[wid]["albums"].append(at)

    # 3ג. שליפת getworkinfo ליצירות עבריות שבהן חסרים מבצעים או אלבומים
    workinfo_cache_path = os.path.join(RAW_CACHE_DIR, "acum_workinfo_cache.json")
    workinfo_cache: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(workinfo_cache_path):
        with open(workinfo_cache_path, "r", encoding="utf-8") as f:
            workinfo_cache = json.load(f)

    # נזהה יצירות שיש להן versions_count > 0 ועדיין לא נשלפו ב-workinfo_cache
    work_ids_to_fetch = [
        wid
        for wid, w in works_by_id.items()
        if w.get("versions_count", 0) > 0
        and len(wid) == 7
        and wid not in workinfo_cache
    ]

    if work_ids_to_fetch:
        print(f"  -> שולף פרטי ביצועים ואלבומים (getworkinfo) עבור {len(work_ids_to_fetch)} יצירות באקו\"ם...")

        def fetch_single_workinfo(wid: str) -> Tuple[str, Dict[str, Any]]:
            time.sleep(0.25)
            data = fetch_acum_json(f"getworkinfo?workId={wid}").get("data") or {}
            # נשמור רק את השדות הרלוונטיים לחיסכון במקום
            slim_versions = []
            for v in data.get("workVersions") or []:
                slim_versions.append({
                    "performer": v.get("performer"),
                    "creators": v.get("creators"),
                    "youtubeId": v.get("youtubeId", ""),
                    "time": v.get("time", ""),
                })
            slim_albums = []
            for a in data.get("workAlbums") or []:
                slim_albums.append({
                    "number": a.get("number", ""),
                    "title": a.get("title", ""),
                })
            return wid, {
                "workVersionCount": data.get("workVersionCount", 0),
                "workVersions": slim_versions,
                "workAlbums": slim_albums,
                "publication_date": (data.get("work") or {}).get("publication_date", ""),
            }

        done_cnt = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fetch_single_workinfo, wid): wid for wid in work_ids_to_fetch}
            for fut in concurrent.futures.as_completed(futures):
                wid, info_dict = fut.result()
                workinfo_cache[wid] = info_dict
                done_cnt += 1
                if done_cnt % 40 == 0 or done_cnt == len(work_ids_to_fetch):
                    print(f"  -> התקדמות getworkinfo באקו\"ם: {done_cnt}/{len(work_ids_to_fetch)} יצירות...")
                    with open(workinfo_cache_path, "w", encoding="utf-8") as f:
                        json.dump(workinfo_cache, f, ensure_ascii=False)
    else:
        print(f"  -> נטען מהמטמון מידע מפורט (getworkinfo) עבור {len(workinfo_cache)} יצירות.")

    # עדכון works_by_id מתוך workinfo_cache
    for wid, winfo in workinfo_cache.items():
        if wid not in works_by_id:
            continue
        w = works_by_id[wid]
        if winfo.get("publication_date") and not w["publication_date"]:
            w["publication_date"] = winfo["publication_date"]
        wv_cnt = int(winfo.get("workVersionCount") or 0)
        if wv_cnt > w["versions_count"]:
            w["versions_count"] = wv_cnt
        for v in winfo.get("workVersions") or []:
            perf = v.get("performer")
            if perf:
                p_name = (perf.get("performerHebName") or perf.get("performerEngName") or "").strip()
                if p_name and p_name not in w["performers"]:
                    w["performers"].append(p_name)
                if str(perf.get("number", "")) in {"1267", "101393"} and "performer" not in w["roles"]:
                    w["roles"].append("performer")
            yt = (v.get("youtubeId") or "").strip()
            if yt and yt not in w["youtube_ids"]:
                w["youtube_ids"].append(yt)
            for cr in v.get("creators") or []:
                if cr.get("roleCode") == "AR":
                    ar_name = (cr.get("creatorHebName") or cr.get("creatorEngName") or "").strip()
                    if ar_name and ar_name not in w["arrangers"]:
                        w["arrangers"].append(ar_name)
                    if cr.get("creatorIpBaseNumber") == ACUM_CREATOR_ID and "arranger" not in w["roles"]:
                        w["roles"].append("arranger")
        for a in winfo.get("workAlbums") or []:
            atitle = (a.get("title") or "").strip()
            if atitle and atitle not in w["albums"]:
                w["albums"].append(atitle)

    result = {
        "works": list(works_by_id.values()),
        "raw_beans": all_beans,
        "albums": albums_list,
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        f"  -> הסתיים איסוף מאקו\"ם: {len(result['works'])} יצירות ייחודיות, "
        f"{len(albums_list)} אלבומים מפורטים."
    )
    return result


# ---------------------------------------------------------------------------
# 4. איסוף מאתר "סטריאו ומונו" (Stereo ve Mono)
# ---------------------------------------------------------------------------

def scrape_stereo_ve_mono() -> Dict[str, Any]:
    print("[4/8] קורא נתונים מאתר סטריאו ומונו (Stereo ve Mono)...")
    cache_path = os.path.join(RAW_CACHE_DIR, "stereo_ve_mono_raw.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            print(
                f"  -> נטען מהמטמון: {len(cached['albums'])} אלבומים/דפים, "
                f"{len(cached['songs'])} שירים ייחודיים."
            )
            return cached

    disco_url = "http://stereo-ve-mono.com/discography?artist=%D7%A0%D7%A2%D7%9E%D7%99_%D7%A9%D7%9E%D7%A8"
    req = urllib.request.Request(disco_url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        disco_html = r.read().decode("utf-8", errors="replace")

    album_links: List[Tuple[str, str]] = []
    seen_urls: Set[str] = set()
    for m in re.finditer(r'<a[^>]*href="(https?://stereo-ve-mono\.com/\d+)"[^>]*>(.*?)</a>', disco_html, re.DOTALL):
        href = m.group(1).strip()
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(2))).strip()
        txt = html.unescape(txt)
        if txt and txt != "למידע נוסף" and href not in seen_urls:
            seen_urls.add(href)
            album_links.append((href, txt))

    albums_data: List[Dict[str, Any]] = []
    songs_dict: Dict[str, Dict[str, Any]] = {}

    for idx, (url, heading_title) in enumerate(album_links, 1):
        time.sleep(0.2)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=BROWSER_HEADERS), timeout=20) as r:
                page_html = r.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  [!] שגיאה בטעינת {url}: {e}", file=sys.stderr)
            continue

        ed_match = re.search(r'<div class="editionDes">(.*?)</div>', page_html, re.DOTALL)
        edition_des = ""
        if ed_match:
            edition_des = html.unescape(re.sub(r"<[^>]+>", "", ed_match.group(1))).strip()

        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", heading_title) or re.search(
            r"\b(19\d{2}|20\d{2})\b", edition_des
        )
        year = year_match.group(1) if year_match else ""

        # זיהוי מבצע האלבום אם קיים במבנה "מבצע - שם האלבום"
        album_performer = ""
        if " - " in heading_title:
            album_performer = heading_title.split(" - ")[0].strip()
        elif "נעמי שמר" in heading_title:
            album_performer = "נעמי שמר"

        tracks_ul = re.search(r'<ul class="postTracks">(.*?)</ul>', page_html, re.DOTALL)
        tracks_list: List[Dict[str, Any]] = []
        if tracks_ul:
            for li_html in re.findall(r"<li>(.*?)</li>", tracks_ul.group(1), re.DOTALL):
                # שליפת קישור יוטיוב ישיר (watch?v=...) אם קיים
                yt_matches = re.findall(r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})", li_html)
                # חילוץ החלק שלפני <span> או <a> כשם הרצועה
                title_part = re.split(r"<span|<a", li_html, maxsplit=1)[0]
                title_part = html.unescape(re.sub(r"<[^>]+>", "", title_part)).strip()
                # הסרת מספור רצועה כגון "1. " או "A1. "
                title_part = re.sub(r"^(?:[A-Da-d]?\d+|\d+)\.\s*", "", title_part).strip()
                title_part = re.sub(r"[\u200e\u200f]", "", title_part).strip()
                if not title_part:
                    continue
                # דילוג על שורות הפניה לשירים לועזיים מקוריים ב-12715 או רצועות טכניות
                if (
                    title_part.startswith("החיפושיות")
                    or title_part.startswith("פאקו איבנז")
                    or title_part.lower() == "audio"
                    or title_part.startswith("Bande Sonore")
                ):
                    continue

                # פיצול "מבצע – שם השיר" באלבומי אוסף/מבצעים שונים באתר סטריאו ומונו
                track_performers: List[str] = []
                if " – " in title_part:
                    perf_part, song_part = title_part.split(" – ", 1)
                    title_part = song_part.strip()
                    for p in re.split(r"\s*,\s*|\s+ו(?=להקת|הגשש|צוות|חבורת|הפרברים|יהודית|אפרים|עופר)", perf_part.strip()):
                        p = p.strip()
                        if p and p not in track_performers:
                            track_performers.append(p)
                elif album_performer and album_performer != "לא משויכים":
                    for p in re.split(r"\s*,\s*", album_performer):
                        p = p.strip()
                        if p and p not in track_performers and p != "מבצעים שונים":
                            track_performers.append(p)

                # שליפת קרדיטים מתוך <span ... color:RoyalBlue>
                credits_match = re.search(r"color:RoyalBlue[^>]*>(.*?)</span>", li_html, re.DOTALL)
                credits_text = html.unescape(credits_match.group(1)) if credits_match else ""
                credits_text = re.sub(r"[\u200e\u200f\xa0]", " ", credits_text)

                authors = [
                    a.strip()
                    for a in re.findall(r"©\s*([^♫⇄♭☚(]+)", credits_text)
                    if a.strip()
                ]
                composers = [
                    c.strip()
                    for c in re.findall(r"♫\s*([^©⇄♭☚(]+)", credits_text)
                    if c.strip()
                ]
                translators = [
                    tr.strip()
                    for tr in re.findall(r"⇄\s*([^©♫♭☚(]+)", credits_text)
                    if tr.strip()
                ]
                arrangers = [
                    ar.strip()
                    for ar in re.findall(r"♭\s*([^©♫⇄☚(]+)", credits_text)
                    if ar.strip()
                ]

                # בדיקת שיר מקורי אחרי ☚ עיין
                orig_match = re.search(r"עיין</span>\s*([^<]+)", li_html)
                orig_title = html.unescape(orig_match.group(1)).strip() if orig_match else ""

                # קביעת תפקידי נעמי שמר ברצועה
                roles: List[str] = []
                if any("נעמי שמר" in a for a in authors):
                    roles.append("author")
                if any("נעמי שמר" in c for c in composers):
                    roles.append("composer")
                if any("נעמי שמר" in tr for tr in translators):
                    roles.append("translator")
                if any("נעמי שמר" in ar for ar in arrangers):
                    roles.append("arranger")
                if (
                    any("נעמי שמר" in p for p in track_performers)
                    or heading_title == "לא משויכים"
                ):
                    if "performer" not in roles:
                        roles.append("performer")

                # באלבומים שבהם כל המילים והלחנים של נעמי שמר ואין קרדיט ספציפי על הרצועה
                if not authors and not composers and not translators and heading_title != "לא משויכים":
                    if "נעמי שמר" in heading_title or "מסעות בנימין השלישי" in heading_title:
                        if "author" not in roles:
                            roles.append("author")
                        if "composer" not in roles:
                            roles.append("composer")

                # באלבומים שאינם אלבומי נעמי שמר (כגון "עשור לדודאים" או "בעלייתי שם יפתי")
                # נכלול רק רצועות שבהן נעמי שמר מופיעה בקרדיטים (או שיירת הרוכבים)
                if (
                    heading_title != "לא משויכים"
                    and "נעמי שמר" not in heading_title
                    and "מסעות בנימין השלישי" not in heading_title
                    and not roles
                    and "שיירת" not in title_part
                ):
                    continue

                tracks_list.append({
                    "title": title_part,
                    "performers": track_performers,
                    "authors": authors,
                    "composers": composers,
                    "translators": translators,
                    "arrangers": arrangers,
                    "original_title": orig_title,
                    "roles": roles,
                    "youtube_ids": yt_matches,
                })

                norm = normalize_song_title(title_part)
                if not norm:
                    continue
                s = songs_dict.setdefault(norm, {
                    "title": title_part,
                    "roles": [],
                    "authors": [],
                    "composers": [],
                    "translators": [],
                    "arrangers": [],
                    "original_title": "",
                    "performers": [],
                    "albums": [],
                    "youtube_ids": [],
                })
                for r in roles:
                    if r not in s["roles"]:
                        s["roles"].append(r)
                for a in authors:
                    if a not in s["authors"]:
                        s["authors"].append(a)
                for c in composers:
                    if c not in s["composers"]:
                        s["composers"].append(c)
                for tr in translators:
                    if tr not in s["translators"]:
                        s["translators"].append(tr)
                for ar in arrangers:
                    if ar not in s["arrangers"]:
                        s["arrangers"].append(ar)
                if orig_title and not s["original_title"]:
                    s["original_title"] = orig_title
                for tp in track_performers:
                    if tp and tp not in s["performers"]:
                        s["performers"].append(tp)
                if heading_title != "לא משויכים" and heading_title not in s["albums"]:
                    s["albums"].append(heading_title)
                for yt in yt_matches:
                    if yt not in s["youtube_ids"]:
                        s["youtube_ids"].append(yt)

        albums_data.append({
            "title": heading_title,
            "year": year,
            "performer": album_performer,
            "edition_description": edition_des,
            "url": url,
            "tracks_count": len(tracks_list),
            "tracks": tracks_list,
            "source": "stereo_ve_mono",
        })

    result = {
        "albums": albums_data,
        "songs": list(songs_dict.values()),
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        f"  -> הסתיים איסוף מסטריאו ומונו: {len(albums_data)} אלבומים/דפים, "
        f"{len(result['songs'])} שירים ייחודיים."
    )
    return result


# ---------------------------------------------------------------------------
# 5. איסוף מאתר "פזמונט" (Pizmonet)
# ---------------------------------------------------------------------------

def scrape_pizmonet() -> Dict[str, Any]:
    print("[5/8] קורא נתונים מאתר פזמונט (Pizmonet)...")
    cache_path = os.path.join(RAW_CACHE_DIR, "pizmonet_raw.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            print(f"  -> נטען מהמטמון: {len(cached['songs'])} שירים מפזמונט.")
            return cached

    def fetch_pizmonet_api(params: Dict[str, str]) -> Dict[str, Any]:
        params = dict(params, format="json")
        url = "https://pizmonet.co.il/w/api.php?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))

    songs_dict: Dict[str, Dict[str, Any]] = {}

    def add_pizmonet_song(
        title: str,
        roles: List[str],
        performer: str = "",
        year: str = "",
        youtube_id: str = "",
        authors: Optional[List[str]] = None,
        composers: Optional[List[str]] = None,
        arrangers: Optional[List[str]] = None,
    ):
        # ניקוי סוגריים של שם מבצע בפזמונט כגון "אור (שושנה דמארי)"
        clean_t = clean_wiki_markup(title)
        m_paren = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", clean_t)
        if m_paren and performer and m_paren.group(2).strip() in performer:
            clean_t = m_paren.group(1).strip()
        clean_t = clean_wiki_song_title(clean_t)
        norm = normalize_song_title(clean_t)
        if not norm:
            return
        entry = songs_dict.setdefault(norm, {
            "title": clean_t,
            "roles": [],
            "performers": [],
            "authors": [],
            "composers": [],
            "arrangers": [],
            "year": "",
            "youtube_ids": [],
        })
        for r in roles:
            if r not in entry["roles"]:
                entry["roles"].append(r)
        if performer:
            for p in re.split(r"\s+ו|\s*,\s*", clean_wiki_markup(performer)):
                p = p.strip()
                if p and p not in entry["performers"]:
                    entry["performers"].append(p)
        if year and not entry["year"]:
            entry["year"] = year
        if youtube_id and youtube_id not in entry["youtube_ids"]:
            entry["youtube_ids"].append(youtube_id)
        for a in authors or []:
            if a and a not in entry["authors"]:
                entry["authors"].append(a)
        for c in composers or []:
            if c and c not in entry["composers"]:
                entry["composers"].append(c)
        for ar in arrangers or []:
            if ar and ar not in entry["arrangers"]:
                entry["arrangers"].append(ar)

    # 1. דף האמן "נעמי שמר" בפזמונט (תבניות שיר שנתי ושיר שבועי)
    artist_data = fetch_pizmonet_api({
        "action": "parse",
        "page": "נעמי_שמר",
        "prop": "wikitext",
    })
    artist_wt = artist_data.get("parse", {}).get("wikitext", {}).get("*", "")
    for tpl in re.findall(r"\{\{שיר (?:שנתי|שבועי)(.*?)\}\}", artist_wt, re.DOTALL):
        s_match = re.search(r"\|שיר=([^\n|]+)", tpl)
        p_match = re.search(r"\|ביצוע=([^\n|]+)", tpl)
        c_match = re.search(r"\|קרדיט=([^\n|]+)", tpl)
        d_match = re.search(r"\b(19\d{2}|20\d{2})\b", tpl)
        if s_match:
            s_title = clean_wiki_markup(s_match.group(1))
            perf = clean_wiki_markup(p_match.group(1)) if p_match else ""
            cred = clean_wiki_markup(c_match.group(1)) if c_match else ""
            yr = d_match.group(1) if d_match else ""
            roles = []
            if "מילים" in cred:
                roles.append("author")
            if "לחן" in cred:
                roles.append("composer")
            if "תרגום" in cred:
                roles.append("translator")
            if "ביצוע" in cred or "נעמי שמר" in perf:
                roles.append("performer")
            add_pizmonet_song(s_title, roles, performer=perf, year=yr)

    # 2. כל דפי השירים בקטגוריה:שירי_נעמי_שמר (כולל מזהי יוטיוב!)
    cat_pages = fetch_pizmonet_api({
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "generator": "categorymembers",
        "gcmtitle": "קטגוריה:שירי_נעמי_שמר",
        "gcmlimit": "500",
    })
    for pid, page_obj in (cat_pages.get("query", {}).get("pages") or {}).items():
        p_title = page_obj.get("title", "")
        wt = (page_obj.get("revisions") or [{}])[0].get("*", "")
        perf_m = re.search(r"\|ביצוע=([^\n|]+)", wt)
        lyr_m = re.search(r"\|מילים=([^\n|]+)", wt)
        comp_m = re.search(r"\|לחן=([^\n|]+)", wt)
        arr_m = re.search(r"\|עיבוד=([^\n|]+)", wt)
        yt_m = re.search(r"<youtube[^>]*>([A-Za-z0-9_-]{11})</youtube>", wt)
        yr_m = re.search(r"\b(19\d{2}|20\d{2})\b", wt)

        perf_str = clean_wiki_markup(perf_m.group(1)) if perf_m else ""
        lyr_str = clean_wiki_markup(lyr_m.group(1)) if lyr_m else ""
        comp_str = clean_wiki_markup(comp_m.group(1)) if comp_m else ""
        arr_str = clean_wiki_markup(arr_m.group(1)) if arr_m else ""
        yt_id = yt_m.group(1).strip() if yt_m else ""
        yr_str = yr_m.group(1) if yr_m else ""

        roles = []
        if "נעמי שמר" in lyr_str:
            roles.append("author")
        if "נעמי שמר" in comp_str:
            roles.append("composer")
        if "נעמי שמר" in perf_str:
            roles.append("performer")
        if "נעמי שמר" in arr_str:
            roles.append("arranger")

        add_pizmonet_song(
            title=p_title,
            roles=roles,
            performer=perf_str,
            year=yr_str,
            youtube_id=yt_id,
            authors=[lyr_str] if lyr_str else [],
            composers=[comp_str] if comp_str else [],
            arrangers=[arr_str] if arr_str else [],
        )

    result = {"songs": list(songs_dict.values())}
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  -> הסתיים איסוף מפזמונט: {len(result['songs'])} שירים ייחודיים (כולל מזהי יוטיוב).")
    return result


# ---------------------------------------------------------------------------
# 6. איסוף מאתר "זמרשת" (Zemereshet)
# ---------------------------------------------------------------------------

def scrape_zemereshet() -> Dict[str, Any]:
    print("[6/8] קורא נתונים מאתר זמרשת (Zemereshet)...")
    cache_path = os.path.join(RAW_CACHE_DIR, "zemereshet_raw.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            print(f"  -> נטען מהמטמון: {len(cached['songs'])} שירים מזמרשת.")
            return cached

    artist_url = "https://www.zemereshet.co.il/artist.asp?id=7970"
    with urllib.request.urlopen(urllib.request.Request(artist_url, headers=BROWSER_HEADERS), timeout=20) as r:
        artist_html = r.read().decode("utf-8", errors="replace")

    song_links: Dict[str, str] = {}
    for m in re.finditer(r'href="(song\.asp\?id=(\d+))"[^>]*>(.*?)</a>', artist_html, re.DOTALL):
        sid = m.group(2)
        title = html.unescape(re.sub(r"<[^>]+>", "", m.group(3))).strip()
        if title and sid not in song_links:
            song_links[sid] = title

    songs_list: List[Dict[str, Any]] = []
    for sid, title in song_links.items():
        time.sleep(0.25)
        s_url = f"https://www.zemereshet.co.il/song.asp?id={sid}"
        with urllib.request.urlopen(urllib.request.Request(s_url, headers=BROWSER_HEADERS), timeout=20) as r:
            s_html = r.read().decode("utf-8", errors="replace")

        roles = []
        if re.search(r"מילים:.*?נעמי שמר", s_html, re.DOTALL) or "מילים ולחן: נעמי שמר" in s_html:
            roles.append("author")
        if re.search(r"לחן:.*?נעמי שמר", s_html, re.DOTALL) or "מילים ולחן: נעמי שמר" in s_html:
            roles.append("composer")
        if not roles:
            roles = ["author", "composer"]

        songs_list.append({
            "zemereshet_id": sid,
            "title": title,
            "url": s_url,
            "roles": roles,
            "source": "zemereshet",
        })

    result = {"songs": songs_list}
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  -> הסתיים איסוף מזמרשת: {len(songs_list)} שירים.")
    return result


# ---------------------------------------------------------------------------
# 7. איסוף מ-Discogs API
# ---------------------------------------------------------------------------

def scrape_discogs() -> Dict[str, Any]:
    print("[7/8] קורא נתונים מ-Discogs API...")
    cache_path = os.path.join(RAW_CACHE_DIR, "discogs_raw.json")
    discogs_headers = {
        "User-Agent": "NaomiShemerComprehensiveCatalog/1.0 +https://discogs.com",
        "Accept": "application/json",
    }

    detailed_releases: List[Dict[str, Any]] = []
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            detailed_releases = cached.get("releases", [])

    if not detailed_releases:
        url = "https://api.discogs.com/artists/800979/releases?per_page=100&page=1"
        req = urllib.request.Request(url, headers=discogs_headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        main_releases = [rel for rel in data.get("releases", []) if rel.get("role") == "Main"]
        for rel in main_releases:
            rel_id = rel.get("id")
            rel_type = rel.get("type", "release")
            rel_title = (rel.get("title") or "").strip()
            rel_year = str(rel.get("year") or "")
            rel_artist = (rel.get("artist") or "נעמי שמר").replace("*", "").strip()
            detailed_releases.append({
                "id": rel_id,
                "type": rel_type,
                "title": rel_title,
                "year": rel_year,
                "artist": rel_artist,
                "tracks_count": 0,
                "tracks": [],
                "url": f"https://www.discogs.com/{rel_type}/{rel_id}",
                "source": "discogs",
            })

    # שליפת רצועות עבור אלבומים שעדיין חסרים להם רצועות (כולל המתנה במקרה של 429)
    missing_releases = [rel for rel in detailed_releases if not rel.get("tracks")]
    if missing_releases:
        print(f"  -> משלים רשימות שירים מ-Discogs עבור {len(missing_releases)} אלבומים...")
        for idx, rel in enumerate(missing_releases, 1):
            rel_id = rel["id"]
            rel_type = rel["type"]
            resource_url = f"https://api.discogs.com/{rel_type}s/{rel_id}"
            for attempt in range(4):
                time.sleep(1.5)
                try:
                    with urllib.request.urlopen(
                        urllib.request.Request(resource_url, headers=discogs_headers), timeout=20
                    ) as rr:
                        rel_detail = json.loads(rr.read().decode("utf-8"))
                        tracks: List[str] = []
                        for t in rel_detail.get("tracklist") or []:
                            t_title = (t.get("title") or "").strip()
                            if t_title:
                                tracks.append(t_title)
                        rel["tracks"] = tracks
                        rel["tracks_count"] = len(tracks)
                        break
                except urllib.error.HTTPError as e:
                    if e.code == 429 and attempt < 3:
                        time.sleep(15.0 * (attempt + 1))
                        continue
                    print(f"  [!] אזהרה: לא ניתן לשלוף פירוט Discogs עבור {rel['title']}: {e}", file=sys.stderr)
                    break
                except Exception as e:
                    print(f"  [!] אזהרה: לא ניתן לשלוף פירוט Discogs עבור {rel['title']}: {e}", file=sys.stderr)
                    break

    # בניית רשימת שירים נקייה מתוך כלל אלבומי Discogs
    songs_dict: Dict[str, Dict[str, Any]] = {}
    for rel in detailed_releases:
        # דילוג על מהדורה 38289066 ("Asif") שבה שמות השירים תורגמו מכונה מאנגלית לעברית עם שגיאות כתיב
        if str(rel.get("id")) == "38289066":
            continue
        rel_title = rel["title"]
        rel_artist = rel["artist"]
        for raw_t in rel.get("tracks") or []:
            t_title = raw_t.strip()
            orig_t = ""
            # אם יש שם בעברית לצד אנגלית מופרד ב-" = " נעדיף את העברית
            if " = " in t_title:
                parts = [p.strip() for p in t_title.split(" = ")]
                heb_parts = [p for p in parts if any("\u0590" <= c <= "\u05FF" for c in p)]
                if heb_parts:
                    t_title = heb_parts[0]
            # אם הכותרת באנגלית ובסוגריים מופיע השם בעברית, למשל "My Lord And Master (אדון ומלך)"
            m_bilingual = re.match(r"^([A-Za-z0-9\s',?!.-]+)\(([\u0590-\u05FF][^)]+)\)$", t_title)
            if m_bilingual:
                orig_t = m_bilingual.group(1).strip()
                t_title = m_bilingual.group(2).strip()

            if t_title in {"שולי נתן", "אוברטורה", "Overture (אוברטורה)"}:
                continue

            if any("\u0590" <= c <= "\u05FF" for c in t_title):
                norm = normalize_song_title(t_title)
                if norm:
                    s = songs_dict.setdefault(norm, {
                        "title": t_title,
                        "original_title": orig_t,
                        "albums": [],
                        "performers": [],
                    })
                    if orig_t and not s.get("original_title"):
                        s["original_title"] = orig_t
                    if rel_title and rel_title not in s["albums"]:
                        s["albums"].append(rel_title)
                    if rel_artist and rel_artist not in s["performers"]:
                        s["performers"].append(rel_artist)

    result = {
        "releases": detailed_releases,
        "songs": list(songs_dict.values()),
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        f"  -> הסתיים איסוף מ-Discogs: {len(detailed_releases)} אלבומים, "
        f"{len(result['songs'])} שירים בעברית."
    )
    return result


# ---------------------------------------------------------------------------
# 8. איסוף מ-MusicBrainz API
# ---------------------------------------------------------------------------

MB_ARTIST_ID = "40a0a2c6-4a92-4442-b16e-1750111818b2"


def scrape_musicbrainz() -> Dict[str, Any]:
    print("[8/8] קורא נתונים מ-MusicBrainz API...")
    cache_path = os.path.join(RAW_CACHE_DIR, "musicbrainz_raw.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            print(
                f"  -> נטען מהמטמון: {len(cached['releases'])} אלבומים מ-MusicBrainz, "
                f"{len(cached['songs'])} שירים."
            )
            return cached

    mb_headers = {
        "User-Agent": "NaomiShemerComprehensiveCatalog/1.0 (https://musicbrainz.org)",
        "Accept": "application/json",
    }

    rel_url = f"https://musicbrainz.org/ws/2/release?artist={MB_ARTIST_ID}&inc=recordings&limit=100&fmt=json"
    with urllib.request.urlopen(urllib.request.Request(rel_url, headers=mb_headers), timeout=20) as r:
        rel_data = json.loads(r.read().decode("utf-8"))

    time.sleep(1.1)
    work_url = f"https://musicbrainz.org/ws/2/work?artist={MB_ARTIST_ID}&limit=100&fmt=json"
    with urllib.request.urlopen(urllib.request.Request(work_url, headers=mb_headers), timeout=20) as r:
        work_data = json.loads(r.read().decode("utf-8"))

    releases_list: List[Dict[str, Any]] = []
    songs_dict: Dict[str, Dict[str, Any]] = {}

    for rel in rel_data.get("releases") or []:
        r_id = rel.get("id", "")
        r_title = (rel.get("title") or "").strip()
        r_date = (rel.get("date") or "")[:4]
        tracks: List[str] = []
        for med in rel.get("media") or []:
            for tr in med.get("tracks") or []:
                t_title = (tr.get("title") or "").strip()
                if t_title:
                    tracks.append(t_title)
                    if any("\u0590" <= c <= "\u05FF" for c in t_title):
                        norm = normalize_song_title(t_title)
                        if norm:
                            s = songs_dict.setdefault(norm, {
                                "title": t_title,
                                "albums": [],
                            })
                            if r_title and r_title not in s["albums"]:
                                s["albums"].append(r_title)

        releases_list.append({
            "id": r_id,
            "title": r_title,
            "year": r_date,
            "tracks_count": len(tracks),
            "tracks": tracks,
            "url": f"https://musicbrainz.org/release/{r_id}",
            "source": "musicbrainz",
        })

    for w in work_data.get("works") or []:
        w_title = (w.get("title") or "").strip()
        if any("\u0590" <= c <= "\u05FF" for c in w_title):
            norm = normalize_song_title(w_title)
            if norm:
                songs_dict.setdefault(norm, {
                    "title": w_title,
                    "albums": [],
                })

    result = {
        "releases": releases_list,
        "songs": list(songs_dict.values()),
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        f"  -> הסתיים איסוף מ-MusicBrainz: {len(releases_list)} אלבומים, "
        f"{len(result['songs'])} שירים ייחודיים."
    )
    return result


# ---------------------------------------------------------------------------
# 9. איסוף מהספרייה הלאומית (National Library of Israel - SRU MARC21 API)
# ---------------------------------------------------------------------------

NLI_SRU_URL = "https://nli.alma.exlibrisgroup.com/view/sru/972NNL_INST"
NLI_NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "marc": "http://www.loc.gov/MARC21/slim",
}


def fetch_nli_sru_records(query: str) -> List[ET.Element]:
    records: List[ET.Element] = []
    start_record = 1
    batch_size = 50
    while True:
        params = {
            "version": "1.2",
            "operation": "searchRetrieve",
            "recordSchema": "marcxml",
            "query": query,
            "maximumRecords": str(batch_size),
            "startRecord": str(start_record),
        }
        url = NLI_SRU_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_HEADERS["User-Agent"]})
        with urllib.request.urlopen(req, timeout=25) as r:
            xml_bytes = r.read()
        root = ET.fromstring(xml_bytes)
        batch = root.findall(".//marc:record", NLI_NS)
        records.extend(batch)
        next_pos_txt = root.findtext("srw:nextRecordPosition", namespaces=NLI_NS)
        if not next_pos_txt or not batch:
            break
        next_pos = int(next_pos_txt)
        if next_pos <= start_record:
            break
        start_record = next_pos
        time.sleep(0.2)
    return records


def format_nli_person_name(raw_name: str) -> str:
    """הופך 'שמר, נעמי,' ל-'נעמי שמר'."""
    name = raw_name.strip().rstrip(",.")
    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            return f"{parts[1]} {parts[0]}"
    return name


def scrape_nli() -> Dict[str, Any]:
    print("[9/9] קורא נתונים מהספרייה הלאומית (בית לזמר העברי, ארכיון הצליל וארכיון נעמי שמר)...")
    cache_path = os.path.join(RAW_CACHE_DIR, "nli_raw.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            cached = json.load(f)
            print(
                f"  -> נטען מהמטמון: {len(cached['songs'])} שירים/דפי שיר, "
                f"{len(cached['albums'])} אלבומים מהספרייה הלאומית."
            )
            return cached

    # 1. שליפת כל דפי השיר הרשמיים ("בית לזמר העברי" - DAFSHIR) של נעמי שמר
    print("  -> שולף דפי שיר (DAFSHIR) מבית לזמר העברי בספרייה הלאומית...")
    dafshir_records = fetch_nli_sru_records('alma.creator="שמר, נעמי" AND alma.local_field_999="DAFSHIR"')
    print(f"  -> נשלפו {len(dafshir_records)} דפי שיר רשמיים (DAFSHIR).")

    # 2. שליפת פריטי יצירות ותרגומים מתוך "ארכיון נעמי שמר" בספרייה הלאומית (סדרה A וסדרה B)
    print("  -> שולף רשומות יצירות ותרגומים מתוך ארכיון נעמי שמר בספרייה הלאומית...")
    archive_a_records = fetch_nli_sru_records('alma.all_for_ui="ארכיון נעמי שמר" AND alma.all_for_ui="סדרה A"')
    archive_b_records = fetch_nli_sru_records('alma.all_for_ui="ארכיון נעמי שמר" AND alma.all_for_ui="סדרה B"')
    print(f"  -> נשלפו {len(archive_a_records) + len(archive_b_records)} רשומות מארכיון נעמי שמר.")

    # 3. שליפת אלבומים מוקלטים מארכיון הצליל הלאומי (Album_Ana_Digi)
    print("  -> שולף אלבומים מארכיון הצליל הלאומי בספרייה הלאומית...")
    album_records = fetch_nli_sru_records('alma.creator="שמר, נעמי" AND alma.local_notes="Album_Ana_Digi"')
    print(f"  -> נשלפו {len(album_records)} אלבומים מארכיון הצליל הלאומי.")

    songs_dict: Dict[str, Dict[str, Any]] = {}

    def clean_nli_text(s: str) -> str:
        s = NIKUD_RE.sub("", s)
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"[\s/:;,.]+$", "", s).strip()
        s = re.sub(
            r"\s*\((?:[^)]*(?:כתב יד|טקסט בלבד|דפוס|צילום|טיוטה|הדפסה|נוסח|סקיצה|עברית|אנגלית|אמהרית|יידיש|צרפתית|manuscript|arrangement|arrangment)[^)]*)\)\s*$",
            "",
            s,
            flags=re.I,
        ).strip()
        return re.sub(r"[\s/:;,.]+$", "", s).strip()

    NON_SONG_ARCHIVE_TITLES = {
        "ארכיון נעמי שמר",
        "רביעית הבנות נעמי שמר",
        "שירים מכנרת",
        "ארבע",
        "משחק בהרמוניות",
    }

    def process_nli_song_record(rec: ET.Element, is_dafshir: bool) -> None:
        mms_id = rec.findtext('marc:controlfield[@tag="001"]', default="", namespaces=NLI_NS).strip()
        f008 = rec.findtext('marc:controlfield[@tag="008"]', default="", namespaces=NLI_NS)
        year = ""
        if len(f008) >= 11 and f008[7:11].isdigit():
            yr_num = int(f008[7:11])
            if 1940 <= yr_num <= 2026:
                year = str(yr_num)

        f245 = rec.find('marc:datafield[@tag="245"]', NLI_NS)
        if f245 is None:
            return
        raw_title = (f245.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "").strip()
        raw_title = clean_nli_text(raw_title)
        if not raw_title or raw_title.isdigit():
            return
        if (raw_title.startswith("[") and raw_title.endswith("]")) or raw_title.startswith("שבשבת") or raw_title in NON_SONG_ARCHIVE_TITLES:
            return
        # עבור רשומות ארכיון שאינן דף שיר, נכלול רק כותרות בעברית
        if not is_dafshir and not any("\u0590" <= c <= "\u05FF" for c in raw_title):
            return

        # תיקון היפוך מספרים כגון "20 אהבה בת"
        m_num = re.match(r"^(\d+)\s+([\u0590-\u05FF].*)$", raw_title)
        if m_num:
            raw_title = f"{m_num.group(2)} {m_num.group(1)}"

        orig_title = ""
        f240 = rec.find('marc:datafield[@tag="240"]', NLI_NS)
        if f240 is not None:
            orig_title = (f240.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "").strip().rstrip(".")

        alt_titles: List[str] = []
        opening_line = ""
        for f246 in rec.findall('marc:datafield[@tag="246"]', NLI_NS):
            i_code = (f246.findtext('marc:subfield[@code="i"]', default="", namespaces=NLI_NS) or "").strip()
            a_val = clean_nli_text(f246.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "")
            if not a_val:
                continue
            if "אתחלתא" in i_code:
                opening_line = a_val
            elif "פזמון" not in i_code:
                if any("\u0590" <= c <= "\u05FF" for c in a_val):
                    alt_titles.append(a_val)
                elif not orig_title:
                    orig_title = a_val

        notes = ""
        f520 = rec.find('marc:datafield[@tag="520"]', NLI_NS)
        if f520 is not None:
            notes = (f520.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "").strip()
        if "פרודיה על השיר" in notes:
            return

        acum_ids: List[str] = []
        for f985 in rec.findall('marc:datafield[@tag="985"]', NLI_NS):
            b_val = (f985.findtext('marc:subfield[@code="b"]', default="", namespaces=NLI_NS) or "").strip()
            if b_val and b_val not in acum_ids:
                acum_ids.append(b_val)

        source_books: List[str] = []
        for f593 in rec.findall('marc:datafield[@tag="593"]', NLI_NS):
            c_val = (f593.findtext('marc:subfield[@code="c"]', default="", namespaces=NLI_NS) or "").strip(" []")
            if c_val and c_val not in source_books:
                source_books.append(c_val)

        authors: List[str] = []
        composers: List[str] = []
        translators: List[str] = []
        arrangers: List[str] = []
        performers: List[str] = []
        roles: List[str] = []

        for tag in ("100", "700", "110", "710"):
            for df in rec.findall(f'marc:datafield[@tag="{tag}"]', NLI_NS):
                lang_sub = df.findtext('marc:subfield[@code="9"]', default="", namespaces=NLI_NS)
                if lang_sub == "lat":
                    continue
                raw_person = df.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or ""
                person = format_nli_person_name(raw_person)
                if not person:
                    continue
                relators = [
                    (s.text or "").strip()
                    for s in df.findall('marc:subfield[@code="e"]', NLI_NS)
                    if s.text
                ]
                is_shemer = "נעמי שמר" in person or "שמר, נעמי" in raw_person
                for rel in relators:
                    if "מחבר" in rel or "משורר" in rel:
                        if person not in authors:
                            authors.append(person)
                        if is_shemer and "author" not in roles:
                            roles.append("author")
                    elif "מלחין" in rel:
                        if person not in composers:
                            composers.append(person)
                        if is_shemer and "composer" not in roles:
                            roles.append("composer")
                    elif "מתרגם" in rel:
                        if person not in translators:
                            translators.append(person)
                        if is_shemer and "translator" not in roles:
                            roles.append("translator")
                    elif "מעבד" in rel:
                        if person not in arrangers:
                            arrangers.append(person)
                        if is_shemer and "arranger" not in roles:
                            roles.append("arranger")
                    elif "מבצע" in rel or "זמר" in rel:
                        if person not in performers:
                            performers.append(person)
                        if is_shemer and "performer" not in roles:
                            roles.append("performer")

        if not roles:
            return
        # עבור פריטי ארכיון שאינם דף שיר רשמי (DAFSHIR), נכלול רק יצירות מולחנות או מתורגמות (ולא טורים עיתונאיים)
        if not is_dafshir and not composers and "translator" not in roles and "composer" not in roles and "arranger" not in roles:
            return

        norm = normalize_song_title(raw_title)
        if not norm:
            return
        entry = songs_dict.setdefault(norm, {
            "title": raw_title,
            "alt_titles": [],
            "original_title": "",
            "year": "",
            "roles": [],
            "authors": [],
            "composers": [],
            "translators": [],
            "arrangers": [],
            "performers": [],
            "albums": [],
            "acum_work_ids": [],
            "nli_mms_ids": [],
            "opening_line": "",
            "notes": "",
            "is_dafshir": is_dafshir,
        })
        if is_dafshir:
            entry["is_dafshir"] = True
        if mms_id and mms_id not in entry["nli_mms_ids"]:
            entry["nli_mms_ids"].append(mms_id)
        for wid in acum_ids:
            if wid not in entry["acum_work_ids"]:
                entry["acum_work_ids"].append(wid)
        for at in alt_titles:
            if at not in entry["alt_titles"] and at != entry["title"]:
                entry["alt_titles"].append(at)
        if orig_title and not entry["original_title"]:
            entry["original_title"] = orig_title
        if year and not entry["year"]:
            entry["year"] = year
        if opening_line and not entry["opening_line"]:
            entry["opening_line"] = opening_line
        if notes and not entry["notes"]:
            entry["notes"] = notes
        for r in roles:
            if r not in entry["roles"]:
                entry["roles"].append(r)
        for a in authors:
            if a not in entry["authors"]:
                entry["authors"].append(a)
        for c in composers:
            if c not in entry["composers"]:
                entry["composers"].append(c)
        for tr in translators:
            if tr not in entry["translators"]:
                entry["translators"].append(tr)
        for ar in arrangers:
            if ar not in entry["arrangers"]:
                entry["arrangers"].append(ar)
        for p in performers:
            if p not in entry["performers"]:
                entry["performers"].append(p)
        for sb in source_books:
            if sb not in entry["albums"]:
                entry["albums"].append(sb)

    for rec in dafshir_records:
        process_nli_song_record(rec, is_dafshir=True)
    for rec in archive_a_records + archive_b_records:
        process_nli_song_record(rec, is_dafshir=False)

    nli_albums: List[Dict[str, Any]] = []
    for rec in album_records:
        mms_id = rec.findtext('marc:controlfield[@tag="001"]', default="", namespaces=NLI_NS).strip()
        f245 = rec.find('marc:datafield[@tag="245"]', NLI_NS)
        if f245 is None:
            continue
        a_part = (f245.findtext('marc:subfield[@code="a"]', default="", namespaces=NLI_NS) or "").strip(" /:")
        b_part = (f245.findtext('marc:subfield[@code="b"]', default="", namespaces=NLI_NS) or "").strip(" /:")
        full_title = f"{a_part}: {b_part}" if b_part else a_part
        f260 = rec.find('marc:datafield[@tag="260"]', NLI_NS) or rec.find('marc:datafield[@tag="264"]', NLI_NS)
        yr = ""
        if f260 is not None:
            c_txt = f260.findtext('marc:subfield[@code="c"]', default="", namespaces=NLI_NS) or ""
            m_yr = re.search(r"\b(19\d{2}|20\d{2})\b", c_txt)
            if m_yr:
                yr = m_yr.group(1)
        nli_albums.append({
            "mms_id": mms_id,
            "title": full_title,
            "year": yr,
            "type": "אלבום/הקלטה (ארכיון הצליל הלאומי - הספרייה הלאומית)",
            "performer": "נעמי שמר / אמנים שונים",
            "url": f"https://www.nli.org.il/he/items/NNL_MUSIC_AL{mms_id}",
            "source": "nli",
        })

    result = {
        "songs": list(songs_dict.values()),
        "albums": nli_albums,
        "dafshir_count": len(dafshir_records),
        "archive_count": len(archive_a_records) + len(archive_b_records),
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(
        f"  -> הסתיים איסוף מהספרייה הלאומית: {len(result['songs'])} שירים ייחודיים "
        f"({len(dafshir_records)} דפי שיר + {len(archive_a_records) + len(archive_b_records)} פריטי ארכיון), "
        f"{len(nli_albums)} אלבומים."
    )
    return result


# ---------------------------------------------------------------------------
# 10. איחוד ויצירת הקטלוג המאוחד מכל 9 המקורות
# ---------------------------------------------------------------------------

ROLE_HEB_LABELS = {
    "author": "מילים",
    "composer": "לחן",
    "translator": "תרגום",
    "performer": "ביצוע",
    "arranger": "עיבוד",
}


def build_unified_catalog(
    wiki_data: Dict[str, Any],
    shironet_data: Dict[str, Any],
    acum_data: Dict[str, Any],
    svm_data: Dict[str, Any],
    pizmonet_data: Dict[str, Any],
    zemereshet_data: Dict[str, Any],
    discogs_data: Dict[str, Any],
    mb_data: Dict[str, Any],
    nli_data: Dict[str, Any],
) -> Dict[str, Any]:
    unified_songs: Dict[str, Dict[str, Any]] = {}

    def get_or_create_song(title: str) -> Optional[Dict[str, Any]]:
        norm = normalize_song_title(title)
        if not norm or norm in EXCLUDED_NORMALIZED_SONGS:
            return None
        # סינון כותרות לועזיות בלבד (רישומי תרגומים לשפות זרות באקו"ם של שירים עבריים קיימים)
        if not any("\u0590" <= c <= "\u05FF" for c in norm):
            return None
        clean_t = NIKUD_RE.sub("", title).strip()
        # אם השם הנוכחי היה מילה נרדפת ב-SYNONYM_MAP, נעדיף את השם הקנוני ככותרת ראשית
        raw_clean = re.sub(r'(?<=[\u0590-\u05FF])["״׳\'\u2018\u2019\u201c\u201d]+(?=[\u0590-\u05FF])', "", clean_t)
        raw_clean = re.sub(r"[\"'״׳`\u2018\u2019\u201c\u201d־\-–—,.!:?()\[\]/\\]", " ", raw_clean)
        raw_clean = re.sub(r"\s+", " ", raw_clean).strip().lower()
        canonical_t = SYNONYM_MAP.get(raw_clean, clean_t)
        if norm not in unified_songs:
            alt_list = []
            if clean_t and clean_t != canonical_t:
                alt_list.append(clean_t)
            unified_songs[norm] = {
                "normalized_key": norm,
                "title": canonical_t,
                "alt_titles": alt_list,
                "english_title": "",
                "original_title": "",
                "year": "",
                "sources": [],
                "roles": [],
                "authors": [],
                "composers": [],
                "translators": [],
                "arrangers": [],
                "performers": [],
                "albums": [],
                "acum_work_ids": [],
                "acum_versions_count": 0,
                "shironet_wrkids": [],
                "shironet_urls": [],
                "nli_mms_ids": [],
                "opening_line": "",
                "notes": [],
                "youtube_ids": [],
                "wiki_details": [],
            }
        else:
            existing = unified_songs[norm]
            if clean_t and clean_t != existing["title"] and clean_t not in existing["alt_titles"]:
                existing["alt_titles"].append(clean_t)
        return unified_songs[norm]

    # 1. מיזוג ויקיפדיה
    for ws in wiki_data["songs"]:
        entry = get_or_create_song(ws["title"])
        if not entry:
            continue
        if "wikipedia" not in entry["sources"]:
            entry["sources"].append("wikipedia")
        for r in ws.get("roles", []):
            if r not in entry["roles"]:
                entry["roles"].append(r)
        if ws.get("original_title") and not entry["original_title"]:
            entry["original_title"] = ws["original_title"]
        for p in ws.get("performers", []):
            if p and p not in entry["performers"]:
                entry["performers"].append(p)
        for a in ws.get("albums", []):
            if a and a not in entry["albums"]:
                entry["albums"].append(a)
        if ws.get("lyricist") and ws["lyricist"] not in entry["authors"]:
            entry["authors"].append(ws["lyricist"])
        for d in ws.get("wiki_sources", []):
            if d not in entry["wiki_details"]:
                entry["wiki_details"].append(d)

    # 2. מיזוג שירונט
    for ss in shironet_data["songs"]:
        entry = get_or_create_song(ss["title"])
        if not entry:
            continue
        if "shironet" not in entry["sources"]:
            entry["sources"].append("shironet")
        for r in ss.get("roles", []):
            if r not in entry["roles"]:
                entry["roles"].append(r)
        for wid in ss.get("wrkids", []):
            if wid not in entry["shironet_wrkids"]:
                entry["shironet_wrkids"].append(wid)
        for url in ss.get("urls", []):
            if url not in entry["shironet_urls"]:
                entry["shironet_urls"].append(url)
        for a in ss.get("albums", []):
            if a and a not in entry["albums"]:
                entry["albums"].append(a)

    # 3. מיזוג אקו"ם
    for aw in acum_data["works"]:
        title = aw["title_heb"] or aw["title_eng"]
        entry = get_or_create_song(title)
        if not entry:
            continue
        if "acum" not in entry["sources"]:
            entry["sources"].append("acum")
        if aw["title_heb"] and not any("\u0590" <= c <= "\u05FF" for c in entry["title"]):
            entry["title"] = aw["title_heb"]
        if aw["title_eng"] and not entry["english_title"]:
            entry["english_title"] = aw["title_eng"]
        if aw["original_title"] and not entry["original_title"]:
            entry["original_title"] = aw["original_title"]
        if aw.get("publication_date") and not entry["year"]:
            entry["year"] = aw["publication_date"]
        for r in aw.get("roles", []):
            if r not in entry["roles"]:
                entry["roles"].append(r)
        for a in aw.get("authors", []):
            if a not in entry["authors"]:
                entry["authors"].append(a)
        for c in aw.get("composers", []):
            if c not in entry["composers"]:
                entry["composers"].append(c)
        for tr in aw.get("translators", []):
            if tr not in entry["translators"]:
                entry["translators"].append(tr)
        for ar in aw.get("arrangers", []):
            if ar not in entry["arrangers"]:
                entry["arrangers"].append(ar)
        for p in aw.get("performers", []):
            if p not in entry["performers"]:
                entry["performers"].append(p)
        for alb in aw.get("albums", []):
            if alb not in entry["albums"]:
                entry["albums"].append(alb)
        if aw["work_id"] not in entry["acum_work_ids"]:
            entry["acum_work_ids"].append(aw["work_id"])
        entry["acum_versions_count"] += aw.get("versions_count", 0)
        for yt in aw.get("youtube_ids", []):
            if yt not in entry["youtube_ids"]:
                entry["youtube_ids"].append(yt)

    # 4. מיזוג סטריאו ומונו
    for svs in svm_data["songs"]:
        entry = get_or_create_song(svs["title"])
        if not entry:
            continue
        if "stereo_ve_mono" not in entry["sources"]:
            entry["sources"].append("stereo_ve_mono")
        for r in svs.get("roles", []):
            if r not in entry["roles"]:
                entry["roles"].append(r)
        for a in svs.get("authors", []):
            if a not in entry["authors"]:
                entry["authors"].append(a)
        for c in svs.get("composers", []):
            if c not in entry["composers"]:
                entry["composers"].append(c)
        for tr in svs.get("translators", []):
            if tr not in entry["translators"]:
                entry["translators"].append(tr)
        for ar in svs.get("arrangers", []):
            if ar not in entry["arrangers"]:
                entry["arrangers"].append(ar)
        if svs.get("original_title") and not entry["original_title"]:
            entry["original_title"] = svs["original_title"]
        for p in svs.get("performers", []):
            if p not in entry["performers"]:
                entry["performers"].append(p)
        for alb in svs.get("albums", []):
            if alb not in entry["albums"]:
                entry["albums"].append(alb)
        for yt in svs.get("youtube_ids", []):
            if yt not in entry["youtube_ids"]:
                entry["youtube_ids"].append(yt)

    # 5. מיזוג פזמונט
    for pzs in pizmonet_data["songs"]:
        entry = get_or_create_song(pzs["title"])
        if not entry:
            continue
        if "pizmonet" not in entry["sources"]:
            entry["sources"].append("pizmonet")
        for r in pzs.get("roles", []):
            if r not in entry["roles"]:
                entry["roles"].append(r)
        if pzs.get("year") and not entry["year"]:
            entry["year"] = pzs["year"]
        for p in pzs.get("performers", []):
            if p not in entry["performers"]:
                entry["performers"].append(p)
        for a in pzs.get("authors", []):
            if a not in entry["authors"]:
                entry["authors"].append(a)
        for c in pzs.get("composers", []):
            if c not in entry["composers"]:
                entry["composers"].append(c)
        for ar in pzs.get("arrangers", []):
            if ar not in entry["arrangers"]:
                entry["arrangers"].append(ar)
        for yt in pzs.get("youtube_ids", []):
            if yt not in entry["youtube_ids"]:
                entry["youtube_ids"].append(yt)

    # 6. מיזוג זמרשת
    for zms in zemereshet_data["songs"]:
        entry = get_or_create_song(zms["title"])
        if not entry:
            continue
        if "zemereshet" not in entry["sources"]:
            entry["sources"].append("zemereshet")
        for r in zms.get("roles", []):
            if r not in entry["roles"]:
                entry["roles"].append(r)

    # 7. מיזוג Discogs (מוסיפים מקור לשירים קיימים או שירים מאלבומיה האישיים של נעמי שמר)
    for ds in discogs_data["songs"]:
        norm = normalize_song_title(ds["title"])
        is_naomi_solo = any("נעמי שמר" in p or "Naomi Shemer" in p for p in ds.get("performers", []))
        if norm not in unified_songs and not is_naomi_solo:
            continue
        entry = get_or_create_song(ds["title"])
        if not entry:
            continue
        if "discogs" not in entry["sources"]:
            entry["sources"].append("discogs")
        for alb in ds.get("albums", []):
            if alb not in entry["albums"]:
                entry["albums"].append(alb)
        for p in ds.get("performers", []):
            if p not in entry["performers"]:
                entry["performers"].append(p)

    # 8. מיזוג MusicBrainz
    for mbs in mb_data["songs"]:
        norm = normalize_song_title(mbs["title"])
        if norm not in unified_songs:
            continue
        entry = get_or_create_song(mbs["title"])
        if not entry:
            continue
        if "musicbrainz" not in entry["sources"]:
            entry["sources"].append("musicbrainz")
        for alb in mbs.get("albums", []):
            if alb not in entry["albums"]:
                entry["albums"].append(alb)

    # 9. מיזוג הספרייה הלאומית (NLI - בית לזמר העברי + ארכיון נעמי שמר)
    # בניית אינדקס עזר לפי שמות חלופיים ומזהי אקו"ם כדי לאחד כתיב חסר עם כתיב מלא
    alt_to_norm: Dict[str, str] = {}
    acum_id_to_norm: Dict[str, str] = {}
    for k_norm, s_ent in unified_songs.items():
        alt_to_norm[k_norm] = k_norm
        for at in s_ent.get("alt_titles", []):
            nat = normalize_song_title(at)
            if nat and nat not in alt_to_norm:
                alt_to_norm[nat] = k_norm
        for wid in s_ent.get("acum_work_ids", []):
            if wid:
                acum_id_to_norm[wid] = k_norm

    for nlis in nli_data["songs"]:
        matched_norm = None
        for wid in nlis.get("acum_work_ids", []):
            if wid in acum_id_to_norm:
                matched_norm = acum_id_to_norm[wid]
                break
        if not matched_norm:
            candidates = [nlis["title"]] + nlis.get("alt_titles", [])
            for cand in candidates:
                nc = normalize_song_title(cand)
                if nc and nc in alt_to_norm:
                    matched_norm = alt_to_norm[nc]
                    break
        if matched_norm and matched_norm in unified_songs:
            entry = unified_songs[matched_norm]
            clean_t = NIKUD_RE.sub("", nlis["title"]).strip()
            if clean_t and clean_t != entry["title"] and clean_t not in entry["alt_titles"]:
                entry["alt_titles"].append(clean_t)
        else:
            # העדפת כתיב מלא מתוך השמות החלופיים אם קיים
            preferred_title = nlis["title"]
            for alt in nlis.get("alt_titles", []):
                if len(alt.split()) == len(preferred_title.split()) and len(alt) > len(preferred_title):
                    preferred_title = alt
                    break
            entry = get_or_create_song(preferred_title)
            if entry and preferred_title != nlis["title"]:
                clean_orig = NIKUD_RE.sub("", nlis["title"]).strip()
                if clean_orig and clean_orig != entry["title"] and clean_orig not in entry["alt_titles"]:
                    entry["alt_titles"].append(clean_orig)
        if not entry:
            continue
        if "nli" not in entry["sources"]:
            entry["sources"].append("nli")
        if nlis.get("year") and not entry["year"]:
            entry["year"] = nlis["year"]
        if nlis.get("original_title") and not entry["original_title"]:
            entry["original_title"] = nlis["original_title"]
        if nlis.get("opening_line") and not entry["opening_line"]:
            entry["opening_line"] = nlis["opening_line"]
        for alt in nlis.get("alt_titles", []):
            clean_alt = NIKUD_RE.sub("", alt).strip()
            if clean_alt and clean_alt != entry["title"] and clean_alt not in entry["alt_titles"]:
                entry["alt_titles"].append(clean_alt)
        for r in nlis.get("roles", []):
            if r not in entry["roles"]:
                entry["roles"].append(r)
        for a in nlis.get("authors", []):
            if a and a not in entry["authors"]:
                entry["authors"].append(a)
        for c in nlis.get("composers", []):
            if c and c not in entry["composers"]:
                entry["composers"].append(c)
        for tr in nlis.get("translators", []):
            if tr and tr not in entry["translators"]:
                entry["translators"].append(tr)
        for ar in nlis.get("arrangers", []):
            if ar and ar not in entry["arrangers"]:
                entry["arrangers"].append(ar)
        for p in nlis.get("performers", []):
            if p and p not in entry["performers"]:
                entry["performers"].append(p)
        for alb in nlis.get("albums", []):
            if alb and alb not in entry["albums"]:
                entry["albums"].append(alb)
        for wid in nlis.get("acum_work_ids", []):
            if wid and wid not in entry["acum_work_ids"]:
                entry["acum_work_ids"].append(wid)
        for mid in nlis.get("nli_mms_ids", []):
            if mid and mid not in entry["nli_mms_ids"]:
                entry["nli_mms_ids"].append(mid)
        note_val = nlis.get("notes", "")
        if isinstance(note_val, str) and note_val:
            if note_val not in entry["notes"]:
                entry["notes"].append(note_val)
        elif isinstance(note_val, list):
            for nv in note_val:
                if nv and nv not in entry["notes"]:
                    entry["notes"].append(nv)

    # ניקוי רשימות מבצעים ומזהי יוטיוב שגויים מתוך המאגרים
    BAD_PERFORMERS = {
        "סאבלימינל", "משפחת תאקט", "הדג נחש", "רד אקסס", "קורנז", "הברון עומר ונונו",
        "הלל יוסף", "יוסף הלל", "יעקובוביץ ירוסלב", "ירוסלב יעקובוביץ", "ירוסלב יעקובוביץ'",
        "ילדים", "מקהלת ילדים", "שלושים שנה ושיר", "האחיות לוז",
    }
    BAD_ALBUMS = {"גור אריה"}
    BAD_YT_IDS = {
        "G5ZP7xVcurg", "ZcKAuoZSzWQ",
        "qS_vPd2O1no",  # נעמי לוי - אחרי השקיעה בשדה (איכות שמע ירודה, הוחלף ב-wO3U1xG7Um0)
        "T5o_o8lO-1M",  # הדואר בא - קטע קטוע של 29 שניות
        "Brq81oCuNKc",  # בגינה - קטע קצרצר של 52 שניות
        "-7qKw4AIGP4",  # אשכולית - קטע קצרצר של 61 שניות
        "dkW3-FfpOEY",  # אשכולית - קטע קצרצר של 58 שניות
        "Bac-K0Wjp2A",  # הסוחר מוונציה - קטע קטוע של 37 שניות
        "3KL06zK4_gM",  # שיר ערש לצבעים - קטע מקוצר של 59 שניות
        "FQson2Wm0iw",  # שיר ערש לצבעים - קטע מקוצר של 59 שניות
        "uknSL-k0Mk4",  # קלי קלות - מערכון באורך 7:56 במקום השיר עצמו (1:22)
        "pTt_42SgJ0U",  # קלי קלות - מערכון באורך 7:56
        "rQkXmnBSc70",  # סיירת עולם - מערכון שלם באורך 10:22 במקום השיר עצמו (3:46)
        "lVWcND5JGXw",  # סיירת עולם - מערכון באורך 11:06
    }
    NAOMI_RARE_VOCAL_SONGS = {
        "אחינו הקטן", "הבית הקטן", "הגברת ישראלה", "הסוחר מוונציה", "לא תנצחו אותי", "פגישה לאין קץ",
        "גינגי", "הדוד שמחה", "פו הדב", "אביב", "סביבון סב סב",
        "נר ראשון של חנוכה", "נומי נוגה", "נומי נגה",
        "אשכולית", "הדואר בא", "בגינה", "גדי קטן", "דוגרת",
    }
    EXTRA_ALT_TITLES = {
        "בלדה על מושבה נידחת": ["מושבה נידחת"],
        "תישן חמודי תישן": ["תישן חמודי"],
        "יום הולדת מתיה": ["יום הולדת למתיה גולן", "יום הולדת למתיה"],
        "הו מה נאה הוא הבוקר": ["או מה נאה הוא הבוקר"],
        "דולי": ["berceuse", "שיר ערש מתוך דולי"],
        "אביב": ["מחרוזת אביב"],
        "סביבון סב סב": ["חג חנוכה שמח"],
        "נומי נוגה": ["numi noga"],
        "נומי נגה": ["numi noga"],
        "יריד": ["היריד"],
        "אוניית הכאב": ["אוניית כאב", "אניית כאב"],
        "הכול בגלל מסמר": ["בגלל מסמר"],
        "הכל בגלל מסמר": ["בגלל מסמר"],
        "סמוך על התרנגול": ["שיר התרנגול"],
        "שיר עבודה": ["ארוך התלם"],
        "אחינו הקטן": ["בקיץ אחינו הקטן"],
        "והוא יושיענו": ["והוא יושיעיני", "האזינה אלוהים תפילתי"],
        "גדי מן ההגדה": ["הגדי מן ההגדה"],
    }
    EXTRA_YT_IDS = {
        "אוניית הכאב": ["K1DBCpPxqeM", "gHzMFPiE8MA"],
        "נר ראשון של חנוכה": ["E3V70DpK_EI", "VtH6NkAXl20"],
        "הכול בגלל מסמר": ["0XhvBFzatFc"],
        "הכל בגלל מסמר": ["0XhvBFzatFc"],
        "הלילה הולך בשדרות": ["DATGdPiFqVA"],
        "החגיגה נגמרת": ["fcRd2ZTQiPA"],
        "על ראש שמחתי": ["_FhoSjLL61A"],
        "העיר באפור": ["5kl6qHnbp9Y", "-9U3mvb1KsQ"],
        "בניך מרחוק": ["yavA7DK-_Lg"],
        "והוא יושיענו": ["tPX2FmmeM6k"],
        "בעלייתי שם יפתי": ["7ML3C4GTeus"],
        "ליבבתיני": ["UIWqYA98hzI"],
        "אחרי השקיעה בשדה": ["wO3U1xG7Um0", "ZEJS25vrGoU"],
        "שבחי מעוז": ["sFB_B3wTXLE"],
        "שלומית בונה סוכה": ["zpFGk2nz_-A", "jfS6bS9BFAU"],
        "ספני שלמה המלך": ["byOUPiav5Yo"],
        "שיר לגדעון": ["me0k188YXNw"],
        "בזכותם": ["Nu5qjz8Ws28"],
        "אחותי רוחמה": ["vVQ0Xmtb9_Q"],
        "פרי חדש": ["WxdVdudBKeE"],
        "תלבשי לבן": ["oCezgzbCZBk"],
        "בקיץ": ["_aoBikUYiBY", "4g6cymurqY0"],
        "גדי מן ההגדה": ["G5RVx22SVzs"],
        "טיול לילי": ["WkG7H2prm7Y"],
        "נערת הסיפון": ["NhX0XzGmv9A", "fVN4cci3DiY"],
        "לבנות שפיה": ["mxCqvGI5iu0"],
        "בגינה": ["dZtHel6cUW8"],
        "הדואר בא": ["SgzeIwaaGMU"],
        "אשכולית": ["eX1bnKDHvnc", "SSJdF9cV8iQ"],
        "אחינו הקטן": ["uquTBB0PbFY", "RJd_8iW_4AQ", "v6wgkaN8mvg"],
        "הסוחר מוונציה": ["t_qzuM6V2Co"],
        "דוגרת": ["ipzIvlpBkbU", "6EEIW68j5lY"],
        "שיר ערש לצבעים": ["-1__PIJhhPI", "a1OLtIB8TdU", "vczM9eWy1yw"],
        "קלי קלות": ["YxZ7ZOkU2pA", "m58C3mRgm5E"],
        "סיירת עולם": ["kO9D3crjEsU"],
        "עולם הפוך": ["lfB0Y5mJ1qk"],
    }
    EXTRA_PRIMARY_PERFORMERS = {
        "נערת הסיפון": ["להקת דליה והמלחים", "גשר הירקון"],
        "לבנות שפיה": ["תזמורת שפיה", "רפי גורן"],
        "יובל": ["דורית פרקש", "הכל עובר חביבי", "גידי גוב ונעמי שמר"],
        "לחם האוהבים": ["דולי מודעי", "נעמי שמר"],
        "אחינו הקטן": ["יפה ירקוני", "נעמי שמר"],
        "שבת": ["יפה ירקוני"],
        "בגינה": ["ריקה זראי", "נעמי שמר"],
        "אשכולית": ["יפה ירקוני", "נעמי שמר"],
        "הדואר בא": ["יפה ירקוני", "נעמי שמר"],
        "גדי קטן": ["דודו זכאי", "נעמי שמר"],
        "דוגרת": ["נתנאלה", "נעמי שמר"],
        "הלילה הולך בשדרות": ["שמעון ישראלי", "אילנית"],
        "צי הצללים": ["חבורת בית רוטשילד", "אפי נצר וחבורתו"],
        "שיר השייטת": ["חבורת בית רוטשילד", "אפי נצר וחבורתו"],
        "אסיף": ["מיכל טל", "יהודית רביץ", "שלישיית המעפיל"],
        "כיתה בארץ": ["צוות הווי נחל"],
        "העיר באפור": ["שלישיית גשר הירקון", "נעמי שמר"],
        "בשדה תלתן": ["להקת פיקוד צפון"],
        "שיר לגדעון": ["נחמה הנדל"],
        "אחרי השקיעה בשדה": ["נעמי לוי", "מקהלת צדיקוב", "נעמי שמר"],
        "שבחי מעוז": ["להקת פיקוד דרום", "נעמי שמר"],
        "שלומית בונה סוכה": ["אילנה רובינא והדודאים", "אילנה רובינא", "נעמי שמר"],
        "ספני שלמה המלך": ["אילנה רובינא"],
        "קומי צאי": ["יהורם גאון", "נעמי שמר"],
        "בזכותם": ["רוחמה רז וצוות הווי פיקוד מרכז", "רוחמה רז"],
        "אחותי רוחמה": ["הגשש החיוור", "אורה זיטנר"],
        "תלבשי לבן": ["הדודאים והפרברים"],
        "בקיץ": ["שולי נתן", "להקת פיקוד המרכז"],
        "מנגנות ויואלדי": ["נעמי שמר", "רבקה מיכאלי ונעמי שמר"],
        "לא ביאליק": ["נעמי שמר", "רבקה מיכאלי ונעמי שמר"],
        "האורח": ["הכל עובר חביבי"],
        "מצעד האביב": ["אריק איינשטיין"],
        "אהבתיך גם כך": ["ג'ינה ג'וי"],
        "שייקספיר איננו": ["רביעיית שייקספיר איננו"],
        "שיר סתיו": ["יפה ירקוני", "נעמי שמר"],
        "הינשוף והירח": ["ריקה זראי"],
        "הלילה הזה הוא דומם": ["רות מימון"],
        "בלדה מודרנית": ["רחל אטאס"],
        "בלדה על מושבה נידחת": ["אילי גורליצקי"],
        "בתיה הסיירת": ["להקת פיקוד מרכז"],
        "היי שלי": ["שייקה לוי", "להקת פיקוד המרכז"],
        "זאת הארץ": ["אולי שוקן"],
        "קרנבל": ["להקת פיקוד מרכז", "רחל אטאס"],
        "השד יודע": ["אריק איינשטיין", "תיאטרון סמבטיון"],
        "פרולוג": ["משתתפי התכנית שייקספיר איננו"],
        "ילדי כל העולם": ["ילדי בית הספר לאמנויות"],
        "פסח כאן": ["ילדי בית הספר לאומנויות", "עודד גדיר"],
        "איש מוזר": ["הדס דגול שמרלינג"],
    }
    for s_ent in unified_songs.values():
        s_norm = s_ent["normalized_key"]
        for extra_alt in EXTRA_ALT_TITLES.get(s_norm, []):
            if extra_alt not in s_ent["alt_titles"]:
                s_ent["alt_titles"].append(extra_alt)
        for extra_yid in EXTRA_YT_IDS.get(s_norm, []):
            if extra_yid not in s_ent["youtube_ids"]:
                s_ent["youtube_ids"].append(extra_yid)
        is_perf_only = set(s_ent["roles"]) == {"performer"}
        has_acum_naomi = (
            any("שמר נעמי" in p for p in s_ent["performers"])
            or (s_norm in NAOMI_RARE_VOCAL_SONGS)
            or is_perf_only
        )
        cleaned_perfs = []
        late_cover_perfs = []
        for p in s_ent["performers"]:
            if normalize_song_title(p) == s_norm or p in BAD_PERFORMERS:
                continue
            if ("נעמי שמר" in p or "Naomi Shemer" in p) and "שמר נעמי" not in p and not has_acum_naomi:
                continue
            if any(x in p for x in ("מארג'ה", "שירולי", "אנסמבל קולי חדש", "חבורת זמר", "חבורת הזמר", "כוכב נולד", "זמיר ורדה", "ורדה זמיר")):
                late_cover_perfs.append(p)
            else:
                cleaned_perfs.append(p)
        cleaned_perfs.extend(late_cover_perfs)
        if (is_perf_only or s_norm in NAOMI_RARE_VOCAL_SONGS) and not any("שמר" in p or "Shemer" in p for p in cleaned_perfs):
            cleaned_perfs.insert(0, "נעמי שמר")
        for extra_p in reversed(EXTRA_PRIMARY_PERFORMERS.get(s_norm, [])):
            if extra_p in cleaned_perfs:
                cleaned_perfs.remove(extra_p)
            cleaned_perfs.insert(0, extra_p)
        if s_norm == "אסיף":
            cleaned_perfs = [p for p in cleaned_perfs if "בצל ירוק" not in p]
        s_ent["performers"] = cleaned_perfs
        s_ent["albums"] = [a for a in s_ent["albums"] if a not in BAD_ALBUMS]
        s_ent["youtube_ids"] = [y for y in s_ent["youtube_ids"] if y not in BAD_YT_IDS]

        # ניקוי קרדיטים זרים שדלפו משירים בעלי שם זהה או מרמיקסים מאוחרים
        BAD_CREATORS = {
            "פונץ'", "פונץ’", "קובי שמעוני", "זאב נחמה", "ענבל פרלמוטר",
            "יעקב גלעד ויהודה פוליקר", "יהודה פוליקר", "הילה רז", "קובי רכט",
            "חנה לוי", "יגאל בשן", "רועי רז", "יוסף הלל", "יהונתן גפן",
            "אלכס קלצ'קין", "אלכס קלצ’קין", "שרה שוהם", "דני גרנות",
            "שמואל בס", "שייקה פייקוב", "הילה כפיר", "יניב שמלצר",
            "יהודה לויכטר", "גל לוגסי", "שי חדד", "אילן שושנה", "אלון רוסרט",
            "משה עובד", "סמדר שיר", "לימור שפירא", "אילון קרני",
            "דידי מנוסי", "נועם הלוי", "Friedrich Hollaender, Frank Loesser",
            "אהוד מנור", "גולן יוסף אזולאי", "דוד צח פרישמן", "אמיתי פריינטא",
            "JULIEN TAWIL", "עודד תאומי", "צלינה לפובסקי",
            "דני סנדרסון",
        }
        s_ent["authors"] = [a for a in s_ent["authors"] if a not in BAD_CREATORS]
        s_ent["composers"] = [c for c in s_ent["composers"] if c not in BAD_CREATORS]

        CREATOR_OVERRIDES = {
            "הבית הקטן": (["author", "composer", "performer"], ["נעמי שמר"], ["נעמי שמר"], []),
            "אביב": (["performer"], ["מתתיהו שלם", "עמנואל זמיר"], ["מתתיהו שלם", "עמנואל זמיר"], []),
            "סביבון סב סב": (["performer"], ["לוין קיפניס", "אברהם אברונין", "אהרון אשמן", "שרה לוי-תנאי"], ["עממי", "יואל ולבה", "עמנואל עמירן"], []),
            "ג’ינג’י": (["composer", "performer"], ["מרים ילן-שטקליס"], ["נעמי שמר"], []),
            "גינגי": (["composer", "performer"], ["מרים ילן-שטקליס"], ["נעמי שמר"], []),
            "הדוד שמחה": (["composer", "performer"], ["ע. הלל"], ["נעמי שמר"], []),
            "פו הדב": (["composer", "performer"], ["א. א. מילן (תרגום: ורה ישראלית ואהרן אמיר)"], ["נעמי שמר"], []),
            "קלי קלות": (["author", "composer", "performer"], ["נעמי שמר"], ["נעמי שמר"], []),
            "צירצורים": (["author", "composer", "performer"], ["נעמי שמר"], ["נעמי שמר"], []),
            "כנרת": (["composer", "performer"], ["רחל המשוררת"], ["נעמי שמר"], []),
            "זמר": (["composer", "performer"], ["רחל המשוררת"], ["נעמי שמר"], []),
            "מה עושים העצים": (["composer", "performer"], ["ע. הלל"], ["נעמי שמר"], []),
            "אסיף": (["composer"], ["איתמר פרת"], ["נעמי שמר"], []),
            "מיכאל": (["composer"], ["מרים ילן-שטקליס"], ["נעמי שמר"], []),
            "על אם הדרך": (["composer"], ["נתן אלתרמן"], ["נעמי שמר"], []),
            "גדי מן ההגדה": (["composer", "performer"], ["נתן אלתרמן"], ["נעמי שמר"], []),
            "הכל שטיח": (["composer", "performer"], ["נתן אלתרמן"], ["נעמי שמר"], []),
            "שייקספיר איננו": (["composer"], ["חיים חפר"], ["נעמי שמר"], []),
            "יומן החדשות": (["composer"], ["עמוס קינן"], ["נעמי שמר"], []),
            "ירושלים של ברזל": (["composer"], ["מאיר אריאל"], ["נעמי שמר"], []),
            "טו בשבט שלי": (["composer", "performer"], ["לוין קיפניס"], ["נעמי שמר"], []),
            "פרלוד": (["author", "composer", "performer"], ["נעמי שמר"], ["נעמי שמר"], []),
            "ילדי כל העולם": (["composer"], ["אהרן זאב"], ["נעמי שמר"], []),
            "בניך מרחוק": (["composer"], ["מן המקורות (ישעיהו ס')"], ["נעמי שמר"], []),
            "סמוך על התרנגול": (["author"], ["נעמי שמר"], ["יוחנן זראי"], []),
            "שיירת הרוכבים": (["author"], ["נעמי שמר"], ["שמעון ישראלי"], []),
            "פרי חדש": (["author", "performer"], ["נעמי שמר"], ["עדי רנרט"], []),
            "דולי": (["author"], ["נעמי שמר"], ["גבריאל פורה (מתוך סוויטת דולי)"], []),
            "על הדרך עץ עומד": (["translator", "performer"], ["איציק מאנגר"], ["פיליפ לסקובסקי"], ["נעמי שמר"]),
            "כמו נערה": (["author"], ["נעמי שמר"], ["במבובסקי"], []),
            "לא פעם בקיץ": (["composer"], ["רחל המשוררת"], ["נעמי שמר"], []),
        }
        if s_norm in CREATOR_OVERRIDES:
            ov_roles, ov_auth, ov_comp, ov_tr = CREATOR_OVERRIDES[s_norm]
            s_ent["roles"] = ov_roles
            s_ent["authors"] = ov_auth
            s_ent["composers"] = ov_comp
            if ov_tr:
                s_ent["translators"] = ov_tr

    sorted_songs = sorted(
        unified_songs.values(),
        key=lambda x: (0 if any("\u0590" <= c <= "\u05FF" for c in x["title"]) else 1, x["title"]),
    )

    # בניית רשימת אלבומים, אוספים וספרים מאוחדת מכל המקורות
    unified_collections: List[Dict[str, Any]] = []
    for a in wiki_data["albums"]:
        unified_collections.append({
            "title": a["raw"],
            "year": a["year"],
            "type": "אלבום (ויקיפדיה)",
            "tracks_count": "",
            "performer": "",
            "source": "wikipedia",
            "id_or_url": "",
        })
    for c in wiki_data["compilations"]:
        unified_collections.append({
            "title": c["raw"],
            "year": c["year"],
            "type": "אוסף (ויקיפדיה)",
            "tracks_count": "",
            "performer": "",
            "source": "wikipedia",
            "id_or_url": "",
        })
    for b in wiki_data["books"]:
        unified_collections.append({
            "title": b["raw"],
            "year": b["year"],
            "type": "ספר שירים (ויקיפדיה)",
            "tracks_count": "",
            "performer": "נעמי שמר",
            "source": "wikipedia",
            "id_or_url": "",
        })
    for sa in shironet_data["albums"]:
        unified_collections.append({
            "title": sa["title"],
            "year": "",
            "type": "אלבום (שירונט)",
            "tracks_count": str(len(sa["tracks"])),
            "performer": "נעמי שמר",
            "source": "shironet",
            "id_or_url": sa["url"],
        })
    for aa in acum_data["albums"]:
        perf_name = ""
        if aa.get("performer"):
            perf_name = aa["performer"].get("performerHebName") or aa["performer"].get("performerEngName") or ""
        unified_collections.append({
            "title": aa.get("title", ""),
            "year": aa.get("release_date", ""),
            "type": "אלבום/אוסף (אקו\"ם)",
            "tracks_count": str(aa.get("tracks_count", "")),
            "performer": perf_name,
            "source": "acum",
            "id_or_url": f"albumId={aa.get('number', '')}",
        })
    for sva in svm_data["albums"]:
        unified_collections.append({
            "title": sva["title"],
            "year": sva["year"],
            "type": "אלבום/תקליט (סטריאו ומונו)",
            "tracks_count": str(sva["tracks_count"]),
            "performer": sva["performer"],
            "source": "stereo_ve_mono",
            "id_or_url": sva["url"],
        })
    for drel in discogs_data["releases"]:
        unified_collections.append({
            "title": drel["title"],
            "year": drel["year"],
            "type": f"תקליט/אלבום ({drel['type']} - Discogs)",
            "tracks_count": str(drel["tracks_count"]),
            "performer": drel["artist"],
            "source": "discogs",
            "id_or_url": drel["url"],
        })
    for mrel in mb_data["releases"]:
        unified_collections.append({
            "title": mrel["title"],
            "year": mrel["year"],
            "type": "אלבום (MusicBrainz)",
            "tracks_count": str(mrel["tracks_count"]),
            "performer": "נעמי שמר",
            "source": "musicbrainz",
            "id_or_url": mrel["url"],
        })
    for nalb in nli_data["albums"]:
        unified_collections.append({
            "title": nalb["title"],
            "year": nalb["year"],
            "type": nalb["type"],
            "tracks_count": "",
            "performer": nalb["performer"],
            "source": "nli",
            "id_or_url": nalb["url"],
        })

    return {
        "songs": sorted_songs,
        "collections": unified_collections,
        "tribute_songs": wiki_data.get("tribute_songs", []),
        "stats": {
            "total_unique_songs": len(sorted_songs),
            "songs_with_performers": sum(1 for s in sorted_songs if s["performers"]),
            "songs_with_albums": sum(1 for s in sorted_songs if s["albums"]),
            "songs_with_youtube_ids": sum(1 for s in sorted_songs if s["youtube_ids"]),
            "songs_with_opening_line": sum(1 for s in sorted_songs if s["opening_line"]),
            "songs_in_acum": sum(1 for s in sorted_songs if "acum" in s["sources"]),
            "songs_in_nli": sum(1 for s in sorted_songs if "nli" in s["sources"]),
            "songs_in_shironet": sum(1 for s in sorted_songs if "shironet" in s["sources"]),
            "songs_in_stereo_ve_mono": sum(1 for s in sorted_songs if "stereo_ve_mono" in s["sources"]),
            "songs_in_wikipedia": sum(1 for s in sorted_songs if "wikipedia" in s["sources"]),
            "songs_in_discogs": sum(1 for s in sorted_songs if "discogs" in s["sources"]),
            "songs_in_musicbrainz": sum(1 for s in sorted_songs if "musicbrainz" in s["sources"]),
            "songs_in_pizmonet": sum(1 for s in sorted_songs if "pizmonet" in s["sources"]),
            "songs_in_zemereshet": sum(1 for s in sorted_songs if "zemereshet" in s["sources"]),
            "songs_in_at_least_two_sources": sum(1 for s in sorted_songs if len(s["sources"]) >= 2),
            "songs_in_at_least_three_sources": sum(1 for s in sorted_songs if len(s["sources"]) >= 3),
            "total_collections": len(unified_collections),
            "wiki_albums": len(wiki_data["albums"]),
            "wiki_compilations": len(wiki_data["compilations"]),
            "wiki_books": len(wiki_data["books"]),
            "shironet_albums": len(shironet_data["albums"]),
            "acum_albums": len(acum_data["albums"]),
            "stereo_ve_mono_albums": len(svm_data["albums"]),
            "discogs_releases": len(discogs_data["releases"]),
            "musicbrainz_releases": len(mb_data["releases"]),
            "nli_albums": len(nli_data["albums"]),
        },
    }


def save_outputs(catalog: Dict[str, Any]) -> None:
    json_path = os.path.join(OUTPUT_DIR, "naomi_shemer_catalog.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    songs_csv_path = os.path.join(OUTPUT_DIR, "naomi_shemer_songs.csv")
    with open(songs_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "שם השיר",
            "שמות חלופיים",
            "שם באנגלית (אקו\"ם)",
            "שם היצירה המקורית (בתרגומים)",
            "שנת פרסום/הקלטה",
            "תפקידי נעמי שמר",
            "מקורות",
            "מספר מקורות",
            "מחברים/פזמונאים",
            "מלחינים",
            "מתרגמים",
            "מעבדים",
            "מספר ביצועים באקו\"ם",
            "מבצעים בולטים",
            "אלבומים/ספרים משויכים",
            "מזהי אקו\"ם (Work IDs)",
            "מזהי הספרייה הלאומית (NLI MMS IDs)",
            "שורת פתיחה (אתחלתא - הספרייה הלאומית)",
            "קישורי שירונט",
            "מזהי יוטיוב (אקו\"ם / סטריאו ומונו / פזמונט)",
        ])
        for s in catalog["songs"]:
            roles_heb = [ROLE_HEB_LABELS.get(r, r) for r in s["roles"]]
            writer.writerow([
                s["title"],
                " | ".join(s["alt_titles"]),
                s["english_title"],
                s["original_title"],
                s["year"],
                ", ".join(roles_heb),
                ", ".join(s["sources"]),
                len(s["sources"]),
                " | ".join(s["authors"]),
                " | ".join(s["composers"]),
                " | ".join(s["translators"]),
                " | ".join(s["arrangers"][:10]),
                s["acum_versions_count"],
                " | ".join(s["performers"][:20]),
                " | ".join(s["albums"][:15]),
                " | ".join(s["acum_work_ids"]),
                " | ".join(s["nli_mms_ids"]),
                s["opening_line"],
                " | ".join(s["shironet_urls"]),
                " | ".join(s["youtube_ids"]),
            ])

    albums_csv_path = os.path.join(OUTPUT_DIR, "naomi_shemer_albums.csv")
    with open(albums_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "שם האלבום / האוסף / הספר",
            "שנה",
            "סוג",
            "מבצע",
            "מספר רצועות",
            "מקור",
            "מזהה / קישור",
        ])
        for c in catalog["collections"]:
            writer.writerow([
                c["title"],
                c["year"],
                c["type"],
                c["performer"],
                c["tracks_count"],
                c["source"],
                c["id_or_url"],
            ])

    stats = catalog["stats"]
    md_path = os.path.join(OUTPUT_DIR, "naomi_shemer_summary.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# קטלוג מקיף של אלבומי ושירי נעמי שמר (9 מקורות)\n\n")
        f.write("## סיכום נתונים\n\n")
        f.write(f"- **סה\"כ שירים ויצירות ייחודיות (לאחר איחוד וניקוי כפילויות):** {stats['total_unique_songs']}\n")
        f.write(f"  - שירים עם רשימת מבצעים: {stats['songs_with_performers']}\n")
        f.write(f"  - שירים המשויכים לאלבום/ספר: {stats['songs_with_albums']}\n")
        f.write(f"  - שירים עם שורת פתיחה (אתחלתא מהספרייה הלאומית): {stats['songs_with_opening_line']}\n")
        f.write(f"  - שירים עם מזהה יוטיוב ישיר (מתוך המאגרים): {stats['songs_with_youtube_ids']}\n")
        f.write(f"- **פילוח שירים לפי מקור:**\n")
        f.write(f"  - אקו\"ם (ACUM): {stats['songs_in_acum']} יצירות\n")
        f.write(f"  - הספרייה הלאומית (NLI - בית לזמר העברי + ארכיון נעמי שמר): {stats['songs_in_nli']} שירים\n")
        f.write(f"  - שירונט (Shironet): {stats['songs_in_shironet']} שירים\n")
        f.write(f"  - סטריאו ומונו (Stereo ve Mono): {stats['songs_in_stereo_ve_mono']} שירים\n")
        f.write(f"  - ויקיפדיה העברית: {stats['songs_in_wikipedia']} שירים\n")
        f.write(f"  - Discogs: {stats['songs_in_discogs']} שירים\n")
        f.write(f"  - MusicBrainz: {stats['songs_in_musicbrainz']} שירים\n")
        f.write(f"  - פזמונט (Pizmonet): {stats['songs_in_pizmonet']} שירים\n")
        f.write(f"  - זמרשת (Zemereshet): {stats['songs_in_zemereshet']} שירים\n")
        f.write(f"  - מופיעים בלפחות 2 מקורות: {stats['songs_in_at_least_two_sources']} שירים\n")
        f.write(f"  - מופיעים בלפחות 3 מקורות: {stats['songs_in_at_least_three_sources']} שירים\n")
        f.write(f"- **סה\"כ רשומות אלבומים, אוספים וספרים:** {stats['total_collections']}\n")
        f.write(f"  - אלבומים מלאים משיריה (ויקיפדיה): {stats['wiki_albums']}\n")
        f.write(f"  - אוספים (ויקיפדיה): {stats['wiki_compilations']}\n")
        f.write(f"  - ספרי שירים (ויקיפדיה): {stats['wiki_books']}\n")
        f.write(f"  - אלבומים בארכיון הצליל הלאומי (הספרייה הלאומית): {stats['nli_albums']}\n")
        f.write(f"  - אלבומים ואוספים במאגר אקו\"ם (עם רשימות שירים): {stats['acum_albums']}\n")
        f.write(f"  - אלבומים ותקליטים באתר סטריאו ומונו: {stats['stereo_ve_mono_albums']}\n")
        f.write(f"  - מהדורות ואלבומים ב-Discogs: {stats['discogs_releases']}\n")
        f.write(f"  - אלבומים ב-MusicBrainz: {stats['musicbrainz_releases']}\n")
        f.write(f"  - אלבומים בשירונט: {stats['shironet_albums']}\n\n")

        f.write("## רשימת השירים המאוחדת\n\n")
        f.write("| # | שם השיר | תפקידים | מקורות | מס' ביצועים באקו\"ם | מבצעים בולטים | מזהי יוטיוב |\n")
        f.write("|---|---------|---------|--------|--------------------:|---------------|-------------|\n")
        for idx, s in enumerate(catalog["songs"], 1):
            roles_heb = ", ".join(ROLE_HEB_LABELS.get(r, r) for r in s["roles"])
            srcs = ", ".join(s["sources"])
            perfs = ", ".join(s["performers"][:4])
            yts = ", ".join(s["youtube_ids"][:2])
            title_clean = s["title"].replace("|", "\\|")
            perfs_clean = perfs.replace("|", "\\|")
            f.write(
                f"| {idx} | {title_clean} | {roles_heb} | {srcs} | "
                f"{s['acum_versions_count']} | {perfs_clean} | {yts} |\n"
            )

    print("\nנשמרו הקבצים הבאים:")
    print(f"  1. {json_path}")
    print(f"  2. {songs_csv_path}")
    print(f"  3. {albums_csv_path}")
    print(f"  4. {md_path}")


def main() -> None:
    wiki_data = scrape_wikipedia()
    shironet_data = scrape_shironet()
    acum_data = scrape_acum()
    svm_data = scrape_stereo_ve_mono()
    pizmonet_data = scrape_pizmonet()
    zemereshet_data = scrape_zemereshet()
    discogs_data = scrape_discogs()
    mb_data = scrape_musicbrainz()
    nli_data = scrape_nli()

    catalog = build_unified_catalog(
        wiki_data=wiki_data,
        shironet_data=shironet_data,
        acum_data=acum_data,
        svm_data=svm_data,
        pizmonet_data=pizmonet_data,
        zemereshet_data=zemereshet_data,
        discogs_data=discogs_data,
        mb_data=mb_data,
        nli_data=nli_data,
    )
    save_outputs(catalog)
    print("\nסיכום סטטיסטי:")
    for k, v in catalog["stats"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
