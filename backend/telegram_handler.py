import os
import logging
import requests
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None

def send_message(chat_id: int, text: str):
    """
    שולח הודעה חזרה ל-Telegram API
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, json=payload)
        logging.info(f"Sent message to {chat_id}: {text} (status {r.status_code})")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

def handle_message(message: dict):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    logging.info(f"Received message from chat {chat_id}: {text}")

    if "/start" in text:
        response = "Welcome to TON NFT Card Game! Use /buy to start or /status."
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
            send_message(chat_id, response)
        except Exception as e:
            logging.error(f"Error preparing purchase instruction: {e}")
            send_message(chat_id, "An error occurred while preparing your purchase. Please try again later.")

    elif "/check_payment" in text:
        # בדיקה אמיתית מול TON API
        try:
            is_paid = asyncio.run(monitor_ton_payments(chat_id, 0.5))
            if is_paid:
                send_message(chat_id, "✅ Payment confirmed! You can now access your NFT card.")
