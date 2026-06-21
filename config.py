import os
from pathlib import Path

# --- تنظیمات ربات ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE" # !!! توکن ربات خود را اینجا قرار دهید !!!

# --- تنظیمات پایگاه داده ---
DB_NAME = "bot_data.db"

# --- مسیرهای فایل ---
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp_audio"

# --- تنظیمات صدا ---
DEFAULT_LANG = "fa" # زبان پیش‌فرض متن به صدا

# --- هش کردن رمز ---
SALT = "tilawya_salt_2026_professional" # سالت برای هش کردن رمز عبور

# --- لاگینگ ---
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# --- اطمینان از وجود پوشه موقت صدا ---
if not TEMP_DIR.exists():
    TEMP_DIR.mkdir(exist_ok=True)
