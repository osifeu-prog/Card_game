import asyncio
import os
import logging
from pytonlib.utils.numbers import from_nano
from pytonapi import Tonapi
from dotenv import load_dotenv

load_dotenv()

TON_API_KEY = os.getenv("TON_API_KEY")
GAME_WALLET_ADDRESS = os.getenv("GAME_WALLET_ADDRESS")

try:
    TON_CLIENT = Tonapi(api_key=TON_API_KEY, is_testnet=True)
except Exception as e:
    logging.error(f"Failed to initialize TONAPI client: {e}")
    TON_CLIENT = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def check_payment(address: str, amount_nano: int) -> bool:
    if not TON_CLIENT or not GAME_WALLET_ADDRESS:
        logging.error("TON client or GAME_WALLET_ADDRESS not configured.")
        return False

    try:
        transactions = await TON_CLIENT.accounts.get_transactions(
            account_id=GAME_WALLET_ADDRESS,
            limit=10,
            accept_data_camel=True
        )

        for tx in transactions.transactions:
            if tx.in_msg and tx.in_msg.source and tx.in_msg.source.account_id == address:
                received_amount_nano = int(tx.in_msg.value)
                if received_amount_nano == amount_nano:
                    logging.info(f"Payment confirmed! Sender: {address}, Amount: {from_nano(amount_nano, 9)} TON")
                    return True
        return False
    except Exception as e:
        logging.error(f"Error checking TON payment: {e}")
        return False

async def monitor_ton_payments(user_id: int, required_ton_amount: float):
    required_nano_amount = int(required_ton_amount * 10**9)
    user_wallet_address = "EQD4sZ3S1vjB8497L46fH0t_F1E1Xh613W5o93tF9Rz2Xq5T"

    logging.info(f"Monitoring TON payment for User {user_id}: {required_ton_amount} TON from {user_wallet_address}")
    is_paid = await check_payment(user_wallet_address, required_nano_amount)

    if is_paid:
        logging.info(f"TON Payment confirmed for User {user_id}.")
    else:
        logging.warning(f"TON Payment NOT found for User {user_id}.")
    return is_paid

if __name__ == "__main__":
    logging.info("ton_watcher is ready.")
