# main.py

import os
import uuid
import logging

from gtts import gTTS

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import db


# =====================
# تنظیمات
# =====================

BOT_TOKEN = "توکن_ربات_خود_را_اینجا_قرار_دهید"


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# =====================
# حالت‌ها
# =====================

(
    RULES,
    LANGUAGE,
    EMAIL,
    PASSWORD,
    CONFIRM,
    MAIN_MENU,
    ACCOUNT_MENU,
    PROFESSION_MENU,
    TTS_TEXT,
    TTS_LANGUAGE
) = range(10)


# =====================
# زبان‌ها
# =====================

LANGUAGES = {
    "fa": "فارسی",
    "en": "English"
}


# =====================
# مشاغل
# =====================

PROFESSIONS = {
    "writer": "نویسنده",
    "musician": "موسیقی‌دان",
    "programmer": "برنامه‌نویس",
    "designer": "طراح",
    "teacher": "معلم"
}


# =====================
# منوی اصلی
# =====================

def main_keyboard():
    keyboard = [
        [
            KeyboardButton("حساب من 👤"),
            KeyboardButton("انتخاب حرفه 💼")
        ],
        [
            KeyboardButton("ساخت صدا 🎵"),
            KeyboardButton("بروزرسانی 🔄")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# =====================
# منوی حساب
# =====================

def account_keyboard():
    keyboard = [
        [
            KeyboardButton("پروفایل 📄"),
            KeyboardButton("تغییر ایمیل 📧")
        ],
        [
            KeyboardButton("تغییر رمز 🔑"),
            KeyboardButton("بازگشت 🔙")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


# =====================
# قوانین
# =====================

def rules_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "قبول قوانین ✅",
                callback_data="accept"
            ),
            InlineKeyboardButton(
                "رد ❌",
                callback_data="reject"
            )
        ]
    ])


# =====================
# زبان
# =====================

def language_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "فارسی 🇮🇷",
                callback_data="fa"
            ),
            InlineKeyboardButton(
                "English 🇺🇸",
                callback_data="en"
            )
        ]
    ])


# =====================
# مشاغل
# =====================

def profession_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "نویسنده",
                callback_data="writer"
            ),
            InlineKeyboardButton(
                "برنامه‌نویس",
                callback_data="programmer"
            )
        ],
        [
            InlineKeyboardButton(
                "موسیقی‌دان",
                callback_data="musician"
            ),
            InlineKeyboardButton(
                "طراح",
                callback_data="designer"
            )
        ],
        [
            InlineKeyboardButton(
                "معلم",
                callback_data="teacher"
            )
        ]
    ])


# =====================
# نمایش پروفایل
# =====================

def profile_text(user):

    return f"""
👤 پروفایل

🆔 آیدی: {user['user_id']}
👤 نام: {user['first_name']}
📧 ایمیل: {user['email'] or 'ثبت نشده'}
🌐 زبان: {user['language']}
💼 حرفه: {user['profession'] or 'ثبت نشده'}
⭐ امتیاز: {user['points']}
👥 دعوت: {user['invited_count']}
🎁 کد دعوت: {user['referral_code']}
"""
    # =====================
# /start
# =====================

async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    db_user = db.get_user(user.id)

    if not db_user:
        db_user = db.create_user(
            user.id,
            user.username,
            user.first_name
        )

    if db_user["first_start"]:

        await update.message.reply_text(
            f"سلام {user.first_name}\n"
            "به ربات خوش آمدید.\n"
            "لطفاً قوانین را قبول کنید.",
            reply_markup=rules_keyboard()
        )

        return RULES

    await update.message.reply_text(
        "خوش آمدید.",
        reply_markup=main_keyboard()
    )

    return MAIN_MENU


# =====================
# قبول قوانین
# =====================

async def accept_rules(update: Update,
                       context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    db.set_accepted_rules(user_id, True)
    db.set_first_start(user_id, False)

    await query.message.reply_text(
        "زبان خود را انتخاب کنید.",
        reply_markup=language_keyboard()
    )

    return LANGUAGE


# =====================
# رد قوانین
# =====================

async def reject_rules(update: Update,
                       context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    await query.message.reply_text(
        "بدون قبول قوانین امکان استفاده وجود ندارد."
    )

    return ConversationHandler.END


# =====================
# انتخاب زبان
# =====================

async def choose_language(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    language = query.data

    user_id = query.from_user.id

    db.set_language(user_id, language)

    await query.message.reply_text(
        "ایمیل خود را وارد کنید."
    )

    return EMAIL


# =====================
# ثبت ایمیل
# =====================

async def register_email(update: Update,
                         context: ContextTypes.DEFAULT_TYPE):

    email = update.message.text

    context.user_data["email"] = email

    await update.message.reply_text(
        "رمز عبور را وارد کنید."
    )

    return PASSWORD


# =====================
# ثبت رمز
# =====================

async def register_password(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):

    password = update.message.text

    context.user_data["password"] = password

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "ثبت نهایی ✅",
                callback_data="finish"
            ),
            InlineKeyboardButton(
                "لغو ❌",
                callback_data="cancel"
            )
        ]
    ])

    await update.message.reply_text(
        "آیا اطلاعات صحیح است؟",
        reply_markup=keyboard
    )

    return CONFIRM


