import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler

# --- הגדרות לוגינג (DEBUG + JSON) ---
class JsonLogFormatter(logging.Formatter):
    """פורמטר לוגים בפורמט JSON."""
    def format(self, record):
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "lineno": record.lineno,
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
BOT_USERNAME = os.getenv("BOT_USERNAME", "DefaultBot")

logger.info(f"Main application module loaded for bot: {BOT_USERNAME}")

# --- Telegram Handlers ---
async def start_command(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """מגיב לפקודה /start"""
    if update.message:
        logger.debug("/start command received.")
        await update.message.reply_text(f"שלום! אני הבוט {BOT_USERNAME}. אני פועל באמצעות Webhook.")

async def handle_message(update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
    """מעבד הודעות טקסט רגילות"""
    if update.message and update.message.text:
        text = update.message.text
        logger.debug("Message update received for background processing.", extra={"chat_id": update.message.chat_id, "text_preview": text[:50]})
        
        # הדמיית פעולה קלה
        await asyncio.sleep(0.05) 
        
        await update.message.reply_text(f"קיבלתי את ההודעה שלך: '{text[:20]}...'")
    else:
        logger.debug("Received an update without a text message or text content.")

# --- Middlewares (רישום בקשות) ---
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = asyncio.get_event_loop().time()
        
        log_data = {
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "url": str(request.url).replace(f"/webhook/{BOT_TOKEN}", "/webhook/REDACTED_TOKEN"),
            "user_agent": request.headers.get("user-agent"),
        }
        
        body: Optional[bytes] = None
        if request.method == "POST":
            try:
                body = await request.body()
                
                try:
                    payload = json.loads(body.decode("utf-8"))
                    log_data["update_id"] = payload.get("update_id", "N/A") 
                except json.JSONDecodeError:
                    pass
                
                logger.debug("Incoming POST request body captured.", extra=log_data)
                request._body = body # החזרת הגוף ל-FastAPI
            except Exception as e:
                logger.error(f"Error reading request body in middleware: {e}")
                
        response: Response = await call_next(request)
        
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

application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(None, handle_message))


# --- FastAPI App ---
app = FastAPI(
    title=f"Telegram Webhook Bot ({BOT_USERNAME})",
    version="2.0.0",
    # הוסר on_startup כדי לאפשר ל-start.sh לנהל את ה-Webhook
    on_shutdown=[lambda: application.shutdown()]
)

app.add_middleware(RequestLoggingMiddleware)

# נתיב ה-Webhook חייב להיות זהה לזה שב-start.sh
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

@app.get("/", status_code=status.HTTP_200_OK, tags=["Healthcheck"])
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Healthcheck"])
async def health_check() -> Dict[str, str]:
    """Healthcheck פשוט."""
    logger.debug("Healthcheck endpoint reached.")
    return {"status": "ok", "message": f"Bot {BOT_USERNAME} is running."}


@app.post(WEBHOOK_PATH, status_code=status.HTTP_200_OK, tags=["Telegram Webhook"])
async def telegram_webhook(request: Request) -> Response:
    """Endpoint לקבלת עדכונים מטלגרם."""
    
    body = await request.body() 

    # 1. ניסיון לפרסר את ה-Update
    try:
        update_json = json.loads(body.decode("utf-8"))
        update = Update.de_json(update_json, application.bot)
        
        # 2. העיבוד מתבצע במשימת רקע (HTTP 200 מהירה)
        asyncio.create_task(application.process_update(update))
        
        logger.debug("Update received and process_update scheduled in background task.", extra={"update_id": update.update_id})
        
    except json.JSONDecodeError:
        logger.error("Received an invalid JSON payload (Failed to decode).")
    except Exception as e:
        logger.error(f"Error in webhook processing: {e}", exc_info=True)
        
    # החזרת תגובה מהירה (HTTP 200)
    return Response(status_code=status.HTTP_200_OK)
