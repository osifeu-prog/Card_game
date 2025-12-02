FROM python:3.11-slim

# הגדרת תיקיית עבודה
WORKDIR /app

# העתקת requirements והתקנת dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# העתקת הקוד
COPY . .

# יצירת user לא-root לאבטחה
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# חשיפת פורט (Railway ישתמש במשתנה PORT)
EXPOSE 8000

# הרצת האפליקציה - Railway יגדיר את PORT אוטומטית
CMD python main.py
