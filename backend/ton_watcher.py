"""
TON Watcher - מעקב אחרי טרנזקציות ב-TON Blockchain
"""
import asyncio
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class TONWatcher:
    """מחלקה למעקב אחרי ארנק TON וטרנזקציות"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        אתחול TON Watcher
        
        Args:
            api_key: API key עבור TON API (אופציונלי)
        """
        self.api_key = api_key or os.getenv("TON_API_KEY")
        self.base_url = "https://toncenter.com/api/v2"
        self.is_watching = False
        self.watched_addresses: Dict[str, Dict[str, Any]] = {}
        
        if not self.api_key:
            logger.warning("TON_API_KEY not set. TON watching functionality will be limited.")
    
    async def get_wallet_info(self, address: str) -> Optional[Dict[str, Any]]:
        """
        קבלת מידע על ארנק TON
        
        Args:
            address: כתובת הארנק
            
        Returns:
            מידע על הארנק או None במקרה של שגיאה
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["X-API-Key"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/getAddressInformation",
                    params={"address": address},
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return data.get("result", {})
                    else:
                        logger.error(f"TON API error: {data.get('error')}")
                else:
                    logger.error(f"HTTP error {response.status_code} when fetching wallet info")
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout when fetching wallet info for {address}")
        except Exception as e:
            logger.error(f"Error fetching wallet info: {e}", exc_info=True)
        
        return None
    
    async def get_transactions(
        self, 
        address: str, 
        limit: int = 10,
        lt: Optional[int] = None,
        hash: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        קבלת טרנזקציות של ארנק
        
        Args:
            address: כתובת הארנק
            limit: מספר טרנזקציות מקסימלי
            lt: logical time של הטרנזקציה האחרונה (לפגינציה)
            hash: hash של הטרנזקציה האחרונה (לפגינציה)
            
        Returns:
            רשימת טרנזקציות
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["X-API-Key"] = self.api_key
                
                params = {
                    "address": address,
                    "limit": limit
                }
                
                if lt:
                    params["lt"] = lt
                if hash:
                    params["hash"] = hash
                
                response = await client.get(
                    f"{self.base_url}/getTransactions",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return data.get("result", [])
                    else:
                        logger.error(f"TON API error: {data.get('error')}")
                else:
                    logger.error(f"HTTP error {response.status_code} when fetching transactions")
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout when fetching transactions for {address}")
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}", exc_info=True)
        
        return []
    
    def add_watched_address(
        self, 
        address: str, 
        callback, 
        poll_interval: int = 30
    ):
        """
        הוספת ארנק למעקב
        
        Args:
            address: כתובת הארנק
            callback: פונקציה שתופעל בעת טרנזקציה חדשה
            poll_interval: מרווח זמן בשניות בין בדיקות
        """
        self.watched_addresses[address] = {
            "callback": callback,
            "poll_interval": poll_interval,
            "last_lt": None,
            "last_hash": None
        }
        logger.info(f"Added address {address} to watch list")
    
    def remove_watched_address(self, address: str):
        """הסרת ארנק מהמעקב"""
        if address in self.watched_addresses:
            del self.watched_addresses[address]
            logger.info(f"Removed address {address} from watch list")
    
    async def start_watching(self):
        """התחלת מעקב אחרי כל הארנקים הרשומים"""
        if self.is_watching:
            logger.warning("Watcher is already running")
            return
        
        self.is_watching = True
        logger.info("Starting TON watcher...")
        
        # יצירת task לכל ארנק
        tasks = []
        for address in self.watched_addresses:
            task = asyncio.create_task(self._watch_address(address))
            tasks.append(task)
        
        # המתנה לכל ה-tasks
        if tasks:
            await asyncio.gather(*tasks)
    
    async def stop_watching(self):
        """עצירת המעקב"""
        self.is_watching = False
        logger.info("Stopping TON watcher...")
    
    async def _watch_address(self, address: str):
        """
        מעקב אחרי ארנק בודד
        
        Args:
            address: כתובת הארנק
        """
        watch_data = self.watched_addresses[address]
        callback = watch_data["callback"]
        poll_interval = watch_data["poll_interval"]
        
        logger.info(f"Started watching address: {address}")
        
        # קבלת הטרנזקציה האחרונה כנקודת התחלה
        initial_txs = await self.get_transactions(address, limit=1)
        if initial_txs:
            watch_data["last_lt"] = initial_txs[0].get("transaction_id", {}).get("lt")
            watch_data["last_hash"] = initial_txs[0].get("transaction_id", {}).get("hash")
        
        while self.is_watching and address in self.watched_addresses:
            try:
                # קבלת טרנזקציות חדשות
                new_txs = await self.get_transactions(address, limit=10)
                
                # סינון טרנזקציות חדשות
                if new_txs and watch_data["last_lt"]:
                    new_transactions = []
                    for tx in new_txs:
                        tx_lt = tx.get("transaction_id", {}).get("lt")
                        if tx_lt and tx_lt > watch_data["last_lt"]:
                            new_transactions.append(tx)
                    
                    # קריאה ל-callback עבור כל טרנזקציה חדשה
                    for tx in reversed(new_transactions):  # מהישנה לחדשה
                        try:
                            await callback(address, tx)
                        except Exception as e:
                            logger.error(f"Error in transaction callback: {e}", exc_info=True)
                    
                    # עדכון last_lt
                    if new_transactions:
                        watch_data["last_lt"] = new_transactions[-1].get("transaction_id", {}).get("lt")
                        watch_data["last_hash"] = new_transactions[-1].get("transaction_id", {}).get("hash")
                
            except Exception as e:
                logger.error(f"Error watching address {address}: {e}", exc_info=True)
            
            # המתנה לפני הבדיקה הבאה
            await asyncio.sleep(poll_interval)
        
        logger.info(f"Stopped watching address: {address}")
    
    @staticmethod
    def format_transaction(tx: Dict[str, Any]) -> str:
        """
        פורמט טרנזקציה להצגה
        
        Args:
            tx: נתוני הטרנזקציה
            
        Returns:
            מחרוזת מעוצבת של הטרנזקציה
        """
        tx_id = tx.get("transaction_id", {})
        in_msg = tx.get("in_msg", {})
        out_msgs = tx.get("out_msgs", [])
        
        # זמן
        utime = tx.get("utime", 0)
        time_str = datetime.fromtimestamp(utime).strftime("%Y-%m-%d %H:%M:%S") if utime else "Unknown"
        
        # סכום
        value = int(in_msg.get("value", 0)) / 1_000_000_000  # המרה מ-nanoton ל-TON
        
        # פורמט
        result = f"🔔 *טרנזקציה חדשה*\n\n"
        result += f"⏰ זמן: {time_str}\n"
        result += f"💰 סכום: {value:.2f} TON\n"
        result += f"📝 Hash: `{tx_id.get('hash', 'N/A')[:16]}...`\n"
        
        if in_msg.get("source"):
            result += f"📤 מאת: `{in_msg['source'][:8]}...{in_msg['source'][-8:]}`\n"
        
        if out_msgs:
            result += f"📥 אל: `{out_msgs[0].get('destination', 'N/A')[:8]}...`\n"
        
        return result


# דוגמה לשימוש
async def example_callback(address: str, transaction: Dict[str, Any]):
    """דוגמה לפונקציית callback"""
    logger.info(f"New transaction for {address}:")
    logger.info(TONWatcher.format_transaction(transaction))


# פונקציה עזר להפעלת watcher
async def start_ton_watcher(addresses: List[str], callback):
    """
    הפעלת watcher עבור רשימת ארנקים
    
    Args:
        addresses: רשימת כתובות ארנקים
        callback: פונקציה לטיפול בטרנזקציות
    """
    watcher = TONWatcher()
    
    for address in addresses:
        watcher.add_watched_address(address, callback, poll_interval=30)
    
    await watcher.start_watching()
