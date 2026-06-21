import os
import uuid
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import *
import db

from edge_tts import Communicate

TOKEN = os.getenv("BOT_TOKEN")

db.init()

# ================= RULES =================
RULES = """
1. قوانین را قبول می‌کنید
2. محتوای غیرقانونی ممنوع
3. اطلاعات محفوظ است
4. سوءاستفاده ممنوع
5. مسئولیت با کاربر است
"""

# ================= MENU =================
def menu():
    return ReplyKeyboardMarkup([
        ["👤 پروفایل", "🎤 صدا"],
        ["💰 امتیاز"]
    ], resize_keyboard=True)

# ================= START =================
async def start(update: Update, context):
    u = update.effective_user
    user = db.get(u.id)

    if not user:
        db.create(u.id, u.username, u.first_name)
        await update.message.reply_text(RULES)
        return

    await update.message.reply_text("خوش آمدید", reply_markup=menu())

# ================= EMAIL CHECK =================
def is_gmail(email):
    return email.endswith("@gmail.com")

# ================= PROFILE =================
async def profile(update: Update, context):
    u = db.get(update.effective_user.id)

    link = f"https://t.me/{context.bot.username}?start={u['user_id']}"

    await update.message.reply_text(f"""
👤 {u['first_name']}
📧 {u['email']}
🌍 {u['language']}
⭐ امتیاز: {u['points']}
🔗 لینک دعوت: {link}
👨‍💻 سازنده: امیرعلی فروزان‌اصل
""")

# ================= EDGE TTS =================
async def voice(update: Update, context):
    text = update.message.text

    file = f"{uuid.uuid4()}.mp3"

    tts = Communicate(text, "en-US-AriaNeural")
    await tts.save(file)

    await update.message.reply_audio(audio=open(file, "rb"))

    os.remove(file)

# ================= TEXT HANDLER =================
async def text(update: Update, context):
    user_id = update.effective_user.id
    msg = update.message.text

    # Gmail check
    if context.user_data.get("email_step"):
        if not msg.endswith("@gmail.com"):
            await update.message.reply_text("فقط Gmail مجاز است")
            return
        db.update("email", msg, user_id)
        context.user_data["email_step"] = False
        await update.message.reply_text("ثبت شد")
        return

# ================= MAIN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

print("Bot Running...")
app.run_polling()
