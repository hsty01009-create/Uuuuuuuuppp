import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from gtts import gTTS
import os
import uuid

# Import database functions
import db

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" # Replace with your actual bot token

# Conversation states
RULES, LANGUAGE, REGISTER_EMAIL, REGISTER_PASSWORD, REGISTER_CONFIRM, MAIN_MENU, PROFESSIONS_MENU, ACCOUNT_MENU, TTS_TEXT, TTS_LANGUAGE = range(10)

# --- Helper Functions ---

def clean_username(username):
    """Removes special characters from username if needed, though telegram usernames are usually fine."""
    if username:
        return "".join(c for c in username if c.isalnum() or c in ['_'])
    return None

def get_profession_name(profession_key, lang='fa'):
    """Returns the display name of a profession based on its key."""
    professions = {
        'writer': {'fa': 'نویسنده', 'en': 'Writer'},
        'musician': {'fa': 'موسیقی‌دان', 'en': 'Musician'},
        'programmer': {'fa': 'برنامه‌نویس', 'en': 'Programmer'},
        'designer': {'fa': 'طراح', 'en': 'Designer'},
        'teacher': {'fa': 'معلم', 'en': 'Teacher'},
    }
    return professions.get(profession_key, {}).get(lang, profession_key.capitalize())

def get_language_name(lang_key):
    """Returns the display name of a language."""
    languages = {'fa': 'فارسی', 'en': 'English'}
    return languages.get(lang_key, lang_key)

def get_display_name(user):
    """Returns the best available display name for the user."""
    return user.get('first_name') or user.get('username') or f"User {user['user_id']}"

def get_profile_text(user):
    """Generates the profile information text."""
    lang = user.get('language', 'fa')
    profession_name = get_profession_name(user.get('profession'), lang) if user.get('profession') else "انتخاب نشده"
    registered_status = "ثبت نام شده" if user.get('registered') else "ثبت نام نشده"

    profile = f"**اطلاعات حساب کاربری شما:**\n\n"
    profile += f"ID: `{user['user_id']}`\n"
    if user.get('username'):
        profile += f"Username: @{user['username']}\n"
    if user.get('first_name'):
        profile += f"نام: {user['first_name']}\n"
    if user.get('email'):
        profile += f"ایمیل: {user['email']}\n"
    profile += f"زبان: {get_language_name(lang)}\n"
    profile += f"امتیاز: {user.get('points', 0)}\n"
    profile += f"تعداد دعوت‌ها: {user.get('invited_count', 0)}\n"
    profile += f"حرفه: {profession_name}\n"
    profile += f"وضعیت ثبت نام: {registered_status}\n"

    if user.get('invited_by'):
        inviter = db.get_user(user.get('invited_by'))
        if inviter:
            inviter_name = get_display_name(inviter)
            profile += f"توسط: {inviter_name} (ID: `{inviter['user_id']}`)\n"

    return profile

# --- Keyboards ---

