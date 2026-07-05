BOT_TOKEN = "YOUR_BOT_TOKEN"

ADMINS = [
    123456789  
]

BOT_NAME = "🕉 Hindu Community Bot"
import time

def add_xp(user_id, amount=10):
    cur.execute(
        "UPDATE users SET xp = xp + ? WHERE user_id=?",
        (amount, user_id)
    )

    cur.execute(
        "SELECT xp, level FROM users WHERE user_id=?",
        (user_id,)
    )

    xp, level = cur.fetchone()

    need = level * 100

    if xp >= need:
        cur.execute(
            "UPDATE users SET level = level + 1 WHERE user_id=?",
            (user_id,)
        )

    conn.commit()


def add_coins(user_id, amount):
    cur.execute(
        "UPDATE users SET coins = coins + ? WHERE user_id=?",
        (amount, user_id)
    )
    conn.commit()


cur.execute("""
CREATE TABLE IF NOT EXISTS daily(
user_id INTEGER PRIMARY KEY,
last_claim INTEGER
)
""")
conn.commit()


def claim_daily(user_id):
    now = int(time.time())

    cur.execute(
        "SELECT last_claim FROM daily WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    if row:
        if now-row[0] < 86400:
            return False

        cur.execute(
            "UPDATE daily SET last_claim=? WHERE user_id=?",
            (now, user_id)
        )

    else:
        cur.execute(
            "INSERT INTO daily VALUES(?,?)",
            (user_id, now)
        )

    add_coins(user_id,100)

    conn.commit()

    return True
