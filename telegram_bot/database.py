import sqlite3
from config import BOT_DB_PATH

def get_bot_db():
    conn = sqlite3.connect(BOT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_bot_db()
    cursor = conn.cursor()
    
    # Tabel Users Telegram
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS telegram_users (
        chat_id TEXT PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        role TEXT DEFAULT 'user',
        is_active BOOLEAN DEFAULT 1,
        joined_at TEXT
    )
    ''')
    
    # Tabel Preferensi Notifikasi (Personalized Alert)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        chat_id TEXT PRIMARY KEY,
        alert_tender BOOLEAN DEFAULT 1,
        alert_tax BOOLEAN DEFAULT 1,
        alert_market BOOLEAN DEFAULT 1,
        alert_vendor BOOLEAN DEFAULT 1,
        FOREIGN KEY (chat_id) REFERENCES telegram_users (chat_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# ---- Fungsi Pembantu (Helper) CRUD ----

def add_or_update_user(chat_id, username, first_name):
    from datetime import datetime
    conn = get_bot_db()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("SELECT chat_id FROM telegram_users WHERE chat_id=?", (str(chat_id),))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO telegram_users (chat_id, username, first_name, joined_at) VALUES (?, ?, ?, ?)",
                       (str(chat_id), username, first_name, today))
        # Default preference on
        cursor.execute("INSERT INTO user_preferences (chat_id) VALUES (?)", (str(chat_id),))
    else:
        cursor.execute("UPDATE telegram_users SET is_active=1, username=?, first_name=? WHERE chat_id=?",
                       (username, first_name, str(chat_id)))
    conn.commit()
    conn.close()

def get_all_active_users():
    conn = get_bot_db()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM telegram_users WHERE is_active=1")
    users = [row['chat_id'] for row in cursor.fetchall()]
    conn.close()
    return users

def get_user_preferences(chat_id):
    conn = get_bot_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_preferences WHERE chat_id=?", (str(chat_id),))
    prefs = cursor.fetchone()
    conn.close()
    return prefs

def update_preference(chat_id, key, value):
    conn = get_bot_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE user_preferences SET {key}=? WHERE chat_id=?", (value, str(chat_id)))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database Telegram Bot berhasil diinisialisasi!")
