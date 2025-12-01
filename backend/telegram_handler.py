import os
import logging
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# אין צורך ב-Address
from pytonlib.utils.numbers import from_nano

from ton_watcher import monitor_ton_payments

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GAME_WALLET_ADDRESS = os.getenv("GAME_WALLET_ADDRESS")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None

def handle_message(message: dict):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    logging.info(f"Received message from chat {chat_id}: {text}")

    if "/start" in text:
        response = "Welcome to TON NFT Card Game! Use /buy to start or /status."
        logging.info(f"Sending response to {chat_id}: {response}")
    elif "/buy" in text:
        try:
            user_id = chat_id
            required_amount = 0.5
            payment_address = GAME_WALLET_ADDRESS
            payment_amount = from_nano(int(required_amount * 10**9), 9)

            response = (
                f"Please send {payment_amount} TON to the game wallet address:\n"
                f"`{payment_address}`\n"
                "Once paid, use /check_payment."
            )
            logging.info(f"Instructed user {chat_id} to pay {payment_amount} TON.")
        except Exception as e:
            logging.error(f"Error preparing purchase instruction: {e}")
            response = "An error occurred while preparing your purchase. Please try again later."

        logging.info(f"Sending response to {chat_id}: {response}")

@app.post(f"/webhook/{TELEGRAM_BOT_TOKEN}")
async def telegram_webhook(update: TelegramUpdate):
    try:
        if update.message:
            handle_message(update.message)
        elif update.callback_query:
            logging.info(f"Received callback query: {update.callback_query}")
    except Exception as e:
        logging.error(f"Error handling Telegram update: {e}")
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"status": "Application Running", "service": "Card Game Backend"}
