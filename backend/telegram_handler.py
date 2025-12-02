"""
Telegram Handler - ניהול handlers עבור הבוט
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

logger = logging.getLogger(__name__)


class TelegramHandlers:
    """מחלקה לניהול handlers של הבוט"""
    
    def __init__(self, application):
        self.application = application
        self._register_handlers()
    
    def _register_handlers(self):
        """רישום כל ה-handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("game", self.game_command))
        
        # Callback query handler למענה לכפתורים
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handlers
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message)
        )
        
        logger.info("All handlers registered successfully")
    
    async def start_command(self, update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
        """Handler לפקודת /start"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
        welcome_text = (
            f"שלום {user.first_name}! 👋\n\n"
            "🎴 ברוכים הבאים לבוט משחק הקלפים!\n\n"
            "השתמש ב-/game כדי להתחיל משחק חדש\n"
            "או ב-/help כדי לראות את כל הפקודות הזמינות."
        )
        
        # יצירת כפתורים
        keyboard = [
            [InlineKeyboardButton("🎮 התחל משחק", callback_data="start_game")],
            [InlineKeyboardButton("ℹ️ עזרה", callback_data="show_help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
        """Handler לפקודת /help"""
        help_text = (
            "📋 *פקודות זמינות:*\n\n"
            "/start - התחלת השיחה עם הבוט\n"
            "/help - הצגת הודעת עזרה זו\n"
            "/game - התחלת משחק חדש\n"
            "/status - בדיקת סטטוס הבוט\n\n"
            "🎴 *איך משחקים?*\n"
            "1. לחץ על /game להתחלת משחק\n"
            "2. בחר אפשרות מהתפריט\n"
            "3. תהנה מהמשחק! 🎉"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def status_command(self, update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
        """Handler לפקודת /status"""
        user = update.effective_user
        
        status_text = (
            "✅ *סטטוס הבוט*\n\n"
            f"👤 משתמש: {user.first_name}\n"
            f"🆔 ID: `{user.id}`\n"
            f"⚡ הבוט: פעיל ועובד\n"
            f"🔗 חיבור: תקין"
        )
        
        await update.message.reply_text(status_text, parse_mode="Markdown")
    
    async def game_command(self, update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
        """Handler לפקודת /game - התחלת משחק"""
        game_text = (
            "🎴 *משחק הקלפים*\n\n"
            "בחר אפשרות מהתפריט:"
        )
        
        keyboard = [
            [InlineKeyboardButton("🆕 משחק חדש", callback_data="new_game")],
            [InlineKeyboardButton("📊 הסטטיסטיקות שלי", callback_data="my_stats")],
            [InlineKeyboardButton("🏆 לוח מובילים", callback_data="leaderboard")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(game_text, parse_mode="Markdown", reply_markup=reply_markup)
    
    async def button_callback(self, update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
        """Handler לטיפול בלחיצות על כפתורים"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        logger.info(f"Button callback received: {callback_data}")
        
        if callback_data == "start_game":
            await self._handle_start_game(query)
        elif callback_data == "show_help":
            await self._handle_show_help(query)
        elif callback_data == "new_game":
            await self._handle_new_game(query)
        elif callback_data == "my_stats":
            await self._handle_my_stats(query)
        elif callback_data == "leaderboard":
            await self._handle_leaderboard(query)
        else:
            await query.edit_message_text("אפשרות לא מזוהה")
    
    async def _handle_start_game(self, query):
        """טיפול בלחיצה על כפתור התחל משחק"""
        text = "🎮 *משחק חדש*\n\nהמשחק מתחיל! בהצלחה! 🍀"
        await query.edit_message_text(text, parse_mode="Markdown")
    
    async def _handle_show_help(self, query):
        """טיפול בלחיצה על כפתור עזרה"""
        help_text = (
            "📋 *עזרה*\n\n"
            "זהו בוט למשחק קלפים.\n"
            "השתמש בפקודות השונות כדי לשחק ולנהל את המשחקים שלך."
        )
        await query.edit_message_text(help_text, parse_mode="Markdown")
    
    async def _handle_new_game(self, query):
        """התחלת משחק חדש"""
        text = "🆕 *משחק חדש נוצר!*\n\nהמשחק שלך מוכן. בהצלחה! 🎴"
        await query.edit_message_text(text, parse_mode="Markdown")
    
    async def _handle_my_stats(self, query):
        """הצגת סטטיסטיקות"""
        user = query.from_user
        stats_text = (
            f"📊 *הסטטיסטיקות של {user.first_name}*\n\n"
            "🎮 משחקים: 0\n"
            "🏆 ניצחונות: 0\n"
            "📉 הפסדים: 0\n"
            "⭐ דירוג: חדש"
        )
        await query.edit_message_text(stats_text, parse_mode="Markdown")
    
    async def _handle_leaderboard(self, query):
        """הצגת לוח מובילים"""
        leaderboard_text = (
            "🏆 *לוח המובילים*\n\n"
            "1. 👑 שחקן 1 - 100 נקודות\n"
            "2. 🥈 שחקן 2 - 85 נקודות\n"
            "3. 🥉 שחקן 3 - 70 נקודות\n\n"
            "המשך לשחק כדי להגיע לראש הטבלה! 💪"
        )
        await query.edit_message_text(leaderboard_text, parse_mode="Markdown")
    
    async def handle_text_message(self, update: Update, context: CallbackContext.DEFAULT_TYPE) -> None:
        """Handler להודעות טקסט רגילות"""
        user = update.effective_user
        text = update.message.text
        
        logger.debug(f"Text message from {user.id}: {text[:50]}...")
        
        # תגובה בסיסית
        response = f"קיבלתי את ההודעה: '{text[:100]}{'...' if len(text) > 100 else ''}'\n\n"
        response += "השתמש ב-/help כדי לראות את הפקודות הזמינות."
        
        await update.message.reply_text(response)
