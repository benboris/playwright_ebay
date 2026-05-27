from playwright.sync_api import sync playwright
from selenium import webdriver
import time

def test_search_functionality():
       browser = sync_playwright().start().chromium.launch()
       page = browser.new_page()
       page.goto("https://example.com")

      time.sleep(2)
      search_box = page.locator("#search")
      search_box.fill = ("playwright testing")
     page.loctor(".button").click()
     time.sleep(3)
     results = page.lctor(".result-item")
     browser.close()

1. - שגיאת תחביר בייבוא: רווח בתוך שם מודול

Python אינו מאפשר רווח בתוך שם מזהה (identifier). `sync playwright` הן שתי מילים נפרדות,
ולכן המפרש יזרוק `SyntaxError` עוד לפני שתשורת אחת מהפונקציה תרוץ.
בנוסף, שם המחלקה הנכון ב-Playwright הוא `sync_playwright` עם קו תחתון.

solution:
from playwright.sync_api import sync_playwright

2.- השמה שגויה לתוכנה במקום לקרוא למתודה "fill"

search_box.fill = ("playwright testing")

`fill` היא **מתודה** (פונקציה) של אובייקט Locator, לא תכונה (property).
השימוש ב-`=` גורם לכך שבמקום לקרוא לפונקציה ולהקליד טקסט בשדה,
Python פשוט **מחליף** את האובייקט `fill` בתוך ה-namespace של המשתנה בערך המחרוזת.
כלומר – שום דבר לא נכתב בדפדפן, ולא נזרקת שגיאה, מה שהופך את הבאג לקשה לאיתור.

sulotion:

search_box.fill("playwright testing")

3.שגיאת כתיב במתודת playwright

page.loctor(".button").click()   # שורה 13 – loctor במקום locator
results = page.lctor(".result-item")  # שורה 15 – lctor במקום locator

שתי הקריאות מכילות שגיאות כתיב במתודה `locator`:
- שורה 13: `loctor` (חסרה האות `a`)
- שורה 15: `lctor` (חסרות האותיות `oca`)
Python יזרוק `AttributeError: 'Page' object has no attribute 'loctor'` בזמן ריצה.
הבעיה לא תתגלה בזמן ייבוא הקובץ, רק כאשר השורות הספציפיות האלה יתבצעו.



sulotion:

page.locator(".button").click()          # שורה 13
results = page.locator(".result-item")   # שורה 15

4. ייבוא מיותר של selenium

```python
from selenium import webdriver
```
1. אם `selenium` לא מותקן בסביבה – הקוד ייפול בזמן ייבוא עם `ModuleNotFoundError`
2. מסרבל את הקוד וגורם לבלבול לקורא
3. מעלה חשד שמישהו ניסה לשלב שתי ספריות שאינן תואמות זו לזו

sulotion:

הסרה לגמרי של השורה

5. שימוש ב time.sleep במקום playwright waits

time.sleep(2)
time.sleep(3)

`time.sleep` הוא **המתנה קשיחה (hard wait)** – הקוד עוצר לחלוטין לפרק זמן קבוע,
ללא קשר למצב הדף. זה מוביל לשני כשלים:

- **איטיות מיותרת:** אם הדף נטען תוך 0.5 שניות – הבדיקה עדיין ממתינה 2–3 שניות.
- **אי-יציבות (Flakiness):** אם הדף איטי מהצפוי – הבדיקה תיכשל למרות שהאלמנט עוד יגיע.
Playwright מספקת `wait_for_selector` / `expect` / `wait_for_load_state` שמחכים בדיוק
עד שהאלמנט זמין, ולא יותר.

sulotion:

# במקום time.sleep(2) לפני search_box:
page.wait_for_selector("#search")

# במקום time.sleep(3) לפני results:
page.wait_for_selector(".result-item")


לסיכום הקוד הנכון צריך להיות:

from playwright.sync_api import sync_playwright   # תוקן: קו תחתון
 
# הוסר: from selenium import webdriver (לא נחוץ)
# הוסר: import time (לא נחוץ לאחר הסרת sleep)
 
def test_search_functionality():
    with sync_playwright() as pw:                          # תוקן: context manager
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
 
        page.wait_for_selector("#search")                  # תוקן: wait אמיתי
        search_box = page.locator("#search")
        search_box.fill("playwright testing")              # תוקן: קריאה למתודה
 
        page.locator(".button").click()                    # תוקן: locator (כתיב נכון)
 
        page.wait_for_selector(".result-item")             # תוקן: wait אמיתי
        results = page.locator(".result-item")             # תוקן: locator (כתיב נכון)
 
        browser.close()
