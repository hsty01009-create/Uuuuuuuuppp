import sqlite3
import os

DATABASE_FILE = 'bot.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return conn

def init_db():
    """Initializes the database and creates the users table if it doesn't exist."""
    if os.path.exists(DATABASE_FILE):
        print("Database already exists.")
        return

    print("Initializing database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
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
            accepted_rules BOOLEAN DEFAULT 0,
            first_start BOOLEAN DEFAULT 1,
            referral_code TEXT UNIQUE,
            invited_by INTEGER,
            registered BOOLEAN DEFAULT 0,
            FOREIGN KEY (invited_by) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def create_user(user_id, username=None, first_name=None):
    """Creates a new user entry in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name, referral_code)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, str(user_id))) # Using user_id as referral code for simplicity
        conn.commit()
        print(f"User {user_id} created.")
        return get_user(user_id)
    except sqlite3.IntegrityError:
        print(f"User {user_id} already exists.")
        return get_user(user_id)
    finally:
        conn.close()

def get_user(user_id):
    """Retrieves a user's data from the database by user_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_referral_code(code):
    """Retrieves a user's data from the database by referral code."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE referral_code = ?", (code,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_field(user_id, field, value):
    """Updates a specific field for a given user. Uses a whitelist for security."""
    allowed_fields = [
        'username', 'first_name', 'email', 'password', 'language',
        'points', 'invited_count', 'profession', 'accepted_rules',
        'first_start', 'referral_code', 'invited_by', 'registered'
    ]
    if field not in allowed_fields:
        print(f"Error: Field '{field}' is not allowed for update.")
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
        conn.commit()
        print(f"User {user_id} field '{field}' updated to '{value}'.")
        return True
    except Exception as e:
        print(f"Error updating user {user_id} field '{field}': {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def set_language(user_id, language):
    return update_user_field(user_id, 'language', language)

def set_accepted_rules(user_id, accepted):
    return update_user_field(user_id, 'accepted_rules', int(accepted)) # Store as 0 or 1

def set_first_start(user_id, first_start_done):
    return update_user_field(user_id, 'first_start', int(first_start_done))

def set_profession(user_id, profession):
    return update_user_field(user_id, 'profession', profession)

def set_email(user_id, email):
    return update_user_field(user_id, 'email', email)

def set_password(user_id, password):
    # In a real application, you should hash the password here
    return update_user_field(user_id, 'password', password)

def set_registered(user_id, registered):
    return update_user_field(user_id, 'registered', int(registered))

def set_invited_by(user_id, inviter_id):
    return update_user_field(user_id, 'invited_by', inviter_id)

def add_points(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    print(f"Added {amount} points to user {user_id}.")

def add_invite(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    print(f"Incremented invite count for user {user_id}.")

# Initialize the database if it doesn't exist when the module is imported
if not os.path.exists(DATABASE_FILE):
    init_db()
