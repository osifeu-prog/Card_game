import os
import logging
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# התיקון הקריטי, בהנחה שזהו מקור השגיאה בקובץ זה:
# במקום 'from pytonlib.address import Address'
from pytonlib import Address 
from pytonlib.utils.numbers import from_nano

# יבוא פנימי של לוגיקת TON (בהנחה ש-main.py מייבא את זה)
from .ton_watcher import monitor_ton_payments

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_URL")
GAME_WALLET_ADDRESS = os.getenv("GAME_WALLET_ADDRESS")

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# FastAPI app instance (assuming this handler is part of the main app)
app = FastAPI()

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None

def handle_message(message: dict):
    """Handles incoming Telegram messages."""
    chat_id = message['chat']['id']
    text = message.get('text', '')
    logging.info(f"Received message from chat {chat_id}: {text}")
    
    # Placeholder logic for the card game bot
    if '/start' in text:
        # Example response to the user
        response = "Welcome to TON NFT Card Game! Use /buy to start or /status."
        # In a real app, you would send this response back via Telegram API
        logging.info(f"Sending response to {chat_id}: {response}")
    elif '/buy' in text:
        # Simulate triggering the TON watcher for a payment
        try:
            # We'd ideally store a mapping of user_id to their TON address here
            user_id = chat_id # Using chat_id as user_id for simplicity
            required_amount = 0.5 # Example purchase amount
            
            # Since this is a FastAPI handler, we don't block the event loop
            # The actual monitoring should happen in a background task, 
            # but we can call the core logic here for demonstration purposes.
            # In production, this would queue a job for a worker process.

            # NOTE: We can't await an async function inside a sync handler easily,
            # so for a simple webhook, this part needs careful design (e.g., background tasks).
            # For now, we simulate the instruction given to the user.
            
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
    """Handles incoming updates from Telegram via webhook."""
    try:
        if update.message:
            handle_message(update.message)
        elif update.callback_query:
            # Handle callback queries if any
            logging.info(f"Received callback query: {update.callback_query}")
            pass
            
    except Exception as e:
        logging.error(f"Error handling Telegram update: {e}")
        # Telegram expects a 200 OK response even on internal errors
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"status": "Application Running", "service": "Card Game Backend"}

# NOTE: The setup of the webhook itself (calling Telegram API to set the URL) 
# is typically done on application startup, but the function above is the handler.
