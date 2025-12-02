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
TON_TESTNET_ENDPOINT = os.getenv("TON_TESTNET_ENDPOINT", "https://testnet.tonapi.io")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

tonapi = AsyncTonapi(api_key=TON_API_KEY, base_url=TON_TESTNET_ENDPOINT)

async def check_payment(address: str, amount_nano: int) -> bool:
    logging.debug(f"Checking payment from {address} for {amount_nano} nanoTON")
    try:
        transactions = await tonapi.accounts.get_transactions(
            account_id=GAME_WALLET_ADDRESS,
            limit=20
        )
        logging.debug(f"Fetched {len(transactions.transactions)} transactions")

        for tx in transactions.transactions:
            logging.debug(f"Inspecting transaction: {tx}")
            if tx.in_msg and tx.in_msg.source and tx.in_msg.source.account_id == address:
                received_amount_nano = int(tx.in_msg.value)
                logging.debug(f"Transaction from {address} with amount {received_amount_nano}")
                if received_amount_nano == amount_nano:
                    logging.info(f"Payment confirmed! Sender: {address}, Amount: {from_nano(amount_nano)} TON")
                    return True
        return False
    except Exception as e:
        logging.exception("Error checking TON payment")
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
    logging.debug("ton_watcher is ready.")
    asyncio.run(monitor_ton_payments(user_id=12345, required_ton_amount=0.5))
