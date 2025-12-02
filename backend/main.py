import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from uvicorn.logging import Default:'AccessFormatter'

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler
from telegram.constants import MessageType
from telegram.error import TelegramError

# --- הגדרות לוגינג (פתרון: לוגים מפורטים ברמת DEBUG) ---
class JsonLogFormatter(logging.Formatter):
    """פורמטר לוגים בפורמט JSON, עם שדות מותאמים אישית."""
    def format(self, record):
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        
        # הוספת שדות קונטקסט (extra)
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName'] and not key.startswith('_'):
                log_record[key] = value

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record, ensure_ascii=False)

# הגדרת ה-Root Logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG) # רמת DEBUG לרישום מפורט

# הסרת Handlers קיימים
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

# הוספת Console Handler עם פורמט JSON
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonLogFormatter())
logger.addHandler(console_handler)

# השתקה חלקית של Uvicorn כדי לא להעמיס
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

# --- משתני סביבה ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
BOT_USERNAME = os.getenv("BOT_USERNAME", "DefaultBot")

if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")

# נתיב Webhook מאובטח עם הטוקן (מומלץ)
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}" if BASE_URL and BOT_TOKEN else None

logger.info(f"Starting application for bot: {BOT_USERNAME}")


# --- Telegram Handlers ---
async def start_command(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """מגיב לפקודה /start"""
    if update.message:
        logger.debug("Executing /start command.")
        await update.message.reply_text(f"שלום! אני הבוט {BOT_USERNAME}. אני פועל באמצעות Webhook על FastAPI.")

async def handle_message(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """מעבד הודעות טקסט רגילות (עיבוד קל)"""
    if update.message and update.message.text:
        text = update.message.text
        logger.debug("Received message for processing.", extra={"chat_id": update.message.chat_id, "text_preview": text[:50]})
        
        # הדמיית פעולה קלה
        await asyncio.sleep(0.05) 
        
        await update.message.reply_text(f"קיבלתי את ההודעה שלך: '{text[:20]}...'")
    else:
        logger.debug("Received an update without a text message.")


# --- Middlewares (רישום בקשות) ---
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware לרישום בקשות HTTP נכנסות"""
    async def dispatch(self, request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        # רישום מידע על הבקשה הנכנסת
        log_data = {
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            # הסתרת הטוקן ב-URL לפני הרישום
            "url": str(request.url).replace(f"/webhook/{BOT_TOKEN}", "/webhook/REDACTED_TOKEN"),
            "user_agent": request.headers.get("user-agent"),
        }
        
        body: Optional[bytes] = None
        if request.method == "POST":
            try:
                # קריאת הגוף ושמירתו לצורך העברה ל-endpoint
                body = await request.body()
                
                try:
                    # ניסיון לפרסר JSON עבור לוגים
                    payload = json.loads(body.decode("utf-8"))
                    # רישום מזהה העדכון
                    log_data["update_id"] = payload.get("update_id", "N/A") 
                    log_data["payload_preview"] = str(payload)[:100]
                except json.JSONDecodeError:
                    log_data["payload_preview"] = f"Raw body bytes (first 100): {body[:100].hex()}"
                
                logger.debug("Incoming POST request body captured.", extra=log_data)
                
            except Exception as e:
                logger.error(f"Error reading request body in middleware: {e}", extra=log_data)
                
            # יצירת Request חדש עם הגוף שנקרא
            request._body = body
            
        else:
            logger.debug("Incoming request.", extra=log_data)
        
        response: Response = await call_next(request)
        
        # רישום זמן התגובה
        process_time = asyncio.get_event_loop().time() - start_time
        logger.info(
            "Request finished.", 
            extra={
                "method": request.method, 
                "url": log_data["url"],
                "status_code": response.status_code, 
                "process_time_ms": int(process_time * 1000)
            }
        )
        
        return response


# --- Application Setup ---
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .concurrent_updates(True) 
    .build()
)

# הוספת Handlers
application.add_handler(CommandHandler("start", start_command))
# הוספת handler להודעות טקסט (פועל כברירת מחדל אם אין פקודות)
application.add_handler(MessageHandler(None, handle_message))


# --- Set Webhook Function (פתרון לבעיה 2) ---
async def set_webhook_on_startup() -> None:
    """מגדיר את ה-webhook לאחר שהשרת התחיל"""
    logger.debug("Checking for Telegram Bot setup...")
    if not WEBHOOK_URL or not BOT_TOKEN:
        logger.error("BASE_URL or TELEGRAM_BOT_TOKEN is missing. Cannot set webhook. Check your environment variables.")
        return
    
    try:
        logger.info(f"Attempting to set webhook to: {WEBHOOK_URL}")
        
        # Set Webhook בפועל
        await application.bot.set_webhook(url=WEBHOOK_URL, allowed_updates=Update.ALL_TYPES)
        
        # בדיקת סטטוס ה-webhook לאחר ההגדרה
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
        logger.error(f"Failed to set webhook due to Telegram API error (Set Webhook Failed): {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Failed to set webhook due to unexpected error (Startup Error): {e}", exc_info=True)


# --- FastAPI App ---
app = FastAPI(
    title=f"Telegram Webhook Bot ({BOT_USERNAME})",
    version="1.0.0",
    # קריאה ל-set_webhook ברגע שה-app עולה
    on_startup=[set_webhook_on_startup], 
    on_shutdown=[lambda: application.shutdown()]
)

# הוספת ה-Middleware לרישום בקשות
app.add_middleware(RequestLoggingMiddleware)


@app.get("/", status_code=status.HTTP_200_OK, tags=["Healthcheck"])
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Healthcheck"])
async def health_check() -> Dict[str, str]:
    """Healthcheck פשוט לבדיקת תקינות היישום (פתרון לבעיה 3)."""
    logger.debug("Healthcheck endpoint reached.")
    return {"status": "ok", "message": f"Bot {BOT_USERNAME} is running."}


@app.post(WEBHOOK_PATH, status_code=status.HTTP_200_OK, tags=["Telegram Webhook"])
async def telegram_webhook(request: Request) -> Response:
    """Endpoint לקבלת עדכונים מטלגרם."""
    
    # הגוף נקרא כבר ב-Middleware, אנחנו ניגשים אליו
    body = await request.body() 

    # 1. ניסיון לפרסר את ה-Update
    try:
        update_json = json.loads(body.decode("utf-8"))
        update = Update.de_json(update_json, application.bot)
        
        # 2. העיבוד עצמו מתבצע במשימת רקע (HTTP 200 מהירה)
        asyncio.create_task(application.process_update(update))
        
        logger.debug("Update received and process_update scheduled in background task.", extra={"update_id": update.update_id})
        
    except json.JSONDecodeError:
        # טיפול ב-JSON לא תקין
        logger.error("Received an invalid JSON payload (Failed to decode).", extra={"body_preview": body[:100].decode("utf-8", errors='ignore')})
    except TelegramError as e:
        logger.error(f"Error processing update by python-telegram-bot: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in webhook processing: {e}", exc_info=True)
        
    # החזרת תגובה מהירה (HTTP 200)
    return Response(status_code=status.HTTP_200_OK)


# --- Shutdown Hook ---
@app.on_event("shutdown")
async def shutdown_event():
    """מבוצע בעת כיבוי היישום - מכבה את ה-Application."""
    logger.info("Application shutting down.")
