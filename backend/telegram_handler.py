# python-telegram-bot משתמש ב-Handler כדי לטפל בפקודות
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

# --- קבועים ---
GAME_WALLET_ADDRESS = os.environ.get("GAME_WALLET_ADDRESS", "UQ...TESTNET_ADDRESS")
COST_LEVEL_1 = 0.5  # TON

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """מענה לפקודה /start והצגת רמה 0"""
    
    # **TODO 1: עדכון DB** - שמור user_id ב-DB עם level=0
    
    keyboard = [
        [InlineKeyboardButton("הצג קלף בסיסי", callback_data='view_basic_card')],
        [InlineKeyboardButton(f"שדרג לרמה 1 ({COST_LEVEL_1} TON) 🔒", callback_data='upgrade_level_1')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"שלום {update.effective_user.first_name}!\nברוכים הבאים למשחק ה-NFT של TON.\nאתה כרגע ברמה 0.",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """טיפול בלחיצות על כפתורים"""
    query = update.callback_query
    await query.answer() # חיוני לסגור את חלון הטעינה של טלגרם
    
    if query.data == 'upgrade_level_1':
        # **TODO 2: לוגיקת חשבונית** - קריאה ל-ton_watcher.generate_invoice
        
        # כתובת תשלום זמנית (צריך להיות כתובת ה-Contract שלך)
        memo = f"LEVEL1_{query.from_user.id}"
        invoice_url = f"https://wallet.tonkeeper.com/transfer/{GAME_WALLET_ADDRESS}?amount={COST_LEVEL_1}&text={memo}"

        keyboard = [
            [InlineKeyboardButton("שלם באמצעות Tonkeeper 💎", url=invoice_url)],
            [InlineKeyboardButton("אישרתי את התשלום ✅", callback_data='check_payment')] # כפתור סרק, יטופל אוטומטית על ידי ה-Watcher
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"כדי לפתוח את רמה 1, אנא שלח **{COST_LEVEL_1} TON** לכתובת:\n`{GAME_WALLET_ADDRESS}`\nעם ה-Memo הייחודי: `{memo}`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # **TODO 3: טיפול בכפתורים נוספים** - לוגיקה לרמות 1-30.
