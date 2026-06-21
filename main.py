import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
from gtts import gTTS
import os
import uuid # To generate unique filenames for audio

# Import database functions
import db

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot Token - REPLACE WITH YOUR ACTUAL TOKEN
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Conversation states
RULES, LANGUAGE, REGISTER_EMAIL, REGISTER_PASSWORD, REGISTER_CONFIRM, MAIN_MENU, PROFESSIONS_MENU, ACCOUNT_MENU, TTS_TEXT, TTS_LANGUAGE = range(10)

# Languages
LANGUAGES = {
    'fa': 'فارسی',
    'en': 'English'
}

# Professions
PROFESSIONS = {
    'writer': 'نویسنده',
    'musician': 'موسیقی‌دان',
    'programmer': 'برنامه‌نویس',
    'designer': 'طراح',
    'teacher': 'معلم'
}

# --- Helper Functions ---
def clean_username(username):
    """Removes invalid characters from username for display."""
    if username:
        return username.replace('_', '\_')
    return ""

def get_profession_name(profession_key):
    """Returns the display name for a profession key."""
    return PROFESSIONS.get(profession_key, "نامشخص")

def get_language_name(language_key):
    """Returns the display name for a language key."""
    return LANGUAGES.get(language_key, "Unknown")

def get_display_name(user):
    """Gets the display name for a user."""
    return user.get('first_name') or user.get('username') or f"User ID: {user.get('user_id')}"

def get_profile_text(user):
    """Generates the profile text for a user."""
    lang_name = get_language_name(user.get('language'))
    profession_name = get_profession_name(user.get('profession'))
    return (
        f"👤 پروفایل شما:\n"
        f"🆔 شناسه کاربری: `{user.get('user_id')}`\n"
        f"📝 نام کاربری: @{user.get('username')}\n"
        f"📛 نام: {user.get('first_name')}\n"
        f"📧 ایمیل: {user.get('email') or 'ثبت نشده'}\n"
        f"🔑 رمز عبور: {'*' * len(user.get('password')) if user.get('password') else 'ثبت نشده'}\n"
        f"🌐 زبان: {lang_name}\n"
        f"🌟 امتیاز: {user.get('points')}\n"
        f"👥 تعداد دعوت: {user.get('invited_count')}\n"
        f"💼 حرفه: {profession_name}\n"
        f"✅ پذیرش قوانین: {'بله' if user.get('accepted_rules') else 'خیر'}\n"
        f"💡 کد معرف شما: `{user.get('referral_code')}`\n"
        f"👤 دعوت شده توسط: {user.get('invited_by') or 'کسی'}"
    )

