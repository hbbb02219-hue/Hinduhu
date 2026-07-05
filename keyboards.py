# -*- coding: utf-8 -*-
"""
सारे Keyboards (Reply + Inline) यहाँ हैं।
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import game_data

MAIN_MENU_BUTTONS = [
    ["👤 Profile", "⚔️ Fight"],
    ["🥊 PvP Fight", "🎒 Inventory"],
    ["💎 Shop", "🎁 Daily Reward"],
    ["🎯 Daily Missions", "🏆 Leaderboard"],
    ["👥 Clan", "🎰 Lucky Spin"],
    ["🎲 Dice Game", "🎖️ Achievements"],
    ["ℹ️ Help"],
]


def main_menu(is_admin: bool = False):
    buttons = [row[:] for row in MAIN_MENU_BUTTONS]
    if is_admin:
        buttons.append(["👑 Admin Panel"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def shop_menu():
    kb = [
        [InlineKeyboardButton("🗡️ Weapons", callback_data="shop_weapons")],
        [InlineKeyboardButton("🛡️ Armor", callback_data="shop_armor")],
        [InlineKeyboardButton("❌ Close", callback_data="shop_close")],
    ]
    return InlineKeyboardMarkup(kb)


def shop_weapons_kb(owned_names):
    kb = []
    for name, w in game_data.WEAPONS.items():
        label = f"{w['emoji']} {name} - 💰{w['price']} (DMG {w['damage']})"
        if name in owned_names:
            label = f"✅ {name} (खरीदा हुआ)"
            kb.append([InlineKeyboardButton(f"⚔️ Equip: {name}", callback_data=f"equip_weapon:{name}")])
        else:
            kb.append([InlineKeyboardButton(label, callback_data=f"buy_weapon:{name}")])
    kb.append([InlineKeyboardButton("⬅️ Back", callback_data="shop_back")])
    return InlineKeyboardMarkup(kb)


def shop_armor_kb(owned_names):
    kb = []
    for name, a in game_data.ARMORS.items():
        if name in owned_names:
            kb.append([InlineKeyboardButton(f"🛡️ Equip: {name}", callback_data=f"equip_armor:{name}")])
        else:
            label = f"{a['emoji']} {name} - 💰{a['price']} (DEF {a['defense']})"
            kb.append([InlineKeyboardButton(label, callback_data=f"buy_armor:{name}")])
    kb.append([InlineKeyboardButton("⬅️ Back", callback_data="shop_back")])
    return InlineKeyboardMarkup(kb)


def clan_menu(in_clan: bool):
    if in_clan:
        kb = [
            [InlineKeyboardButton("📋 Clan Info", callback_data="clan_info")],
            [InlineKeyboardButton("🏆 Clan Leaderboard", callback_data="clan_leaderboard")],
            [InlineKeyboardButton("🚪 Leave Clan", callback_data="clan_leave")],
        ]
    else:
        kb = [
            [InlineKeyboardButton("➕ Create Clan", callback_data="clan_create")],
            [InlineKeyboardButton("📜 Clan List / Join", callback_data="clan_list")],
            [InlineKeyboardButton("🏆 Clan Leaderboard", callback_data="clan_leaderboard")],
        ]
    return InlineKeyboardMarkup(kb)


def pvp_challenge_kb(challenge_id: int):
    kb = [
        [InlineKeyboardButton("✅ Accept", callback_data=f"pvp_accept:{challenge_id}"),
         InlineKeyboardButton("❌ Decline", callback_data=f"pvp_decline:{challenge_id}")]
    ]
    return InlineKeyboardMarkup(kb)


def dice_bet_kb():
    kb = [
        [InlineKeyboardButton("💰 50", callback_data="dice_bet:50"),
         InlineKeyboardButton("💰 100", callback_data="dice_bet:100")],
        [InlineKeyboardButton("💰 250", callback_data="dice_bet:250"),
         InlineKeyboardButton("💰 500", callback_data="dice_bet:500")],
    ]
    return InlineKeyboardMarkup(kb)


def admin_panel_kb():
    kb = [
        [InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Broadcast Guide", callback_data="admin_broadcast_help")],
        [InlineKeyboardButton("💰 Give Coins Guide", callback_data="admin_givecoins_help")],
        [InlineKeyboardButton("🚫 Ban / Unban Guide", callback_data="admin_ban_help")],
    ]
    return InlineKeyboardMarkup(kb)
