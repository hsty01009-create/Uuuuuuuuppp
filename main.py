from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
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
    cur.execute(
        "INSERT OR IGNORE INTO users(id) VALUES(?)",
        (user_id,)
    )
    db.commit()


def accept_rules(user_id):
    cur.execute(
        "UPDATE users SET accepted=1 WHERE id=?",
        (user_id,)
    )
    db.commit()


def check_rules(user_id):
    cur.execute(
        "SELECT accepted FROM users WHERE id=?",
        (user_id,)
    )
    data = cur.fetchone()

    if data:
        return data[0] == 1

    return False


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    add_user(user)

    if not check_rules(user):

        btn = [
            [
                InlineKeyboardButton(
                    "✅ قبول قوانین",
                    callback_data="accept"
                )
            ]
        ]

        await update.message.reply_text(
            """
📜 قوانین ربات:

1- استفاده درست از ربات الزامی است
2- اسپم ممنوع است
3- محتوای غیرقانونی ممنوع است
4- احترام به کاربران رعایت شود
5- سوء استفاده از ربات ممنوع است
6- فایل خطرناک ارسال نکنید
7- سکه‌ها طبق سیستم ربات هستند
8- دعوت باید واقعی باشد
9- ربات رایگان است
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
        [
            InlineKeyboardButton("🎬 ساخت ویدیو", callback_data="video")
        ],
        [
            InlineKeyboardButton("🎵 ساخت آهنگ", callback_data="music")
        ],
        [
            InlineKeyboardButton("🪙 سکه من", callback_data="coins")
        ]
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

        await q.message.reply_text("منوی ربات فعال شد /start")

    elif q.data == "video":

        await q.edit_message_text("🎬 متن ویدیو را بفرست")

    elif q.data == "music":

        await q.edit_message_text("🎵 متن آهنگ را بفرست")

    elif q.data == "coins":

        cur.execute(
            "SELECT coins FROM users WHERE id=?",
            (q.from_user.id,)
        )

        coins = cur.fetchone()[0]

        await q.edit_message_text(f"🪙 موجودی شما: {coins}")


# ---------------- RUN BOT ----------------
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Bot Started")
app.run_polling()
