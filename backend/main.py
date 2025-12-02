import logging
from telegram_handler import app

# הגדרת לוגים ברמת DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.debug("Main.py loaded, FastAPI app imported successfully")
