import logging
import os

from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters
from config import BOT_TOKEN, LOG_FORMAT, LOG_LEVEL, TEMP_DIR
from db import init_db
from handlers.auth import start as auth_start, accept_rules, choose_language, enter_email, enter_password, ACCEPT_RULES, CHOOSE_LANGUAGE, ENTER_EMAIL, ENTER_PASSWORD
from handlers.menu import handle_selection as menu_handle_selection, MAIN_MENU, EDIT_EMAIL, EDIT_PASSWORD, CHOOSE_PROFESSION, PROFILE
from handlers.tts import do_tts as tts_do_tts, TTS_WAIT_TEXT
from keyboards import kb_main_menu, kb_remove

# --- تنظیمات لاگینگ ---
logging.basicConfig(
    format=LOG_FORMAT,
    level=LOG_LEVEL
)
logger = logging.getLogger(__name__)

# --- تابع اصلی برنامه ---
def main():
    """اجرای ربات."""
    # اطمینان از وجود پوشه موقت صدا
    if not TEMP_DIR.exists():
        try:
            TEMP_DIR.mkdir(exist_ok=True)
            logger.info(f"Temporary audio directory created at: {TEMP_DIR}")
        except OSError as e:
            logger.error(f"Failed to create temporary audio directory: {e}")
            return # Exit if temp dir cannot be created

    # اولیه سازی پایگاه داده
    init_db()

    # ساخت اپلیکیشن تلگرام
    application = Application.builder().token(BOT_TOKEN).build()

    # --- تعریف ConversationHandlers ---

    # ConversationHandler برای احراز هویت (ثبت نام)
    auth_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", auth_start)],
        states={
            ACCEPT_RULES: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_rules)],
            CHOOSE_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            ENTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_email)],
            ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password)],
        },
        fallbacks=[], # در این بخش fallbacks برای لغو وجود ندارد، چون /start نقطه ورود است
        name="auth_conversation",
        # persistence=None # در صورت نیاز به persistence می‌توان اینجا تنظیم کرد
    )

    # ConversationHandler برای منوی اصلی و ویرایش اطلاعات
    menu_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^/$") | filters.Regex("^/start$"), auth_start)], # اگر کاربر ثبت نام کرده باشد، /start او را به منوی اصلی هدایت می‌کند
        states={
            # اگر کاربر قبلا ثبت نام کرده باشد، state اصلی MAIN_MENU است
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handle_selection),
            ],
            EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_email)],
            EDIT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_password)],
            CHOOSE_PROFESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_profession)],
            TTS_WAIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tts_do_tts)],
            # اطمینان از بازگشت درست از مکالمه احراز هویت
            ACCEPT_RULES: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_rules)],
            CHOOSE_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            ENTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_email)],
            ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)], # هندلر لغو کلی
        # برای مدیریت حالت شروع و اینکه آیا کاربر ثبت نام کرده یا نه، منطق بیشتری نیاز است.
        # این بخش را در ادامه تنظیم می‌کنیم.
        name="menu_conversation",
    )

    # --- مدیریت جریان ربات ---
    # ابتدا بررسی می‌کنیم که آیا کاربر ثبت نام کرده است یا نه
    async def handle_start_or_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not db.is_registered(user_id):
            # اگر ثبت نام نکرده، مکالمه احراز هویت را شروع کن
            return await auth_start(update, context)
        else:
            # اگر ثبت نام کرده، منوی اصلی را نمایش بده
            await menu_handlers.send_main_menu(update, context, "خوش برگشتی!")
            return MAIN_MENU # بازگشت به state منوی اصلی

    # جایگزینی entry_points در menu_conv_handler
    menu_conv_handler.states = {
        **menu_conv_handler.states, # نگه داشتن state های موجود
        # state های جدید را اضافه می‌کنیم
        MAIN_MENU: [
             MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handle_selection),
             CommandHandler("start", lambda u,c: menu_handlers.send_main_menu(u,c, "خوش برگشتی!") ) # برای /start در حین مکالمه
             ],
        EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handlers.edit_email)],
        EDIT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handlers.edit_password)],
        CHOOSE_PROFESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handlers.choose_profession)],
        TTS_WAIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tts_do_tts)],
        # حالت‌های مکالمه ثبت نام هم اینجا اضافه می‌شوند تا بتوان از منو به آنها برگشت
        ACCEPT_RULES: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_rules)],
        CHOOSE_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
        ENTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_email)],
        ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password)],
    }

    # تغییر entry_points برای شروع صحیح مکالمه
    # اگر کاربر ثبت نام کرده باشد، مستقیماً وارد منوی اصلی می‌شود.
    # در غیر این صورت، مکالمه احراز هویت شروع می‌شود.
    async def route_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not db.is_registered(update.effective_user.id):
            return await auth_start(update, context) # شروع مکالمه احراز هویت
        else:
            return await menu_handlers.send_main_menu(update, context, "خوش برگشتی!") # نمایش منوی اصلی

    # ادغام دو ConversationHandler برای مدیریت یکپارچه
    # ابتدا Handlers را تعریف می‌کنیم
    application.add_handler(CommandHandler("start", route_start))
    application.add_handler(CommandHandler("cancel", lambda u, c: ConversationHandler.END))

    # اگر مکالمه شروع نشده باشد (کاربر ثبت نام نکرده)
    conv_auth = ConversationHandler(
        entry_points=[CommandHandler("start", auth_start)],
        states={
            ACCEPT_RULES: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_rules)],
            CHOOSE_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            ENTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_email)],
            ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_password)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        name="auth_conv",
        allow_reentry=True # اجازه ورود مجدد به مکالمه
    )

    # اگر مکالمه شروع شده باشد (کاربر ثبت نام کرده)
    conv_menu = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^/$") | filters.COMMAND, lambda u,c: menu_handlers.send_main_menu(u,c,"خوش برگشتی!"))], # یا دستور start اگر قبلا ثبت نام کرده
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handlers.handle_menu_selection)],
            EDIT_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handlers.edit_email)],
            EDIT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handlers.edit_password)],
            CHOOSE_PROFESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handlers.choose_profession)],
            TTS_WAIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tts_do_tts)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        name="menu_conv",
        allow_reentry=True
    )

    # برای مدیریت اینکه کدام ConversationHandler اجرا شود
    async def handle_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not db.is_registered(user_id):
            # اگر ثبت نام نکرده، مکالمه احراز هویت را شروع کن
            return await auth_start(update, context)
        else:
            # اگر ثبت نام کرده، منوی اصلی را نمایش بده و مکالمه منو را فعال کن
            return await menu_handlers.send_main_menu(update, context, "خوش برگشتی!")


    # تنظیم Application handlers
    application.add_handler(CommandHandler("start", handle_route))
    # اضافه کردن Handlers مکالمه
    application.add_handler(conv_auth)
    application.add_handler(conv_menu)

    # هندلر برای دستورات ناشناخته
    async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("متوجه نشدم. لطفاً از دستورات موجود یا منو استفاده کنید.")

    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    # هندلر برای پیام‌های متنی که در هیچ مکالمه‌ای نیستند
    async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
         await update.message.reply_text("لطفاً از منو استفاده کنید یا دستور /start را بزنید.")

    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message)) # این خط ممکن است باعث مشکل شود، بهتر است در ConversationHandler مدیریت شود.

    # اجرای ربات
    print("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    # Import db and menu handlers here to avoid circular imports
    import db
    import handlers.menu as menu_handlers # Alias for clarity

    main()
