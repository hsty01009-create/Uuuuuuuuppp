from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import sqlite3
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------------- DATABASE ----------------
db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 100,
    accepted INTEGER DEFAULT 0
)
""")

db.commit()

def add_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (user_id,))
    db.commit()

def accept_rules(user_id):
    cur.execute("UPDATE users SET accepted=1 WHERE id=?", (user_id,))
    db.commit()

def check_rules(user_id):
    cur.execute("SELECT accepted FROM users WHERE id=?", (user_id,))
    data = cur.fetchone()
    return data and data[0] == 1


# ---------------- STATE ----------------
user_state = {}

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    add_user(user)

    if not check_rules(user):

        btn = [[InlineKeyboardButton("✅ قبول قوانین", callback_data="accept")]]

        await update.message.reply_text(
            """
📜 قوانین ربات:

1- استفاده درست
2- اسپم ممنوع
3- محتوای غیرقانونی ممنوع
4- احترام
5- سوء استفاده ممنوع
6- فایل خطرناک ممنوع
7- سکه‌ها سیستم ربات
8- دعوت واقعی
9- رایگان
10- قوانین ممکن است تغییر کند
11- سازنده: امیر علی فروزان اصل
""",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    await menu(update, context)


# ---------------- MENU ----------------
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = [
        [InlineKeyboardButton("🎬 ساخت ویدیو", callback_data="video")],
        [InlineKeyboardButton("🎵 ساخت آهنگ", callback_data="music")],
        [InlineKeyboardButton("🪙 سکه من", callback_data="coins")]
    ]

    await update.message.reply_text(
        "خوش آمدی 👋\nانتخاب کن:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ---------------- CALLBACK ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    if q.data == "accept":
        accept_rules(q.from_user.id)
        await q.edit_message_text("✅ قوانین قبول شد")
        await q.message.reply_text("بزن /start")

    elif q.data == "video":
        user_state[q.from_user.id] = "video"
        await q.edit_message_text("🎬 حالا متن ویدیو را بفرست")

    elif q.data == "music":
        user_state[q.from_user.id] = "music"
        await q.edit_message_text("🎵 حالا متن آهنگ را بفرست")

    elif q.data == "coins":
        cur.execute("SELECT coins FROM users WHERE id=?", (q.from_user.id,))
        coins = cur.fetchone()[0]
        await q.edit_message_text(f"🪙 موجودی شما: {coins}")


# ---------------- MESSAGE HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    state = user_state.get(user_id)

    if state == "video":
        await update.message.reply_text("🎬 در حال ساخت ویدیو... (فعلاً خام)")

    elif state == "music":
        await update.message.reply_text("🎵 در حال ساخت آهنگ... (فعلاً خام)")

    else:
        await update.message.reply_text("از /start استفاده کن")


# ---------------- RUN BOT ----------------
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot Started")
app.run_polling()
