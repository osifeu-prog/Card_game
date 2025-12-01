import asyncio
import os
import logging
from typing import Optional, List
from pytonlib import Address # התיקון הקריטי: Address מיובא ישירות מ-pytonlib
from pytonlib.utils.numbers import from_nano
from pytonapi import Tonapi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TON_API_KEY = os.getenv("TON_API_KEY")
GAME_WALLET_ADDRESS = os.getenv("GAME_WALLET_ADDRESS")
TON_TESTNET_ENDPOINT = os.getenv("TON_TESTNET_ENDPOINT")

# Initialize TON API client
try:
    TON_CLIENT = Tonapi(api_key=TON_API_KEY, is_testnet=True)
except Exception as e:
    logging.error(f"Failed to initialize TONAPI client: {e}")
    TON_CLIENT = None

# Logger setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def check_payment(address: str, amount_nano: int, min_conf_blocks: int = 1) -> bool:
    """
    Checks if a payment of a specific amount has been received by the game wallet.

    :param address: The address of the sender (user's wallet).
    :param amount_nano: The required payment amount in nanoTON.
    :param min_conf_blocks: Minimum number of blocks to confirm transaction.
    :return: True if payment is confirmed, False otherwise.
    """
    if not TON_CLIENT or not GAME_WALLET_ADDRESS:
        logging.error("TON client or GAME_WALLET_ADDRESS not configured.")
        return False

    try:
        # Get the latest transactions for the game wallet
        transactions = await TON_CLIENT.accounts.get_transactions(
            account_id=GAME_WALLET_ADDRESS,
            limit=10, # Check the last 10 transactions
            accept_data_camel=True
        )

        for tx in transactions.transactions:
            # Check for incoming messages
            if tx.in_msg and tx.in_msg.source and tx.in_msg.source.account_id == address:
                # Check for the required amount (with a small buffer for gas fees if needed, 
                # but we usually check the exact amount)
                received_amount_nano = int(tx.in_msg.value)
                
                # Check if amount matches exactly
                if received_amount_nano == amount_nano:
                    logging.info(f"Payment confirmed! Sender: {address}, Amount: {from_nano(amount_nano, 9)} TON")
                    return True

        return False

    except Exception as e:
        logging.error(f"Error checking TON payment: {e}")
        return False

async def monitor_ton_payments(user_id: int, required_ton_amount: float):
    """
    Simulates monitoring the TON blockchain for a specific user payment.
    In a real app, this would integrate with the database to check pending payments.

    :param user_id: The ID of the user expecting the payment.
    :param required_ton_amount: The required amount in TON (not nano).
    :return: True if payment is confirmed.
    """
    # Convert TON to nanoTON for API use
    required_nano_amount = int(required_ton_amount * 10**9)
    # Placeholder: In a real app, you would retrieve the user's TON wallet address from DB.
    # For demonstration, let's assume the user's address is known or passed.
    # We will use a dummy address for the sake of the example function signature.
    user_wallet_address = "EQD4sZ3S1vjB8497L46fH0t_F1E1Xh613W5o93tF9Rz2Xq5T" # Example address

    logging.info(f"Monitoring TON payment for User {user_id}: {required_ton_amount} TON from {user_wallet_address}")
    
    # Check for payment (we only check once here, but real monitoring is a loop)
    is_paid = await check_payment(user_wallet_address, required_nano_amount)

    if is_paid:
        logging.info(f"TON Payment confirmed for User {user_id}.")
    else:
        logging.warning(f"TON Payment NOT found for User {user_id}.")
        
    return is_paid

if __name__ == '__main__':
    # Example usage (for testing outside the main application)
    # Note: Replace with actual logic when integrated into the FastAPI app
    # asyncio.run(monitor_ton_payments(user_id=12345, required_ton_amount=0.5))
    logging.info("ton_watcher is ready.")
