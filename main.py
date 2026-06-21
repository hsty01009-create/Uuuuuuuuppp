import os
import uuid
from gtts import gTTS

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

import db


# ================= TOKEN =================
TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN")


# ================= LANGUAGES =================
LANGS = {
    "fa": "🇮🇷 فارسی",
    "en": "🇺🇸 English",
    "ar": "🇸🇦 العربية",
    "tr": "🇹🇷 Türkçe",
    "de": "🇩🇪 Deutsch",
    "ru": "🇷🇺 Русский",
    "es": "🇪🇸 Español"
}


TEXTS = {
    "fa": {
        "welcome": "👋 خوش آمدید",
        "choose_lang": "🌍 زبان را انتخاب کنید",
        "voice": "🎤 متن را ارسال کن",
    },
    "en": {
        "welcome": "👋 Welcome",
        "choose_lang": "🌍 Choose language",
        "voice": "🎤 Send text",
    }
}


# ================= KEYBOARD =================
def main_kb():
    return ReplyKeyboardMarkup([
        ["👤 پروفایل", "💰 امتیاز"],
        ["🎤 ساخت صدا", "🔗 دعوت"],
        ["🌍 زبان"]
    ], resize_keyboard=True)


def lang_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(v, callback_data=k)] for k, v in LANGS.items()
    ])


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = update.effective_user
    db.create_user(u.id, u.username, u.first_name)

    # referral
    if context.args:
        ref = context.args[0]
        if ref.isdigit() and int(ref) != u.id:
            db.add_points(int(ref), 200)

    await update.message.reply_text(
        "👋 خوش آمدید / Welcome",
        reply_markup=main_kb()
    )


# ================= PROFILE =================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = db.get_user(update.effective_user.id)

    await update.message.reply_text(f"""
👤 پروفایل
🆔 {u['user_id']}
👤 {u['first_name']}
🌍 {u['language']}
⭐ {u['points']}
👥 {u['invited_count']}

👨‍💻 امیرعلی فروزان‌اصل
""")


# ================= POINTS =================
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = db.get_user(update.effective_user.id)
    await update.message.reply_text(f"⭐ امتیاز: {u['points']}")


# ================= INVITE =================
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = update.effective_user
    bot = await context.bot.get_me()

    link = f"https://t.me/{bot.username}?start={u.id}"

    await update.message.reply_text(f"🔗 لینک دعوت:\n{link}")


# ================= LANGUAGE =================
async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🌍 انتخاب زبان",
        reply_markup=lang_kb()
    )


async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    db.update("language", q.data, q.from_user.id)

    await q.message.reply_text("✅ زبان تغییر کرد")


# ================= VOICE =================
async def voice_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("🎤 متن را ارسال کن")


async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text in ["👤 پروفایل", "💰 امتیاز", "🔗 دعوت", "🎤 ساخت صدا", "🌍 زبان"]:
        return

    filename = f"{uuid.uuid4()}.mp3"

    tts = gTTS(text=text, lang="en")
    tts.save(filename)

    await update.message.reply_audio(audio=open(filename, "rb"))

    os.remove(filename)

    db.add_points(update.effective_user.id, 50)


# ================= MAIN =================
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.Regex("👤 پروفایل"), profile))
    app.add_handler(MessageHandler(filters.Regex("💰 امتیاز"), points))
    app.add_handler(MessageHandler(filters.Regex("🔗 دعوت"), invite))
    app.add_handler(MessageHandler(filters.Regex("🌍 زبان"), lang))
    app.add_handler(MessageHandler(filters.Regex("🎤 ساخت صدا"), voice_start))

    app.add_handler(CallbackQueryHandler(set_lang))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, voice))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
