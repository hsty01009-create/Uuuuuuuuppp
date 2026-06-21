# db.py

import sqlite3
import os

DATABASE_FILE = "bot.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    if os.path.exists(DATABASE_FILE):
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE users (
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
            invited_by INTEGER,
            registered INTEGER DEFAULT 0,
            FOREIGN KEY(invited_by)
            REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cursor.fetchone()
    conn.close()

    return dict(user) if user else None


def get_user_by_referral_code(code):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE referral_code=?",
        (code,)
    )

    user = cursor.fetchone()
    conn.close()

    return dict(user) if user else None


def create_user(user_id, username=None, first_name=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users
            (user_id, username, first_name, referral_code)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            username,
            first_name,
            str(user_id)
        ))

        conn.commit()

    except sqlite3.IntegrityError:
        pass

    finally:
        conn.close()

    return get_user(user_id)


def update_user_field(user_id, field, value):

    allowed = [
        "username",
        "first_name",
        "email",
        "password",
        "language",
        "points",
        "invited_count",
        "profession",
        "accepted_rules",
        "first_start",
        "referral_code",
        "invited_by",
        "registered"
    ]

    if field not in allowed:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"UPDATE users SET {field}=? WHERE user_id=?",
        (value, user_id)
    )

    conn.commit()
    conn.close()

    return True


def set_email(user_id, email):
    return update_user_field(
        user_id,
        "email",
        email
    )


def set_password(user_id, password):
    return update_user_field(
        user_id,
        "password",
        password
    )


def set_language(user_id, language):
    return update_user_field(
        user_id,
        "language",
        language
    )


def set_profession(user_id, profession):
    return update_user_field(
        user_id,
        "profession",
        profession
    )


def set_registered(user_id, value):
    return update_user_field(
        user_id,
        "registered",
        int(value)
    )


def set_accepted_rules(user_id, value):
    return update_user_field(
        user_id,
        "accepted_rules",
        int(value)
    )


def set_first_start(user_id, value):
    return update_user_field(
        user_id,
        "first_start",
        int(value)
    )


def set_invited_by(user_id, inviter):
    return update_user_field(
        user_id,
        "invited_by",
        inviter
    )


def add_points(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (amount, user_id)
    )

    conn.commit()
    conn.close()


def add_invite(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET invited_count = invited_count + 1
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


if not os.path.exists(DATABASE_FILE):
    init_db()