def main_menu_keyboard(lang='fa'):
    keyboard = [
        [KeyboardButton("حساب من 👤"), KeyboardButton("انتخاب حرفه 💼")],
        [KeyboardButton("ساخت صدا 🔊"), KeyboardButton("بروزرسانی 🔄")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def rules_keyboard(lang='fa'):
    return ReplyKeyboardMarkup([
        [KeyboardButton("قبول قوانین ✅"), KeyboardButton("رد قوانین ❌")]
    ], resize_keyboard=True, one_time_keyboard=True)

def language_keyboard(lang='fa'):
    return ReplyKeyboardMarkup([
        [KeyboardButton("فارسی 🇮🇷"), KeyboardButton("English 🇬🇧")]
    ], resize_keyboard=True, one_time_keyboard=True)

def professions_keyboard(lang='fa'):
    professions = {
        'writer': 'حروم خور', 'musician': 'دزد',
        'programmer': 'حلال خور', 'designer': 'پول مردم خور', 'teacher': 'بد بدخت مثل من'
    }
    buttons = [
        [InlineKeyboardButton(text=professions[key], callback_data=f"set_profession_{key}") for key in list(professions.keys())[i*2:(i+1)*2]]
        for i in range(len(professions)//2)
    ]
    # Add remaining buttons if odd number
    if len(professions) % 2 != 0:
        buttons.append([InlineKeyboardButton(text=professions[list(professions.keys())[-1]], callback_data=f"set_profession_{list(professions.keys())[-1]}")])

    return InlineKeyboardMarkup(buttons)

def account_keyboard(lang='fa'):
    return ReplyKeyboardMarkup([
        [KeyboardButton("مشاهده پروفایل 📄"), KeyboardButton("تغییر ایمیل 📧")],
        [KeyboardButton("تغییر رمز عبور 🔑"), KeyboardButton("بازگشت به منوی اصلی ↩️")]
    ], resize_keyboard=True, one_time_keyboard=True)

def tts_keyboard(lang='fa'):
    return ReplyKeyboardMarkup([
        [KeyboardButton("فارسی 🇮🇷"), KeyboardButton("English 🇬🇧")],
        [KeyboardButton("بازگشت به منوی اصلی ↩️")]
    ], resize_keyboard=True, one_time_keyboard=True)

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /start command and user initialization."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    # Check if user is already in DB
    user = db.get_user(user_id)
    if not user:
        # New user, create them
        db.create_user(user_id, username, first_name)
        user = db.get_user(user_id) # Fetch again to get referral code etc.
        logger.info(f"New user created: ID {user_id}, Username: {username}")
        context.user_data['state'] = RULES # Start the conversation flow
        await update.message.reply_text(
            "به ربات ما خوش آمدید! برای شروع، لطفا قوانین را مطالعه و تایید کنید.",
            reply_markup=rules_keyboard()
        )
        return RULES
    else:
        # Existing user, check if they need to complete registration or show main menu
        if user.get('first_start', True):
             context.user_data['state'] = RULES # Start the conversation flow
             await update.message.reply_text(
                "شما قبلا ثبت نام کرده‌اید، اما برای ادامه لطفا قوانین را مجددا مطالعه و تایید کنید.",
                reply_markup=rules_keyboard()
            )
             return RULES
        elif not user.get('registered', False):
            # User accepted rules but didn't finish registration
            context.user_data['state'] = LANGUAGE
            await update.message.reply_text(
                "لطفا زبان مورد نظر خود را انتخاب کنید:",
                reply_markup=language_keyboard()
            )
            return LANGUAGE
        else:
            # Fully registered user, show main menu
            lang = user.get('language', 'fa')
            await update.message.reply_text(f"سلام {get_display_name(user)}! به منوی اصلی خوش آمدید.", reply_markup=main_menu_keyboard(lang))
            return MAIN_MENU

async def accept_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the acceptance of rules."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    db.set_accepted_rules(user_id, True)
    db.set_first_start(user_id, False) # Mark as first start complete
    context.user_data['state'] = LANGUAGE

    lang = 'fa' # Default to Persian for language selection
    user = db.get_user(user_id)
    if user and user.get('language'):
        lang = user['language']

    await query.message.reply_text(
        "قوانین با موفقیت تایید شد.\n\n"
        "لطفا زبان مورد نظر خود را انتخاب کنید:",
        reply_markup=language_keyboard(lang)
    )
    return LANGUAGE

async def reject_rules_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the rejection of rules."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("شما قوانین را رد کردید. برای استفاده از ربات، لطفا دوباره /start را بزنید.")
    # Potentially reset user's first_start status or prompt them to restart
    return ConversationHandler.END

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles language selection."""
    user_id = update.effective_user.id
    text = update.message.text
    lang = 'fa' # Default

    if "فارسی" in text:
        lang = 'fa'
    elif "English" in text:
        lang = 'en'
    else:
        await update.message.reply_text("لطفا یکی از گزینه‌های ارائه شده را انتخاب کنید.")
        return LANGUAGE

    db.set_language(user_id, lang)
    context.user_data['state'] = REGISTER_EMAIL
    await update.message.reply_text(
        f"زبان شما روی **{get_language_name(lang)}** تنظیم شد.\n\n"
        "حالا لطفا ایمیل خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup([["لغو ↩️"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return REGISTER_EMAIL

async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles email registration."""
    user_id = update.effective_user.id
    email = update.message.text

    if email.lower() == "لغو":
        lang = db.get_user(user_id).get('language', 'fa')
        await update.message.reply_text("ثبت نام لغو شد.", reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    # Basic email format validation
    if "@" not in email or "." not in email:
        await update.message.reply_text("فرمت ایمیل نامعتبر است. لطفا دوباره تلاش کنید.")
        return REGISTER_EMAIL

    # Check if email is already registered (optional, depends on desired behavior)
    # existing_user_by_email = db.get_user_by_email(email) # You'd need to implement this in db.py
    # if existing_user_by_email and existing_user_by_email['user_id'] != user_id:
    #     await update.message.reply_text("این ایمیل قبلا توسط کاربر دیگری ثبت شده است.")
    #     return REGISTER_EMAIL

    context.user_data['email'] = email
    context.user_data['state'] = REGISTER_PASSWORD
    await update.message.reply_text("ایمیل شما دریافت شد.\n\nحالا لطفا رمز عبور خود را وارد کنید:", reply_markup=ReplyKeyboardMarkup([["لغو ↩️"]], resize_keyboard=True, one_time_keyboard=True))
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles password registration."""
    user_id = update.effective_user.id
    password = update.message.text

    if password.lower() == "لغو":
        lang = db.get_user(user_id).get('language', 'fa')
        await update.message.reply_text("ثبت نام لغو شد.", reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END

    context.user_data['password'] = password
    context.user_data['state'] = REGISTER_CONFIRM
    await update.message.reply_text("رمز عبور شما دریافت شد.\n\nلطفا برای تایید نهایی، روی دکمه \"تایید ثبت نام\" کلیک کنید:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("تایید ثبت نام ✅", callback_data="confirm_register")]]))
    return REGISTER_CONFIRM

async def finish_register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the final confirmation of registration."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    email = context.user_data.get('email')
    password = context.user_data.get('password')

    if not email or not password:
        await query.message.reply_text("خطا در اطلاعات ثبت نام. لطفا دوباره شروع کنید.")
        return ConversationHandler.END

    # Update user in DB
    db.set_email(user_id, email)
    db.set_password(user_id, password) # In a real app, hash the password!
    db.set_registered(user_id, True)

    user = db.get_user(user_id)
    lang = user.get('language', 'fa')

    # Handle referral if applicable (this is where invited_by would be set if starting from referral link)
    inviter_id = context.user_data.get('invited_by')
    if inviter_id:
        inviter = db.get_user(inviter_id)
        if inviter:
            db.set_invited_by(user_id, inviter_id)
            db.add_points(inviter_id, 100) # Points for inviting
            db.add_invite(inviter_id)      # Increment invite count
            logger.info(f"User {user_id} invited by {inviter_id}. Added 100 points to inviter.")
            # Optionally notify the inviter
            try:
                await context.bot.send_message(
                    chat_id=inviter_id,
                    text=f"کاربر جدید ({get_display_name(user)}) با کد شما ثبت نام کرد! 100 امتیاز دریافت کردید."
                )
            except Exception as e:
                logger.error(f"Could not notify inviter {inviter_id}: {e}")

    # Clear temporary user data
    context.user_data.clear()

    await query.message.reply_text(
        f"ثبت نام شما با موفقیت تکمیل شد!\n\n"
        f"به {get_display_name(user)} خوش آمدید!",
        reply_markup=main_menu_keyboard(lang)
    )
    return MAIN_MENU

async def cancel_register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles cancellation during registration."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    lang = db.get_user(user_id).get('language', 'fa')
    await query.message.reply_text("ثبت نام لغو شد.", reply_markup=main_menu_keyboard(lang))
    # Clean up any temporary data
    context.user_data.clear()
    return ConversationHandler.END

async def show_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows the main menu."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد. لطفا /start را مجدد بزنید.")
        return ConversationHandler.END

    lang = user.get('language', 'fa')
    await update.message.reply_text("به منوی اصلی خوش آمدید!", reply_markup=main_menu_keyboard(lang))
    return MAIN_MENU

async def show_home_by_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles navigation back home from other states via text message."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد. لطفا /start را مجدد بزنید.")
        return ConversationHandler.END
    lang = user.get('language', 'fa')
    await update.message.reply_text("بازگشت به منوی اصلی.", reply_markup=main_menu_keyboard(lang))
    return MAIN_MENU


async def account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'My Account' button press."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد. لطفا /start را مجدد بزنید.")
        return ConversationHandler.END

    lang = user.get('language', 'fa')
    await update.message.reply_text(
        "به بخش حساب کاربری خوش آمدید. لطفا یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=account_keyboard(lang)
    )
    return ACCOUNT_MENU

async def account_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the user's account status/profile."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد. لطفا /start را مجدد بزنید.")
        return ACCOUNT_MENU # Stay in account menu

    lang = user.get('language', 'fa')
    profile_text = get_profile_text(user)
    await update.message.reply_text(profile_text, parse_mode='Markdown', reply_markup=account_keyboard(lang))
    return ACCOUNT_MENU

async def change_email_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates the email change process."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد.")
        return ACCOUNT_MENU

    lang = user.get('language', 'fa')
    context.user_data['state'] = REGISTER_EMAIL # Reuse email registration state
    context.user_data['changing_email'] = True # Flag to indicate email change
    await update.message.reply_text(
        "لطفا ایمیل جدید خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup([["لغو ↩️"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return REGISTER_EMAIL

async def change_password_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates the password change process."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد.")
        return ACCOUNT_MENU

    lang = user.get('language', 'fa')
    context.user_data['state'] = REGISTER_PASSWORD # Reuse password registration state
    context.user_data['changing_password'] = True # Flag to indicate password change
    await update.message.reply_text(
        "لطفا رمز عبور جدید خود را وارد کنید:",
        reply_markup=ReplyKeyboardMarkup([["لغو ↩️"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return REGISTER_PASSWORD

async def professions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Select Profession' button press."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد. لطفا /start را مجدد بزنید.")
        return ConversationHandler.END

    lang = user.get('language', 'fa')
    current_profession = user.get('profession')
    profession_text = f"حرفه فعلی شما: **{get_profession_name(current_profession, lang)}**" if current_profession else "شما هنوز حرفه‌ای را انتخاب نکرده‌اید."

    await update.message.reply_text(
        f"{profession_text}\n\n"
        "لطفا یکی از حرفه‌های زیر را انتخاب کنید:",
        reply_markup=professions_keyboard(lang),
        parse_mode='Markdown'
    )
    return PROFESSIONS_MENU

async def profession_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sets the user's profession."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()

    profession_key = query.data.split('_')[-1] # e.g., "set_profession_writer" -> "writer"

    # Basic validation
    allowed_professions = ['writer', 'musician', 'programmer', 'designer', 'teacher']
    if profession_key not in allowed_professions:
        await query.message.reply_text("انتخاب حرفه نامعتبر است.")
        return PROFESSIONS_MENU

    db.set_profession(user_id, profession_key)
    user = db.get_user(user_id)
    lang = user.get('language', 'fa')

    await query.message.reply_text(
        f"حرفه شما با موفقیت به **{get_profession_name(profession_key, lang)}** تغییر یافت.",
        reply_markup=main_menu_keyboard(lang),
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Refreshes the current view or main menu."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد. لطفا /start را مجدد بزنید.")
        return ConversationHandler.END

    lang = user.get('language', 'fa')
    await update.message.reply_text("بروزرسانی شد.", reply_markup=main_menu_keyboard(lang))
    return MAIN_MENU

async def tts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the 'Text to Speech' button press."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد. لطفا /start را مجدد بزنید.")
        return ConversationHandler.END

    lang = user.get('language', 'fa')
    await update.message.reply_text(
        "برای تبدیل متن به صدا، لطفا متن مورد نظر را وارد کنید.\n\n"
        "سپس زبان صدا را انتخاب کنید:",
        reply_markup=tts_keyboard(lang)
    )
    context.user_data['state'] = TTS_TEXT
    return TTS_TEXT

async def tts_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the text to convert to speech."""
    user_id = update.effective_user.id
    text = update.message.text
    user = db.get_user(user_id)

    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد.")
        return ConversationHandler.END

    lang = user.get('language', 'fa')

    if text.lower() == "بازگشت به منوی اصلی ↩️":
        await update.message.reply_text("بازگشت به منوی اصلی.", reply_markup=main_menu_keyboard(lang))
        return MAIN_MENU

    context.user_data['tts_text'] = text
    context.user_data['state'] = TTS_LANGUAGE
    await update.message.reply_text(
        "لطفا زبان صدا را انتخاب کنید (فارسی یا انگلیسی):",
        reply_markup=tts_keyboard(lang) # Re-show TTS keyboard for language selection
    )
    return TTS_LANGUAGE

async def tts_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the language selection for text-to-speech."""
    user_id = update.effective_user.id
    text_input = update.message.text
    user = db.get_user(user_id)

    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد.")
        return ConversationHandler.END

    lang = user.get('language', 'fa')

    if text_input.lower() == "بازگشت به منوی اصلی ↩️":
        await update.message.reply_text("بازگشت به منوی اصلی.", reply_markup=main_menu_keyboard(lang))
        return MAIN_MENU

    tts_text = context.user_data.get('tts_text')
    if not tts_text:
        await update.message.reply_text("خطا: متن مورد نظر برای تبدیل یافت نشد. لطفا دوباره تلاش کنید.")
        return MAIN_MENU

    tts_lang = 'fa' # Default
    if "فارسی" in text_input:
        tts_lang = 'fa'
    elif "English" in text_input:
        tts_lang = 'en'
    else:
        await update.message.reply_text("لطفا زبان صدا را (فارسی یا انگلیسی) انتخاب کنید.")
        return TTS_LANGUAGE

    try:
        # Generate speech using gTTS
        tts = gTTS(text=tts_text, lang=tts_lang)
        filename = f"tts_{uuid.uuid4()}.mp3"
        filepath = os.path.join("temp", filename) # Save to a temp directory

        # Ensure temp directory exists
        os.makedirs("temp", exist_ok=True)

        tts.save(filepath)

        # Send the audio file
        await update.message.reply_audio(audio=open(filepath, 'rb'), caption="صدای تولید شده")

        # Clean up the temporary file
        os.remove(filepath)

        # Add points for TTS usage (example: 20 points)
        db.add_points(user_id, 20)

        # Clear temporary data
        context.user_data.clear()
        await update.message.reply_text("صدای شما با موفقیت تولید و ارسال شد. 20 امتیاز دریافت کردید.", reply_markup=main_menu_keyboard(lang))
        return MAIN_MENU

    except Exception as e:
        logger.error(f"Error during TTS generation for user {user_id}: {e}")
        await update.message.reply_text("متاسفانه خطایی در تولید صدا رخ داد. لطفا دوباره امتحان کنید.")
        return MAIN_MENU


async def back_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generic handler to go back home."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("خطا: اطلاعات کاربری یافت نشد. لطفا /start را مجدد بزنید.")
        return ConversationHandler.END
    lang = user.get('language', 'fa')
    await update.message.reply_text("بازگشت به منوی اصلی.", reply_markup=main_menu_keyboard(lang))
    return MAIN_MENU

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Default handler for text messages not matching other commands/states."""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("لطفا با /start ربات را شروع کنید.")
        return ConversationHandler.END

    lang = user.get('language', 'fa')
    current_state = context.user_data.get('state', None)

    # If we are in a conversation state and the input doesn't match expected, inform user
    if current_state in [RULES, LANGUAGE, REGISTER_EMAIL, REGISTER_PASSWORD, REGISTER_CONFIRM, TTS_TEXT, TTS_LANGUAGE]:
         # Specific messages handled within state handlers, this is a fallback
         await update.message.reply_text("لطفا به دستورالعمل‌های فعلی توجه کنید یا با \"لغو\" یا \"بازگشت\" خارج شوید.", reply_markup=main_menu_keyboard(lang) if current_state == REGISTER_CONFIRM else None)
         return current_state # Stay in the current state

    # If not in a specific conversation state, assume it's a general message or navigation attempt
    if update.message.text.lower() == "حساب من 👤":
        return await account_callback(update, context)
    elif update.message.text.lower() == "انتخاب حرفه 💼":
        return await professions_callback(update, context)
    elif update.message.text.lower() == "ساخت صدا 🔊":
        return await tts_callback(update, context)
    elif update.message.text.lower() == "بروزرسانی 🔄":
        return await refresh_callback(update, context)
    elif update.message.text.lower() == "مشاهده پروفایل 📄":
        return await account_status_callback(update, context)
    elif update.message.text.lower() == "تغییر ایمیل 📧":
        return await change_email_callback(update, context)
    elif update.message.text.lower() == "تغییر رمز عبور 🔑":
        return await change_password_callback(update, context)
    elif update.message.text.lower() == "بازگشت به منوی اصلی ↩️":
        return await back_home_callback(update, context)
    else:
        # Default response for unrecognized messages
        await update.message.reply_text("دستور نامعتبر است. لطفا از منوی ارائه شده استفاده کنید.", reply_markup=main_menu_keyboard(lang))
        return MAIN_MENU # Or return current_state if applicable


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Conversation Handlers ---

    # Registration Conversation
    conv_handler_register = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            RULES: [
                CallbackQueryHandler(accept_rules_callback, pattern="^accept_rules$"),
                CallbackQueryHandler(reject_rules_callback, pattern="^reject_rules$"),
                MessageHandler(filters.Regex("^(قبول قوانین ✅|رد قوانین ❌)$"), lambda u, c: accept_rules_callback(u, c) if "قبول" in u.message.text else reject_rules_callback(u, c)) # Handle button click text
            ],
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_callback)],
            REGISTER_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_email),
                CallbackQueryHandler(cancel_register_callback, pattern="^cancel_register$") # If cancellation button is pressed
            ],
            REGISTER_PASSWORD: [
                 MessageHandler(filters.TEXT & ~filters.COMMAND, register_password),
                 CallbackQueryHandler(cancel_register_callback, pattern="^cancel_register$")
            ],
            REGISTER_CONFIRM: [
                CallbackQueryHandler(finish_register_callback, pattern="^confirm_register$"),
                # Allow cancelling from confirm state too
                CallbackQueryHandler(cancel_register_callback, pattern="^cancel_register$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: query.message.reply_text("لطفا روی دکمه تایید کلیک کنید.")), # Catch text inputs here
            ],
            PROFESSIONS_MENU: [CallbackQueryHandler(profession_set_callback, pattern="^set_profession_")],
            ACCOUNT_MENU: [
                MessageHandler(filters.Regex("^مشاهده پروفایل 📄$"), account_status_callback),
                MessageHandler(filters.Regex("^تغییر ایمیل 📧$"), change_email_callback),
                MessageHandler(filters.Regex("^تغییر رمز عبور 🔑$"), change_password_callback),
                MessageHandler(filters.Regex("^بازگشت به منوی اصلی ↩️$"), back_home_callback),
            ],
             TTS_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tts_receive_text)],
             TTS_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tts_language_callback)],
        },
        fallbacks=[
             CommandHandler("start", start), # Allow restarting from any state
             MessageHandler(filters.Regex("^بازگشت به منوی اصلی ↩️$"), back_home_callback),
             MessageHandler(filters.Regex("^لغو ↩️$"), cancel_register_callback), # General cancel
             MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text) # Fallback for other text messages
        ],
        # Per-user state timeouts (optional)
        # conversation_timeout=300, # 5 minutes
        # per_message=True # State timeout per message
    )

    # --- General Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler_register)

    # Handlers for main menu buttons and other direct actions
    application.add_handler(MessageHandler(filters.Regex("^حساب من 👤$"), account_callback))
    application.add_handler(MessageHandler(filters.Regex("^انتخاب حرفه 💼$"), professions_callback))
    application.add_handler(MessageHandler(filters.Regex("^ساخت صدا 🔊$"), tts_callback))
    application.add_handler(MessageHandler(filters.Regex("^بروزرسانی 🔄$"), refresh_callback))
    # Handlers within conversation states are inside ConversationHandler

    # Fallback handler for any text message not caught by above handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))


    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    # Initialize the database when the script starts
    db.init_db()
    main()
