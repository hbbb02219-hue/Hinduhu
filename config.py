# -*- coding: utf-8 -*-
"""
Bot Configuration
अपना BOT_TOKEN और ADMIN_IDS यहाँ डालें।
"""

# अपने BotFather से मिला टोकन यहाँ डालें
BOT_TOKEN = "8239368102:AAFqhdH4Zr9VrDEaYo3vzyVZZ22LSCRtFpg"

# Admin user IDs (Telegram numeric user id). अपनी ID @userinfobot से पता करें।
ADMIN_IDS = [7663073502]

DB_PATH = "game_bot.db"

# ---------------- Game balance settings ----------------
STARTING_HEALTH = 100
STARTING_ENERGY = 50
STARTING_COINS = 100

ENERGY_PER_FIGHT = 10
ENERGY_PER_PVP = 15
ENERGY_REGEN_MINUTES = 5      # हर 5 मिनट में +1 energy
HEALTH_REGEN_MINUTES = 3      # हर 3 मिनट में +1 health

DAILY_REWARD_COINS = 100
DAILY_REWARD_XP = 20
DAILY_COOLDOWN_HOURS = 24

SPIN_COOLDOWN_HOURS = 24

REFERRAL_REWARD_COINS = 100
REFERRAL_REWARD_XP = 30

CLAN_CREATE_COST = 1000

# XP needed to go from level N -> N+1 :  level * 100
def xp_for_level(level: int) -> int:
    return level * 100
