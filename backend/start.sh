#!/bin/bash
# start.sh
# מבצע Set Webhook באמצעות curl ואז מפעיל את השרת (Gunicorn)

echo "--- 1. Set Webhook Phase ---"

# קורא את משתני הסביבה
TOKEN=${TELEGRAM_BOT_TOKEN}
URL=${BASE_URL}/webhook/${TELEGRAM_BOT_TOKEN}

if [ -z "$TOKEN" ] || [ -z "$BASE_URL" ]; then
    echo "ERROR: TELEGRAM_BOT_TOKEN or BASE_URL is not set. Cannot continue."
    exit 1
fi

# 1. מחיקת Webhook ישן (לניקיון)
echo "Attempting to delete old webhook..."
curl -s "https://api.telegram.org/bot${TOKEN}/deleteWebhook"

# 2. הגדרת Webhook חדש
echo "Attempting to set new webhook to: ${URL}"
# RESPONSE מכיל את הפלט של טלגרם, שיעזור בניפוי שגיאות
RESPONSE=$(curl -s -X POST -F "url=${URL}" "https://api.telegram.org/bot${TOKEN}/setWebhook")

if echo "${RESPONSE}" | grep -q '"ok":true'; then
    echo "Webhook set successfully!"
    echo "Response: ${RESPONSE}"
else
    echo "ERROR: Failed to set webhook. Check TOKEN/BASE_URL/SSL."
    echo "Response: ${RESPONSE}"
    # קריטי: הפסקת התהליך אם Set Webhook נכשל (Failure Early)
    exit 1 
fi

echo "--- 2. Server Startup Phase (Gunicorn + Uvicorn) ---"

# חישוב מספר ה-workers (כפול 2 + 1 מליבות ה-CPU, אם זמין)
WEB_CONCURRENCY=${WEB_CONCURRENCY:-$((2 * $(nproc) + 1))}
# אם nproc נכשל, נשתמש ב-3 כברירת מחדל
if [ $WEB_CONCURRENCY -lt 3 ]; then
    WEB_CONCURRENCY=3
fi

# הפעלת Gunicorn שמנהל את Uvicorn Workers על הפורט שסופק
exec gunicorn main:app \
  --workers ${WEB_CONCURRENCY} \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT} \
  --log-level info \
  --access-logfile '-' \
  --error-logfile '-'
