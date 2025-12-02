# main.py - safe startup example
import os
import logging
import asyncio
from fastapi import FastAPI
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = os.getenv("BASE_URL")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI()
bot = Bot(token=TOKEN)
application: Application = ApplicationBuilder().token(TOKEN).build()

async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("שלום! הבוט עובד")

application.add_handler(CommandHandler("start", start_cmd))

WEBHOOK_PATH = f"/webhook/{TOKEN}"

@app.on_event("startup")
async def on_startup():
    logger.info("startup: initializing telegram application")
    await application.initialize()
    await application.start()
    # schedule webhook setup in background so startup is fast
    if BASE_URL:
        asyncio.create_task(set_webhook_background())

async def set_webhook_background():
    try:
        webhook_url = f"{BASE_URL}{WEBHOOK_PATH}"
        logger.info("Setting webhook to %s", webhook_url)
        result = await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("set_webhook result: %s", result)
    except Exception:
        logger.exception("Failed to set webhook in background")

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request):
    data = await request.json()
    update = Update.de_json(data, bot)
    # process update quickly; consider creating background tasks for heavy work
    await application.process_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"ok": True, "status": "running"}
