import sqlite3
import os

DB = "bot.db"

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    if os.path.exists(DB):
        return
    c = conn()
    c.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        language TEXT DEFAULT 'fa',
        points INTEGER DEFAULT 0,
        voice TEXT DEFAULT 'male',
        invited_by INTEGER
    )
    """)
    c.commit()
    c.close()

def get_user(uid):
    c = conn()
    u = c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    c.close()
    return u

def create_user(uid, name):
    c = conn()
    c.execute("INSERT OR IGNORE INTO users (user_id,name) VALUES (?,?)", (uid,name))
    c.commit()
    c.close()

def add_points(uid, p):
    c = conn()
    c.execute("UPDATE users SET points = points + ? WHERE user_id=?", (p,uid))
    c.commit()
    c.close()

def set_voice(uid, v):
    c = conn()
    c.execute("UPDATE users SET voice=? WHERE user_id=?", (v,uid))
    c.commit()
    c.close()

init()