# =====================
# تکمیل ثبت نام
# =====================

async def finish_register(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    db.set_email(
        user_id,
        context.user_data["email"]
    )

    db.set_password(
        user_id,
        context.user_data["password"]
    )

    db.set_registered(
        user_id,
        True
    )

    user = db.get_user(user_id)

    await query.message.reply_text(
        "ثبت نام انجام شد."
    )

    await query.message.reply_text(
        profile_text(user),
        reply_markup=main_keyboard()
    )

    return MAIN_MENU


# =====================
# لغو ثبت نام
# =====================

async def cancel_register(update: Update,
                          context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    await query.message.reply_text(
        "ثبت نام لغو شد."
    )

    return ConversationHandler.END
                              =====================

حساب کاربری

=====================

async def account_menu(update: Update,
context: ContextTypes.DEFAULT_TYPE):

await update.message.reply_text(
    "بخش حساب کاربری",
    reply_markup=account_keyboard()
)

return ACCOUNT_MENU

=====================

نمایش پروفایل

=====================

async def show_profile(update: Update,
context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id

user = db.get_user(user_id)

await update.message.reply_text(
    profile_text(user),
    reply_markup=account_keyboard()
)

return ACCOUNT_MENU

=====================

تغییر ایمیل

=====================

async def change_email(update: Update,
context: ContextTypes.DEFAULT_TYPE):

context.user_data["change_email"] = True

await update.message.reply_text(
    "ایمیل جدید را وارد کنید."
)

return ACCOUNT_MENU

=====================

تغییر رمز

=====================

async def change_password(update: Update,
context: ContextTypes.DEFAULT_TYPE):

context.user_data["change_password"] = True

await update.message.reply_text(
    "رمز جدید را وارد کنید."
)

return ACCOUNT_MENU

=====================

پردازش تغییرات

=====================

async def account_text(update: Update,
context: ContextTypes.DEFAULT_TYPE):

user_id = update.effective_user.id

if context.user_data.get("change_email"):

    db.set_email(
        user_id,
        update.message.text
    )

    context.user_data["change_email"] = False

    await update.message.reply_text(
        "ایمیل تغییر کرد."
    )

    return ACCOUNT_MENU

if context.user_data.get("change_password"):

    db.set_password(
        user_id,
        update.message.text
    )

    context.user_data["change_password"] = False

    await update.message.reply_text(
        "رمز عبور تغییر کرد."
    )

    return ACCOUNT_MENU

return ACCOUNT_MENU

=====================

انتخاب حرفه

=====================

async def profession_menu(update: Update,
context: ContextTypes.DEFAULT_TYPE):

await update.message.reply_text(
    "حرفه خود را انتخاب کنید.",
    reply_markup=profession_keyboard()
)

return PROFESSION_MENU

=====================

ذخیره حرفه

=====================

async def profession_select(update: Update,
context: ContextTypes.DEFAULT_TYPE):

query = update.callback_query

await query.answer()

profession = query.data

user_id = query.from_user.id

db.set_profession(
    user_id,
    profession
)

await query.message.reply_text(
    "حرفه ذخیره شد.",
    reply_markup=main_keyboard()
)

return MAIN_MENU

=====================

بازگشت

=====================

async def back_home(update: Update,
context: ContextTypes.DEFAULT_TYPE):

await update.message.reply_text(
    "منوی اصلی",
    reply_markup=main_keyboard()
)

return MAIN_MENU
async def tts_menu(update, context):
    await update.message.reply_text(
        "متن را بفرست."
    )
    return TTS_TEXT


async def tts_text(update, context):
    text = update.message.text

    tts = gTTS(
        text=text,
        lang="fa"
    )

    tts.save("voice.mp3")

    with open("voice.mp3", "rb") as audio:
        await update.message.reply_audio(audio)

    return MAIN_MENU
