import sqlite3

DB = "bot.db"

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    with conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            email TEXT,
            language TEXT DEFAULT 'fa',
            points INTEGER DEFAULT 0,
            referral TEXT
        )
        """)

def get(user_id):
    with conn() as c:
        return c.execute(
            "SELECT * FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()

def create(user_id, username, first_name):
    with conn() as c:
        c.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, first_name, referral)
        VALUES (?, ?, ?, ?)
        """, (user_id, username, first_name, str(user_id)))
    return get(user_id)

def update(field, value, user_id):
    with conn() as c:
        c.execute(f"UPDATE users SET {field}=? WHERE user_id=?",
                  (value, user_id))
