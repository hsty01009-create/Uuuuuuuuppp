import sqlite3
import hashlib
import logging
from config import DB_NAME, SALT
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def init_db():
    """پایگاه داده و جدول کاربران را در صورت عدم وجود ایجاد می‌کند."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT '',
                email TEXT DEFAULT '',
                password_hash TEXT DEFAULT '',
                profession TEXT DEFAULT '',
                accepted_rules INTEGER DEFAULT 0,
                registered INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """اطلاعات یک کاربر خاص را برمی‌گرداند."""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id, username, first_name, last_name, language,
                   email, password_hash, profession, accepted_rules, registered
            FROM users WHERE user_id = ?
        """, (user_id,))
        row = cur.fetchone()
        if not row:
            return None

        # Convert row to dictionary for easier access
        user_data = dict(zip([
            "user_id", "username", "first_name", "last_name", "language",
            "email", "password_hash", "profession", "accepted_rules", "registered"
        ], row))
        return user_data

    except sqlite3.Error as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def ensure_user_exists(user: Dict[str, Any]):
    """اطمینان حاصل می‌کند که کاربر در پایگاه داده وجود دارد، در غیر این صورت آن را درج می‌کند."""
    if get_user(user['id']):
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (
            user['id'],
            user.get('username', ''),
            user.get('first_name', ''),
            user.get('last_name', '')
        ))
        conn.commit()
        logger.info(f"User {user['id']} added to database.")
    except sqlite3.Error as e:
        logger.error(f"Error ensuring user {user['id']} exists: {e}")
    finally:
        if conn:
            conn.close()

def update_user_field(user_id: int, field: str, value: Any):
    """یک فیلد خاص از جدول کاربر را به‌روزرسانی می‌کند."""
    if not hasattr(sqlite3, field): # Simple check for valid field name, not exhaustive
         logger.warning(f"Attempt to update invalid field '{field}' for user {user_id}.")
         return

    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        query = f"UPDATE users SET {field} = ? WHERE user_id = ?"
        cur.execute(query, (value, user_id))
        conn.commit()
        logger.debug(f"User {user_id} field '{field}' updated to '{value}'.")
    except sqlite3.Error as e:
        logger.error(f"Error updating user {user_id} field '{field}': {e}")
    finally:
        if conn:
            conn.close()

def hash_password(password: str) -> str:
    """رمز عبور را با استفاده از salt هش می‌کند."""
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()

def is_registered(user_id: int) -> bool:
    """بررسی می‌کند که آیا کاربر ثبت‌نام کامل را انجام داده است یا خیر."""
    user_data = get_user(user_id)
    return bool(user_data and user_data.get('registered', 0) == 1)
