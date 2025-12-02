FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

---

### 2️⃣ צור Service חדש ב-Railway

1. **Railway → New Project → Deploy from GitHub**
2. בחר את `Card_game`
3. Railway יתחיל build אוטומטי

---

### 3️⃣ הגדרות ב-Railway

ברגע שה-Service נוצר:

**א. Settings → Source:**
- **Root Directory:** `backend`

**ב. Settings → Build:**
- **Builder:** צריך להיות `Dockerfile` (אוטומטית)

**ג. Variables → הוסף משתנים:**
```
TELEGRAM_BOT_TOKEN=your_token_here
BOT_USERNAME=YourBotName
```

**שמור והמתן ל-Redeploy.**

---

### 4️⃣ אחרי Deploy הראשון

1. **קבל את ה-URL** (למשל: `https://cardgame-production-xxxx.up.railway.app`)
2. **חזור ל-Variables והוסף:**
```
   BASE_URL=https://cardgame-production-xxxx.up.railway.app
