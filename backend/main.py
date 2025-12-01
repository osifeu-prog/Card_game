from fastapi import FastAPI, Request, HTTPException
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram_handler import start_command, button_callback
from ton_watcher import monitor_ton_payments
import asyncio
import os

# --- הגדרות ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_PATH = "/webhook"

# --- איתחול FastAPI ---
app = FastAPI()

# --- איתחול Telegram Application ---
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CallbackQueryHandler(button_callback)) # לחיצות כפתורים


@app.on_event("startup")
async def startup_event():
    """מריץ את ה-TON Watcher ברקע כש FastAPI עולה."""
    print("FastAPI עולה. מריץ את ה-TON Watcher ב-Background.")
    asyncio.create_task(monitor_ton_payments())
    
    # הגדרת ה-Webhook לטלגרם (בפריסה אמיתית, כדאי להגדיר פעם אחת)
    webhook_url = os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("RAILWAY_URL")
    if webhook_url:
        await application.bot.set_webhook(f"{webhook_url}{WEBHOOK_PATH}")
        print(f"Webhook הוגדר בהצלחה ל- {webhook_url}{WEBHOOK_PATH}")


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """מקבל עדכונים מטלגרם ומעביר אותם ל-Handler."""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN אינו מוגדר.")
        
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"message": "OK"}
