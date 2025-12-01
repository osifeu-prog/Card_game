# backend/main.py
import logging
from telegram_handler import app  # מייבא את FastAPI app מהקובץ telegram_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# זהו קובץ ה־entrypoint של האפליקציה
# Railway יריץ את זה עם הפקודה:
# uvicorn main:app --host 0.0.0.0 --port 8000
