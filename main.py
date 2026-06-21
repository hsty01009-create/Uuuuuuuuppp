import os
import uuid
import asyncio
import edge_tts

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
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


# ================= LANG =================
LANG = "fa"


# ================= KEYBOARD =================
def kb():
    return ReplyKeyboardMarkup([
        ["👤 پروفایل", "💰 امتیاز"],
        ["🎤 صدای مرد", "🎤 صدای زن"],
        ["🔗 دعوت"]
    ], resize_keyboard=True)


# ================= RULES (10 LINES) =================
RULES = """
📜 قوانین استفاده از ربات:

1. استفاده از ربات یعنی پذیرش قوانین  
2. هر کاربر مسئول استفاده خود است  
3. ثبت‌نام فقط با اطلاعات واقعی  
4. سوءاستفاده باعث مسدودی می‌شود  
5. ارسال اسپم ممنوع است  
6. محتوای غیرمجاز حذف می‌شود  
7. لینک دعوت معتبر است  
8. امتیاز قابل سوءاستفاده نیست  
9. سازنده: امیرعلی فروزان‌اصل (ساندرا)  
10. استفاده یعنی پذیرش کامل قوانین
"""


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = update.effective_user
    db.create_user(u.id, u.username, u.first_name)

    user = db.get_user(u.id)

    if user["accepted"] == 0:
        await update.message.reply_text(RULES)
        db.update("accepted", 1, u.id)

    await update.message.reply_text("👋 خوش آمدید", reply_markup=kb())


# ================= PROFILE =================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    u = db.get_user(update.effective_user.id)

    await update.message.reply_text(f"""
👤 پروفایل
🆔 {u['user_id']}
👤 {u['first_name']}
🌍 {u['language']}
⭐ {u['points']}

👨‍💻 امیرعلی فروزان‌اصل (سازنده)
""")


# ================= POINTS =================
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    await update.message.reply_text(f"⭐ امتیاز: {u['points']}")


# ================= INVITE =================
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = await context.bot.get_me()
    uid = update.effective_user.id

    link = f"https://t.me/{bot.username}?start={uid}"

    await update.message.reply_text(f"🔗 لینک دعوت:\n{link}")


# ================= EDGE TTS =================
async def make_voice(text, voice):

    file = f"{uuid.uuid4()}.mp3"

    tts = edge_tts.Communicate(text, voice)
    await tts.save(file)

    return file


# ================= VOICE MALE =================
async def male(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text in ["🎤 صدای مرد", "🎤 صدای زن", "👤 پروفایل", "💰 امتیاز", "🔗 دعوت"]:
        await update.message.reply_text("✍ متن را ارسال کن")
        return

    file = await make_voice(text, "fa-IR-FaridNeural")

    await update.message.reply_audio(audio=open(file, "rb"))

    os.remove(file)

    db.add_points(update.effective_user.id, 50)


# ================= VOICE FEMALE =================
async def female(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text in ["🎤 صدای مرد", "🎤 صدای زن", "👤 پروفایل", "💰 امتیاز", "🔗 دعوت"]:
        await update.message.reply_text("✍ متن را ارسال کن")
        return

    file = await make_voice(text, "fa-IR-DilaraNeural")

    await update.message.reply_audio(audio=open(file, "rb"))

    os.remove(file)

    db.add_points(update.effective_user.id, 50)


# ================= MAIN =================
def main():

    db.init()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.Regex("👤 پروفایل"), profile))
    app.add_handler(MessageHandler(filters.Regex("💰 امتیاز"), points))
    app.add_handler(MessageHandler(filters.Regex("🔗 دعوت"), invite))

    app.add_handler(MessageHandler(filters.Regex("🎤 صدای مرد"), male))
    app.add_handler(MessageHandler(filters.Regex("🎤 صدای زن"), female))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, male))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, female))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