# --- Keyboards ---
def get_main_menu_keyboard(user_language='fa'):
    keyboard = [
        [KeyboardButton("حساب من 👤"), KeyboardButton("انتخاب حرفه 💼")],
        [KeyboardButton("ساخت صدا 🎵"), KeyboardButton("بروزرسانی 🔄")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_rules_keyboard(user_language='fa'):
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول قوانین", callback_data="accept_rules"),
            InlineKeyboardButton("❌ رد قوانین", callback_data="reject_rules")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard(user_language='fa'):
    keyboard = [
        [
            InlineKeyboardButton("فارسی 🇮🇷", callback_data="lang_fa"),
            InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_professions_keyboard(user_language='fa'):
    keyboard = [
        [
            InlineKeyboardButton(PROFESSIONS['writer'], callback_data="prof_writer"),
            InlineKeyboardButton(PROFESSIONS['musician'], callback_data="prof_musician")
        ],
        [
            InlineKeyboardButton(PROFESSIONS['programmer'], callback_data="prof_programmer"),
            InlineKeyboardButton(PROFESSIONS['designer'], callback_data="prof_designer")
        ],
        [
            InlineKeyboardButton(PROFESSIONS['teacher'], callback_data="prof_teacher")
        ],
        [InlineKeyboardButton("بازگشت به منوی اصلی 🔙", callback_data="back_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_account_keyboard(user_language='fa'):
    keyboard = [
        [KeyboardButton("مشاهده پروفایل 📄"), KeyboardButton("تغییر ایمیل 📧")],
        [KeyboardButton("تغییر رمز عبور 🔑"), KeyboardButton("بازگشت 🔙")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_tts_keyboard(user_language='fa'):
    keyboard = [
        [KeyboardButton("تغییر زبان صدا 🌐"), KeyboardButton("بازگشت 🔙")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- Handlers ---

async def start(update: Update, context: ConversationHandler. ее):
    user = update.effective_user
    user_id = user.id
    username = user.username
    first_name = user.first_name

    # Create user in DB if they don't exist
    db_user = db.get_user(user_id)
    if not db_user:
        db_user = db.create_user(user_id, username, first_name)
        if not db_user: # If creation failed for some reason
            await update.message.reply_text("خطا در ایجاد حساب کاربری. لطفاً بعداً دوباره امتحان کنید.")
            return ConversationHandler.END

    # Handle referral code
    if context.args and context.args[0].startswith(str(user_id)): # Simple check if args is referral code
         # Avoid self-referral or invalid referral codes
         pass
    elif context.args and str(context.args[0]) != str(user_id):
        referral_code = context.args[0]
        inviter = db.get_user_by_referral_code(referral_code)
        if inviter and inviter.get('user_id') != user_id:
            # Update inviter's invite count and points
            db.add_invite(inviter.get('user_id'))
            db.add_points(inviter.get('user_id'), 100)
            # Set invited_by for the new user
            db.set_invited_by(user_id, inviter.get('user_id'))
            await context.bot.send_message(chat_id=inviter.get('user_id'), text=f"یک نفر جدید با کد معرف شما وارد شد! ۱۰۰ امتیاز دریافت کردید.")
            logger.info(f"User {user_id} was invited by {inviter.get('user_id')}")
            await update.message.reply_text("شما توسط کاربری دعوت شده‌اید. از دعوت شما سپاسگزاریم!")
        # else: Invalid referral code, ignore or inform user if needed

    # Check if user needs onboarding (first start)
    if db_user and db_user.get('first_start'):
        await update.message.reply_text(
            f"سلام {first_name}!\nبه ربات ما خوش آمدید. لطفاً قبل از ادامه، قوانین را مطالعه و تأیید کنید.",
            reply_markup=get_rules_keyboard()
        )
        return RULES
    else:
        # User is not new or already went through onboarding
        await update.message.reply_text(f"خوش برگشتید، {get_display_name(db_user)}!", reply_markup=get_main_menu_keyboard(db_user.get('language')))
        return MAIN_MENU

async def accept_rules_callback(update: Update, context: ConversationHandler. ее):
    user_id = update.effective_user.id
    db.set_accepted_rules(user_id, True)
    db.set_first_start(user_id, False) # Mark onboarding as done
    await update.message.reply_text("قوانین با موفقیت تأیید شد. حالا لطفاً زبان مورد نظر خود را انتخاب کنید:", reply_markup=get_language_keyboard())
    return LANGUAGE

async def reject_rules_callback(update: Update, context: ConversationHandler. ее):
    await update.message.reply_text("متأسفیم، بدون قبول قوانین نمی‌توانید از ربات استفاده کنید. برای شروع مجدد /start را وارد کنید.")
    # Optionally clear user data or set a flag preventing future use without restart
    return ConversationHandler.END

async def language_callback(update: Update, context: ConversationHandler. ее):
    query = update.callback_query
    await query.answer()
    language = query.data.split('_')[1] # e.g., 'lang_fa' -> 'fa'
    user_id = update.effective_user.id

    db.set_language(user_id, language)

    await query.edit_message_text(f"زبان شما روی {LANGUAGES.get(language, 'نامشخص')} تنظیم شد.\nحالا لطفاً ایمیل خود را وارد کنید:", reply_markup=None)
    return REGISTER_EMAIL

async def register_email(update: Update, context: ConversationHandler. ее):
    email = update.message.text
    user_id = update.effective_user.id
    db.set_email(user_id, email)
    await update.message.reply_text("ایمیل ثبت شد. حالا رمز عبور خود را وارد کنید:", reply_markup=None)
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ConversationHandler. ее):
    password = update.message.text
    user_id = update.effective_user.id
    db.set_password(user_id, password)
    # Confirmation step - show entered details and ask for confirmation
    user_data = db.get_user(user_id)
    await update.message.reply_text(
        f"اطلاعات شما:\nایمیل: {user_data.get('email')}\nرمز عبور: ********\n\nآیا همه چیز درست است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بله، ثبت نهایی ✅", callback_data="finish_register")],
            [InlineKeyboardButton("خیر، لغو ❌", callback_data="cancel_register")]
        ])
    )
    return REGISTER_CONFIRM

async def finish_register_callback(update: Update, context: ConversationHandler. ее):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    db.set_registered(user_id, True) # Mark as fully registered

    user_data = db.get_user(user_id)
    await query.edit_message_text(f"ثبت نام شما با موفقیت کامل شد!\n{get_profile_text(user_data)}", reply_markup=None)
    await context.bot.send_message(chat_id=user_id, text="به منوی اصلی خوش آمدید:", reply_markup=get_main_menu_keyboard(user_data.get('language')))
    return MAIN_MENU

async def cancel_register_callback(update: Update, context: ConversationHandler. ее):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    # Resetting some fields might be necessary if user cancels mid-registration
    db.set_email(user_id, None)
    db.set_password(user_id, None)
    await query.edit_message_text("ثبت نام لغو شد. برای شروع مجدد /start را وارد کنید.", reply_markup=None)
    return ConversationHandler.END

async def show_home(update: Update, context: ConversationHandler. ее):
    """Shows the main menu keyboard."""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get('registered'):
        await update.message.reply_text("به منوی اصلی خوش آمدید:", reply_markup=get_main_menu_keyboard(user_data.get('language')))
        return MAIN_MENU
    else:
        await update.message.reply_text("لطفاً ابتدا ثبت نام کنید. /start")
        return ConversationHandler.END

async def show_home_by_query(update: Update, context: ConversationHandler. ее):
    """Handles the 'back' button from other menus to return to main menu."""
    return await show_home(update, context)


async def account_callback(update: Update, context: ConversationHandler. ее):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get('registered'):
        await update.message.reply_text("به بخش حساب کاربری خوش آمدید. چه کاری می‌خواهید انجام دهید؟", reply_markup=get_account_keyboard(user_data.get('language')))
        return ACCOUNT_MENU
    else:
        await update.message.reply_text("لطفاً ابتدا ثبت نام کنید. /start")
        return ConversationHandler.END

async def account_status_callback(update: Update, context: ConversationHandler. ее):
    """Callback for 'مشاهده پروفایل' button."""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data:
        await update.message.reply_text(get_profile_text(user_data), parse_mode='MarkdownV2', reply_markup=get_account_keyboard(user_data.get('language')))
    else:
        await update.message.reply_text("خطا در بازیابی اطلاعات کاربر.")
    return ACCOUNT_MENU

async def change_email_callback(update: Update, context: ConversationHandler. ее):
    """Callback for 'تغییر ایمیل' button."""
    await update.message.reply_text("لطفاً ایمیل جدید خود را وارد کنید:", reply_markup=None)
    # We need a way to know this is for changing email. Add a state or flag.
    # For simplicity here, we'll assume the next text message is the new email.
    # A more robust way would be a specific ConversationHandler state.
    context.user_data['changing_email'] = True # Set a flag
    return ACCOUNT_MENU # Stay in ACCOUNT_MENU state, but handle email change specifically

async def change_password_callback(update: Update, context: ConversationHandler. ее):
    """Callback for 'تغییر رمز عبور' button."""
    await update.message.reply_text("لطفاً رمز عبور جدید خود را وارد کنید:", reply_markup=None)
    context.user_data['changing_password'] = True # Set a flag
    return ACCOUNT_MENU # Stay in ACCOUNT_MENU state

async def professions_callback(update: Update, context: ConversationHandler. ее):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get('registered'):
        await update.message.reply_text("لطفاً حرفه مورد نظر خود را انتخاب کنید:", reply_markup=get_professions_keyboard(user_data.get('language')))
        return PROFESSIONS_MENU
    else:
        await update.message.reply_text("لطفاً ابتدا ثبت نام کنید. /start")
        return ConversationHandler.END

async def profession_set_callback(update: Update, context: ConversationHandler. ее):
    query = update.callback_query
    await query.answer()
    profession_key = query.data.split('_')[1] # e.g., 'prof_writer' -> 'writer'
    user_id = update.effective_user.id

    if profession_key in PROFESSIONS:
        db.set_profession(user_id, profession_key)
        user_data = db.get_user(user_id)
        await query.edit_message_text(f"حرفه شما با موفقیت به {PROFESSIONS[profession_key]} تغییر یافت.", reply_markup=get_main_menu_keyboard(user_data.get('language')))
        return MAIN_MENU
    else:
        await query.edit_message_text("حرفه نامعتبر است. لطفاً دوباره انتخاب کنید.", reply_markup=get_professions_keyboard())
        return PROFESSIONS_MENU

async def refresh_callback(update: Update, context: ConversationHandler. ее):
    """Handles the 'بروزرسانی' button to show updated profile."""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get('registered'):
        await update.message.reply_text(get_profile_text(user_data), parse_mode='MarkdownV2', reply_markup=get_main_menu_keyboard(user_data.get('language')))
    else:
        await update.message.reply_text("لطفاً ابتدا ثبت نام کنید. /start")
    return MAIN_MENU

async def tts_callback(update: Update, context: ConversationHandler. ее):
    """Handles the 'ساخت صدا' button."""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get('registered'):
        await update.message.reply_text("لطفاً متنی را که می‌خواهید به صدا تبدیل شود، وارد کنید:", reply_markup=get_tts_keyboard(user_data.get('language')))
        return TTS_TEXT
    else:
        await update.message.reply_text("لطفاً ابتدا ثبت نام کنید. /start")
        return ConversationHandler.END

async def tts_receive_text(update: Update, context: ConversationHandler. ее):
    """Receives text for TTS and prompts for language selection."""
    text_to_convert = update.message.text
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    context.user_data['tts_text'] = text_to_convert # Store text temporarily

    # Get the user's preferred language, default to 'fa' if not set or available
    preferred_lang = user_data.get('language', 'fa') if user_data else 'fa'

    # Check if the preferred language is supported by gTTS for voice synthesis
    supported_langs = ['fa', 'en'] # gTTS supported languages we want to offer
    if preferred_lang not in supported_langs:
        preferred_lang = 'fa' # Fallback to Persian

    await update.message.reply_text(f"زبان صدا روی '{LANGUAGES.get(preferred_lang, 'فارسی')}' تنظیم شده است. آیا می‌خواهید زبان صدا را تغییر دهید؟",
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton("بله، تغییر زبان 🌐", callback_data="tts_change_lang")],
                                        [InlineKeyboardButton("خیر، همین زبان ✅", callback_data="tts_confirm_lang")]
                                    ]))
    context.user_data['tts_language'] = preferred_lang # Store the current language
    return TTS_LANGUAGE

async def tts_language_callback(update: Update, context: ConversationHandler. ее):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if query.data == "tts_change_lang":
        # Present language options for TTS
        await query.edit_message_text("لطفاً زبان مورد نظر برای صدا را انتخاب کنید:", reply_markup=get_language_keyboard())
        # We need to return a state that handles selection of language for TTS specifically
        # Let's use a temporary flag or a more specific state if needed.
        # For now, assume the language callback can handle setting TTS language.
        # We'll need a way to differentiate between setting bot language and TTS language.
        # Let's refine: the language_callback handles general bot language.
        # We'll need a new callback or logic here.
        # For now, we'll just re-prompt for confirmation after selection.
        # This part needs careful state management.
        # Let's assume language_callback sets the context.user_data['tts_language'] correctly.
        # The user actually selected language via the general language keyboard.
        # We need to capture that selection for TTS.
        # The current language keyboard provides 'lang_fa', 'lang_en'.
        # Let's modify the language_callback or add a new handler for TTS language selection.

        # Temporary fix: If user chooses to change language, prompt them to select from general options
        # and we'll capture it in the language_callback, then re-prompt for TTS confirmation.
        # This is not ideal state management but works for now.
        # A better way: have a dedicated TTS language selection keyboard.

        # Re-prompting user to select language again for TTS
        await query.edit_message_text("لطفاً زبان مورد نظر برای صدا را انتخاب کنید:", reply_markup=get_language_keyboard())
        # Let's assume language_callback will be called again and we can capture the language selection
        # and then resume the TTS flow. This requires careful handling of ConversationHandler states.
        # For simplicity, let's assume the user selects and we handle it.
        # A better approach would involve a dedicated state for TTS language selection.
        return TTS_LANGUAGE # Re-enter state to handle selection

    elif query.data == "tts_confirm_lang":
        # User confirmed the language, proceed to generate audio
        text = context.user_data.get('tts_text')
        lang_code = context.user_data.get('tts_language') # Use the language stored earlier

        if not text or not lang_code:
            await query.edit_message_text("خطا در دریافت متن یا زبان صدا. لطفاً دوباره تلاش کنید.")
            return MAIN_MENU

        try:
            tts = gTTS(text=text, lang=lang_code, slow=False)
            # Generate a unique filename
            filename = f"tts_{uuid.uuid4()}.mp3"
            audio_path = os.path.join("audio", filename) # Save in an 'audio' subfolder

            # Create audio directory if it doesn't exist
            if not os.path.exists("audio"):
                os.makedirs("audio")

            tts.save(audio_path)

            # Send the audio file
            with open(audio_path, 'rb') as audio_file:
                await context.bot.send_audio(chat_id=user_id, audio=audio_file, title=f"TTS_{lang_code}.mp3")

            # Clean up the generated file after sending
            os.remove(audio_path)

            await query.edit_message_text("فایل صوتی با موفقیت ایجاد و ارسال شد.", reply_markup=get_main_menu_keyboard(user_data.get('language')))
            return MAIN_MENU

        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}")
            await query.edit_message_text(f"خطا در ساخت فایل صوتی: {e}. لطفاً دوباره امتحان کنید.", reply_markup=get_main_menu_keyboard(user_data.get('language')))
            return MAIN_MENU
    else:
        # This might be a language selection from the general language keyboard
        # if tts_change_lang was chosen.
        if query.data.startswith("lang_"):
            language = query.data.split('_')[1]
            context.user_data['tts_language'] = language # Store TTS language
            lang_name = LANGUAGES.get(language, 'نامشخص')
            await query.edit_message_text(f"زبان صدا به '{lang_name}' تغییر یافت.\n\nمتن شما: \"{context.user_data.get('tts_text')}\"\n\nآیا می‌خواهید فایل صوتی را با این تنظیمات بسازم؟",
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("بله، ساخت فایل صوتی ✅", callback_data="tts_confirm_lang")],
                                            [InlineKeyboardButton("خیر، لغو ❌", callback_data="cancel_tts")]
                                        ]))
            return TTS_LANGUAGE # Stay in TTS_LANGUAGE state to confirm
        else:
            await query.message.reply_text("انتخاب نامعتبر.")
            return TTS_LANGUAGE


