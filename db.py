import sqlite3
import os

DATABASE_FILE = 'bot.db'

def init_db():
    """Initialize the database and create the users table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            email TEXT UNIQUE,
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

def create_user(user_id, username=None, first_name=None):
    """Create a new user in the database."""
    if not os.path.exists(DATABASE_FILE):
        init_db()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, referral_code) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, str(user_id)) # Simple referral code generation
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # User already exists
        return False
    finally:
        conn.close()

def get_user(user_id):
    """Get user data from the database by user_id."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        # Map columns to dictionary keys for easier access
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, user_data))
    return None

def get_user_by_referral_code(code):
    """Get user data by their referral code."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE referral_code = ?", (code,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, user_data))
    return None

def update_user_field(user_id, field, value):
    """Update a specific field for a user."""
    allowed_fields = [
        'username', 'first_name', 'email', 'password', 'language',
        'points', 'invited_count', 'profession', 'accepted_rules',
        'first_start', 'referral_code', 'invited_by', 'registered'
    ]
    if field not in allowed_fields:
        print(f"Error: Field '{field}' is not allowed for update.")
        return False

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        # Construct the SQL query dynamically and safely
        query = f"UPDATE users SET {field} = ? WHERE user_id = ?"
        cursor.execute(query, (value, user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating field {field} for user {user_id}: {e}")
        return False
    finally:
        conn.close()

def set_language(user_id, language):
    return update_user_field(user_id, 'language', language)

def set_accepted_rules(user_id, accepted):
    return update_user_field(user_id, 'accepted_rules', accepted)

def set_first_start(user_id, value):
    return update_user_field(user_id, 'first_start', value)

def set_profession(user_id, profession):
    return update_user_field(user_id, 'profession', profession)

def set_email(user_id, email):
    return update_user_field(user_id, 'email', email)

def set_password(user_id, password):
    return update_user_field(user_id, 'password', password)

def set_registered(user_id, registered):
    return update_user_field(user_id, 'registered', registered)

def set_invited_by(user_id, inviter_id):
    return update_user_field(user_id, 'invited_by', inviter_id)

def add_points(user_id, amount):
    """Add points to a user's account."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def add_invite(user_id):
    """Increment the invited_count for a user."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Initialize DB if it doesn't exist when the module is imported
if not os.path.exists(DATABASE_FILE):
    init_db()
