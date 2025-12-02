import asyncio
import logging
import os
import json
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler
from telegram.error import TelegramError

# --- הגדרות לוגינג (DEBUG + JSON) ---
class JsonLogFormatter(logging.Formatter):
    """פורמטר לוגים בפורמט JSON."""
    def format(self, record):
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'] and not key.startswith('_'):
                log_record[key] = value
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG) 
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonLogFormatter())
logger.addHandler(console_handler)

logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

# --- משתני סביבה ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
BOT_USERNAME = os.getenv("BOT_USERNAME", "DefaultBot")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}" if BASE_URL and BOT_TOKEN else None

logger.info(f"Main application module loaded for bot: {BOT_USERNAME}")

# --- Set Webhook Function (חזרה ל-Python) ---
async def set_webhook_on_startup(application: Application) -> None:
    """מגדיר את ה-webhook באמצעות python-telegram-bot API."""
    logger.debug("Checking for Telegram Bot setup...")
    if not WEBHOOK_URL or not BOT_TOKEN:
        logger.error("BASE_URL or TELEGRAM_BOT_TOKEN is missing. Cannot set webhook.")
        return
    
    try:
        logger.info(f"Attempting to set webhook to: {WEBHOOK_URL}")
        
        # Set Webhook בפועל באמצעות Application.bot
        await application.bot.set_webhook(url=WEBHOOK_URL, allowed_updates=Update.ALL_TYPES)
        
        info = await application.bot.get_webhook_info()
        
        logger.info(
            "Webhook set successfully!",
            extra={
                "url": info.url,
                "pending_updates": info.pending_update_count,
                "max_connections": info.max_connections,
                "last_error_message": info.last_error_message or "None",
            }
        )
    except TelegramError as e:
        # זה יופיע בלוגים אם יש בעיית TOKEN או SSL/URL
        logger.error(f"Failed to set webhook due to Telegram API error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Failed to set webhook due to unexpected error: {e}", exc_info=True)


# --- Application Setup ---
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .concurrent_updates(True) 
    .build()
)

# הוספת Handlers (כמו קודם)
async def start_command(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("שלום! אני מוכן לעבודה.")
        
async def handle_message(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        await asyncio.sleep(0.05) 
        await update.message.reply_text(f"קיבלתי: '{update.message.text[:20]}...'")

application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(None, handle_message))


# --- FastAPI App ---
app = FastAPI(
    title=f"Telegram Webhook Bot ({BOT_USERNAME})",
    version="3.0.0",
    # קריאה ל-set_webhook כפונקציית Startup
    on_startup=[lambda: set_webhook_on_startup(application)], 
    on_shutdown=[lambda: application.shutdown()]
)

# Middleware לרישום בקשות (כמו קודם)
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        # ... (לוגיקת רישום נשארה זהה) ...
        response: Response = await call_next(request)
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(
            "Request finished.", 
            extra={
                "method": request.method, 
                "url": str(request.url).replace(f"/webhook/{BOT_TOKEN}", "/webhook/REDACTED_TOKEN"),
                "status_code": response.status_code, 
                "process_time_ms": int(process_time * 1000)
            }
        )
        return response

app.add_middleware(RequestLoggingMiddleware)

@app.get("/", status_code=status.HTTP_200_OK, tags=["Healthcheck"])
async def health_check() -> Dict[str, str]:
    logger.debug("Healthcheck endpoint reached.")
    return {"status": "ok", "message": f"Bot {BOT_USERNAME} is running."}


@app.post(WEBHOOK_PATH, status_code=status.HTTP_200_OK, tags=["Telegram Webhook"])
async def telegram_webhook(request: Request) -> Response:
    """Endpoint לקבלת עדכונים מטלגרם."""
    body = await request.body() 
    try:
        update_json = json.loads(body.decode("utf-8"))
        update = Update.de_json(update_json, application.bot)
        # עיבוד במשימת רקע
        asyncio.create_task(application.process_update(update))
        logger.debug("Update received and process_update scheduled.", extra={"update_id": update.update_id})
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        
    return Response(status_code=status.HTTP_200_OK)
