import asyncio
import logging
import os
import json
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from telegram import Update
from telegram.ext import Application
from telegram.error import TelegramError

from telegram_handler import TelegramHandlers

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
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 
                          'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                          'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 
                          'stack_info', 'thread', 'threadName'] and not key.startswith('_'):
                log_record[key] = value
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)

# הגדרת Logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# ניקוי handlers קיימים
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

# הוספת handler חדש
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonLogFormatter())
logger.addHandler(console_handler)

# הגדרת רמות לוג לספריות חיצוניות
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# --- משתני סביבה ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
BOT_USERNAME = os.getenv("BOT_USERNAME", "CardGameBot")

if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN is not set!")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}" if BASE_URL else None

logger.info(f"Main application module loaded for bot: {BOT_USERNAME}")

# --- Set Webhook Function ---
async def set_webhook_on_startup(application: Application) -> None:
    """מגדיר את ה-webhook באמצעות python-telegram-bot API."""
    logger.debug("Checking for Telegram Bot setup...")
    
    if not WEBHOOK_URL:
        logger.warning("BASE_URL is not set. Webhook will not be configured.")
        logger.warning("Set BASE_URL environment variable to enable webhook mode.")
        return
    
    try:
        logger.info(f"Attempting to set webhook to: {WEBHOOK_URL}")
        
        # הסרת webhook קיים תחילה
        await application.bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(1)
        
        # הגדרת webhook חדש
        await application.bot.set_webhook(
            url=WEBHOOK_URL,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        # בדיקת הסטטוס
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

# הוספת handlers באמצעות TelegramHandlers
telegram_handlers = TelegramHandlers(application)

# --- FastAPI App ---
app = FastAPI(
    title=f"Telegram Webhook Bot ({BOT_USERNAME})",
    version="1.0.0",
    description="Telegram bot for card game with FastAPI webhook"
)

# --- Startup/Shutdown Events ---
@app.on_event("startup")
async def startup_event():
    """אירוע startup של FastAPI"""
    logger.info("FastAPI application starting up...")
    await set_webhook_on_startup(application)
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """אירוע shutdown של FastAPI"""
    logger.info("FastAPI application shutting down...")
    await application.shutdown()
    logger.info("Application shutdown complete")

# --- Middleware ---
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware לרישום בקשות HTTP"""
    async def dispatch(self, request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        # עיבוד הבקשה
        response: Response = await call_next(request)
        
        process_time = asyncio.get_event_loop().time() - start_time
        
        # רישום הבקשה
        logger.info(
            "Request processed",
            extra={
                "method": request.method,
                "url": str(request.url).replace(BOT_TOKEN, "***TOKEN***"),
                "status_code": response.status_code,
                "process_time_ms": int(process_time * 1000)
            }
        )
        
        return response

app.add_middleware(RequestLoggingMiddleware)

# --- API Endpoints ---
@app.get("/", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Endpoint לבדיקת בריאות השרת"""
    logger.debug("Health check endpoint accessed")
    return {
        "status": "ok",
        "message": f"Bot {BOT_USERNAME} is running",
        "webhook_configured": WEBHOOK_URL is not None
    }

@app.get("/webhook-info", status_code=status.HTTP_200_OK, tags=["Telegram"])
async def webhook_info() -> Dict[str, Any]:
    """מידע על ה-webhook הנוכחי"""
    try:
        info = await application.bot.get_webhook_info()
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "max_connections": info.max_connections,
            "allowed_updates": info.allowed_updates,
            "last_error_date": info.last_error_date,
            "last_error_message": info.last_error_message,
        }
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}", exc_info=True)
        return {"error": str(e)}

@app.post(WEBHOOK_PATH, status_code=status.HTTP_200_OK, tags=["Telegram"])
async def telegram_webhook(request: Request) -> Response:
    """Endpoint לקבלת עדכונים מטלגרם"""
    try:
        body = await request.body()
        update_json = json.loads(body.decode("utf-8"))
        
        # יצירת אובייקט Update
        update = Update.de_json(update_json, application.bot)
        
        if update:
            # עיבוד העדכון באופן אסינכרוני
            asyncio.create_task(application.process_update(update))
            logger.debug(
                "Update received and scheduled for processing",
                extra={"update_id": update.update_id}
            )
        else:
            logger.warning("Received invalid update (None)")
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
    
    # תמיד להחזיר 200 OK לטלגרם
    return Response(status_code=status.HTTP_200_OK)

if __name__ == "__main__":
    import uvicorn
    
    # קריאת PORT מ-Railway (ברירת מחדל 8000)
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
