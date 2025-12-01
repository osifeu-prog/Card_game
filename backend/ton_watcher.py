# ton_watcher.py

import os
import asyncio
from aiotonsdk.ton.client import TonClient # הלקוח של aiotonsdk
from aiotonsdk.ton.exceptions import CellBuildError

TON_API_KEY = os.environ.get("TON_API_KEY") # לא חובה ל-aiotonsdk, משתמשים ב-HTTP API של TON
TON_TESTNET_ENDPOINT = os.environ.get("TON_TESTNET_ENDPOINT", "https://testnet.toncenter.com/api/v2/jsonRPC")
GAME_WALLET_ADDRESS = os.environ.get("GAME_WALLET_ADDRESS")

async def monitor_ton_payments():
    """פונקציה שתרוץ ברקע ותנטר את כתובת ה-Game Wallet."""
    
    if not GAME_WALLET_ADDRESS:
        print("TON Watcher: חסרים משתני סביבה. הניטור מושעה.")
        return 

    # איתחול ה-Client של TON
    ton_client = TonClient(base_url=TON_TESTNET_ENDPOINT)
    
    print("TON Watcher: מתחיל ניטור טרנזקציות בכתובת המשחק...")
    
    while True:
        try:
            # TODO 4: קריאה ל-API - שימוש ב-aiotonsdk לקבלת טרנזקציות
            
            # (בדיקת שיוך טרנזקציות)
            transactions = await ton_client.get_transactions(
                address=GAME_WALLET_ADDRESS, limit=10
            )

            print(f"בדיקת {len(transactions)} טרנזקציות אחרונות בכתובת: {GAME_WALLET_ADDRESS}")

            # ... כאן תתבצע לוגיקת האימות (TODO 5)
            
            await asyncio.sleep(10) # בדיקה כל 10 שניות
            
        except Exception as e:
            print(f"TON Watcher Error: {e}")
            await asyncio.sleep(60)
