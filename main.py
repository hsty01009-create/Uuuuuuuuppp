from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from config import BOT_TOKEN
from database import create_db, add_user, accept_rules, is_accepted, get_coins
from ai import generate_music, generate_video, generate_voice

# ذخیره وضعیت کاربر: video / music / voice
user_state = {}


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await add_user(user_id)

    if not await is_accepted(user_id):
        btn = [[InlineKeyboardButton("✅ قبول قوانین", callback_data="accept")]]
        await update.message.reply_text(
            "برای استفاده از ربات باید قوانین را بپذیرید.",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    await menu(update)


# ---------------- MENU ----------------
async def menu(update: Update):
    buttons = [
        [InlineKeyboardButton("🎬 ساخت ویدیو", callback_data="video")],
        [InlineKeyboardButton("🎵 ساخت موسیقی", callback_data="music")],
        [InlineKeyboardButton("🗣 ساخت ویس", callback_data="voice")],
        [InlineKeyboardButton("🪙 موجودی سکه", callback_data="coins")]
    ]

    await update.message.reply_text(
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ---------------- CALLBACK ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "accept":
        await accept_rules(uid)
        await q.edit_message_text("✅ قوانین با موفقیت پذیرفته شد.")
        await menu_from_callback(q, context)
        return

    if q.data in ["video", "music", "voice"]:
        user_state[uid] = q.data

        if q.data == "video":
            text = "🎬 حالا متن یا توضیح ویدیو را ارسال کنید."
        elif q.data == "music":
            text = "🎵 حالا متن یا توضیح موسیقی را ارسال کنید."
        else:
            text = "🗣 حالا متن موردنظر برای تولید ویس را ارسال کنید."

        await q.edit_message_text(text)
        return

    if q.data == "coins":
        coins = await get_coins(uid)
        await q.edit_message_text(f"🪙 موجودی شما: {coins} سکه")
        return


async def menu_from_callback(q, context):
    buttons = [
        [InlineKeyboardButton("🎬 ساخت ویدیو", callback_data="video")],
        [InlineKeyboardButton("🎵 ساخت موسیقی", callback_data="music")],
        [InlineKeyboardButton("🗣 ساخت ویس", callback_data="voice")],
        [InlineKeyboardButton("🪙 موجودی سکه", callback_data="coins")]
    ]

    await q.message.reply_text(
        "یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ---------------- TEXT HANDLER ----------------
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.message.text
    state = user_state.get(uid)

    if state == "music":
        await update.message.reply_text("⏳ در حال ساخت موسیقی...")
        audio = await generate_music(msg)
        await update.message.reply_document(audio)

    elif state == "video":
        await update.message.reply_text("⏳ در حال ساخت ویدیو...")
        video = await generate_video(msg)
        await update.message.reply_document(video)

    elif state == "voice":
        await update.message.reply_text("⏳ در حال ساخت ویس...")
        voice = await generate_voice(msg)
        await update.message.reply_document(voice)

    else:
        await update.message.reply_text("لطفاً ابتدا یکی از گزینه‌های منو را انتخاب کنید.")


# ---------------- RUN ----------------
async def main():
    await create_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
