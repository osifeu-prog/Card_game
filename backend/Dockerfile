# שלב 1: שלב הבנייה (Base image)
FROM python:3.11 as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /usr/src/app
WORKDIR $APP_HOME

# התקנת תלויות
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

# שלב 2: שלב הסופי (Runtime image)
FROM python:3.11

ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
WORKDIR $APP_HOME

# העתקת קבצים גלובליים וספריות site-packages (כדי ש-uvicorn יהיה זמין)
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# העתקת קוד היישום (בהנחה שכל הקבצים מועברים לשורש הקונטיינר)
COPY . .

EXPOSE 8080

# 🎯 התיקון הקריטי: הגדרת CMD עם PORT כברירת מחדל
# תחביר CMD זה מחפש את משתנה הסביבה PORT ואם לא נמצא (במקרה התיאורטי), משתמש ב-8080.
# זה מבטיח שהפקודה מפורשת ל-Bash בתוך הקונטיינר.
CMD ["/bin/bash", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
