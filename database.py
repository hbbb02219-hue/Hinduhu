# ==========================================
# Hindu Community Bot
# database.py
# ==========================================

import sqlite3

DB_NAME = "data.db"

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()


def create_tables():
    # ==========================
    # Users Table
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,

        coins INTEGER DEFAULT 1000,
        gems INTEGER DEFAULT 10,

        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,

        health INTEGER DEFAULT 100,
        energy INTEGER DEFAULT 100,

        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,

        weapon TEXT DEFAULT 'Wooden Sword',
        armor TEXT DEFAULT 'None',

        referrals INTEGER DEFAULT 0,

        daily_reward TEXT DEFAULT '',

        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ==========================
    # Inventory
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_name TEXT,
        quantity INTEGER DEFAULT 1
    )
    """)

    conn.commit()


create_tables()


def add_user(user_id, username, first_name):
    cursor.execute(
        """
        INSERT OR IGNORE INTO users(
            user_id,
            username,
            first_name
        )
        VALUES(?,?,?)
        """,
        (user_id, username, first_name)
    )

    conn.commit()


def get_user(user_id):
    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    return cursor.fetchone()


def add_coins(user_id, amount):
    cursor.execute(
        """
        UPDATE users
        SET coins = coins + ?
        WHERE user_id=?
        """,
        (amount, user_id)
    )

    conn.commit()


def remove_coins(user_id, amount):
    cursor.execute(
        """
        UPDATE users
        SET coins = coins - ?
        WHERE user_id=?
        """,
        (amount, user_id)
    )

    conn.commit()


def add_xp(user_id, amount):
    cursor.execute(
        """
        UPDATE users
        SET xp = xp + ?
        WHERE user_id=?
        """,
        (amount, user_id)
    )

    conn.commit()


def level_up(user_id):
    cursor.execute(
        """
        UPDATE users
        SET
            level = level + 1,
            xp = 0
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()


def set_health(user_id, hp):
    cursor.execute(
        """
        UPDATE users
        SET health=?
        WHERE user_id=?
        """,
        (hp, user_id)
    )

    conn.commit()


def update_daily(user_id, date):
    cursor.execute(
        """
        UPDATE users
        SET daily_reward=?
        WHERE user_id=?
        """,
        (date, user_id)
    )

    conn.commit()


def add_inventory(user_id, item):
    cursor.execute(
        """
        INSERT INTO inventory(
            user_id,
            item_name
        )
        VALUES(?,?)
        """,
        (user_id, item)
    )

    conn.commit()


def get_inventory(user_id):
    cursor.execute(
        """
        SELECT item_name, quantity
        FROM inventory
        WHERE user_id=?
        """,
        (user_id,)
    )

    return cursor.fetchall()


def top_players(limit=10):
    cursor.execute(
        """
        SELECT
            first_name,
            level,
            coins
        FROM users

        ORDER BY
            level DESC,
            coins DESC

        LIMIT ?
        """,
        (limit,)
    )

    return cursor.fetchall()