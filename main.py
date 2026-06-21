import logging
import os
import asyncio
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
from pydub import AudioSegment
import uuid # برای ایجاد نام فایل‌های موقت و منحصر به فرد
from dotenv import load_dotenv # برای بارگذاری متغیرهای محیطی از فایل .env

# --- تنظیمات ---
# بارگذاری متغیرهای محیطی از فایل .env (برای اجرای محلی)
load_dotenv()

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# خواندن توکن ربات از متغیر محیطی
# در Railway، این متغیر محیطی را تنظیم خواهید کرد.
# برای اجرای محلی، یک فایل .env در کنار این کد بسازید و در آن بنویسید:
# BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("خطا: متغیر محیطی BOT_TOKEN تنظیم نشده است.")
    raise ValueError("BOT_TOKEN is not set. Please set it in your environment or in a .env file.")

CREATOR_NAME = "امیر علی فروزان اصل"

# --- هندلرهای ربات ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور /start را مدیریت می‌کند."""
    user = update.effective_user
    await update.message.reply_html(
        rf"سلام {user.mention_html()}! من ربات تبدیل متن به صدا هستم."
        f"\nمن توسط {CREATOR_NAME} ساخته شده‌ام."
        "\nلطفاً متن خود را به فارسی یا انگلیسی برای من بفرستید تا آن را به صدا تبدیل کنم."
        "\nمی‌توانید زبان را با دستور /lang مشخص کنید (مثلاً /lang fa یا /lang en)."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور /help را مدیریت می‌کند."""
    await update.message.reply_text(
        "دستورات موجود:\n"
        "/start - شروع مکالمه و نمایش پیام خوش‌آمدگویی\n"
        "/help - نمایش این پیام راهنما\n"
        "/lang <fa|en> - تغییر زبان متن برای تبدیل به صدا (پیش‌فرض: فارسی)\n"
        "\nفقط کافیست متن مورد نظرتان را تایپ کنید و برای من بفرستید."
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """زبان تبدیل متن به صدا را تنظیم می‌کند."""
    chat_id = update.message.chat_id
    args = context.args

    if not args:
        await update.message.reply_text("لطفاً زبان را مشخص کنید. مثلاً: /lang fa یا /lang en")
        return

    lang_code = args[0].lower()
    if lang_code not in ["fa", "en"]:
        await update.message.reply_text("زبان نامعتبر است. لطفاً از 'fa' برای فارسی یا 'en' برای انگلیسی استفاده کنید.")
        return

    # ذخیره زبان در داده‌های کاربر (برای حفظ در طول مکالمه)
    context.user_data['language'] = lang_code
    await update.message.reply_text(f"زبان به '{'فارسی' if lang_code == 'fa' else 'انگلیسی'}' تغییر یافت.")

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """متن کاربر را گرفته و به صدا تبدیل می‌کند."""
    user_text = update.message.text
    chat_id = update.message.chat_id
    
    # دریافت زبان از داده‌های کاربر، اگر تنظیم نشده باشد، پیش‌فرض فارسی در نظر گرفته می‌شود
    lang = context.user_data.get('language', 'fa')

    logger.info(f"دریافت متن برای تبدیل به صدا از کاربر {update.effective_user.id} (زبان: {lang}): {user_text[:50]}...")

    await update.message.reply_text("⏳ در حال ساخت صدا...")

    try:
        # --- تولید فایل صوتی با gTTS ---
        tts = gTTS(text=user_text, lang=lang, slow=False) # slow=False برای سرعت عادی
        
        # ایجاد یک نام فایل منحصر به فرد برای ذخیره موقت
        temp_filename = f"temp_audio_{uuid.uuid4()}.mp3"
        tts.save(temp_filename)
        
        # --- تبدیل فرمت با pydub (اختیاری، اگر لازم باشد) ---
        # gTTS مستقیماً MP3 تولید می‌کند، اما اگر فرمت دیگری نیاز بود، اینجا تبدیل انجام می‌شود
        # audio = AudioSegment.from_mp3(temp_filename)
        # converted_filename = f"output_audio_{uuid.uuid4()}.ogg" # مثال: تبدیل به OGG
        # audio.export(converted_filename, format="ogg")
        
        # --- ارسال فایل صوتی به تلگرام ---
        # برای ارسال به عنوان فایل صوتی، از InputFile استفاده می‌کنیم
        audio_file = InputFile(temp_filename)
        
        await update.message.reply_audio(audio_file, caption=f"صدای تولید شده از متن شما (زبان: {lang})")
        
        # --- پاک کردن فایل موقت ---
        os.remove(temp_filename)
        # if os.path.exists(converted_filename):
        #     os.remove(converted_filename)

    except Exception as e:
        logger.error(f"خطای غیرمنتظره در تبدیل متن به صدا: {e}")
        await update.message.reply_text("😥 متاسفانه خطایی در ساخت صدا رخ داد. لطفاً دوباره امتحان کنید.")
        # پاک کردن فایل موقت در صورت بروز خطا
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)

def main() -> None:
    """ربات را راه‌اندازی می‌کند."""
    if not BOT_TOKEN:
        logger.error("توکن ربات تنظیم نشده است. لطفاً متغیر محیطی BOT_TOKEN را تنظیم کنید.")
        return

    # ساخت Application
    application = Application.builder().token(BOT_TOKEN).build()

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("lang", set_language))
    
    # هندلر پیام متنی که دستور نیست
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))

    logger.info("ربات شروع به کار کرد. منتظر دستورات...")

    # اجرای ربات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
