import sqlite3

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    name TEXT,
    xp INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 100,
    level INTEGER DEFAULT 1
)
""")

conn.commit()

def add_user(user_id, username, name):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users(user_id, username, name) VALUES(?,?,?)",
            (user_id, username, name),
        )
        conn.commit()

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()