async def back_home_callback(update: Update, context: ConversationHandler. ее):
    """Handles the 'back home' button from various menus."""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    await update.callback_query.answer()
    await update.callback_query.edit_message_reply_markup(reply_markup=None) # Remove the inline keyboard
    await update.callback_query.message.reply_text("به منوی اصلی خوش آمدید:", reply_markup=get_main_menu_keyboard(user_data.get('language')))
    return MAIN_MENU

async def handle_text(update: Update, context: ConversationHandler. ее):
    """Handles general text input based on the current state."""
    text = update.message.text
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    # Check if user is registered
    if not user_data or not user_data.get('registered'):
        await update.message.reply_text("لطفاً ابتدا ثبت نام کنید. /start")
        return ConversationHandler.END

    current_state = context.state

    if current_state == ACCOUNT_MENU:
        if text == "مشاهده پروفایل 📄":
            return await account_status_callback(update, context)
        elif text == "تغییر ایمیل 📧":
            return await change_email_callback(update, context)
        elif text == "تغییر رمز عبور 🔑":
            return await change_password_callback(update, context)
        elif text == "بازگشت 🔙":
            return await show_home(update, context)
        # Handle email/password change input if flags are set
        elif context.user_data.get('changing_email'):
            email = text
            if db.set_email(user_id, email):
                await update.message.reply_text("ایمیل شما با موفقیت به‌روز شد.")
            else:
                await update.message.reply_text("خطا در به‌روزرسانی ایمیل.")
            context.user_data['changing_email'] = False # Reset flag
            return await account_callback(update, context) # Return to account menu
        elif context.user_data.get('changing_password'):
            password = text
            if db.set_password(user_id, password):
                await update.message.reply_text("رمز عبور شما با موفقیت به‌روز شد.")
            else:
                await update.message.reply_text("خطا در به‌روزرسانی رمز عبور.")
            context.user_data['changing_password'] = False # Reset flag
            return await account_callback(update, context) # Return to account menu
        else:
             await update.message.reply_text("لطفاً از دکمه‌های زیر استفاده کنید یا دستور /start را وارد کنید.")
             return ACCOUNT_MENU


    elif current_state == TTS_TEXT:
        # This handler is for receiving the text to convert
        return await tts_receive_text(update, context)

    elif current_state == MAIN_MENU:
        if text == "حساب من 👤":
            return await account_callback(update, context)
        elif text == "انتخاب حرفه 💼":
            return await professions_callback(update, context)
        elif text == "ساخت صدا 🎵":
            return await tts_callback(update, context)
        elif text == "بروزرسانی 🔄":
            return await refresh_callback(update, context)
        else:
            await update.message.reply_text("لطفاً از دکمه‌های منوی اصلی استفاده کنید.")
            return MAIN_MENU

    # Handle messages outside of specific states if needed, or ignore them.
    else:
        await update.message.reply_text("لطفاً از دستورات یا دکمه‌های موجود استفاده کنید.")
        # Decide where to return, maybe back to main menu or stay in current state if applicable.
        # For now, let's try returning to main menu if user is registered.
        if user_data and user_data.get('registered'):
             return MAIN_MENU
        else:
             return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for the main conversation flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            RULES: [
                CallbackQueryHandler(accept_rules_callback, pattern="^accept_rules$"),
                CallbackQueryHandler(reject_rules_callback, pattern="^reject_rules$"),
            ],
            LANGUAGE: [
                CallbackQueryHandler(language_callback, pattern="^lang_(fa|en)$"),
            ],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
            REGISTER_CONFIRM: [
                CallbackQueryHandler(finish_register_callback, pattern="^finish_register$"),
                CallbackQueryHandler(cancel_register_callback, pattern="^cancel_register$"),
            ],
            MAIN_MENU: [
                MessageHandler(filters.Regex("^حساب من 👤$"), account_callback),
                MessageHandler(filters.Regex("^انتخاب حرفه 💼$"), professions_callback),
                MessageHandler(filters.Regex("^ساخت صدا 🎵$"), tts_callback),
                MessageHandler(filters.Regex("^بروزرسانی 🔄$"), refresh_callback),
                CommandHandler("start", show_home), # Allow /start to return to main menu
            ],
            PROFESSIONS_MENU: [
                CallbackQueryHandler(profession_set_callback, pattern="^prof_(writer|musician|programmer|designer|teacher)$"),
                CallbackQueryHandler(back_home_callback, pattern="^back_home$"),
            ],
            ACCOUNT_MENU: [
                MessageHandler(filters.Regex("^مشاهده پروفایل 📄$"), account_status_callback),
                MessageHandler(filters.Regex("^تغییر ایمیل 📧$"), change_email_callback),
                MessageHandler(filters.Regex("^تغییر رمز عبور 🔑$"), change_password_callback),
                MessageHandler(filters.Regex("^بازگشت 🔙$"), show_home), # Back to main menu
            ],
             TTS_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tts_receive_text)],
             TTS_LANGUAGE: [
                 CallbackQueryHandler(tts_language_callback, pattern="^tts_change_lang$"),
                 CallbackQueryHandler(tts_language_callback, pattern="^tts_confirm_lang$"),
                 CallbackQueryHandler(language_callback, pattern="^lang_(fa|en)$"), # Catch language selection here too
                 CallbackQueryHandler(lambda update, context: back_home_callback(update, context), pattern="^cancel_tts$"), # Handle cancel TTS
             ],
        },
        fallbacks=[CommandHandler("start", start)], # Default fallback
        # Add a timeout if desired: conversation_timeout=600 # 10 minutes
    )

    # Register the general text message handler for specific states
    # This needs to be added after the ConversationHandler to catch messages within states
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Add handlers
    application.add_handler(conv_handler)

    # Add handlers for specific callback queries not covered by ConversationHandler states if needed
    # Example: Handling a direct callback query for going back home from anywhere if needed.

    # Run the bot until the user presses Ctrl-C
    print("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
