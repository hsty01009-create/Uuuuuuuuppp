import uuid
import asyncio
import edge_tts
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

import db

TOKEN = os.getenv("BOT_TOKEN")

# ---------- KEYBOARD ----------
def kb():
    return ReplyKeyboardMarkup([
        ["👤 پروفایل", "🎤 ساخت صدا"],
        ["💰 امتیاز", "🔗 دعوت"],
        ["👨 صدا مرد", "👩 صدا زن"]
    ], resize_keyboard=True)

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    db.create_user(user.id, user.first_name)

    if context.args:
        inviter = int(context.args[0])
        if inviter != user.id:
            db.add_points(inviter, 200)

    await update.message.reply_text(
        "به ربات حرفه‌ای خوش آمدی 👋",
        reply_markup=kb()
    )

# ---------- PROFILE ----------
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = db.get_user(update.effective_user.id)

    text = f"""
👤 پروفایل
🆔 {u['user_id']}
👤 {u['name']}
🎤 صدا: {u['voice']}
⭐ امتیاز: {u['points']}
👨‍💻 سازنده: امیرعلی فروزان‌اصل
"""

    await update.message.reply_text(text)

# ---------- POINTS ----------
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    await update.message.reply_text(f"⭐ امتیاز شما: {u['points']}")

# ---------- INVITE ----------
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):

    link = f"https://t.me/YOUR_BOT?start={update.effective_user.id}"

    await update.message.reply_text(
        f"🔗 لینک دعوت:\n{link}\n\n+200 امتیاز"
    )

# ---------- VOICE ----------
async def male(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_voice(update.effective_user.id, "male")
    await update.message.reply_text("👨 صدای مرد فعال شد")

async def female(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_voice(update.effective_user.id, "female")
    await update.message.reply_text("👩 صدای زن فعال شد")

# ---------- TTS (FIXED) ----------
async def tts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user = db.get_user(update.effective_user.id)

    voice = "fa-IR-FaridNeural" if user["voice"] == "male" else "fa-IR-DilaraNeural"

    file = f"{uuid.uuid4()}.mp3"

    communicate = edge_tts.Communicate(text, voice)

    await communicate.save(file)

    with open(file, "rb") as audio:
        await update.message.reply_audio(audio=audio)

    os.remove(file)

    db.add_points(user["user_id"], 50)

# ---------- MAIN ----------
def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.Regex("👤 پروفایل"), profile))
    app.add_handler(MessageHandler(filters.Regex("💰 امتیاز"), points))
    app.add_handler(MessageHandler(filters.Regex("🔗 دعوت"), invite))

    app.add_handler(MessageHandler(filters.Regex("👨 صدا مرد"), male))
    app.add_handler(MessageHandler(filters.Regex("👩 صدا زن"), female))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tts))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
