import os
import logging
import requests
import asyncio
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from ton_watcher import monitor_ton_payments

# פונקציה מקומית להמרת nano ל-TON
def from_nano(amount: int, decimals: int = 9) -> float:
    return amount / (10 ** decimals)

# טעינת משתני סביבה
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GAME_WALLET_ADDRESS = os.getenv("GAME_WALLET_ADDRESS")

# הגדרת לוגים עם דיבוג מלא
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None

def send_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    logging.debug(f"Sending payload: {payload}")
    try:
        r = requests.post(url, json=payload)
        logging.info(f"Sent message to {chat_id}: {text} (status {r.status_code})")
        logging.debug(f"Telegram response: {r.text}")
    except Exception as e:
        logging.exception("Failed to send message")

def handle_message(message: dict):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    logging.debug(f"Raw message object: {message}")
    logging.info(f"Received message from chat {chat_id}: {text}")

    if "/start" in text:
        response = "Welcome to TON NFT Card Game! Use /buy to start or /status."
        logging.debug(f"Responding to /start with: {response}")
        send_message(chat_id, response)

    elif "/buy" in text:
        try:
            required_amount = 0.5
            payment_address = GAME_WALLET_ADDRESS
            payment_amount = from_nano(int(required_amount * 10**9), 9)

            response = (
                f"Please send {payment_amount} TON to the game wallet address:\n"
                f"{payment_address}\n"
                "Once paid, use /check_payment."
            )
            logging.debug(f"Responding to /buy with: {response}")
            send_message(chat_id, response)
        except Exception as e:
            logging.exception("Error preparing purchase instruction")
            send_message(chat_id, "An error occurred while preparing your purchase. Please try again later.")

    elif "/check_payment" in text:
        try:
            logging.debug("Starting payment check via TON API")
            is_paid = asyncio.run(monitor_ton_payments(chat_id, 0.5))
            logging.debug(f"Payment check result: {is_paid}")
            if is_paid:
                send_message(chat_id, "✅ Payment confirmed! You can now access your NFT card.")
            else:
                send_message(chat_id, "❌ Payment not found yet. Please try again later.")
        except Exception as e:
            logging.exception("Error checking payment")
            send_message(chat_id, "An error occurred while checking your payment.")

@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdate):
    logging.debug(f"Incoming webhook update: {update.dict()}")
    try:
        if update.message:
            handle_message(update.message)
        elif update.callback_query:
            logging.info(f"Received callback query: {update.callback_query}")
    except Exception as e:
        logging.exception("Error handling Telegram update")
        return {"status": "error", "message": str(e)}

    logging.debug("Webhook processed successfully, returning OK")
    return {"status": "ok"}

@app.get("/")
def read_root():
    logging.debug("Root endpoint called")
    return {"status": "Application Running", "service": "Card Game Backend"}
