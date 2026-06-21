import logging
import re
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from db import get_user, update_user_field, hash_password, is_registered
from keyboards import kb_rules, kb_language, kb_main_menu, kb_remove
from config import DEFAULT_LANG

logger = logging.getLogger(__name__)

# --- State های مربوط به احراز هویت ---
ACCEPT_RULES, CHOOSE_LANGUAGE, ENTER_EMAIL, ENTER_PASSWORD = range(4)

def valid_email(email: str) -> bool:
    """اعتبارسنجی فرمت ایمیل."""
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /start."""
    user_id = update.effective_user.id
    if is_registered(user_id):
        await update.message.reply_text(
            "شما قبلاً ثبت‌نام کرده‌اید.", reply_markup=kb_main_menu()
        )
        return ConversationHandler.END # پایان مکالمه اگر ثبت نام شده

    await update.message.reply_text(
        "به ربات خوش آمدید.\n\n"
        "قبل از ادامه، قوانین را بپذیرید:\n"
        "1) استفاده صحیح از ربات\n"
        "2) رعایت ادب\n"
        "3) عدم سوءاستفاده\n",
        reply_markup=kb_rules()
    )
    return ACCEPT_RULES

async def accept_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مرحله پذیرش قوانین."""
    if update.message.text == "✅ قبول می‌کنم":
        update_user_field(update.effective_user.id, "accepted_rules", 1)
        await update.message.reply_text(
            "قوانین پذیرفته شد.\n"
            f"اکنون زبان خود را انتخاب کنید (پیش‌فرض: {DEFAULT_LANG}):",
            reply_markup=kb_language()
        )
        return CHOOSE_LANGUAGE

    await update.message.reply_text(
        "برای استفاده از ربات باید قوانین را بپذیرید.",
        reply_markup=kb_remove()
    )
    # لغو مکالمه اگر قوانین را قبول نکرد
    return ConversationHandler.END

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مرحله انتخاب زبان."""
    lang = update.message.text.strip().lower()
    if lang not in ["fa", "en"]:
        await update.message.reply_text("لطفاً فقط 'fa' یا 'en' را انتخاب کنید.")
        return CHOOSE_LANGUAGE

    update_user_field(update.effective_user.id, "language", lang)
    await update.message.reply_text(
        "زبان ذخیره شد.\n"
        "لطفاً ایمیل خود را وارد کنید:",
        reply_markup=kb_remove()
    )
    return ENTER_EMAIL

async def enter_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مرحله ورود ایمیل."""
    email = update.message.text.strip()
    if not valid_email(email):
        await update.message.reply_text("ایمیل معتبر نیست. لطفاً دوباره وارد کنید:")
        return ENTER_EMAIL

    update_user_field(update.effective_user.id, "email", email)
    await update.message.reply_text("ایمیل ثبت شد.\nحالا رمز عبور خود را وارد کنید (حداقل 4 کاراکتر):")
    return ENTER_PASSWORD

async def enter_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مرحله ورود رمز عبور و تکمیل ثبت‌نام."""
    password = update.message.text.strip()
    if len(password) < 4:
        await update.message.reply_text("رمز عبور باید حداقل 4 کاراکتر باشد. دوباره وارد کنید:")
        return ENTER_PASSWORD

    hashed_password = hash_password(password)
    update_user_field(update.effective_user.id, "password_hash", hashed_password)
    update_user_field(update.effective_user.id, "registered", 1) # علامت‌گذاری به عنوان ثبت‌نام شده

    logger.info(f"User {update.effective_user.id} registered successfully.")
    await update.message.reply_text(
        "ثبت‌نام شما با موفقیت تکمیل شد!",
        reply_markup=kb_main_menu()
    )
    return ConversationHandler.END # پایان مکالمه پس از ثبت نام موفق
