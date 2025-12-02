# main.py
# Telegram webhook bot (FastAPI) - Railway/Docker ready
# Requires: fastapi, uvicorn, python-telegram-bot, python-dotenv
# Behavior:
# - Healthcheck on /
# - Webhook endpoint on /webhook/<TOKEN>
# - set_webhook runs in background during startup
# - Incoming updates are scheduled for background processing to return 200 quickly

import os
import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application

# Load .env for local development
load_dotenv()

# Environment variables (set these in Railway)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # e.g. https://cardgame-production-d1cd.up.railway.app
PORT = int(os.getenv("PORT", "8080"))

if not TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_TOKEN environment variable")

# Logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("telegram-webhook")

# FastAPI app
app = FastAPI()

# Telegram bot and application
bot = Bot(token=TOKEN)
application: Application = ApplicationBuilder().token(TOKEN).build()

# Webhook path (unique by token)
WEBHOOK_PATH = f"/webhook/{TOKEN}"

# Example command handler
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        name = user.first_name if user else "there"
        await update.message.reply_text(f"שלום {name}! הבוט עובד דרך webhook ✅")
        logger.debug("Replied to /start for user_id=%s", getattr(user, "id", None))
    except Exception:
        logger.exception("Error in start_handler")

application.add_handler(CommandHandler("start", start_handler))

# Middleware to log incoming HTTP requests (headers + body preview)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    req_id = id(request)
    logger.debug("HTTP start id=%s method=%s path=%s", req_id, request.method, request.url.path)
    try:
        body = await request.body()
        body_preview = body.decode(errors="ignore")[:1000] if body else ""
        logger.debug("Request id=%s headers=%s body_preview=%s", req_id, dict(request.headers), body_preview)
    except Exception:
        logger.debug("Request id=%s could not read body", req_id)
    response = await call_next(request)
    logger.debug("HTTP end id=%s status=%s", req_id, response.status_code)
    return response

# Health endpoints
@app.get("/")
async def root():
    logger.debug("Healthcheck / requested")
    return JSONResponse({"ok": True, "status": "running"})

@app.get("/health")
async def health():
    logger.debug("Healthcheck /health requested")
    return JSONResponse({"ok": True, "status": "healthy"})

# Background task to set webhook (non-blocking)
async def set_webhook_background():
    if not BASE_URL:
        logger.warning("BASE_URL not set; skipping webhook setup")
        return
    webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
    try:
        logger.info("Setting webhook to %s", webhook_url)
        result = await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("set_webhook result: %s", result)
    except Exception:
        logger.exception("Failed to set webhook")

# Startup: initialize and start telegram Application, schedule webhook setup
@app.on_event("startup")
async def on_startup():
    logger.info("Application startup: initializing telegram Application")
    try:
        await application.initialize()
        await application.start()
        logger.info("telegram Application initialized and started")
    except Exception:
        logger.exception("Failed to initialize/start telegram Application")

    # Schedule webhook setup in background so startup returns quickly
    asyncio.create_task(set_webhook_background())

# Shutdown: delete webhook and stop telegram Application
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutdown: deleting webhook and stopping telegram Application")
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

# Helper to process update in background to avoid blocking the HTTP response
async def process_update_in_background(update: Update):
    try:
        await application.process_update(update)
        logger.debug("Update processed: update_id=%s", getattr(update, "update_id", None))
    except Exception:
        logger.exception("Error while processing update: update_id=%s", getattr(update, "update_id", None))

# Webhook endpoint - returns quickly, processes update in background
@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    request_id = id(request)
    logger.debug("Incoming webhook request id=%s", request_id)
    try:
        data = await request.json()
        logger.debug("Webhook payload id=%s: %s", request_id, data if isinstance(data, dict) else str(data)[:1000])
    except Exception as e:
        logger.exception("Invalid JSON in webhook request id=%s: %s", request_id, e)
        raise HTTPException(status_code=400, detail="Invalid JSON")

    try:
        update = Update.de_json(data, bot)
    except Exception:
        logger.exception("Failed to parse Update JSON id=%s", request_id)
        raise HTTPException(status_code=400, detail="Invalid Update object")

    # Schedule processing in background and return 200 immediately
    try:
        asyncio.create_task(process_update_in_background(update))
    except Exception:
        logger.exception("Failed to schedule update processing id=%s", request_id)
    return JSONResponse({"ok": True})

# Local run for development
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn for local testing on port %s", PORT)
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="debug")
