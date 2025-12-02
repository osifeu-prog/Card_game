import os
import logging
import requests
import asyncio
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv

# ניסיון לייבא את monitor_ton_payments אם קיים
try:
    from ton_watcher import monitor_ton_payments
except Exception as e:
    monitor_ton_payments = None
    logging.warning(f"ton_watcher import failed: {e}")

# לוגים ברמת DEBUG
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# טעינת משתני סביבה
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GAME_WALLET_ADDRESS = os.getenv("GAME_WALLET_ADDRESS")

if not TELEGRAM_BOT_TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN is missing in environment")
if not GAME_WALLET_ADDRESS:
    logging.warning("GAME_WALLET_ADDRESS is missing in environment")

# יצירת ה־FastAPI app קודם לכל שימוש ב־app
app = FastAPI()

# Middleware לוגינג של כל בקשת HTTP
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.debug(f"HTTP request start: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception:
        logging.exception("Exception in request handling")
        raise
    logging.debug(f"HTTP request end: {request.method} {request.url} -> {response.status_code}")
    return response

# מודל גמיש לעדכוני Telegram
class TelegramUpdate(BaseModel):
    update_id: Optional[int] = None
    message: Optional[Dict[str, Any]] = None
    edited_message: Optional[Dict[str, Any]] = None
    channel_post: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None

# עוזר לשליחת הודעה ל־Telegram
def send_message(chat_id: int, text: str):
    if not TELEGRAM_BOT_TOKEN:
        logging.error("Cannot send message: TELEGRAM_BOT_TOKEN not set")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    logging.debug(f"send_message payload: {payload}")
    try:
        r = requests.post(url, json=payload, timeout=10)
        logging.info(f"Sent message to {chat_id}: status {r.status_code}")
        logging.debug(f"Telegram response: {r.text}")
    except Exception:
        logging.exception(f"Failed to send message to {chat_id}")

# המרת nano ל‑TON
def from_nano(amount: int, decimals: int = 9) -> float:
    return amount / (10 ** decimals)

# עיבוד הודעות טקסט
def handle_text_message(message: Dict[str, Any]):
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "")

    logging.debug(f"Raw message: {message}")
    logging.info(f"Incoming text from chat {chat_id}: {text}")

    if not chat_id:
        logging.error("Missing chat_id in message")
        return

    cmd = text.strip().lower()
    if cmd.startswith("/start"):
        reply = "Welcome to TON NFT Card Game! Use /buy to start or /check_payment."
        logging.debug(f"Reply to /start: {reply}")
        send_message(chat_id, reply)

    elif cmd.startswith("/buy"):
        required_amount_ton = 0.5
        if not GAME_WALLET_ADDRESS:
            send_message(chat_id, "Game wallet is not configured. Please try again later.")
            logging.error("GAME_WALLET_ADDRESS missing while handling /buy")
            return
        payment_amount_ton = from_nano(int(required_amount_ton * 10**9))
        reply = (
            f"Please send {payment_amount_ton} TON to the game wallet address:\n"
            f"{GAME_WALLET_ADDRESS}\n"
            "After payment, send /check_payment."
        )
        logging.debug(f"Reply to /buy: {reply}")
        send_message(chat_id, reply)

    elif cmd.startswith("/check_payment"):
        if monitor_ton_payments is None:
            logging.error("monitor_ton_payments is not available (import failed)")
            send_message(chat_id, "Payment checker is temporarily unavailable. Please try again later.")
            return
        try:
            logging.debug("Starting TON payment check...")
            is_paid = asyncio.run(monitor_ton_payments(user_id=chat_id, required_ton_amount=0.5))
            logging.debug(f"TON payment result for {chat_id}: {is_paid}")
            if is_paid:
                send_message(chat_id, "✅ Payment confirmed! You can now access your NFT card.")
            else:
                send_message(chat_id, "❌ Payment not found yet. Please try again later.")
        except Exception:
            logging.exception("Error while checking TON payment")
            send_message(chat_id, "An error occurred while checking your payment. Please try again later.")
    else:
        logging.debug("Message did not match any command. Sending help.")
        send_message(chat_id, "Unknown command. Use /start, /buy, or /check_payment.")

# GET healthcheck ל־/webhook כדי לבדוק בדפדפן
@app.get("/webhook")
def webhook_healthcheck():
    logging.debug("GET /webhook healthcheck called")
    return {"status": "ok", "message": "Webhook endpoint is alive"}

# POST לעדכוני Telegram
@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdate):
    logging.debug(f"POST /webhook payload: {update.dict()}")
    try:
        if update.message and isinstance(update.message, dict):
            if "text" in update.message:
                handle_text_message(update.message)
            else:
                logging.info("Received non-text message; ignoring.")
        elif update.edited_message:
            logging.info("Received edited_message; ignored.")
        elif update.channel_post:
            logging.info("Received channel_post; ignored.")
        elif update.callback_query and isinstance(update.callback_query, dict):
            logging.info(f"Received callback_query: {update.callback_query}")
        else:
            logging.info("Update did not match known structures; ignoring.")
    except Exception:
        logging.exception("Error handling Telegram update")
        return {"status": "error", "message": "internal error"}

    logging.debug("Webhook update processed successfully, returning OK")
    return {"status": "ok"}

# root endpoint
@app.get("/")
def root():
    logging.debug("GET / called")
    return {"status": "Application Running", "service": "Card Game Backend"}
