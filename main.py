import logging
import re
from uuid import uuid4

from gtts import gTTS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

from db import (
    init_db, create_user, get_user, get_user_by_referral_code,
    set_language, set_accepted_rules, set_first_start, set_profession,
    set_email, set_password, set_registered, set_invited_by,
    add_points, add_invite
)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

(
    RULES,
    LANGUAGE,
    REGISTER_EMAIL,
    REGISTER_PASSWORD,
    REGISTER_CONFIRM,
    MAIN_MENU,
    PROFESSIONS_MENU,
    ACCOUNT_MENU,
    TTS_TEXT,
    TTS_LANGUAGE
) = range(10)

LANGUAGES = {
    "fa": "فارسی",
    "en": "English"
}

PROFESSIONS = {
    "writer": "نویسنده",
    "musician": "موسیقی‌دان",
    "programmer": "برنامه‌نویس",
    "designer": "طراح",
    "teacher": "معلم"
}


def clean_username(username):
    if not username:
        return "ندارد"
    return username.lstrip("@").strip()


def get_profession_name(key):
    return PROFESSIONS.get(key, "انتخاب نشده")


def get_language_name(code):
    return LANGUAGES.get(code, "فارسی")


def get_display_name(user):
    if user.username:
        return clean_username(user.username)
    return user.first_name or "کاربر"


def get_profile_text(user_row, bot_username):
    referral_link = f"https://t.me/{bot_username}?start={user_row['referral_code']}"
    return (
        f"👤 نام: {user_row['first_name'] or 'ندارد'}\n"
        f"🔹 یوزرنیم: @{user_row['username'] or 'ندارد'}\n"
        f"🌍 زبان: {get_language_name(user_row['language'])}\n"
        f"⭐ امتیاز: {user_row['points'] or 0}\n"
        f"👥 دعوت‌ها: {user_row['invited_count'] or 0}\n"
        f"💼 حرفه: {get_profession_name(user_row['profession'])}\n"
        f"📧 ایمیل: {user_row['email'] or 'ثبت نشده'}\n"
        f"🔗 لینک دعوت: {referral_link}"
    )


def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 حساب من", callback_data="account")],
        [InlineKeyboardButton("💼 انتخاب حرفه", callback_data="professions")],
        [InlineKeyboardButton("🎤 ساخت صدا", callback_data="tts")],
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh")]
    ])


def rules_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ قبول قوانین", callback_data="accept_rules"),
            InlineKeyboardButton("❌ رد قوانین", callback_data="reject_rules")
        ]
    ])


def language_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        ]
    ])


def professions_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("دزد", callback_data="prof_writer")],
        [InlineKeyboardButton("حروم خور", callback_data="prof_musician")],
        [InlineKeyboardButton("حلال خور", callback_data="prof_programmer")],
        [InlineKeyboardButton("کار ازاد", callback_data="prof_designer")],
        [InlineKeyboardButton("مال مردم خور", callback_data="prof_teacher")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]
    ])


def account_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 وضعیت حساب", callback_data="account_status")],
        [InlineKeyboardButton("🔑 تغییر رمز عبور", callback_data="change_password")],
        [InlineKeyboardButton("📧 تغییر ایمیل", callback_data="change_email")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referral_code = args[0] if args else None

    create_user(user.id, clean_username(user.username), user.first_name)
    row = get_user(user.id)

    if referral_code and referral_code != row["referral_code"]:
        inviter = get_user_by_referral_code(referral_code)
        if inviter and inviter["user_id"] != user.id and not row["invited_by"]:
            set_invited_by(user.id, referral_code)
            add_invite(inviter["user_id"])
            add_points(inviter["user_id"], 100)

    if row["first_start"]:
        text = (
            f"سلام {get_display_name(user)}\n\n"
            f"سازنده: امیرعلی فروزان‌اصل\n\n"
            f"برای استفاده از ربات باید قوانین را بپذیری."
        )
        await update.message.reply_text(text, reply_markup=rules_keyboard())
        return RULES

    return await show_home(update, context)


async def accept_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    set_accepted_rules(user.id, 1)
    set_first_start(user.id, 0)

    await query.edit_message_text("قوانین پذیرفته شد. زبان را انتخاب کن:", reply_markup=language_keyboard())
    return LANGUAGE


async def reject_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("شما قوانین را رد کردید و نمی‌توانید از ربات استفاده کنید.")
    return ConversationHandler.END


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    code = query.data.replace("lang_", "")
    set_language(user.id, code)

    await query.edit_message_text(
        f"زبان شما روی {get_language_name(code)} تنظیم شد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 ادامه ثبت‌نام", callback_data="continue_register")]
        ])
    )
    return REGISTER_EMAIL


async def continue_register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("ایمیل خود را بفرست:")
    return REGISTER_EMAIL


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        await update.message.reply_text("ایمیل درست نیست. دوباره بفرست.")
        return REGISTER_EMAIL

    context.user_data["email"] = email
    await update.message.reply_text("رمز عبور را بفرست:")
    return REGISTER_PASSWORD


async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    if len(password) < 4:
        await update.message.reply_text("رمز عبور باید حداقل 4 کاراکتر باشد.")
        return REGISTER_PASSWORD

    context.user_data["password"] = password
    email = context.user_data.get("email")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید و ثبت نهایی", callback_data="finish_register")],
        [InlineKeyboardButton("🔙 لغو", callback_data="cancel_register")]
    ])

    await update.message.reply_text(
        f"ایمیل: {email}\nرمز عبور: {'*' * len(password)}\n\nاگر درست است ثبت را بزن.",
        reply_markup=kb
    )
    return REGISTER_CONFIRM


