import uuid
import os
import asyncio
from gtts import gTTS

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import db


TOKEN = "YOUR_BOT_TOKEN"


# ---------------- KEYBOARD ----------------
def main_kb():
    return ReplyKeyboardMarkup([
        ["👤 پروفایل", "💰 امتیاز"],
        ["🎤 ساخت صدا", "🔗 دعوت"]
    ], resize_keyboard=True)


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    db.create_user(user.id, user.username, user.first_name)

    ref = context.args[0] if context.args else None

    if ref and str(ref) != str(user.id):
        db.add_points(int(ref), 200)

    await update.message.reply_text(
        "سلام 👋\nبه ربات حرفه‌ای خوش آمدی",
        reply_markup=main_kb()
    )


# ---------------- PROFILE ----------------
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = db.get_user(update.effective_user.id)

    text = f"""
👤 پروفایل
🆔 {user['user_id']}
📛 {user['first_name']}
🌍 {user['language']}
⭐ امتیاز: {user['points']}
👥 دعوت: {user['invited_count']}

👨‍💻 سازنده: امیرعلی فروزان‌اصل
"""

    await update.message.reply_text(text)


# ---------------- POINTS ----------------
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = db.get_user(update.effective_user.id)

    await update.message.reply_text(f"⭐ امتیاز شما: {user['points']}")


# ---------------- INVITE ----------------
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    link = f"https://t.me/YourBot?start={user_id}"

    await update.message.reply_text(f"🔗 لینک دعوت:\n{link}")


# ---------------- TTS ----------------
async def tts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text in ["🎤 ساخت صدا"]:
        await update.message.reply_text("متن را ارسال کن 👇")
        return

    filename = f"{uuid.uuid4()}.mp3"

    tts = gTTS(text=text, lang="en")
    tts.save(filename)

    await update.message.reply_audio(audio=open(filename, "rb"))

    os.remove(filename)

    db.add_points(update.effective_user.id, 50)


# ---------------- HANDLER ----------------
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.Regex("👤 پروفایل"), profile))
    app.add_handler(MessageHandler(filters.Regex("💰 امتیاز"), points))
    app.add_handler(MessageHandler(filters.Regex("🔗 دعوت"), invite))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tts))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
