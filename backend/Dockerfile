# שלב 1: שלב הבנייה (Base image)
FROM python:3.11 as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /usr/src/app # נתיב ייעודי לבנייה
WORKDIR $APP_HOME

# התקנת תלויות
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

# --- שלב 2: שלב הסופי (Runtime image) ---
FROM python:3.11

ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app # נתיב ריצה
WORKDIR $APP_HOME

# 🎯 תיקון: העתקת קבצים גלובליים וספריות site-packages
# אנחנו מעתיקים עכשיו את כל הספריות הדרושות מתוך ה-builder
# ומגדירים את ה-PATH בצורה נכונה.
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# העתקת קוד היישום (בהנחה שכל הקבצים מועברים לשורש הקונטיינר)
COPY . .

EXPOSE 8080

# הפעלת Uvicorn (פקודה זו נדרסת על ידי railway.toml startCommand)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
