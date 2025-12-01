from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

# --- לוגיקת משחק ---
# כרגע רק לוגיקה פשוטה, תושלם בהמשך

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """מענה לפקודה /start ושולח הודעת קבלת פנים."""
    
    # בדיקה אם יש ID למשתמש (לא אמור להיכשל, אבל לוודאות)
    chat_id = update.effective_chat.id
    if not chat_id:
        await update.message.reply_text("שגיאה: לא ניתן לזהות את הצ'אט ID.")
        return
        
    # כפתור לדוגמה
    keyboard = [[InlineKeyboardButton("התחל משחק", callback_data='start_game')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = (
        f"שלום! אני בוט משחק הקלפים של TON.\n\n"
        f"כדי לשחק, תצטרך לשלוח סכום מינימלי של TON לכתובת המשחק שלנו.\n"
        f"אנא לחץ על 'התחל משחק' כדי לראות את הכתובת."
    )
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def debug_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """פקודת דיבוג: מחזירה את ה-ID של המשתמש."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    message = (
        f"שלום! הנה פרטי ה-ID שלך:\n"
        f"**Chat ID:** `{chat_id}`\n"
        f"**User ID:** `{user_id}`\n\n"
        f"נתונים אלה חיוניים לאיתור המשתמשים וניהול המשחק."
    )
    await update.message.reply_text(message, parse_mode='Markdown')


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """מטפל בלחיצות על כפתורים פנימיים."""
    query = update.callback_query
    await query.answer() # מסיר את מצב הטעינה
    
    data = query.data
    
    if data == 'start_game':
        game_address = os.environ.get("GAME_WALLET_ADDRESS", "כתובת ארנק לא הוגדרה")
        
        response_text = (
            "🚀 **מוכנים להתחיל!**\n\n"
            "כדי להצטרף לשולחן, אנא שלח **0.1 TON** (סכום מינימלי לדוגמה) לכתובת הבאה (Testnet):\n\n"
            f"`{game_address}`\n\n"
            "לאחר שהתשלום שלך יאושר על ידי הרשת, הבוט יעדכן אותך ותקבל את הקלפים שלך!"
        )
        
        await query.edit_message_text(text=response_text, parse_mode='Markdown')
    else:
        await query.edit_message_text(text=f"פעולה לא ידועה: {data}")
