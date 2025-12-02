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

WORKDIR $APP_HOME

# העתקת התלויות המותקנות משלב הבנייה
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# העתקת קוד היישום
COPY . .

# EXPOSE נועד לתיעוד; הפורט האמיתי נלקח ממשתנה הסביבה PORT
EXPOSE 8080

# פקודת ההפעלה הראשית: הפעלה דרך Uvicorn על הפורט שסופק ע"י המערכת.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
