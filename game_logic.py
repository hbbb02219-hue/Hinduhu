# -*- coding: utf-8 -*-
"""
Fight simulation logic (PvE और PvP दोनों के लिए)
"""

import random
import game_data
import config


def get_weapon_damage(weapon_name: str) -> int:
    w = game_data.WEAPONS.get(weapon_name)
    return w["damage"] if w else 5


def get_armor_defense(armor_name: str) -> int:
    a = game_data.ARMORS.get(armor_name)
    return a["defense"] if a else 0


def player_power(user: dict) -> dict:
    weapon_dmg = get_weapon_damage(user["equipped_weapon"])
    armor_def = get_armor_defense(user["equipped_armor"])
    return {
        "health": user["health"],
        "max_health": user["max_health"],
        "damage": weapon_dmg + user["level"] * 2,
        "defense": armor_def,
    }


def simulate_pve_fight(user: dict, enemy_template: dict):
    """
    Simple turn based simulation. Returns dict with result info.
    Enemy stats scale a bit with player level for balance.
    """
    scale = 1 + (user["level"] - 1) * 0.08
    enemy_health = int(enemy_template["base_health"] * scale)
    enemy_damage = int(enemy_template["base_damage"] * scale)

    player = player_power(user)
    player_hp = min(user["health"], user["max_health"])
    if player_hp <= 0:
        player_hp = 1

    log = []
    turn = 1
    while player_hp > 0 and enemy_health > 0 and turn <= 30:
        # player attacks
        dmg_to_enemy = max(1, player["damage"] + random.randint(-3, 5))
        enemy_health -= dmg_to_enemy
        log.append(f"🗡️ आपने {dmg_to_enemy} डैमेज किया!")
        if enemy_health <= 0:
            break
        # enemy attacks
        raw = enemy_damage + random.randint(-2, 4)
        dmg_to_player = max(1, raw - player["defense"] // 2)
        player_hp -= dmg_to_player
        log.append(f"👹 दुश्मन ने {dmg_to_player} डैमेज किया!")
        turn += 1

    won = enemy_health <= 0 and player_hp > 0
    return {
        "won": won,
        "player_hp_left": max(0, player_hp),
        "enemy_hp_left": max(0, enemy_health),
        "log": log,
        "coin_reward": enemy_template["coin"] if won else max(5, enemy_template["coin"] // 5),
        "xp_reward": enemy_template["xp"] if won else max(2, enemy_template["xp"] // 5),
    }


def simulate_pvp_fight(user_a: dict, user_b: dict):
    """Simulate a PvP battle between two players. Returns winner user_id and log."""
    a = player_power(user_a)
    b = player_power(user_b)
    hp_a = min(user_a["health"], user_a["max_health"]) or 1
    hp_b = min(user_b["health"], user_b["max_health"]) or 1

    log = []
    turn = 1
    while hp_a > 0 and hp_b > 0 and turn <= 30:
        dmg_a = max(1, a["damage"] + random.randint(-3, 5) - b["defense"] // 3)
        hp_b -= dmg_a
        log.append(f"⚔️ {user_a['first_name']} ने {dmg_a} डैमेज दिया")
        if hp_b <= 0:
            break
        dmg_b = max(1, b["damage"] + random.randint(-3, 5) - a["defense"] // 3)
        hp_a -= dmg_b
        log.append(f"⚔️ {user_b['first_name']} ने {dmg_b} डैमेज दिया")
        turn += 1

    if hp_a <= 0 and hp_b <= 0:
        winner = None
    elif hp_b <= 0:
        winner = user_a["user_id"]
    elif hp_a <= 0:
        winner = user_b["user_id"]
    else:
        winner = user_a["user_id"] if hp_a >= hp_b else user_b["user_id"]

    return {"winner": winner, "log": log, "hp_a_left": max(0, hp_a), "hp_b_left": max(0, hp_b)}


def pick_random_enemy(level: int):
    # bias toward enemies suited to player level, but keep it simple/random
    return random.choice(game_data.ENEMIES)


def weighted_spin_choice():
    rewards = game_data.SPIN_REWARDS
    total = sum(r["weight"] for r in rewards)
    r = random.uniform(0, total)
    upto = 0
    for reward in rewards:
        upto += reward["weight"]
        if r <= upto:
            return reward
    return rewards[0]
