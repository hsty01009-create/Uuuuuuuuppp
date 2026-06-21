import sqlite3
import uuid
from pathlib import Path

DB_PATH = Path("bot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        email TEXT,
        password TEXT,
        language TEXT DEFAULT 'fa',
        points INTEGER DEFAULT 0,
        invited_count INTEGER DEFAULT 0,
        profession TEXT,
        accepted_rules INTEGER DEFAULT 0,
        first_start INTEGER DEFAULT 1,
        referral_code TEXT UNIQUE,
        invited_by TEXT,
        registered INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


def create_user(user_id, username=None, first_name=None):
    conn = get_conn()
    c = conn.cursor()
    referral_code = str(uuid.uuid4())[:8]

    c.execute("""
    INSERT OR IGNORE INTO users (user_id, username, first_name, referral_code)
    VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, referral_code))

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row


def get_user_by_referral_code(code):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE referral_code = ?", (code,))
    row = c.fetchone()
    conn.close()
    return row


def update_user_field(user_id, field, value):
    allowed = {
        "username", "first_name", "email", "password", "language",
        "points", "invited_count", "profession", "accepted_rules",
        "first_start", "referral_code", "invited_by", "registered"
    }
    if field not in allowed:
        raise ValueError("Invalid field")

    conn = get_conn()
    c = conn.cursor()
    c.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()


def set_language(user_id, language):
    update_user_field(user_id, "language", language)


def set_accepted_rules(user_id, value=1):
    update_user_field(user_id, "accepted_rules", value)


def set_first_start(user_id, value=0):
    update_user_field(user_id, "first_start", value)


def set_profession(user_id, profession):
    update_user_field(user_id, "profession", profession)


def set_email(user_id, email):
    update_user_field(user_id, "email", email)


def set_password(user_id, password):
    update_user_field(user_id, "password", password)


def set_registered(user_id, value=1):
    update_user_field(user_id, "registered", value)


def set_invited_by(user_id, code):
    update_user_field(user_id, "invited_by", code)


def add_points(user_id, amount):
    user = get_user(user_id)
    if not user:
        return
    new_points = (user["points"] or 0) + amount
    update_user_field(user_id, "points", new_points)


def add_invite(user_id):
    user = get_user(user_id)
    if not user:
        return
    new_count = (user["invited_count"] or 0) + 1
    update_user_field(user_id, "invited_count", new_count)
