import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
import re
from typing import Dict, Any

from config import *
from database import DatabaseManager
from auth_handler import AuthHandler
from task_handler import TaskHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

(WAITING_FOR_PHONE, WAITING_FOR_CODE, WAITING_FOR_2FA) = range(3)

class StarCollectorBot:
    def __init__(self):
        self.db = DatabaseManager(DATABASE_FILE)
        self.auth_handler = AuthHandler(API_ID, API_HASH)
        self.task_handler = TaskHandler(API_ID, API_HASH, TARGET_BOT)
        self.user_states: Dict[int, Dict[str, Any]] = {}
        
    def get_main_keyboard(self, user_id: int):
        user = self.db.get_user(user_id)
        buttons = []
        
        if not user or not user.get('session_string'):
            buttons.append([KeyboardButton(REGISTER_ACCOUNT)])
        else:
            if self.task_handler.is_user_collecting(user_id):
                buttons.append([KeyboardButton(STOP_COLLECTING)])
            else:
                buttons.append([KeyboardButton(START_COLLECTING)])
            buttons.append([KeyboardButton(ACCOUNT_STATUS)])
            
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.db.add_user(user_id)
        
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=self.get_main_keyboard(user_id)
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        
        if text == REGISTER_ACCOUNT:
            await self.start_registration(update, context)
        elif text == START_COLLECTING:
            await self.start_collection(update, context)
        elif text == STOP_COLLECTING:
            await self.stop_collection(update, context)
        elif text == ACCOUNT_STATUS:
            await self.show_account_status(update, context)
        else:
            user_state = self.user_states.get(user_id, {})
            state = user_state.get('state')
            
            if state == WAITING_FOR_PHONE:
                await self.process_phone(update, context)
            elif state == WAITING_FOR_CODE:
                await self.process_code(update, context)
            elif state == WAITING_FOR_2FA:
                await self.process_2fa(update, context)
            else:
                await update.message.reply_text(
                    "يرجى استخدام الأزرار المتاحة للتفاعل مع البوت.",
                    reply_markup=self.get_main_keyboard(user_id)
                )
    
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        user = self.db.get_user(user_id)
        if user and user.get('session_string'):
            await update.message.reply_text(
                "✅ أنت مسجل بالفعل! يمكنك بدء التجميع التلقائي.",
                reply_markup=self.get_main_keyboard(user_id)
            )
            return
        
        await self.auth_handler.cancel_auth(user_id)
        self.user_states[user_id] = {'state': WAITING_FOR_PHONE}
        await update.message.reply_text(PHONE_REQUEST)
    
    async def process_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        phone = update.message.text.strip()
        
        success, message = await self.auth_handler.start_auth(user_id, phone)
        
        if success:
            self.db.update_user_phone(user_id, phone)
            self.user_states[user_id] = {'state': WAITING_FOR_CODE}
            await update.message.reply_text(CODE_REQUEST)
        else:
            await update.message.reply_text(
                message + "\n\n" + PHONE_REQUEST,
                reply_markup=self.get_main_keyboard(user_id)
            )
    
    async def process_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        code = update.message.text.strip()
        
        success, message, session_string = await self.auth_handler.verify_code(user_id, code)
        
        if success:
            if session_string:
                self.db.update_user_session(user_id, session_string)
                self.user_states.pop(user_id, None)
                
                await update.message.reply_text(
                    REGISTRATION_SUCCESS,
                    reply_markup=self.get_main_keyboard(user_id)
                )
            else:
                self.user_states[user_id] = {'state': WAITING_FOR_2FA}
                await update.message.reply_text(TWO_FA_REQUEST)
        else:
            await update.message.reply_text(
                message + "\n\n" + CODE_REQUEST
            )
    
    async def process_2fa(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        password = update.message.text
        
        success, message, session_string = await self.auth_handler.verify_2fa(user_id, password)
        
        if success and session_string:
            self.db.update_user_session(user_id, session_string)
            self.user_states.pop(user_id, None)
            
            await update.message.reply_text(
                REGISTRATION_SUCCESS,
                reply_markup=self.get_main_keyboard(user_id)
            )
        else:
            await update.message.reply_text(
                message + "\n\n" + TWO_FA_REQUEST
            )
    
    async def start_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        user = self.db.get_user(user_id)
        if not user or not user.get('session_string'):
            await update.message.reply_text(
                "❌ يجب تسجيل حسابك أولاً!",
                reply_markup=self.get_main_keyboard(user_id)
            )
            return
        
        success, message = await self.task_handler.start_collection(user_id, user['session_string'])
        
        if success:
            self.db.set_auto_collect(user_id, True)
            
        await update.message.reply_text(
            message,
            reply_markup=self.get_main_keyboard(user_id)
        )
    
    async def stop_collection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        success, message = await self.task_handler.stop_collection(user_id)
        
        if success:
            self.db.set_auto_collect(user_id, False)
        
        await update.message.reply_text(
            message,
            reply_markup=self.get_main_keyboard(user_id)
        )
    
    async def show_account_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        user = self.db.get_user(user_id)
        if not user:
            await update.message.reply_text(
                "❌ لم يتم العثور على بيانات حسابك.",
                reply_markup=self.get_main_keyboard(user_id)
            )
            return
        
        stats = self.db.get_user_stats(user_id)
        settings = self.db.get_user_settings(user_id)
        
        status_text = f"""
📊 **حالة حسابك**

👤 **المعرف:** {user_id}
📱 **رقم الهاتف:** {user.get('phone_number', 'غير محدد')}
✅ **مسجل:** {'نعم' if user.get('session_string') else 'لا'}

⭐ **إجمالي النجوم:** {stats['total_stars']:.2f}
📈 **إجمالي المهام:** {stats['total_tasks']}
📅 **مهام اليوم:** {stats['today_tasks']}

🔄 **الحالة الحالية:** {'نشط' if self.task_handler.is_user_collecting(user_id) else 'متوقف'}
🔔 **التنبيهات:** {'مفعلة' if settings and settings.get('notifications') else 'معطلة'}

📅 **تاريخ التسجيل:** {user.get('created_at', 'غير محدد')}
🕒 **آخر نشاط:** {user.get('last_activity', 'غير محدد')}
        """
        
        await update.message.reply_text(
            status_text,
            reply_markup=self.get_main_keyboard(user_id),
            parse_mode='Markdown'
        )
    
    async def notify_user(self, user_id: int, message: str):
        try:
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=self.get_main_keyboard(user_id),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error {context.error}")
        
        if "bot was blocked by the user" in str(context.error):
            logger.info("User blocked the bot, skipping error message")
            return
            
        if update and update.effective_chat and update.message:
            try:
                await update.message.reply_text(
                    "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
                )
            except Exception as e:
                logger.error(f"Could not send error message: {e}")
    
    def setup_handlers(self, application):
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_error_handler(self.error_handler)
        
        self.application = application
        
        async def enhanced_notify_user(user_id: int, message: str):
            await self.notify_user(user_id, message)
        
        self.task_handler._notify_user = enhanced_notify_user
    
    def run(self):
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        self.setup_handlers(application)
        
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ يرجى تحديث BOT_TOKEN في ملف config.py")
        print("احصل على الرمز من @BotFather على تيليجرام")
        return
    
    if API_ID == 12345 or API_HASH == "your_api_hash_here":
        print("❌ يرجى تحديث API_ID و API_HASH في ملف config.py")
        print("احصل على البيانات من https://my.telegram.org")
        return
    
    bot = StarCollectorBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == '__main__':
    main()