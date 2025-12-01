# Dockerfile
# משתמשים בגרסת buster המלאה יותר שכוללת את כלי הקומפילציה (כמו gcc)
FROM python:3.11-buster

# הגדרת משתני סביבה סטנדרטיים ל-Python
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# הגדרת ספריית העבודה
WORKDIR /app

# העתק את קובץ התלויות והתקן אותן
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתק את כל שאר קבצי הפרויקט
COPY . .

# הגדרת הפקודה להרצת השרת באמצעות Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
