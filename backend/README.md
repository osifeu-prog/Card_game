# Telegram Webhook Bot (Railway / Docker ready)

## מה זה
פרויקט בוט טלגרם שמקבל עדכונים דרך Webhook, מותאם לפריסה ב‑Railway באמצעות Docker. כולל healthcheck, לוגים ברמת DEBUG, והגדרת webhook ברקע.

## קבצים חשובים
- `main.py` — אפליקציה (FastAPI) וממשק ל‑python-telegram-bot.
- `Dockerfile` — בניית תמונה מותאמת ל‑Railway.
- `railway.toml` — הגדרות פריסה (startCommand, healthcheck).
- `.env.sample` — דוגמת משתני סביבה.

## הגדרות לפני פריסה
1. צרו בוט ב‑@BotFather וקבלו `TELEGRAM_BOT_TOKEN`.
2. בפרויקט Railway הוסיפו משתני סביבה:
   - `TELEGRAM_BOT_TOKEN` (או `TELEGRAM_TOKEN`)
   - `BASE_URL` — הכתובת הציבורית של הפרויקט (לדוגמה `https://cardgame-production-d1cd.up.railway.app`)
3. דחפו את הקבצים ל‑GitHub; Railway יבנה ויפרס את היישום.
4. לאחר שה‑service עולה, הריצו:
   - `deleteWebhook` ואז `setWebhook` עם ה‑URL המדויק (או בדקו שה‑set_webhook בלוגים החזיר `True`).

## בדיקות מהירות
- בדוק health: `curl https://<your-app>/`
- בדוק webhook ידנית: שלח POST ל`/webhook/<TOKEN>` עם JSON של Update ובדוק שהשרת מחזיר 200.

## הערות
- ודא שה‑Target port ב‑Railway תואם (בדף שלך מופיע 8080).
- אל תחשוף את הטוקן בפומבי; השתמש ב‑Environment Variables.
