import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from gtts import gTTS
from config import TEMP_DIR
from keyboards import kb_main_menu, kb_remove
import os

logger = logging.getLogger(__name__)

# --- State مربوط به تبدیل متن به صدا ---
TTS_WAIT_TEXT = range(1)

async def do_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تبدیل متن ارسالی کاربر به صدا و ارسال فایل MP3."""
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if not text:
        await update.message.reply_text("متن خالی است. لطفاً دوباره ارسال کنید:")
        return TTS_WAIT_TEXT

    try:
        # مسیر فایل صوتی موقت
        filename = TEMP_DIR / f"tts_{user_id}_{hash(text)}.mp3" # Unique filename based on text too
        
        # زبان را از دیتابیس بخوانید یا از پیش‌فرض استفاده کنید
        lang = context.user_data.get("language", "fa") # Assuming language is stored in user_data or db
        # اگر زبان در user_data نیست، از دیتابیس بخوانید
        if not lang:
            from db import get_user
            user_data = get_user(user_id)
            lang = user_data.get('language', 'fa') if user_data else 'fa'

        tts = gTTS(text=text, lang=lang)
        tts.save(str(filename))

        with open(filename, "rb") as f:
            await update.message.reply_voice(voice=f)

        # پاک کردن فایل موقت پس از ارسال
        if filename.exists():
            os.remove(filename)

        logger.info(f"TTS audio file created and sent for user {user_id}.")
        await update.message.reply_text("فایل صوتی با موفقیت ایجاد و ارسال شد.", reply_markup=kb_main_menu())
        return ConversationHandler.END # بازگشت به منوی اصلی

    except Exception as e:
        logger.error(f"TTS processing failed for user {user_id}: {e}")
        await update.message.reply_text(
            "متاسفانه خطایی در پردازش صدا رخ داد. لطفاً کمی صبر کنید و دوباره امتحان کنید.",
            reply_markup=kb_main_menu()
        )
        # پاک کردن فایل در صورت ایجاد بخشی از آن
        if 'filename' in locals() and filename.exists():
            os.remove(filename)
        return ConversationHandler.END # بازگشت به منوی اصلی حتی در صورت خطا
