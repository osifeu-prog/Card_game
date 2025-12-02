# backend/ton_watcher.py
import asyncio
import os
import logging
from dotenv import load_dotenv
from pytonapi import AsyncTonapi

def from_nano(amount: int, decimals: int = 9) -> float:
    return amount / (10 ** decimals)

load_dotenv()

TON_API_KEY = os.getenv("TON_API_KEY")
GAME_WALLET_ADDRESS = os.getenv("GAME_WALLET_ADDRESS")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# יצירת לקוח TON API אסינכרוני
tonapi = AsyncTonapi(api_key=TON_API_KEY)

async def check_payment(address: str, amount_nano: int) -> bool:
    try:
        # קבלת העסקאות האחרונות בארנק המשחק
        transactions = await tonapi.accounts.get_transactions(
            account_id=GAME_WALLET_ADDRESS,
            limit=10
        )

        for tx in transactions.transactions:
            if tx.in_msg and tx.in_msg.source and tx.in_msg.source.account_id == address:
                received_amount_nano = int(tx.in_msg.value)
                if received_amount_nano == amount_nano:
                    logging.info(f"Payment confirmed! Sender: {address}, Amount: {from_nano(amount_nano)} TON")
                    return True
        return False
    except Exception as e:
        logging.error(f"Error checking TON payment: {e}")
        return False

async def monitor_ton_payments(user_id: int, required_ton_amount: float):
    required_nano_amount = int(required_ton_amount * 10**9)
    # כאן תצטרך לקבל את הארנק של המשתמש מה־DB או מה־Webhook
    user_wallet_address = "EQD4sZ3S1vjB8497L46fH0t_F1E1Xh613W5o93tF9Rz2Xq5T"

    logging.info(f"Monitoring TON payment for User {user_id}: {required_ton_amount} TON from {user_wallet_address}")
    is_paid = await check_payment(user_wallet_address, required_nano_amount)

    if is_paid:
        logging.info(f"TON Payment confirmed for User {user_id}.")
    else:
        logging.warning(f"TON Payment NOT found for User {user_id}.")
    return is_paid
