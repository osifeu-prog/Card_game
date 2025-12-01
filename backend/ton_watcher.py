import os
import asyncio
# הייבוא הנכון, ככל הנראה (השתמש ב-T גדולה)
from pytonapi import Tonapi
# זה עדיין נשאר בתור שלד, אבל נשתמש ב-Tonapi כעת

TON_API_KEY = os.environ.get("TON_API_KEY")
TON_TESTNET_ENDPOINT = os.environ.get("TON_TESTNET_ENDPOINT")
GAME_WALLET_ADDRESS = os.environ.get("GAME_WALLET_ADDRESS")

async def monitor_ton_payments():
    """פונקציה שתרוץ ברקע ותנטר את כתובת ה-Game Wallet."""
    
    if not TON_API_KEY or not GAME_WALLET_ADDRESS:
        print("TON Watcher: חסרים משתני סביבה. הניטור מושעה.")
        return 

    # איתחול ה-API של TON
    # השתמש ב-is_testnet=True ובכתובת ה-endpoint שסיפקת
    tonapi = Tonapi(api_key=TON_API_KEY, is_testnet=True, url=TON_TESTNET_ENDPOINT)
    
    print("TON Watcher: מתחיל ניטור טרנזקציות בכתובת המשחק...")
    
    while True:
        try:
            # בדיקה פשוטה של ה-API
            transactions = await tonapi.blockchain.get_account_transactions(
                account=GAME_WALLET_ADDRESS, limit=10
            )
            print(f"בדיקת {len(transactions)} טרנזקציות אחרונות בכתובת: {GAME_WALLET_ADDRESS}")

            # ... כאן תתבצע לוגיקת האימות (TODO 5)
            
            await asyncio.sleep(10) # בדיקה כל 10 שניות
            
        except Exception as e:
            # שגיאת API או שגיאת חיבור
            print(f"TON Watcher Error: {e}")
            await asyncio.sleep(60)
