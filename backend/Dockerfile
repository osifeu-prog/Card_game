# Dockerfile
# שנה את השורה הראשונה מ-slim ל-buster כדי לקבל את כלי הקומפילציה הדרושים
FROM python:3.11-buster

# הגדרת משתני סביבה כדי לאפשר Python לכתוב קבצים סטנדרטיים (חשוב ל-Railway)
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# הגדרת ספריית העבודה
WORKDIR /app

# העתק את קובץ התלויות והתקן אותן
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתק את כל שאר קבצי הפרויקט
COPY . .

# הגדרת הפקודה להרצת השרת
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
