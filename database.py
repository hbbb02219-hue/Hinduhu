# -*- coding: utf-8 -*-
"""
SQLite Database Layer
सारे DB operations यहाँ हैं।
"""

import sqlite3
import datetime
from contextlib import contextmanager

import config
from config import xp_for_level


def _now():
    return datetime.datetime.utcnow().isoformat()


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            health INTEGER DEFAULT 100,
            max_health INTEGER DEFAULT 100,
            energy INTEGER DEFAULT 50,
            max_energy INTEGER DEFAULT 50,
            coins INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            pvp_wins INTEGER DEFAULT 0,
            pvp_losses INTEGER DEFAULT 0,
            equipped_weapon TEXT DEFAULT 'Wooden Sword',
            equipped_armor TEXT DEFAULT 'Cloth Armor',
            clan_id INTEGER,
            referred_by INTEGER,
            referral_count INTEGER DEFAULT 0,
            total_coins_earned INTEGER DEFAULT 0,
            last_daily TEXT,
            last_spin TEXT,
            last_regen TEXT,
            banned INTEGER DEFAULT 0,
            created_at TEXT
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_type TEXT,
            item_name TEXT,
            quantity INTEGER DEFAULT 1,
            UNIQUE(user_id, item_type, item_name)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS clans (
            clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            leader_id INTEGER,
            coins INTEGER DEFAULT 0,
            created_at TEXT
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS user_missions (
            user_id INTEGER,
            mission_key TEXT,
            progress INTEGER DEFAULT 0,
            target INTEGER,
            reward_coins INTEGER,
            reward_xp INTEGER,
            completed INTEGER DEFAULT 0,
            claimed INTEGER DEFAULT 0,
            date TEXT,
            PRIMARY KEY (user_id, mission_key, date)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS achievements_unlocked (
            user_id INTEGER,
            achievement_key TEXT,
            unlocked_at TEXT,
            PRIMARY KEY (user_id, achievement_key)
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS pvp_challenges (
            challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenger_id INTEGER,
            opponent_id INTEGER,
            chat_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )""")


# ---------------------------------------------------------------------------
# USER FUNCTIONS
# ---------------------------------------------------------------------------

def get_user(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def create_user(user_id: int, username: str, first_name: str, referred_by: int = None):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users
            (user_id, username, first_name, health, max_health, energy, max_energy,
             coins, xp, level, referred_by, last_regen, created_at)
            VALUES (?,?,?,?,?,?,?,?,0,1,?,?,?)
        """, (user_id, username, first_name, config.STARTING_HEALTH, config.STARTING_HEALTH,
              config.STARTING_ENERGY, config.STARTING_ENERGY, config.STARTING_COINS,
              referred_by, _now(), _now()))
        # starting gear
        conn.execute("""INSERT OR IGNORE INTO inventory (user_id, item_type, item_name, quantity)
                         VALUES (?, 'weapon', 'Wooden Sword', 1)""", (user_id,))
        conn.execute("""INSERT OR IGNORE INTO inventory (user_id, item_type, item_name, quantity)
                         VALUES (?, 'armor', 'Cloth Armor', 1)""", (user_id,))


def update_user(user_id: int, **fields):
    if not fields:
        return
    keys = ", ".join(f"{k}=?" for k in fields.keys())
    values = list(fields.values()) + [user_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {keys} WHERE user_id=?", values)


def add_coins(user_id: int, amount: int):
    with get_conn() as conn:
        conn.execute("""UPDATE users SET coins = coins + ?,
                         total_coins_earned = total_coins_earned + MAX(?,0)
                         WHERE user_id=?""", (amount, amount, user_id))


def add_xp(user_id: int, amount: int):
    """Adds xp and handles level ups. Returns list of new levels reached."""
    user = get_user(user_id)
    if not user:
        return []
    xp = user["xp"] + amount
    level = user["level"]
    max_health = user["max_health"]
    max_energy = user["max_energy"]
    levels_gained = []
    while xp >= xp_for_level(level):
        xp -= xp_for_level(level)
        level += 1
        max_health += 10
        max_energy += 5
        levels_gained.append(level)
    with get_conn() as conn:
        conn.execute("""UPDATE users SET xp=?, level=?, max_health=?, max_energy=?,
                         health=?, energy=? WHERE user_id=?""",
                      (xp, level, max_health, max_energy, max_health, max_energy, user_id))
    return levels_gained


def regen_stats(user_id: int):
    """Passive regen of health & energy based on time elapsed."""
    user = get_user(user_id)
    if not user:
        return
    last = user["last_regen"]
    if not last:
        return
    last_dt = datetime.datetime.fromisoformat(last)
    now_dt = datetime.datetime.utcnow()
    minutes = (now_dt - last_dt).total_seconds() / 60

    energy_gain = int(minutes // config.ENERGY_REGEN_MINUTES)
    health_gain = int(minutes // config.HEALTH_REGEN_MINUTES)

    if energy_gain <= 0 and health_gain <= 0:
        return

    new_energy = min(user["max_energy"], user["energy"] + energy_gain)
    new_health = min(user["max_health"], user["health"] + health_gain)
    with get_conn() as conn:
        conn.execute("UPDATE users SET energy=?, health=?, last_regen=? WHERE user_id=?",
                      (new_energy, new_health, _now(), user_id))


def get_leaderboard(limit=10):
    with get_conn() as conn:
        rows = conn.execute("""SELECT user_id, username, first_name, level, xp, wins, coins
                                FROM users WHERE banned=0
                                ORDER BY level DESC, xp DESC LIMIT ?""", (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_all_user_ids():
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id FROM users WHERE banned=0").fetchall()
        return [r["user_id"] for r in rows]


def set_ban(user_id: int, banned: bool):
    update_user(user_id, banned=1 if banned else 0)


# ---------------------------------------------------------------------------
# INVENTORY
# ---------------------------------------------------------------------------

def add_item(user_id: int, item_type: str, item_name: str, qty: int = 1):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO inventory (user_id, item_type, item_name, quantity)
            VALUES (?,?,?,?)
            ON CONFLICT(user_id, item_type, item_name)
            DO UPDATE SET quantity = quantity + excluded.quantity
        """, (user_id, item_type, item_name, qty))


def get_inventory(user_id: int, item_type: str = None):
    with get_conn() as conn:
        if item_type:
            rows = conn.execute("""SELECT * FROM inventory WHERE user_id=? AND item_type=?
                                    AND quantity > 0""", (user_id, item_type)).fetchall()
        else:
            rows = conn.execute("""SELECT * FROM inventory WHERE user_id=? AND quantity > 0""",
                                 (user_id,)).fetchall()
        return [dict(r) for r in rows]


def has_item(user_id: int, item_type: str, item_name: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("""SELECT quantity FROM inventory
                               WHERE user_id=? AND item_type=? AND item_name=?""",
                            (user_id, item_type, item_name)).fetchone()
        return bool(row and row["quantity"] > 0)


# ---------------------------------------------------------------------------
# CLANS
# ---------------------------------------------------------------------------

def create_clan(name: str, leader_id: int):
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO clans (name, leader_id, created_at) VALUES (?,?,?)",
                            (name, leader_id, _now()))
        clan_id = cur.lastrowid
        conn.execute("UPDATE users SET clan_id=? WHERE user_id=?", (clan_id, leader_id))
        return clan_id


def get_clan(clan_id: int = None, name: str = None):
    with get_conn() as conn:
        if clan_id is not None:
            row = conn.execute("SELECT * FROM clans WHERE clan_id=?", (clan_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM clans WHERE name=?", (name,)).fetchone()
        return dict(row) if row else None


def join_clan(user_id: int, clan_id: int):
    update_user(user_id, clan_id=clan_id)


def leave_clan(user_id: int):
    update_user(user_id, clan_id=None)


def get_clan_members(clan_id: int):
    with get_conn() as conn:
        rows = conn.execute("""SELECT user_id, username, first_name, level, xp
                                FROM users WHERE clan_id=? ORDER BY level DESC""",
                             (clan_id,)).fetchall()
        return [dict(r) for r in rows]


def clan_leaderboard(limit=10):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT c.clan_id, c.name, SUM(u.level) as total_level, COUNT(u.user_id) as members
            FROM clans c LEFT JOIN users u ON u.clan_id = c.clan_id
            GROUP BY c.clan_id ORDER BY total_level DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


def list_all_clans():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM clans ORDER BY clan_id DESC").fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# DAILY MISSIONS
# ---------------------------------------------------------------------------

def get_today_missions(user_id: int):
    today = datetime.date.today().isoformat()
    with get_conn() as conn:
        rows = conn.execute("""SELECT * FROM user_missions WHERE user_id=? AND date=?""",
                             (user_id, today)).fetchall()
        return [dict(r) for r in rows]


def assign_daily_missions(user_id: int, missions: list):
    today = datetime.date.today().isoformat()
    with get_conn() as conn:
        for m in missions:
            conn.execute("""INSERT OR IGNORE INTO user_missions
                (user_id, mission_key, progress, target, reward_coins, reward_xp, date)
                VALUES (?,?,0,?,?,?,?)""",
                (user_id, m["key"], m["target"], m["reward_coins"], m["reward_xp"], today))


def update_mission_progress(user_id: int, mission_type: str, amount: int = 1):
    """Increments progress for today's missions matching a type. Returns list of newly completed mission_keys."""
    import game_data
    today = datetime.date.today().isoformat()
    completed_now = []
    key_to_type = {m["key"]: m["type"] for m in game_data.MISSIONS_POOL}
    with get_conn() as conn:
        rows = conn.execute("""SELECT * FROM user_missions WHERE user_id=? AND date=? AND completed=0""",
                             (user_id, today)).fetchall()
        for r in rows:
            m_type = key_to_type.get(r["mission_key"])
            if m_type == mission_type:
                new_progress = r["progress"] + amount
                completed = 1 if new_progress >= r["target"] else 0
                conn.execute("""UPDATE user_missions SET progress=?, completed=?
                                 WHERE user_id=? AND mission_key=? AND date=?""",
                              (new_progress, completed, user_id, r["mission_key"], today))
                if completed:
                    completed_now.append(r["mission_key"])
    return completed_now


def claim_mission(user_id: int, mission_key: str):
    today = datetime.date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute("""SELECT * FROM user_missions WHERE user_id=? AND mission_key=? AND date=?""",
                            (user_id, mission_key, today)).fetchone()
        if not row or not row["completed"] or row["claimed"]:
            return None
        conn.execute("""UPDATE user_missions SET claimed=1
                         WHERE user_id=? AND mission_key=? AND date=?""",
                      (user_id, mission_key, today))
        return dict(row)


# ---------------------------------------------------------------------------
# ACHIEVEMENTS
# ---------------------------------------------------------------------------

def get_unlocked_achievements(user_id: int):
    with get_conn() as conn:
        rows = conn.execute("SELECT achievement_key FROM achievements_unlocked WHERE user_id=?",
                             (user_id,)).fetchall()
        return [r["achievement_key"] for r in rows]


def unlock_achievement(user_id: int, key: str) -> bool:
    """Returns True if newly unlocked (False if already had it)."""
    with get_conn() as conn:
        existing = conn.execute("""SELECT 1 FROM achievements_unlocked
                                    WHERE user_id=? AND achievement_key=?""",
                                 (user_id, key)).fetchone()
        if existing:
            return False
        conn.execute("""INSERT INTO achievements_unlocked (user_id, achievement_key, unlocked_at)
                         VALUES (?,?,?)""", (user_id, key, _now()))
        return True


# ---------------------------------------------------------------------------
# PVP CHALLENGES
# ---------------------------------------------------------------------------

def create_challenge(challenger_id: int, opponent_id: int, chat_id: int):
    with get_conn() as conn:
        cur = conn.execute("""INSERT INTO pvp_challenges
            (challenger_id, opponent_id, chat_id, status, created_at)
            VALUES (?,?,?, 'pending', ?)""",
            (challenger_id, opponent_id, chat_id, _now()))
        return cur.lastrowid


def get_challenge(challenge_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM pvp_challenges WHERE challenge_id=?",
                            (challenge_id,)).fetchone()
        return dict(row) if row else None


def set_challenge_status(challenge_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE pvp_challenges SET status=? WHERE challenge_id=?",
                      (status, challenge_id))
