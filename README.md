# eBay E2E Automation – Playwright + Python

## ארכיטקטורה

```
ebay_automation/
├── pages/                    # Page Object Model
│   ├── base_page.py          # Base class – ניווט, צילומי מסך, לוגים
│   ├── login_page.py         # הזדהות
│   ├── search_page.py        # חיפוש + סינון מחיר
│   ├── item_page.py          # דף מוצר + Add to Cart
│   └── cart_page.py          # אימות סל קניות
├── tests/
│   ├── conftest.py           # Pytest hooks + Allure screenshots
│   └── test_ebay_e2e.py      # תרחיש E2E מלא (Data-Driven)
├── data/
│   └── test_data.json        # קלטי בדיקה (תומך גם ב-CSV/YAML)
├── utils/
│   ├── data_loader.py        # טעינת נתונים מקובץ חיצוני
│   └── logger.py             # הגדרת לוגינג
├── screenshots/              # צילומי מסך (נוצר אוטומטית)
├── reports/
│   └── allure-results/       # תוצאות Allure
├── pytest.ini
└── requirements.txt
```

## עקרונות עיצוב

| עיקרון | יישום |
|--------|-------|
| **Page Object Model** | כל עמוד – מחלקה נפרדת עם Locators ו-Actions בלבד |
| **OOP** | ירושה מ-`BasePage`, Encapsulation, Single Responsibility |
| **Data-Driven** | `DataLoader` טוען JSON/CSV/YAML; `pytest_generate_tests` מפרמטר את הבדיקות |
| **Separation of Concerns** | Test logic ≠ Page logic ≠ Data loading |

## פונקציות מרכזיות

### 1. `LoginPage.login(username, password)`
- ניווט לדף הכניסה
- מילוי email ← לחיצה Continue ← מילוי password ← Sign In
- אימות הצלחה + צילום מסך

### 2. `SearchPage.search_items_by_name_under_price(query, max_price, limit=5)`
```python
urls = search_page.search_items_by_name_under_price("shoes", 220, 5)
# → רשימת עד 5 URLs לפריטים במחיר ≤ $220
```
- חיפוש לפי מילת מפתח
- החלת פילטר מחיר מקסימלי
- איסוף קישורים בעזרת XPath
- מעבר עמודים (Paging) אוטומטי אם נדרש

### 3. `ItemPage.add_items_to_cart(urls)`
```python
item_page.add_items_to_cart(urls)
```
- פתיחת כל URL בלולאה
- בחירת וריאנטים (מידה/צבע) אקראית מהאפשרויות הזמינות
- לחיצה על "Add to cart"
- סגירת overlay חזרה לחיפוש
- צילום מסך לכל פריט

### 4. `CartPage.assert_cart_total_not_exceeds(budget_per_item, items_count)`
```python
cart_page.assert_cart_total_not_exceeds(220, len(urls))
# → מאמת שסכום הסל ≤ 220 × מספר_הפריטים
```
- פתיחת עמוד הסל
- קריאת הסכום הכולל
- חישוב סף: budget_per_item × items_count
- AssertionError אם חורג

## התקנה והרצה

```bash
# 1. התקנת תלויות
pip install -r requirements.txt
playwright install chromium

# 2. עדכון פרטי כניסה ב-data/test_data.json
#    (credentials → username / password)

# 3. הרצת כל הבדיקות
pytest tests/ -v

# 4. יצירת דוח Allure
allure serve reports/allure-results
```

## קובץ נתונים (data/test_data.json)

ניתן להוסיף תרחישים נוספים ב-`test_scenarios`:
```json
{
  "scenario_id": "TC004",
  "description": "Custom scenario",
  "search_query": "watch",
  "max_price": 150,
  "limit": 5,
  "budget_per_item": 150
}
```
הבדיקה מתווספת אוטומטית ללא שינוי קוד.

## דוחות

- **Allure**: `allure serve reports/allure-results`
- **Logs**: `reports/logs/test_run_TIMESTAMP.log`
- **Screenshots**: `screenshots/` – לכל שלב קריטי

## זרימת התרחיש המלא

```
Login
  ↓
searchItemsByNameUnderPrice("shoes", 220, 5)
  ↓ returns [url1, url2, ..., url5]
addItemsToCart([url1...url5])
  ↓ opens each item, selects variants, clicks Add to Cart
assertCartTotalNotExceeds(220, 5)
  ↓ reads cart total, asserts ≤ $1100
```
