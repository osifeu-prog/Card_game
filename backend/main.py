import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from uvicorn.logging import Default:'AccessFormatter'

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

# --- הגדרות לוגינג ---
# שימוש ב-JSON Logger מפורט
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
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # הוספת שדות מותאמים אישית (כגון data שנוסף ע"י logger.debug(..., extra={...}))
        for key, value in record.__dict__.items():
            if key not in log_record and not key.startswith('_') and key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName']:
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False)

# הגדרת ה-Root Logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# הסרת Handlers קיימים
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

# הוספת Console Handler עם פורמט JSON
console_handler = logging.StreamHandler()
console_handler.setFormatter(JsonLogFormatter())
logger.addHandler(console_handler)

# הגדרת Logger ל-Uvicorn (גישה) להשתמש בפורמט בסיסי יותר או להתעלם ממנו אם נרצה רק את לוגי ה-FastAPI
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

# --- משתני סביבה ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
BOT_USERNAME = os.getenv("BOT_USERNAME", "DefaultBot")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}" if BASE_URL and BOT_TOKEN else None

logger.info(f"Starting application for bot: {BOT_USERNAME}")
logger.debug(f"Webhook Path: {WEBHOOK_PATH}")
logger.debug(f"Webhook URL: {WEBHOOK_URL}")


