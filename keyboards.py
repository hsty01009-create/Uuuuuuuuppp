from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# --- کلید بردها برای مراحل مختلف ---

def kb_rules() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["✅ قبول می‌کنم", "❌ قبول نمی‌کنم"]],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True # Show keyboard only to the user who triggered it
    )

def kb_language() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["fa", "en"]],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True
    )

def kb_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["👤 پروفایل", "🎙 تبدیل متن به صدا"],
            ["✉ تغییر ایمیل", "🔑 تغییر رمز عبور"],
            ["💼 انتخاب حرفه", "🧭 داشبورد"],
        ],
        resize_keyboard=True,
        selective=True
    )

def kb_profession_choice() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["برنامه‌نویس", "دانشجو"],
            ["مهندس", "طراح"],
            ["معلم", "پزشک"],
            ["آزاد", "سایر"],
            ["🏠 بازگشت به منوی اصلی"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        selective=True
    )

def kb_dashboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["👤 پروفایل", "✉ تغییر ایمیل"],
            ["🔑 تغییر رمز عبور", "💼 انتخاب حرفه"],
            ["🎙 تبدیل متن به صدا", "🏠 بازگشت به منوی اصلی"],
        ],
        resize_keyboard=True,
        selective=True
    )

def kb_remove() -> ReplyKeyboardRemove:
    """کلید برد را حذف می‌کند."""
    return ReplyKeyboardRemove()
