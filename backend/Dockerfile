FROM python:3.11-slim

# הגדרת תיקיית עבודה
WORKDIR /app

# התקנת דרישות
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# העתקת כל הקוד
COPY . .

# פתיחת פורט
EXPOSE 8000

# פקודת הרצה
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