# --- Telegram Handlers ---
async def start_command(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """מגיב לפקודה /start"""
    if update.message:
        await update.message.reply_text(f"שלום! אני הבוט {BOT_USERNAME}. אני פועל באמצעות Webhook על FastAPI.")

async def help_command(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """מגיב לפקודה /help"""
    if update.message:
        await update.message.reply_text("השתמש בפקודה /start כדי להתחיל. אני מוכן לקבל עדכונים!")

async def handle_message(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """מעבד הודעות טקסט רגילות"""
    if update.message and update.message.text:
        text = update.message.text
        logger.debug("Received message for processing.", extra={"chat_id": update.message.chat_id, "text_preview": text[:50]})
        
        # הדמיית פעולה כבדה שרצה ברקע
        await asyncio.sleep(0.1) 
        
        await update.message.reply_text(f"קיבלתי את ההודעה שלך: '{text[:20]}...'")
    else:
        logger.debug("Received an update without a text message.")


# --- Middlewares ---
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware לרישום בקשות HTTP נכנסות"""
    async def dispatch(self, request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        # רישום מידע על הבקשה הנכנסת
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent"),
        }
        
        # קריאת הגוף (ה-body) של הבקשה במקרה של POST ל-webhook
        body: Optional[bytes] = None
        if request.method == "POST":
            try:
                # קריאת הגוף ושמירתו לצורך העברה ל-endpoint
                body = await request.body()
                
                # הסתרת טוקנים רגישים ב-URL של ה-webhook לפני הרישום
                log_url = str(request.url).replace(f"/webhook/{BOT_TOKEN}", "/webhook/REDACTED_TOKEN")
                log_data["url"] = log_url
                
                # ניסיון לפרסר JSON עבור לוגים
                try:
                    payload = json.loads(body.decode("utf-8"))
                    log_data["payload_preview"] = str(payload)[:100]
                except json.JSONDecodeError:
                    log_data["payload_preview"] = f"Raw body bytes (first 100): {body[:100].hex()}"
                
                logger.debug("Incoming request body captured.", extra=log_data)
                
            except Exception as e:
                logger.error(f"Error reading request body: {e}", extra=log_data)
                
            # יצירת Request חדש עם הגוף שנקרא, כדי ש-FastAPI יוכל להשתמש בו בהמשך
            request._body = body
            
        else:
            logger.debug("Incoming request.", extra=log_data)
        
        # המשך לעיבוד הבקשה
        response: Response = await call_next(request)
        
        # רישום זמן התגובה
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


# --- Application Setup ---
# בניית ה-Application
application = (
    Application.builder()
    .token(BOT_TOKEN)
    .concurrent_updates(True) # מאפשר עדכונים מקבילים
    .build()
)

# הוספת Handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("h", help_command))
# ה-handler של ההודעות צריך להיות אחרון, הוא מעין fallback
application.add_handler(application.add_handler(handle_message))


# --- Set Webhook Function ---
async def set_webhook_on_startup() -> None:
    """מגדיר את ה-webhook לאחר שהשרת התחיל"""
    if not WEBHOOK_URL:
        logger.error("BASE_URL or TELEGRAM_BOT_TOKEN is missing. Cannot set webhook.")
        return
    
    try:
        logger.info(f"Attempting to set webhook to: {WEBHOOK_URL}")
        
        # השתמש ב-set_webhook של Application.bot (מומלץ)
        webhook_info = await application.bot.set_webhook(url=WEBHOOK_URL, allowed_updates=Update.ALL_TYPES)
        
        # בדיקת סטטוס ה-webhook לאחר ההגדרה
        info = await application.bot.get_webhook_info()
        
        logger.info(
            "Webhook set successfully!",
            extra={
                "url": info.url,
                "has_custom_cert": info.has_custom_certificate,
                "pending_updates": info.pending_update_count,
                "last_error": info.last_error_date or "None",
                "last_error_message": info.last_error_message or "None",
            }
        )

    except TelegramError as e:
        logger.error(f"Failed to set webhook due to Telegram API error: {e}")
    except Exception as e:
        logger.error(f"Failed to set webhook due to unexpected error: {e}")


# --- FastAPI App ---
app = FastAPI(
    title=f"Telegram Webhook Bot ({BOT_USERNAME})",
    version="1.0.0",
    on_startup=[set_webhook_on_startup], # קריאה ל-set_webhook ברגע שה-app עולה
    on_shutdown=[lambda: application.shutdown()] # כיבוי Application נקי
)

# הוספת ה-Middleware לרישום בקשות
app.add_middleware(RequestLoggingMiddleware)


@app.get("/", status_code=status.HTTP_200_OK, tags=["Healthcheck"])
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Healthcheck"])
async def health_check() -> Dict[str, str]:
    """Healthcheck פשוט לבדיקת תקינות היישום."""
    logger.debug("Healthcheck endpoint reached.")
    return {"status": "ok", "message": f"Bot {BOT_USERNAME} is running."}


@app.post(WEBHOOK_PATH, status_code=status.HTTP_200_OK, tags=["Telegram Webhook"])
async def telegram_webhook(request: Request) -> Response:
    """Endpoint לקבלת עדכונים מטלגרם."""
    
    # 1. קריאת הגוף (הוא כבר נקרא ב-Middleware, אנחנו מקבלים גישה אליו)
    try:
        body = await request.body()
    except Exception:
        logger.error("Failed to read request body in webhook handler.")
        # החזרת 200 בכל מקרה, כמקובל ב-Telegram API
        return Response(status_code=status.HTTP_200_OK)

    # 2. ניסיון לפרסר את ה-Update
    try:
        # פתרון מומלץ: יצירת משימה ברקע ל-Application.process_update
        # המחיר: Python-Telegram-Bot לא מספק דרך קלה ליצירת Update מ-body של FastAPI
        # לכן נשתמש בדרך המקובלת שמטפלת ב-JSON ישירות:
        update_json = json.loads(body.decode("utf-8"))
        update = Update.de_json(update_json, application.bot)
        
        # 3. העיבוד עצמו מתבצע במשימת רקע
        # ה-update נשלח ל-dispatcher, שמעבד אותו ומבצע את הפעולות הנדרשות.
        asyncio.create_task(application.process_update(update))
        
        logger.debug("Update received and process_update scheduled in background task.", extra={"update_id": update.update_id})
        
    except json.JSONDecodeError:
        logger.error("Received an invalid JSON payload.", extra={"body_preview": body[:100].decode("utf-8", errors='ignore')})
    except TelegramError as e:
        logger.error(f"Error processing update by python-telegram-bot: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in webhook processing: {e}", exc_info=True)
        
    # החזרת תגובה מהירה (HTTP 200) כדי לאפשר לטלגרם להמשיך הלאה.
    return Response(status_code=status.HTTP_200_OK)


# --- Shutdown Hook ---
@app.on_event("shutdown")
async def shutdown_event():
    """מבוצע בעת כיבוי היישום."""
    logger.info("Application shutting down. Deleting webhook (optional, but good practice)...")
    try:
        # מחיקת ה-webhook (אופציונלי, עוזר בסביבת פיתוח מקומית)
        await application.bot.delete_webhook()
        logger.info("Webhook deleted successfully on shutdown.")
    except Exception as e:
        logger.warning(f"Could not delete webhook on shutdown: {e}")
