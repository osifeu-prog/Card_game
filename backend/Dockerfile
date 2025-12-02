# שלב 1: שלב הבנייה (Base image)
FROM python:3.11-slim as builder

# הגדרת משתני סביבה כלליים
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# יצירת ספריית האפליקציה והפיכתה לספריית העבודה
WORKDIR $APP_HOME

# התקנת תלויות
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

# שלב 2: שלב הסופי (Runtime image)
FROM python:3.11-slim

# הגדרת משתני סביבה כלליים
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
ENV PORT 8080 # ברירת מחדל, תידרס על ידי Railway

# יצירת ספריית האפליקציה
WORKDIR $APP_HOME

# העתקת התלויות המותקנות משלב הבנייה
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# --- ✅ התיקון: התקנת curl ---
# עדכון רשימת החבילות והתקנת curl (חיוני עבור start.sh)
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*
# --- סוף התיקון ---

# העתקת קוד היישום וסקריפט ההתחלה
COPY . .

# הגדרת הרשאות הרצה לסקריפט start.sh - קריטי!
RUN chmod +x $APP_HOME/start.sh

# EXPOSE נועד לתיעוד
EXPOSE 8080

# הפעלת start.sh שמנהל את Set Webhook ואז מריץ את Gunicorn
CMD ["/bin/bash", "start.sh"]