async def finish_register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    email = context.user_data.get("email")
    password = context.user_data.get("password")

    set_email(user.id, email)
    set_password(user.id, password)
    set_registered(user.id, 1)

    await query.edit_message_text("ثبت‌نام کامل شد.")
    return await show_home_by_query(query, context)


async def cancel_register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("ثبت‌نام لغو شد.")
    return ConversationHandler.END


async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = get_user(user.id)
    bot = await context.bot.get_me()

    text = (
        f"سلام {get_display_name(user)} 👋\n\n"
        f"امتیاز شما: {row['points'] or 0}\n"
        f"دعوت‌ها: {row['invited_count'] or 0}\n"
        f"حساب: {'فعال' if row['registered'] else 'ناقص'}"
    )

    await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def show_home_by_query(query, context):
    user = query.from_user
    row = get_user(user.id)
    bot = await context.bot.get_me()
    await query.message.reply_text(get_profile_text(row, bot.username), reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    row = get_user(query.from_user.id)
    bot = await context.bot.get_me()

    await query.edit_message_text(get_profile_text(row, bot.username), reply_markup=account_keyboard())
    return ACCOUNT_MENU


async def account_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    row = get_user(query.from_user.id)

    text = (
        f"📌 وضعیت حساب\n\n"
        f"ایمیل: {row['email'] or 'ثبت نشده'}\n"
        f"رمز: {'تنظیم شده' if row['password'] else 'ثبت نشده'}\n"
        f"زبان: {get_language_name(row['language'])}\n"
        f"امتیاز: {row['points'] or 0}\n"
        f"دعوت‌ها: {row['invited_count'] or 0}"
    )

    await query.edit_message_text(text, reply_markup=account_keyboard())
    return ACCOUNT_MENU


async def change_email_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("ایمیل جدید را ارسال کن:")
    context.user_data["mode"] = "change_email"
    return REGISTER_EMAIL


async def change_password_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("رمز عبور جدید را ارسال کن:")
    context.user_data["mode"] = "change_password"
    return REGISTER_PASSWORD


async def professions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("یک حرفه انتخاب کن:", reply_markup=professions_keyboard())
    return PROFESSIONS_MENU


async def profession_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prof = query.data.replace("prof_", "")
    set_profession(query.from_user.id, prof)

    row = get_user(query.from_user.id)
    bot = await context.bot.get_me()

    await query.edit_message_text(get_profile_text(row, bot.username), reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    row = get_user(query.from_user.id)
    bot = await context.bot.get_me()

    await query.edit_message_text(get_profile_text(row, bot.username), reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def tts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("متن را بفرست تا صدا ساخته شود:")
    return TTS_TEXT


async def tts_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tts_text"] = update.message.text.strip()

    await update.message.reply_text(
        "زبان صدا را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("فارسی", callback_data="tts_fa")],
            [InlineKeyboardButton("English", callback_data="tts_en")]
        ])
    )
    return TTS_LANGUAGE


async def tts_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.replace("tts_", "")
    text = context.user_data.get("tts_text", "")

    if not text:
        await query.edit_message_text("متن پیدا نشد.")
        return MAIN_MENU

    filename = f"[/mnt/data/{uuid4(](https://storage.gapgpt.app/media/code_interpreter/e58b2c2b-b172-48b1-a918-4e3defae1d7d/%7Buuid4%28)).hex}.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)

    await query.message.reply_audio(audio=open(filename, "rb"), caption="فایل صدا آماده شد.")
    return MAIN_MENU


async def back_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    row = get_user(query.from_user.id)
    bot = await context.bot.get_me()

    await query.edit_message_text(get_profile_text(row, bot.username), reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("از دکمه‌ها استفاده کن.")


def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            RULES: [
                CallbackQueryHandler(accept_rules_callback, pattern="^accept_rules$"),
                CallbackQueryHandler(reject_rules_callback, pattern="^reject_rules$")
            ],
            LANGUAGE: [
                CallbackQueryHandler(language_callback, pattern="^lang_")
            ],
            REGISTER_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_email),
                CallbackQueryHandler(continue_register_callback, pattern="^continue_register$"),
                CallbackQueryHandler(change_email_callback, pattern="^change_email$")
            ],
            REGISTER_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_password),
                CallbackQueryHandler(change_password_callback, pattern="^change_password$")
            ],
            REGISTER_CONFIRM: [
                CallbackQueryHandler(finish_register_callback, pattern="^finish_register$"),
                CallbackQueryHandler(cancel_register_callback, pattern="^cancel_register$")
            ],
            MAIN_MENU: [
                CallbackQueryHandler(account_callback, pattern="^account$"),
                CallbackQueryHandler(professions_callback, pattern="^professions$"),
                CallbackQueryHandler(refresh_callback, pattern="^refresh$"),
                CallbackQueryHandler(tts_callback, pattern="^tts$"),
                CallbackQueryHandler(back_home_callback, pattern="^back_home$")
            ],
            ACCOUNT_MENU: [
                CallbackQueryHandler(account_status_callback, pattern="^account_status$"),
                CallbackQueryHandler(change_email_callback, pattern="^change_email$"),
                CallbackQueryHandler(change_password_callback, pattern="^change_password$"),
                CallbackQueryHandler(back_home_callback, pattern="^back_home$")
            ],
            PROFESSIONS_MENU: [
                CallbackQueryHandler(profession_set_callback, pattern="^prof_"),
                CallbackQueryHandler(back_home_callback, pattern="^back_home$")
            ],
            TTS_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tts_receive_text)
            ],
            TTS_LANGUAGE: [
                CallbackQueryHandler(tts_language_callback, pattern="^tts_")
            ],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
