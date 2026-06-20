import os
import time
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from TTS.api import TTS

# مشخصات سازنده
CREATOR = "امیر علی فروزان اصل"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

user_status = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_status[user_id] = {'accepted': False, 'gender': None}
    
    rules_text = (
        f"✨ *خوش آمدید به ربات هوش مصنوعی حرفه‌ای*\n\n"
        f"📜 *قوانین استفاده:*\n"
        f"۱. استفاده از ربات برای مقاصد غیرقانونی ممنوع است.\n"
        f"۲. مسئولیت هرگونه استفاده بر عهده کاربر است.\n\n"
        f"👤 *سازنده:* {CREATOR}"
    )
    
    keyboard = [[InlineKeyboardButton("✅ قبول قوانین و شروع", callback_data='accept')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(rules_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'accept':
        user_status[user_id]['accepted'] = True
        keyboard = [
            [InlineKeyboardButton("👩 صدای زن (Female)", callback_data='female')],
            [InlineKeyboardButton("👨 صدای مرد (Male)", callback_data='male')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("✅ قوانین تایید شد. حالا جنسیت صدا را انتخاب کنید:", reply_markup=reply_markup)

    elif query.data in ['female', 'male']:
        user_status[user_id]['gender'] = query.data
        gender_name = "زن" if query.data == 'female' else "مرد"
        await query.edit_message_text(f"✅ مدل صدای {gender_name} انتخاب شد.\n\n📝 حالا متن خود را بفرستید.")

async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_status.get(user_id, {}).get('accepted'):
        await update.message.reply_text("❌ ابتدا باید قوانین را قبول کنید.")
        return
    
    if not user_status.get(user_id, {}).get('gender'):
        await update.message.reply_text("⚠️ ابتدا جنسیت را انتخاب کنید.")
        return

    user_text = update.message.text
    status_msg = await update.message.reply_text("🚀 در حال ساخت صدا توسط هوش مصنوعی...")

    try:
        output_path = f"voice_{user_id}.wav"
        # استفاده از مدل بسیار باکیفیت Coqui
        tts = TTS(model_name="tts_models/en/ljspeech/vits", progress_bar=False)
        tts.tts_to_file(text=user_text, file_path=output_path)

        await update.message.reply_voice(
            voice=open(output_path, 'rb'),
            caption=f"✅ آماده شد!\n👤 سازنده: {CREATOR}"
        )
        os.remove(output_path)
        await status_msg.delete()
    except Exception as e:
        await update.message.reply_text("❌ خطا در تولید صدا.")

def main():
    # حتما توکن خود را اینجا بگذارید
    TOKEN = "توکن_ربات_خودرا_اینجا_بگذار"
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))
    application.run_polling()

if __name__ == '__main__':
    main()
