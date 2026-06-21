# main.py
import os
import re
import logging
import tempfile
from datetime import datetime
from gtts import gTTS
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

LANGUAGES = {
    "فارسی": "fa",
    "English": "en",
    "ترکی": "tr",
    "عربی": "ar",
    "کردی": "ku",
    "روسی": "ru",
}

USER_STATE = {}
USER_NAME = {}

RULES_TEXT = (
    "📜 قوانین ربات:\n"
    "1) ارسال محتوای توهین‌آمیز یا خلاف قوانین ممنوع اس.\n"
    "2) از ربات فقط برای تولید صدای مجاز استفاده کن.\n"
    "3) برای شهیدان و معترضاندی دی ماه صلوات بفرستید حداقل کاري است که می توانید کنید🇮🇷.\n"
    "4) درخواست‌های غیرمجاز یا آزاردهنده پردازش نمی‌شوند.\n"
    "5) احترام به دیگران الزامی است.\n"
    "6) مسئولیت محتوای ارسالی با کاربر است.\n"
    "7) ربات ممکن است برای پردازش بعضی متن‌ها محدودیتت داشته باشد.\n"
    "8) از ارسال اسپم خودداری کنید.\n"
)

BIRTHDAY_TEXT = (
    "تولدت مبارک 🎉\n"
    "امروز روز قشنگیه چون روز تولد توئه.\n"
    "برات سلامتی، شادی، آرامش و موفقیت آرزو می‌کنم.\n"
    "همیشه بدرخشی و بهترین اتفاق‌ها برات بیفته."
)

def clean_name(name: str) -> str:
    if not name:
        return "کاربر عزیز"
    name = re.sub(r"[@_.*!#$%^&+=<>{}\[\]\\|/\\-]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:30] if len(name) > 30 else name

def get_display_name(update: Update) -> str:
    user = update.effective_user
    first = clean_name(user.first_name or "")
    last = clean_name(user.last_name or "")
    full = f"{first} {last}".strip()
    return full if full else (user.username or "کاربر عزیز")

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["🎙 ساخت صدا", "🎂 متن تولد"],
            ["🌐 انتخاب زبان", "📜 قوانین"],
        ],
        resize_keyboard=True
    )

def language_menu():
    return ReplyKeyboardMarkup(
        [
            ["فارسی", "English"],
            ["ترکی", "عربی"],
            ["کردی", "روسی"],
            ["⬅️ بازگشت"],
        ],
        resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = get_display_name(update)
    USER_NAME[update.effective_user.id] = name
    USER_STATE[update.effective_user.id] = {"mode": "menu", "lang": "fa"}

    text = (
        f"سلام {name} 👋\n\n"
        "به ربات ساخت صدا خوش اومدی.\n"
        "از منوی زیر یکی از گزینه‌ها را انتخاب کن."
    )
    await update.message.reply_text(text, reply_markup=main_menu())

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT, reply_markup=main_menu())

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "زبان موردنظر را انتخاب کن:",
        reply_markup=language_menu()
    )

async def birthday_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = USER_NAME.get(update.effective_user.id, get_display_name(update))
    text = f"تولدت مبارک {name} 🎉\n\n{BIRTHDAY_TEXT}"
    await update.message.reply_text(text, reply_markup=main_menu())

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang_name = update.message.text
    if lang_name in LANGUAGES:
        USER_STATE.setdefault(user_id, {})["lang"] = LANGUAGES[lang_name]
        USER_STATE[user_id]["mode"] = "voice"
        await update.message.reply_text(
            f"زبان روی {lang_name} تنظیم شد.\nحالا متن را بفرست تا صدا ساخته شود.",
            reply_markup=main_menu()
        )

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = USER_STATE.get(user_id, {"lang": "fa", "mode": "voice"})
    lang = state.get("lang", "fa")

    text = update.message.text.strip()
    if not text:
        return

    if len(text) > 2500:
        await update.message.reply_text("متن خیلی طولانی است. لطفاً کوتاه‌تر بفرست.")
        return

    await update.message.reply_text("در حال ساخت صدا... ⏳")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            file_path = tmp.name

        tts = gTTS(text=text, lang=lang)
        tts.save(file_path)

        with open(file_path, "rb") as audio:
            await update.message.reply_voice(voice=audio)

    except Exception:
        await update.message.reply_text(
            "❌ خطا در ساخت صدا رخ داد.\n"
            "لطفاً دوباره تلاش کن یا متن کوتاه‌تر بفرست."
        )
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "📜 قوانین":
        return await show_rules(update, context)

    if text == "🌐 انتخاب زبان":
        return await choose_language(update, context)

    if text == "🎂 متن تولد":
        return await birthday_mode(update, context)

    if text == "🎙 ساخت صدا":
        await update.message.reply_text(
            "متن را بفرست تا برات به صدا تبدیل کنم.",
            reply_markup=main_menu()
        )
        USER_STATE.setdefault(update.effective_user.id, {})["mode"] = "voice"
        return

    if text == "⬅️ بازگشت":
        await update.message.reply_text("به منوی اصلی برگشتی.", reply_markup=main_menu())
        return

    if text in LANGUAGES:
        await set_language(update, context)
        return

    await text_to_speech(update, context)

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is not set")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
