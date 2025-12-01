# backend/Dockerfile
FROM python:3.11-slim

# התקנת תלותים בסיסיים
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# יצירת תיקיית עבודה
WORKDIR /app

# התקנת ספריות
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת הקוד
COPY . .

# הפקודה להרצה
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
