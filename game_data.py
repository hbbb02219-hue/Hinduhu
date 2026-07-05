# -*- coding: utf-8 -*-
"""
सारा static game data यहाँ है: Weapons, Armor, Enemies, Missions, Achievements, Spin rewards
"""

WEAPONS = {
    "Wooden Sword":   {"price": 0,    "damage": 5,  "rarity": "Common",   "emoji": "🗡️"},
    "Sword":          {"price": 200,  "damage": 15, "rarity": "Common",   "emoji": "⚔️"},
    "Bow":            {"price": 500,  "damage": 25, "rarity": "Uncommon", "emoji": "🏹"},
    "Trishul":        {"price": 800,  "damage": 35, "rarity": "Rare",     "emoji": "🔱"},
    "Gada":           {"price": 1200, "damage": 45, "rarity": "Epic",     "emoji": "🏏"},
    "Katana":         {"price": 2000, "damage": 60, "rarity": "Legendary","emoji": "🗡️"},
    "Divine Sudarshan Chakra": {"price": 5000, "damage": 100, "rarity": "Mythic", "emoji": "🌀"},
}

ARMORS = {
    "Cloth Armor":    {"price": 0,    "defense": 2,  "rarity": "Common",   "emoji": "👕"},
    "Leather Armor":  {"price": 300,  "defense": 10, "rarity": "Common",   "emoji": "🦺"},
    "Iron Kavach":    {"price": 900,  "defense": 25, "rarity": "Rare",     "emoji": "🛡️"},
    "Steel Shield":   {"price": 1500, "defense": 40, "rarity": "Epic",     "emoji": "🛡️"},
    "Divine Kavach":  {"price": 3000, "defense": 60, "rarity": "Legendary","emoji": "✨🛡️"},
}

# Random enemies for PvE fights, scaled roughly with level via a multiplier in game_logic
ENEMIES = [
    {"name": "जंगली भेड़िया",      "emoji": "🐺", "base_health": 40,  "base_damage": 6,  "coin": 30,  "xp": 15},
    {"name": "डाकू",              "emoji": "🥷", "base_health": 55,  "base_damage": 9,  "coin": 45,  "xp": 22},
    {"name": "राक्षस",            "emoji": "👹", "base_health": 80,  "base_damage": 13, "coin": 70,  "xp": 35},
    {"name": "अजगर",              "emoji": "🐍", "base_health": 100, "base_damage": 17, "coin": 90,  "xp": 45},
    {"name": "पत्थर दानव",        "emoji": "🗿", "base_health": 130, "base_damage": 20, "coin": 120, "xp": 60},
    {"name": "अग्नि दैत्य",        "emoji": "🔥", "base_health": 170, "base_damage": 26, "coin": 160, "xp": 80},
    {"name": "महाकाय ड्रैगन",      "emoji": "🐉", "base_health": 250, "base_damage": 35, "coin": 250, "xp": 120},
]

# Daily missions pool - one random set of 3 assigned per user per day
MISSIONS_POOL = [
    {"key": "win_3_fights",  "desc": "3 Fights जीतो",           "type": "win_fight", "target": 3,  "reward_coins": 100, "reward_xp": 30},
    {"key": "win_1_pvp",     "desc": "1 PvP Fight जीतो",         "type": "win_pvp",   "target": 1,  "reward_coins": 150, "reward_xp": 40},
    {"key": "play_5_dice",   "desc": "5 बार Dice Game खेलो",     "type": "play_dice", "target": 5,  "reward_coins": 80,  "reward_xp": 20},
    {"key": "spin_1",        "desc": "1 बार Lucky Spin करो",     "type": "spin",      "target": 1,  "reward_coins": 60,  "reward_xp": 15},
    {"key": "earn_200_coins","desc": "200 Coins कमाओ",           "type": "earn_coins","target": 200,"reward_coins": 100, "reward_xp": 25},
    {"key": "fight_5_times", "desc": "5 बार Fight करो",          "type": "fight_count","target": 5, "reward_coins": 90,  "reward_xp": 25},
]

# Achievements: key -> metadata. Unlock condition checked in code (achievements.py logic)
ACHIEVEMENTS = {
    "first_blood":   {"name": "🩸 First Blood",     "desc": "अपनी पहली Fight जीतो"},
    "warrior_10":    {"name": "⚔️ Warrior",         "desc": "10 Fights जीतो"},
    "champion_50":   {"name": "🏆 Champion",        "desc": "50 Fights जीतो"},
    "pvp_king":      {"name": "👑 PvP King",        "desc": "10 PvP Fights जीतो"},
    "level_10":      {"name": "📈 Rising Star",     "desc": "Level 10 पर पहुंचो"},
    "level_25":      {"name": "🌟 Legend",          "desc": "Level 25 पर पहुंचो"},
    "rich_1000":     {"name": "💰 Rich",            "desc": "1000 Coins इकट्ठा करो"},
    "rich_10000":    {"name": "💎 Millionaire",     "desc": "10000 Coins इकट्ठा करो"},
    "collector":     {"name": "🎒 Collector",       "desc": "5 अलग Weapons इकट्ठा करो"},
    "clan_member":   {"name": "👥 Team Player",     "desc": "किसी Clan में शामिल हो"},
    "lucky":         {"name": "🍀 Lucky",           "desc": "Lucky Spin से Jackpot जीतो"},
    "referrer":      {"name": "🎁 Recruiter",       "desc": "5 दोस्तों को Refer करो"},
}

# Lucky spin rewards with weights (higher weight = more common)
SPIN_REWARDS = [
    {"type": "coins", "amount": 20,  "weight": 30, "label": "20 💰 Coins"},
    {"type": "coins", "amount": 50,  "weight": 20, "label": "50 💰 Coins"},
    {"type": "coins", "amount": 100, "weight": 12, "label": "100 💰 Coins"},
    {"type": "xp",    "amount": 20,  "weight": 15, "label": "20 ⭐ XP"},
    {"type": "xp",    "amount": 50,  "weight": 8,  "label": "50 ⭐ XP"},
    {"type": "energy","amount": 20,  "weight": 10, "label": "20 ⚡ Energy"},
    {"type": "jackpot","amount": 1000,"weight": 3, "label": "🎉 JACKPOT 1000 Coins!"},
    {"type": "nothing","amount": 0,  "weight": 2,  "label": "😢 कुछ नहीं मिला"},
]
