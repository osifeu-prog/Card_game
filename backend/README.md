# Card Game Telegram Bot

בוט טלגרם למשחק קלפים עם FastAPI webhook.

## 🚀 תכונות

- ✅ תמיכה ב-Webhooks של Telegram
- ✅ לוגינג מתקדם בפורמט JSON
- ✅ ארכיטקטורה אסינכרונית
- ✅ הרצה על Railway/Docker
- ✅ ניהול בריאות (Health checks)

## 📋 דרישות מקדימות

- Python 3.11+
- חשבון Telegram Bot (דרך [@BotFather](https://t.me/botfather))
- חשבון Railway (או כל פלטפורמת deployment אחרת)

## 🛠️ התקנה מקומית

1. **שכפל את הריפו**
```bash
git clone <repository-url>
cd Card_game/backend
```

2. **צור סביבה וירטואלית**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# או
venv\Scripts\activate  # Windows
```

3. **התקן תלויות**
```bash
pip install -r requirements.txt
```

4. **הגדר משתני סביבה**
```bash
cp .env.sample .env
# ערוך את .env והוסף את הפרטים שלך
```

5. **הרץ את האפליקציה**
```bash
python main.py
```

## 🌐 Deploy ל-Railway

### שלב 1: הכנת הבוט

1. צור בוט חדש דרך [@BotFather](https://t.me/botfather)
2. שמור את ה-Token שקיבלת

### שלב 2: Deploy ל-Railway

1. התחבר ל-[Railway](https://railway.app)
2. לחץ על "New Project" → "Deploy from GitHub repo"
3. בחר את הריפו שלך
4. Railway יזהה אוטומטית את ה-Dockerfile

### שלב 3: הגדרת משתני סביבה

ב-Railway, הוסף את המשתנים הבאים:

```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
BOT_USERNAME=YourBotName
BASE_URL=https://your-app-name.railway.app
```

**חשוב:** ה-`BASE_URL` יהיה זמין רק אחרי ה-deployment הראשון.

### שלב 4: השלמת הגדרת Webhook

1. אחרי ה-deployment הראשון, העתק את ה-URL שניתן על ידי Railway
2. חזור להגדרות ב-Railway והוסף/עדכן את `BASE_URL`
3. הפעל מחדש את השירות (Redeploy)

## 📡 API Endpoints

### Health Check
```
GET /
```
בודק שהשרת פעיל.

### Webhook Info
```
GET /webhook-info
```
מציג מידע על ה-webhook הנוכחי.

### Telegram Webhook
```
POST /webhook/{BOT_TOKEN}
```
Endpoint לקבלת עדכונים מטלגרם (נגיש רק לטלגרם).

## 🤖 פקודות בוט

- `/start` - התחלת שיחה עם הבוט
- `/help` - הצגת עזרה
- `/status` - בדיקת סטטוס הבוט

## 🔧 פתרון בעיות

### הבוט לא עונה להודעות

1. בדוק שה-webhook מוגדר נכון:
   ```
   GET https://your-app.railway.app/webhook-info
   ```

2. בדוק את הלוגים ב-Railway:
   - לך ל-Deployments → בחר את ה-deployment האחרון → Logs

3. ודא שה-`BASE_URL` נכון ומכיל `https://`

### שגיאות SSL/Certificate

ודא שה-`BASE_URL` מתחיל ב-`https://` (לא `http://`)

### העדכונים לא מגיעים

נסה למחוק את ה-webhook ולהגדיר מחדש:
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/deleteWebhook
```
ואז הפעל מחדש את האפליקציה.

## 📁 מבנה הפרויקט

```
backend/
├── .env.sample          # דוגמת קובץ משתני סביבה
├── .gitignore          # קבצים להתעלמות
├── Dockerfile          # הגדרות Docker
├── README.md           # מסמך זה
├── main.py            # קובץ ראשי
├── requirements.txt   # תלויות Python
└── railway.toml       # הגדרות Railway
```

## 🔐 אבטחה

- ה-Token של הבוט מוסתר בלוגים
- האפליקציה רצה עם user לא-root ב-Docker
- משתמש ב-HTTPS בלבד לתקשורת עם Telegram

## 📝 רישוי

פרויקט זה מיועד לשימוש חינמי.

## 🤝 תרומה

נשמח לתרומות! פתח Issue או Pull Request.

## 📞 תמיכה

אם נתקלת בבעיות, פתח Issue בגיטהאב.
