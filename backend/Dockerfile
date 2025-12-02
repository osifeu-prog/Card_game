# שלב 1: שלב הבנייה
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

WORKDIR $APP_HOME

# התקנת תלויות
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

# שלב 2: שלב הסופי (Runtime image)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
ENV PORT 8080 # ברירת מחדל, תידרס על ידי Railway

WORKDIR $APP_HOME

# העתקת התלויות המותקנות
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# העתקת קוד היישום וסקריפט ההתחלה
COPY . .

# הגדרת הרשאות הרצה לסקריפט start.sh - קריטי!
RUN chmod +x $APP_HOME/start.sh

EXPOSE 8080

# הפעלת start.sh שמנהל את Set Webhook ואז מריץ את Gunicorn
CMD ["/bin/bash", "start.sh"]
