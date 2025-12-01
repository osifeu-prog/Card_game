from fastapi import FastAPI, Request, HTTPException
# 🚨 תיקון קריטי: ייבוא Update
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram_handler import start_command, button_callback, debug_id_command
from ton_watcher import monitor_ton_payments
import asyncio
import os

# --- הגדרות ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_PATH = "/webhook"

# --- איתחול FastAPI ---
app = FastAPI()

# --- איתחול Telegram Application ---
if not TELEGRAM_BOT_TOKEN:
    # מונע קריסה אם ה-TOKEN לא מוגדר
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables.")

# בונה את אובייקט היישום של הבוט
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# הוספת ה-Handlers
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("getid", debug_id_command)) # פקודת הדיבוג החדשה
application.add_handler(CallbackQueryHandler(button_callback)) 


@app.on_event("startup")
async def startup_event():
    """מריץ את ה-TON Watcher ברקע ומגדיר את ה-Webhook."""
    
    # הפעלת ה-TON Watcher במקביל לשרת
    print("FastAPI עולה. מריץ את ה-TON Watcher ב-Background.")
    asyncio.create_task(monitor_ton_payments())
    
    # הגדרת ה-Webhook לטלגרם
    # Railway מספקת RAILWAY_STATIC_URL או RAILWAY_URL
    webhook_base_url = os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("RAILWAY_URL")
    
    if webhook_base_url:
        webhook_url = f"{webhook_base_url}{WEBHOOK_PATH}"
        await application.bot.set_webhook(webhook_url)
        print(f"Webhook הוגדר בהצלחה ל- {webhook_url}")
    else:
        print("אזהרה: RAILWAY_URL לא הוגדר. Webhook לא הוגדר אוטומטית.")


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """מקבל עדכונים מטלגרם ומעביר אותם ל-Handler."""
    # בדיקת האם הבוט אכן נוצר
    if not application.bot:
        raise HTTPException(status_code=500, detail="Telegram bot not initialized.")
        
    # קבלת ה-Update והעברתו ללוגיקה של python-telegram-bot
    # זה דורש ש-telegram.Update ייוצא בראש הקובץ
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"message": "OK"}
