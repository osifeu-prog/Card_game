import asyncio
import logging
from dotenv import load_dotenv
import os

# פונקציה מקומית במקום pytonlib
def from_nano(amount: int, decimals: int = 9) -> float:
    return amount / (10 ** decimals)

load_dotenv()

GAME_WALLET_ADDRESS = os.getenv("GAME_WALLET_ADDRESS")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# פונקציה מדומה – במקום pytonapi
async def check_payment(address: str, amount_nano: int) -> bool:
    logging.info(f"Stub check_payment called for address={address}, amount={amount_nano}")
    # כאן אפשר להוסיף לוגיקה אמיתית בעתיד
    return True  # כרגע תמיד מחזיר הצלחה

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
