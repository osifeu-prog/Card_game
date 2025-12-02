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

# יצירת ספריית האפליקציה
WORKDIR $APP_HOME

# העתקת התלויות המותקנות משלב הבנייה
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# העתקת קוד היישום
COPY . .

# חשוב: Uvicorn מאזין על הפורט שמוגדר במשתנה הסביבה PORT (ב-Railway, זהו הפורט הנדרש).
# EXPOSE אינו פותח את הפורט בפועל, אך משמש לתיעוד ולכלי ניתוח.
EXPOSE 8080

# פקודת ההפעלה הראשית (ניתן להחליף ב-Procfile או railway.toml)
# שימוש במשתנה הסביבה $PORT (ברירת מחדל 8080 אם לא מוגדר)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
