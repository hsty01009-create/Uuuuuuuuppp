from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import BOT_TOKEN


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    buttons = [
        [InlineKeyboardButton("🎵 ساخت آهنگ", callback_data="music")],
        [InlineKeyboardButton("🎬 ساخت ویدیو", callback_data="video")],
        [InlineKeyboardButton("🪙 سکه من", callback_data="coins")]
    ]

    await update.message.reply_text(
        "سلام 👋\nربات ساخت آهنگ و ویدیو آماده است",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    if q.data == "music":
        await q.edit_message_text("🎵 متن آهنگ را بفرست")

    elif q.data == "video":
        await q.edit_message_text("🎬 متن ویدیو را بفرست")

    elif q.data == "coins":
        await q.edit_message_text("🪙 موجودی: 100 سکه")


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))


print("Bot started...")
app.run_polling()
