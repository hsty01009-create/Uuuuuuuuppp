import sqlite3

DB = "bot.db"

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        language TEXT DEFAULT 'fa',
        points INTEGER DEFAULT 0,
        invited_count INTEGER DEFAULT 0
    )
    """)

    c.commit()
    c.close()

def create_user(user_id, username, first_name):
    c = conn()
    cur = c.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (user_id, username, first_name)
    VALUES (?, ?, ?)
    """, (user_id, username, first_name))

    c.commit()
    c.close()

def get_user(user_id):
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def update(field, value, user_id):
    c = conn()
    cur = c.cursor()
    cur.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, user_id))
    c.commit()
    c.close()

def add_points(user_id, amount):
    c = conn()
    cur = c.cursor()
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, user_id))
    c.commit()
    c.close()

init()
