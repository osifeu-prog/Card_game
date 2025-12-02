# 🤖 Telegram Webhook Bot עם FastAPI ו-python-telegram-bot (v20+)

פרויקט זה מספק תבנית מלאה לבוט טלגרם הפועל באמצעות **Webhook** על גבי שרת **FastAPI** ופריסתו ב-**Railway** (או כל שירות תואם Docker).

**דגשים:**
* **עיבוד רקע:** השרת מחזיר HTTP 200 במהירות לטלגרם, ועיבוד העדכון מתבצע במשימת רקע (asyncio.create_task).
* **לוגים מפורטים:** רישום מלא של כל שלב, כולל Startup, Set Webhook, ובקשות נכנסות (HTTP & Update).
* **Healthchecks:** נתיבים `/` ו־`/health` לבדיקת תקינות.

---

## 🚀 פריסה ב-Railway (או Docker)

### 1. הכנת משתני סביבה

ודא שמשתני הסביבה הבאים מוגדרים במערכת הפריסה שלך (Railway: Settings -> Variables):

| משתנה | תיאור | דוגמה |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | הטוקן שקיבלת מ-BotFather. | `123456:ABC-DEF123456` |
| `BASE_URL` | הכתובת הציבורית של היישום שלך (חייבת להיות HTTPS). | `https://your-domain.up.railway.app` |
| `PORT` | הפורט שעליו השרת מאזין (ברירת מחדל: 8080). ב-Railway מוגדר אוטומטית. | `8080` |
| `BOT_USERNAME` | שם הבוט, לרישום נוח בלוגים. | `@MyAwesomeBot` |

### 2. קובץ `railway.toml`

הקובץ `railway.toml` מגדיר את הפריסה, כולל פקודת ההפעלה (Uvicorn) וה-Healthcheck:

```toml
[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port ${PORT}"
healthcheckPath = "/"
# ...
