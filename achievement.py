# -*- coding: utf-8 -*-
"""
Achievement check logic - हर बड़ी action के बाद call करो।
Returns a list of newly unlocked achievement keys (to notify the user).
"""

import database
import game_data


def check_and_unlock(user_id: int) -> list:
    user = database.get_user(user_id)
    if not user:
        return []

    newly_unlocked = []

    def try_unlock(key, condition):
        if condition and database.unlock_achievement(user_id, key):
            newly_unlocked.append(key)

    try_unlock("first_blood", user["wins"] >= 1)
    try_unlock("warrior_10", user["wins"] >= 10)
    try_unlock("champion_50", user["wins"] >= 50)
    try_unlock("pvp_king", user["pvp_wins"] >= 10)
    try_unlock("level_10", user["level"] >= 10)
    try_unlock("level_25", user["level"] >= 25)
    try_unlock("rich_1000", user["coins"] >= 1000)
    try_unlock("rich_10000", user["coins"] >= 10000)
    try_unlock("clan_member", user["clan_id"] is not None)
    try_unlock("referrer", user["referral_count"] >= 5)

    weapons_owned = [i for i in database.get_inventory(user_id, "weapon")]
    try_unlock("collector", len(weapons_owned) >= 5)

    return newly_unlocked


def unlock_lucky(user_id: int) -> bool:
    return database.unlock_achievement(user_id, "lucky")


def format_achievement_notice(keys: list) -> str:
    if not keys:
        return ""
    lines = ["\n🎖️ *नया Achievement Unlock हुआ!*"]
    for k in keys:
        a = game_data.ACHIEVEMENTS.get(k)
        if a:
            lines.append(f"{a['name']} — {a['desc']}")
    return "\n".join(lines)
