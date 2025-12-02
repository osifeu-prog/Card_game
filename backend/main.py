# main.py
import os
import logging
import traceback
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", "8000"))

if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_TOKEN environment variable")
if not BASE_URL:
    # allow BASE_URL to be empty for local testing but warn
    logging.warning("BASE_URL not set; webhook won't be configured automatically")

# Logging - full debug
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("telegram-webhook-bot")

logger.debug("Starting main.py - initializing FastAPI and Telegram bot")

# FastAPI app
app = FastAPI()

# Telegram bot and application
bot = Bot(token=TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

# Example command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Handling /start command from user_id=%s", update.effective_user.id if update.effective_user else "unknown")
    await update.message.reply_text("שלום! הבוט עובד דרך webhook ✅")

application.add_handler(CommandHandler("start", start))

# Middleware to log incoming HTTP requests (body + headers)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = id(request)
    logger.debug("HTTP request start id=%s method=%s path=%s", request_id, request.method, request.url.path)
    try:
        body = await request.body()
        logger.debug("Request id=%s headers=%s body=%s", request_id, dict(request.headers), body.decode(errors="ignore"))
    except Exception as e:
        logger.debug("Request id=%s could not read body: %s", request_id, e)
    response = await call_next(request)
    logger.debug("HTTP request end id=%s status_code=%s", request_id, response.status_code)
    return response

# Healthcheck root path (Railway healthcheck expects 200 on /)
@app.get("/")
async def root():
    logger.debug("Healthcheck requested on /")
    return JSONResponse({"ok": True, "status": "running"})

# Additional health endpoint
@app.get("/health")
async def health():
    logger.debug("Health requested on /health")
    return JSONResponse({"ok": True, "status": "healthy"})

# Webhook path
WEBHOOK_PATH = f"/webhook/{TOKEN}"

@app.on_event("startup")
async def on_startup():
    logger.info("Application startup: setting webhook (if BASE_URL provided)")
    if BASE_URL:
        webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
        try:
            result = await bot.set_webhook(webhook_url, drop_pending_updates=True)
            logger.info("set_webhook returned: %s", result)
            if not result:
                logger.warning("set_webhook returned falsy value; check token and BASE_URL")
            else:
                logger.debug("Webhook successfully set to %s", webhook_url)
        except Exception as e:
            logger.exception("Failed to set webhook to %s: %s", webhook_url, e)
    else:
        logger.warning("BASE_URL not set; skipping webhook setup")

    # Initialize the telegram application (ensures internal data structures ready)
    try:
        await application.initialize()
        await application.start()
        logger.info("telegram Application initialized and started")
    except Exception:
        logger.exception("Failed to initialize/start telegram Application")

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    request_id = id(request)
    logger.debug("Incoming webhook request id=%s", request_id)
    try:
        data = await request.json()
        logger.debug("Webhook payload id=%s: %s", request_id, data)
    except Exception as e:
        logger.exception("Invalid JSON in webhook request id=%s: %s", request_id, e)
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        update = Update.de_json(data, bot)
        logger.debug("Converted payload to Update id=%s: update_id=%s", request_id, getattr(update, "update_id", None))
        # Process update with the telegram application
        await application.process_update(update)
        logger.debug("Processed update id=%s", request_id)
    except Exception as e:
        logger.exception("Error processing update id=%s: %s", request_id, e)
        # Return 200 to Telegram to avoid retries if you handled it; but log the error
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    return JSONResponse({"ok": True})

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown: deleting webhook and stopping telegram application")
    try:
        await bot.delete_webhook()
        logger.info("Webhook deleted")
    except Exception:
        logger.exception("Failed to delete webhook")
    try:
        await application.stop()
        await application.shutdown()
        logger.info("telegram Application stopped and shutdown")
    except Exception:
        logger.exception("Failed to stop/shutdown telegram Application")
