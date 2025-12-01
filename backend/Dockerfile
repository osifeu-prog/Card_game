# השתמש ב-Python 3.11 כבסיס
FROM python:3.11-slim

# הגדרת תיקיית העבודה בתוך ה-Container
WORKDIR /app

# העתק את קובץ התלויות והתקן אותן
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתק את כל שאר קבצי הפרויקט
COPY . .

# הפעל את השרת באמצעות Uvicorn, האזנה לכל הממשקים (0.0.0.0) בפורט 8000
# Railway תפנה את התעבורה לפורט זה אוטומטית.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
