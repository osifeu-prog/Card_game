import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# --- קבועים ---
# אלה צריכים להיות מוגדרים במשתני סביבה (ENV Vars) ב-Railway!
GAME_WALLET_ADDRESS = os.environ.get("GAME_WALLET_ADDRESS", "UQ...TESTNET_ADDRESS")
COST_LEVEL_1 = 0.5  # TON

# יש להחליף את זה ב-User ID האישי שלך לאחר שתקבל אותו מ-/getid
YOUR_OWN_USER_ID = 0 # הגדר כ-0 כברירת מחדל או השתמש ב-ENV Var

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """מענה לפקודה /start והצגת רמה 0"""
    
    # **TODO 1: עדכון DB** - שמור user_id ב-DB עם level=0 (עדיין לא מחובר ל-DB)
    
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
    await query.answer() 
    
    if query.data == 'upgrade_level_1':
        # **TODO 2: לוגיקת חשבונית** - קריאה ל-ton_watcher.generate_invoice
        
        # כתובת תשלום זמנית (צריך להיות כתובת ה-Contract שלך)
        memo = f"LEVEL1_{query.from_user.id}"
        # יצירת קישור ל-Tonkeeper עם פרטי התשלום
        invoice_url = f"https://wallet.tonkeeper.com/transfer/{GAME_WALLET_ADDRESS}?amount={COST_LEVEL_1}&text={memo}"

        keyboard = [
            [InlineKeyboardButton("שלם באמצעות Tonkeeper 💎", url=invoice_url)],
            [InlineKeyboardButton("אישרתי את התשלום ✅", callback_data='check_payment')] 
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"כדי לפתוח את רמה 1, אנא שלח **{COST_LEVEL_1} TON** לכתובת:\n`{GAME_WALLET_ADDRESS}`\nעם ה-Memo הייחודי: `{memo}`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# ===============================================
# פקודת DEBUG: לקבלת ID של משתמש, בוט וקבוצה
# ===============================================
async def debug_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """מענה לפקודה /getid ומספק נתונים קריטיים."""
    
    # בדיקת הרשאות (רק המשתמש הראשי יכול להריץ)
    # נשתמש ב-update.effective_user.id != int(YOUR_OWN_USER_ID) לאחר שתגדיר את זה ב-ENV
    
    chat_type = update.effective_chat.type
    
    # 1. מידע על השולח
    user_info = (
        f"**👤 המשתמש (אתה):**\n"
        f"   - User ID: `{update.effective_user.id}`\n"
        f"   - שם משתמש: @{update.effective_user.username or 'N/A'}\n"
    )
    
    # 2. מידע על הצ'אט/קבוצה
    chat_info = f"**💬 הצ'אט הנוכחי ({chat_type}):**\n"
    chat_id = update.effective_chat.id
    chat_info += f"   - Chat ID: `{chat_id}`\n"

    if chat_type in ["group", "supergroup"]:
        chat_info += (
            f"   - שם הקבוצה: {update.effective_chat.title}\n"
        )
    
    # 3. מידע על הבוט עצמו
    bot_me = await context.bot.get_me()
    bot_info = (
        f"**🤖 הבוט:**\n"
        f"   - Bot ID: `{bot_me.id}`\n"
        f"   - שם הבוט: @{bot_me.username}\n"
        f"   - Webhook URL (מהשרת): {context.bot.get_webhook_info().url}\n"
    )

    await update.message.reply_text(
        f"🛠️ **נתוני Debug קריטיים (העתק ושמור!)**\n\n{user_info}\n{chat_info}\n{bot_info}",
        parse_mode='Markdown'
    )
