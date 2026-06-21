import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from db import get_user, update_user_field
from keyboards import kb_main_menu, kb_profession_choice, kb_dashboard, kb_remove
from handlers.auth import ENTER_EMAIL, ENTER_PASSWORD, ACCEPT_RULES, CHOOSE_LANGUAGE # برای ریترن کردن State ها

logger = logging.getLogger(__name__)

# --- State های مربوط به منو و پروفایل ---
MAIN_MENU, EDIT_EMAIL, EDIT_PASSWORD, CHOOSE_PROFESSION = range(4)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text="به منوی اصلی خوش آمدید."):
    """ارسال کیبورد منوی اصلی."""
    await update.message.reply_text(text, reply_markup=kb_main_menu())
    return MAIN_MENU

async def send_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال کیبورد داشبورد."""
    await update.message.reply_text(
        "🧭 داشبورد شما:\n"
        "از گزینه‌های زیر یکی را انتخاب کنید.",
        reply_markup=kb_dashboard()
    )
    return MAIN_MENU # پس از نمایش داشبورد به منوی اصلی برمی‌گردیم

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش پروفایل کاربر."""
    user_id = update.effective_user.id
    user_data = get_user(user_id)

    if not user_data:
        await update.message.reply_text("خطا در دریافت اطلاعات پروفایل.", reply_markup=kb_main_menu())
        return MAIN_MENU

    msg = (
        "👤 پروفایل شما\n\n"
        f"نام: {user_data.get('first_name', '-')}\n"
        f"نام خانوادگی: {user_data.get('last_name', '-')}\n"
        f"یوزرنیم: @{user_data.get('username', '-')}\n"
        f"زبان: {user_data.get('language', '-')}\n"
        f"ایمیل: {user_data.get('email', '-')}\n"
        f"حرفه: {user_data.get('profession', '-')}\n"
        f"قوانین: {'پذیرفته شده' if user_data.get('accepted_rules') else 'پذیرفته نشده'}\n"
        f"ثبت‌نام: {'کامل' if user_data.get('registered') else 'ناقص'}"
    )
    await update.message.reply_text(msg, reply_markup=kb_main_menu())
    return MAIN_MENU

async def ask_edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرایند تغییر ایمیل."""
    await update.message.reply_text("ایمیل جدید خود را وارد کنید:", reply_markup=kb_remove())
    return EDIT_EMAIL

async def edit_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انجام تغییر ایمیل."""
    email = update.message.text.strip()
    # اعتبارسنجی ایمیل (می‌توانید از تابع اعتبارسنجی موجود در auth.py استفاده کنید)
    # from handlers.auth import valid_email
    # if not valid_email(email):
    #     await update.message.reply_text("ایمیل معتبر نیست. لطفاً دوباره وارد کنید:")
    #     return EDIT_EMAIL

    update_user_field(update.effective_user.id, "email", email)
    await update.message.reply_text("ایمیل شما با موفقیت تغییر کرد.", reply_markup=kb_main_menu())
    return MAIN_MENU

async def ask_edit_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرایند تغییر رمز عبور."""
    await update.message.reply_text("رمز عبور جدید خود را وارد کنید (حداقل 4 کاراکتر):", reply_markup=kb_remove())
    return EDIT_PASSWORD

async def edit_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انجام تغییر رمز عبور."""
    password = update.message.text.strip()
    if len(password) < 4:
        await update.message.reply_text("رمز عبور باید حداقل 4 کاراکتر باشد. دوباره وارد کنید:")
        return EDIT_PASSWORD

    # هش کردن رمز عبور جدید
    from db import hash_password #Import inside function if not globally imported
    hashed_password = hash_password(password)
    update_user_field(update.effective_user.id, "password_hash", hashed_password)
    await update.message.reply_text("رمز عبور شما با موفقیت تغییر کرد.", reply_markup=kb_main_menu())
    return MAIN_MENU

async def ask_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش گزینه‌های انتخاب حرفه."""
    await update.message.reply_text("حرفه خود را انتخاب کنید:", reply_markup=kb_profession_choice())
    return CHOOSE_PROFESSION

async def choose_profession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره حرفه انتخاب شده."""
    profession = update.message.text.strip()
    if profession == "🏠 بازگشت به منوی اصلی":
        return await send_main_menu(update, context)

    update_user_field(update.effective_user.id, "profession", profession)
    await update.message.reply_text(f"حرفه شما روی «{profession}» ثبت شد.", reply_markup=kb_main_menu())
    return MAIN_MENU

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر اصلی برای انتخاب گزینه‌های منوی اصلی."""
    text = update.message.text.strip()

    if text == "👤 پروفایل":
        return await profile(update, context)
    elif text == "✉ تغییر ایمیل":
        return await ask_edit_email(update, context)
    elif text == "🔑 تغییر رمز عبور":
        return await ask_edit_password(update, context)
    elif text == "💼 انتخاب حرفه":
        return await ask_profession(update, context)
    elif text == "🎙 تبدیل متن به صدا":
        # اگر بخواهید به هندلر TTS بروید
        from handlers.tts import TTS_WAIT_TEXT # Import here to avoid circular dependency
        await update.message.reply_text("متنی را که می‌خواهید به صدا تبدیل شود، ارسال کنید:", reply_markup=kb_remove())
        return TTS_WAIT_TEXT
    elif text == "🧭 داشبورد":
        return await send_dashboard(update, context)
    elif text == "🏠 بازگشت به منوی اصلی":
        return await send_main_menu(update, context)
    else:
        await update.message.reply_text("لطفاً از گزینه‌های منو استفاده کنید.")
        return MAIN_MENU
