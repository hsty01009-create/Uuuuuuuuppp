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

# ---------- TOKEN SAFE ----------
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN is missing!")
    exit()

# ---------- KEYBOARD ----------
def kb():
    return ReplyKeyboardMarkup([
        ["👤 پروفایل", "🎤 ساخت صدا"],
        ["💰 امتیاز", "🔗 دعوت"],
        ["👨 صدا مرد", "👩 صدا زن"]
    ], resize_keyboard=True)

# ---------- SAFE USER ----------
def safe_user(user):
    u = db.get_user(user.id)

    if not u:
        db.create_user(user.id, user.first_name)
        u = db.get_user(user.id)

    return u

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    db.create_user(user.id, user.first_name)

    if context.args:
        try:
            inviter = int(context.args[0])
            if inviter != user.id:
                db.add_points(inviter, 200)
        except:
            pass

    await update.message.reply_text(
        "به ربات حرفه‌ای خوش آمدی 👋",
        reply_markup=kb()
    )

# ---------- PROFILE ----------
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = safe_user(update.effective_user)

    text = f"""
👤 پروفایل
🆔 {u['user_id']}
👤 {u['name']}
🎤 صدا: {u['voice']}
⭐ امتیاز: {u['points']}
"""

    await update.message.reply_text(text)

# ---------- POINTS ----------
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = safe_user(update.effective_user)
    await update.message.reply_text(f"⭐ امتیاز شما: {u['points']}")

# ---------- INVITE ----------
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):

    link = f"https://t.me/YOUR_BOT?start={update.effective_user.id}"

    await update.message.reply_text(
        f"🔗 لینک دعوت:\n{link}\n\n+200 امتیاز"
    )

# ---------- VOICE ----------
async def male(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = safe_user(update.effective_user)
    db.set_voice(u["user_id"], "male")

    await update.message.reply_text("👨 صدای مرد فعال شد")

async def female(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = safe_user(update.effective_user)
    db.set_voice(u["user_id"], "female")

    await update.message.reply_text("👩 صدای زن فعال شد")

# ---------- TTS SAFE ----------
async def tts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        text = update.message.text
        u = safe_user(update.effective_user)

        voice = "fa-IR-FaridNeural" if u["voice"] == "male" else "fa-IR-DilaraNeural"

        file = f"{uuid.uuid4()}.mp3"

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(file)

        with open(file, "rb") as audio:
            await update.message.reply_audio(audio=audio)

        os.remove(file)

        db.add_points(u["user_id"], 50)

    except Exception as e:
        print("TTS ERROR:", e)
        await update.message.reply_text("❌ خطا در ساخت صدا")

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
