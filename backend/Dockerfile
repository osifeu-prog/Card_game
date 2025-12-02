# שלב 1: שלב הבנייה
FROM python:3.11 as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

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

# העתקת התלויות המותקנות משלב הבנייה
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# העתקת קוד היישום
COPY . .

EXPOSE 8080

# הפעלה פשוטה של Uvicorn (כאשר PORT מגיע ממשתנה הסביבה של Railway)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
