# -*- coding: utf-8 -*-
"""
🎮 RPG Telegram Bot - Main entry point
python-telegram-bot v20+ पर आधारित।

चलाने के लिए:
    pip install -r requirements.txt
    python main.py
"""

import logging
import random
import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

import config
import database
import game_data
import game_logic
import keyboards
import achievements

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def ensure_user(update: Update):
    """Create user if not exists, refresh basic info, apply passive regen. Returns user dict."""
    tg_user = update.effective_user
    user = database.get_user(tg_user.id)
    if not user:
        database.create_user(tg_user.id, tg_user.username or "", tg_user.first_name or "Player")
        user = database.get_user(tg_user.id)
    else:
        database.update_user(tg_user.id, username=tg_user.username or "", first_name=tg_user.first_name or "Player")
    database.regen_stats(tg_user.id)
    return database.get_user(tg_user.id)


def progress_bar(current, maximum, length=10):
    if maximum <= 0:
        maximum = 1
    filled = int(length * max(0, min(current, maximum)) / maximum)
    return "🟩" * filled + "⬜" * (length - filled)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    existing = database.get_user(tg_user.id)
    referred_by = None

    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_") and not existing:
            try:
                ref_id = int(arg.replace("ref_", ""))
                if ref_id != tg_user.id and database.get_user(ref_id):
                    referred_by = ref_id
            except ValueError:
                pass

    if not existing:
        database.create_user(tg_user.id, tg_user.username or "", tg_user.first_name or "Player", referred_by)
        if referred_by:
            database.add_coins(referred_by, config.REFERRAL_REWARD_COINS)
            database.add_xp(referred_by, config.REFERRAL_REWARD_XP)
            with database.get_conn() as conn:
                conn.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id=?", (referred_by,))
            newly = achievements.check_and_unlock(referred_by)
            try:
                notice = achievements.format_achievement_notice(newly)
                text = (f"🎉 आपके referral से एक नया player जुड़ा!\n"
                        f"+{config.REFERRAL_REWARD_COINS} 💰 और +{config.REFERRAL_REWARD_XP} ⭐ मिले!{notice}")
                await context.bot.send_message(referred_by, text, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                pass

    user = ensure_user(update)

    welcome_text = (
        "🚩🚩🚩 *WARRIOR ARENA में आपका स्वागत है!* 🚩🚩🚩\n\n"
        f"👋 नमस्ते *{tg_user.first_name}*!\n\n"
        "⚔️ यहाँ आप दुश्मनों से लड़ेंगे, दूसरे players को PvP में चुनौती देंगे,\n"
        "🗡️ शक्तिशाली हथियार और 🛡️ कवच इकट्ठा करेंगे,\n"
        "👥 अपना Clan बनाएंगे, और 🏆 Leaderboard में टॉप पर पहुंचेंगे!\n\n"
        "🎮 नीचे दिए मेनू से खेलना शुरू करें।\n"
        "ℹ️ पूरी जानकारी के लिए *Help* बटन दबाएँ।\n\n"
        f"💰 Starting Coins: {config.STARTING_COINS}\n"
        f"❤️ Health: {config.STARTING_HEALTH} | ⚡ Energy: {config.STARTING_ENERGY}\n\n"
        "आपकी यात्रा अभी शुरू होती है, योद्धा! 🔥"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboards.main_menu(is_admin(tg_user.id))
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update)
    text = (
        "📖 *Bot Guide*\n\n"
        "👤 *Profile* - अपनी stats देखें\n"
        "⚔️ *Fight* - Random दुश्मन से लड़ें (Energy खर्च होगी)\n"
        "🥊 *PvP Fight* - Group में किसी की message पर reply करके `/duel` भेजें\n"
        "🎒 *Inventory* - अपने हथियार व कवच देखें\n"
        "💎 *Shop* - नए हथियार/कवच खरीदें\n"
        "🎁 *Daily Reward* - रोज़ाना मुफ़्त इनाम\n"
        "🎯 *Daily Missions* - रोज़ के मिशन पूरे कर इनाम पाएं\n"
        "🏆 *Leaderboard* - टॉप players\n"
        "👥 *Clan* - Clan बनाएं या join करें\n"
        "🎰 *Lucky Spin* - रोज़ाना एक मुफ़्त स्पिन\n"
        "🎲 *Dice Game* - Coins लगा कर dice खेलें\n"
        "🎖️ *Achievements* - अपनी उपलब्धियां देखें\n\n"
        f"🔗 Referral Link: `https://t.me/{context.bot.username}?start=ref_{update.effective_user.id}`\n"
        "इसे दोस्तों को भेजें, हर join पर आपको इनाम मिलेगा!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# 👤 Profile
# ---------------------------------------------------------------------------

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    clan_name = "कोई नहीं"
    if user["clan_id"]:
        clan = database.get_clan(clan_id=user["clan_id"])
        if clan:
            clan_name = clan["name"]

    xp_needed = config.xp_for_level(user["level"])
    text = (
        f"👤 *{user['first_name']}* की Profile\n\n"
        f"📈 Level: *{user['level']}*\n"
        f"⭐ XP: {user['xp']}/{xp_needed}\n"
        f"❤️ Health: {user['health']}/{user['max_health']}  {progress_bar(user['health'], user['max_health'])}\n"
        f"⚡ Energy: {user['energy']}/{user['max_energy']}  {progress_bar(user['energy'], user['max_energy'])}\n"
        f"💰 Coins: {user['coins']}\n\n"
        f"⚔️ Fights Won: {user['wins']} | Lost: {user['losses']}\n"
        f"🥊 PvP Won: {user['pvp_wins']} | Lost: {user['pvp_losses']}\n\n"
        f"🗡️ Weapon: {user['equipped_weapon']}\n"
        f"🛡️ Armor: {user['equipped_armor']}\n"
        f"👥 Clan: {clan_name}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# ⚔️ Fight (PvE)
# ---------------------------------------------------------------------------

async def fight_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)

    if user["energy"] < config.ENERGY_PER_FIGHT:
        await update.message.reply_text(
            f"⚡ पर्याप्त Energy नहीं है! आपके पास {user['energy']} energy है, "
            f"{config.ENERGY_PER_FIGHT} चाहिए। थोड़ी देर बाद फिर कोशिश करें या Lucky Spin से energy पाएं।"
        )
        return
    if user["health"] <= 5:
        await update.message.reply_text("❤️ आपकी Health बहुत कम है! पहले आराम करें, health regenerate होने दें।")
        return

    enemy = game_logic.pick_random_enemy(user["level"])
    result = game_logic.simulate_pve_fight(user, enemy)

    database.update_user(
        user["user_id"],
        energy=user["energy"] - config.ENERGY_PER_FIGHT,
        health=result["player_hp_left"] if result["player_hp_left"] > 0 else 1,
    )

    lines = [f"{enemy['emoji']} *{enemy['name']}* से मुकाबला!\n"]
    lines.extend(result["log"][-6:])
    lines.append("")

    if result["won"]:
        database.add_coins(user["user_id"], result["coin_reward"])
        levels = database.add_xp(user["user_id"], result["xp_reward"])
        with database.get_conn() as conn:
            conn.execute("UPDATE users SET wins = wins + 1 WHERE user_id=?", (user["user_id"],))
        database.update_mission_progress(user["user_id"], "win_fight")
        database.update_mission_progress(user["user_id"], "earn_coins", result["coin_reward"])
        lines.append(f"🎉 *जीत गए!* +{result['coin_reward']} 💰 +{result['xp_reward']} ⭐")
        if levels:
            lines.append(f"🆙 Level Up! अब आप Level *{levels[-1]}* हैं! 🎊")
    else:
        database.add_coins(user["user_id"], result["coin_reward"])
        with database.get_conn() as conn:
            conn.execute("UPDATE users SET losses = losses + 1 WHERE user_id=?", (user["user_id"],))
        lines.append(f"💀 *हार गए!* फिर भी +{result['coin_reward']} 💰 सांत्वना इनाम मिला।")

    database.update_mission_progress(user["user_id"], "fight_count")
    newly = achievements.check_and_unlock(user["user_id"])
    notice = achievements.format_achievement_notice(newly)
    if notice:
        lines.append(notice)

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# 🥊 PvP Fight
# ---------------------------------------------------------------------------

async def pvp_info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update)
    await update.message.reply_text(
        "🥊 *PvP Fight कैसे खेलें:*\n\n"
        "1️⃣ किसी Group में जाएं\n"
        "2️⃣ जिस player को चुनौती देनी है, उसकी किसी message पर *Reply* करें\n"
        "3️⃣ Reply में `/duel` टाइप करें\n\n"
        "सामने वाला Accept करेगा तो लड़ाई शुरू हो जाएगी! ⚔️",
        parse_mode=ParseMode.MARKDOWN
    )


async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    challenger = ensure_user(update)
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "⚠️ किसी player की message पर Reply करके `/duel` भेजें ताकि उसे challenge मिल सके।"
        )
        return

    opponent_tg = update.message.reply_to_message.from_user
    if opponent_tg.id == challenger["user_id"]:
        await update.message.reply_text("😂 आप खुद को चुनौती नहीं दे सकते!")
        return
    if opponent_tg.is_bot:
        await update.message.reply_text("🤖 आप किसी बॉट को चुनौती नहीं दे सकते!")
        return

    opponent = database.get_user(opponent_tg.id)
    if not opponent:
        await update.message.reply_text(
            "⚠️ उस player ने अभी तक बॉट को शुरू नहीं किया। उन्हें पहले बॉट को DM में /start भेजने को कहें।"
        )
        return

    if challenger["energy"] < config.ENERGY_PER_PVP:
        await update.message.reply_text(f"⚡ PvP के लिए {config.ENERGY_PER_PVP} energy चाहिए।")
        return

    challenge_id = database.create_challenge(challenger["user_id"], opponent["user_id"], update.effective_chat.id)

    await update.message.reply_text(
        f"⚔️ {update.effective_user.first_name} ने {opponent_tg.first_name} को PvP Duel के लिए चुनौती दी है!\n"
        f"{opponent_tg.first_name}, क्या आप Accept करते हैं?",
        reply_markup=keyboards.pvp_challenge_kb(challenge_id)
    )


async def pvp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    action, challenge_id_str = data.split(":")
    challenge_id = int(challenge_id_str)
    challenge = database.get_challenge(challenge_id)

    if not challenge or challenge["status"] != "pending":
        await query.edit_message_text("⚠️ यह चुनौती अब मान्य नहीं है।")
        return

    if query.from_user.id != challenge["opponent_id"]:
        await query.answer("यह चुनौती आपके लिए नहीं है!", show_alert=True)
        return

    if action == "pvp_decline":
        database.set_challenge_status(challenge_id, "declined")
        await query.edit_message_text("❌ चुनौती अस्वीकार कर दी गई।")
        return

    database.set_challenge_status(challenge_id, "accepted")

    user_a = database.get_user(challenge["challenger_id"])
    user_b = database.get_user(challenge["opponent_id"])

    if user_a["energy"] < config.ENERGY_PER_PVP or user_b["energy"] < config.ENERGY_PER_PVP:
        await query.edit_message_text("⚡ किसी player के पास पर्याप्त Energy नहीं बची, Duel रद्द।")
        return

    result = game_logic.simulate_pvp_fight(user_a, user_b)

    database.update_user(user_a["user_id"], energy=user_a["energy"] - config.ENERGY_PER_PVP,
                          health=max(1, result["hp_a_left"]))
    database.update_user(user_b["user_id"], energy=user_b["energy"] - config.ENERGY_PER_PVP,
                          health=max(1, result["hp_b_left"]))

    lines = [f"⚔️ *PvP Duel:* {user_a['first_name']} 🆚 {user_b['first_name']}\n"]
    lines.extend(result["log"][-6:])
    lines.append("")

    if result["winner"] is None:
        lines.append("🤝 मुकाबला बराबरी पर छूटा!")
    else:
        winner_id = result["winner"]
        loser_id = user_b["user_id"] if winner_id == user_a["user_id"] else user_a["user_id"]
        winner_name = user_a["first_name"] if winner_id == user_a["user_id"] else user_b["first_name"]
        reward_coins = 80
        reward_xp = 40
        database.add_coins(winner_id, reward_coins)
        levels = database.add_xp(winner_id, reward_xp)
        with database.get_conn() as conn:
            conn.execute("UPDATE users SET pvp_wins = pvp_wins + 1 WHERE user_id=?", (winner_id,))
            conn.execute("UPDATE users SET pvp_losses = pvp_losses + 1 WHERE user_id=?", (loser_id,))
        database.update_mission_progress(winner_id, "win_pvp")
        lines.append(f"🏆 *{winner_name} जीत गए!* +{reward_coins} 💰 +{reward_xp} ⭐")
        if levels:
            lines.append(f"🆙 {winner_name} अब Level {levels[-1]} पर पहुंच गए! 🎊")
        newly = achievements.check_and_unlock(winner_id)
        notice = achievements.format_achievement_notice(newly)
        if notice:
            lines.append(notice)

    await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# 🎒 Inventory
# ---------------------------------------------------------------------------

async def inventory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    weapons = database.get_inventory(user["user_id"], "weapon")
    armors = database.get_inventory(user["user_id"], "armor")

    lines = ["🎒 *आपकी Inventory*\n", "🗡️ *Weapons:*"]
    for w in weapons:
        tag = " ✅ (Equipped)" if w["item_name"] == user["equipped_weapon"] else ""
        dmg = game_data.WEAPONS.get(w["item_name"], {}).get("damage", "?")
        lines.append(f"  • {w['item_name']} (DMG {dmg}){tag}")

    lines.append("\n🛡️ *Armor:*")
    for a in armors:
        tag = " ✅ (Equipped)" if a["item_name"] == user["equipped_armor"] else ""
        defn = game_data.ARMORS.get(a["item_name"], {}).get("defense", "?")
        lines.append(f"  • {a['item_name']} (DEF {defn}){tag}")

    lines.append("\n💎 नए items के लिए Shop खोलें।")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# 💎 Shop
# ---------------------------------------------------------------------------

async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update)
    await update.message.reply_text("💎 *Shop में आपका स्वागत है!*\nक्या खरीदना चाहेंगे?",
                                     parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.shop_menu())


async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = database.get_user(user_id)
    data = query.data

    if data == "shop_close":
        await query.edit_message_text("🛒 Shop बंद कर दी गई।")
        return

    if data == "shop_back":
        await query.edit_message_text("💎 *Shop में आपका स्वागत है!*\nक्या खरीदना चाहेंगे?",
                                       parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.shop_menu())
        return

    if data == "shop_weapons":
        owned = [i["item_name"] for i in database.get_inventory(user_id, "weapon")]
        await query.edit_message_text("🗡️ *Weapons Shop*", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=keyboards.shop_weapons_kb(owned))
        return

    if data == "shop_armor":
        owned = [i["item_name"] for i in database.get_inventory(user_id, "armor")]
        await query.edit_message_text("🛡️ *Armor Shop*", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=keyboards.shop_armor_kb(owned))
        return

    if data.startswith("buy_weapon:"):
        name = data.split(":", 1)[1]
        item = game_data.WEAPONS.get(name)
        if not item:
            return
        if user["coins"] < item["price"]:
            await query.answer("❌ पर्याप्त Coins नहीं हैं!", show_alert=True)
            return
        database.add_coins(user_id, -item["price"])
        database.add_item(user_id, "weapon", name, 1)
        owned = [i["item_name"] for i in database.get_inventory(user_id, "weapon")]
        newly = achievements.check_and_unlock(user_id)
        await query.answer(f"✅ {name} खरीदा गया!")
        await query.edit_message_text(
            f"🗡️ *Weapons Shop*\n\n✅ आपने *{name}* खरीदा!" + achievements.format_achievement_notice(newly),
            parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.shop_weapons_kb(owned))
        return

    if data.startswith("buy_armor:"):
        name = data.split(":", 1)[1]
        item = game_data.ARMORS.get(name)
        if not item:
            return
        if user["coins"] < item["price"]:
            await query.answer("❌ पर्याप्त Coins नहीं हैं!", show_alert=True)
            return
        database.add_coins(user_id, -item["price"])
        database.add_item(user_id, "armor", name, 1)
        owned = [i["item_name"] for i in database.get_inventory(user_id, "armor")]
        await query.answer(f"✅ {name} खरीदा गया!")
        await query.edit_message_text(f"🛡️ *Armor Shop*\n\n✅ आपने *{name}* खरीदा!",
                                       parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.shop_armor_kb(owned))
        return

    if data.startswith("equip_weapon:"):
        name = data.split(":", 1)[1]
        database.update_user(user_id, equipped_weapon=name)
        owned = [i["item_name"] for i in database.get_inventory(user_id, "weapon")]
        await query.answer(f"⚔️ {name} equip किया गया!")
        await query.edit_message_text(f"🗡️ *Weapons Shop*\n\n⚔️ *{name}* अब equipped है!",
                                       parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.shop_weapons_kb(owned))
        return

    if data.startswith("equip_armor:"):
        name = data.split(":", 1)[1]
        database.update_user(user_id, equipped_armor=name)
        owned = [i["item_name"] for i in database.get_inventory(user_id, "armor")]
        await query.answer(f"🛡️ {name} equip किया गया!")
        await query.edit_message_text(f"🛡️ *Armor Shop*\n\n🛡️ *{name}* अब equipped है!",
                                       parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.shop_armor_kb(owned))
        return


# ---------------------------------------------------------------------------
# 🎁 Daily Reward
# ---------------------------------------------------------------------------

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    now = datetime.datetime.utcnow()

    if user["last_daily"]:
        last = datetime.datetime.fromisoformat(user["last_daily"])
        elapsed_hours = (now - last).total_seconds() / 3600
        if elapsed_hours < config.DAILY_COOLDOWN_HOURS:
            remaining = config.DAILY_COOLDOWN_HOURS - elapsed_hours
            hrs = int(remaining)
            mins = int((remaining - hrs) * 60)
            await update.message.reply_text(
                f"⏳ Daily Reward पहले ही ले लिया है। अगला reward {hrs}घं {mins}मि बाद मिलेगा।"
            )
            return

    database.add_coins(user["user_id"], config.DAILY_REWARD_COINS)
    levels = database.add_xp(user["user_id"], config.DAILY_REWARD_XP)
    database.update_user(user["user_id"], last_daily=now.isoformat())
    database.update_mission_progress(user["user_id"], "earn_coins", config.DAILY_REWARD_COINS)

    text = (f"🎁 *Daily Reward मिला!*\n\n"
            f"+{config.DAILY_REWARD_COINS} 💰 Coins\n"
            f"+{config.DAILY_REWARD_XP} ⭐ XP\n\n"
            f"रोज़ आकर reward लेना न भूलें! 🔥")
    if levels:
        text += f"\n\n🆙 Level Up! अब आप Level {levels[-1]} हैं!"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# 🎯 Daily Missions
# ---------------------------------------------------------------------------

async def missions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    today_missions = database.get_today_missions(user["user_id"])

    if not today_missions:
        chosen = random.sample(game_data.MISSIONS_POOL, k=min(3, len(game_data.MISSIONS_POOL)))
        database.assign_daily_missions(user["user_id"], chosen)
        today_missions = database.get_today_missions(user["user_id"])

    key_to_desc = {m["key"]: m["desc"] for m in game_data.MISSIONS_POOL}
    lines = ["🎯 *आज के Missions:*\n"]
    kb_rows = []
    for m in today_missions:
        desc = key_to_desc.get(m["mission_key"], m["mission_key"])
        status = "✅ पूरा" if m["completed"] else f"{m['progress']}/{m['target']}"
        claimed = " (Claimed)" if m["claimed"] else ""
        lines.append(f"• {desc} — {status}{claimed}  |  🎁 {m['reward_coins']}💰 {m['reward_xp']}⭐")
        if m["completed"] and not m["claimed"]:
            kb_rows.append([InlineKeyboardButton(f"🎁 Claim: {desc}", callback_data=f"claim_mission:{m['mission_key']}")])

    markup = InlineKeyboardMarkup(kb_rows) if kb_rows else None
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=markup)


async def claim_mission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mission_key = query.data.split(":", 1)[1]
    user_id = query.from_user.id
    result = database.claim_mission(user_id, mission_key)
    if not result:
        await query.answer("⚠️ यह mission claim नहीं किया जा सकता।", show_alert=True)
        return
    database.add_coins(user_id, result["reward_coins"])
    levels = database.add_xp(user_id, result["reward_xp"])
    text = f"🎉 Mission इनाम मिला: +{result['reward_coins']} 💰 +{result['reward_xp']} ⭐"
    if levels:
        text += f"\n🆙 Level Up! अब Level {levels[-1]}!"
    await query.edit_message_text(text)


# ---------------------------------------------------------------------------
# 🏆 Leaderboard
# ---------------------------------------------------------------------------

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update)
    top = database.get_leaderboard(10)
    if not top:
        await update.message.reply_text("अभी कोई player नहीं है।")
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 *Top Players Leaderboard*\n"]
    for i, p in enumerate(top):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = p["first_name"] or p["username"] or "Player"
        lines.append(f"{medal} {name} — Lv.{p['level']} ({p['xp']} XP) 💰{p['coins']}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# 👥 Clan System
# ---------------------------------------------------------------------------

async def clan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    in_clan = user["clan_id"] is not None
    await update.message.reply_text("👥 *Clan Menu*", parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=keyboards.clan_menu(in_clan))


async def clan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = database.get_user(user_id)
    data = query.data

    if data == "clan_create":
        if user["clan_id"]:
            await query.answer("आप पहले से किसी Clan में हैं!", show_alert=True)
            return
        if user["coins"] < config.CLAN_CREATE_COST:
            await query.answer(f"❌ Clan बनाने के लिए {config.CLAN_CREATE_COST} coins चाहिए!", show_alert=True)
            return
        context.user_data["awaiting_clan_name"] = True
        await query.edit_message_text(
            f"➕ Clan बनाने के लिए {config.CLAN_CREATE_COST} 💰 लगेंगे।\n"
            "अपने Clan का नाम टाइप करके भेजें (message में सिर्फ नाम लिखें)।"
        )
        return

    if data == "clan_list":
        clans = database.list_all_clans()
        if not clans:
            await query.edit_message_text("😔 अभी कोई Clan मौजूद नहीं है। आप पहला बना सकते हैं!")
            return
        kb = [[InlineKeyboardButton(f"👥 {c['name']}", callback_data=f"clan_join:{c['clan_id']}")] for c in clans[:15]]
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="clan_back")])
        await query.edit_message_text("📜 *उपलब्ध Clans:*", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("clan_join:"):
        clan_id = int(data.split(":", 1)[1])
        if user["clan_id"]:
            await query.answer("आप पहले से किसी Clan में हैं!", show_alert=True)
            return
        database.join_clan(user_id, clan_id)
        newly = achievements.check_and_unlock(user_id)
        clan = database.get_clan(clan_id=clan_id)
        await query.edit_message_text(f"✅ आप *{clan['name']}* Clan में शामिल हो गए!" +
                                       achievements.format_achievement_notice(newly),
                                       parse_mode=ParseMode.MARKDOWN)
        return

    if data == "clan_info":
        if not user["clan_id"]:
            await query.answer("आप किसी Clan में नहीं हैं!", show_alert=True)
            return
        clan = database.get_clan(clan_id=user["clan_id"])
        members = database.get_clan_members(user["clan_id"])
        lines = [f"👥 *{clan['name']}*\nLeader ID: {clan['leader_id']}\nसदस्य: {len(members)}\n"]
        for m in members[:20]:
            lines.append(f"• {m['first_name']} — Lv.{m['level']}")
        await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "clan_leaderboard":
        top = database.clan_leaderboard(10)
        if not top:
            await query.edit_message_text("अभी कोई Clan मौजूद नहीं है।")
            return
        lines = ["🏆 *Clan Leaderboard*\n"]
        for i, c in enumerate(top):
            lines.append(f"{i+1}. {c['name']} — कुल Level: {c['total_level'] or 0} ({c['members']} सदस्य)")
        await query.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "clan_leave":
        if not user["clan_id"]:
            await query.answer("आप किसी Clan में नहीं हैं!", show_alert=True)
            return
        database.leave_clan(user_id)
        await query.edit_message_text("🚪 आप Clan से बाहर आ गए।")
        return

    if data == "clan_back":
        in_clan = user["clan_id"] is not None
        await query.edit_message_text("👥 *Clan Menu*", parse_mode=ParseMode.MARKDOWN,
                                       reply_markup=keyboards.clan_menu(in_clan))
        return


async def text_router_clan_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handles the follow-up plain-text message when user is creating a clan. Returns True if handled."""
    if not context.user_data.get("awaiting_clan_name"):
        return False
    context.user_data["awaiting_clan_name"] = False
    name = update.message.text.strip()[:30]
    user = ensure_user(update)
    if user["coins"] < config.CLAN_CREATE_COST:
        await update.message.reply_text("❌ अब पर्याप्त coins नहीं हैं।")
        return True
    if database.get_clan(name=name):
        await update.message.reply_text("⚠️ इस नाम का Clan पहले से मौजूद है। दोबारा /clan try करें।")
        return True
    database.add_coins(user["user_id"], -config.CLAN_CREATE_COST)
    database.create_clan(name, user["user_id"])
    newly = achievements.check_and_unlock(user["user_id"])
    await update.message.reply_text(f"🎉 Clan *{name}* बन गया! आप इसके Leader हैं।" +
                                     achievements.format_achievement_notice(newly),
                                     parse_mode=ParseMode.MARKDOWN)
    return True


# ---------------------------------------------------------------------------
# 🎰 Lucky Spin
# ---------------------------------------------------------------------------

async def spin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    now = datetime.datetime.utcnow()

    if user["last_spin"]:
        last = datetime.datetime.fromisoformat(user["last_spin"])
        elapsed_hours = (now - last).total_seconds() / 3600
        if elapsed_hours < config.SPIN_COOLDOWN_HOURS:
            remaining = config.SPIN_COOLDOWN_HOURS - elapsed_hours
            hrs = int(remaining)
            mins = int((remaining - hrs) * 60)
            await update.message.reply_text(f"⏳ अगला Spin {hrs}घं {mins}मि बाद उपलब्ध होगा।")
            return

    reward = game_logic.weighted_spin_choice()
    database.update_user(user["user_id"], last_spin=now.isoformat())

    text = f"🎰 Spin घूम रहा है... 🎡\n\n🎉 आपको मिला: *{reward['label']}*"

    if reward["type"] in ("coins", "jackpot"):
        database.add_coins(user["user_id"], reward["amount"])
        database.update_mission_progress(user["user_id"], "earn_coins", reward["amount"])
    elif reward["type"] == "xp":
        levels = database.add_xp(user["user_id"], reward["amount"])
        if levels:
            text += f"\n🆙 Level Up! अब Level {levels[-1]}!"
    elif reward["type"] == "energy":
        new_energy = min(user["max_energy"], user["energy"] + reward["amount"])
        database.update_user(user["user_id"], energy=new_energy)

    database.update_mission_progress(user["user_id"], "spin")

    newly = []
    if reward["type"] == "jackpot":
        if achievements.unlock_lucky(user["user_id"]):
            newly.append("lucky")
    newly.extend(achievements.check_and_unlock(user["user_id"]))
    notice = achievements.format_achievement_notice(newly)
    if notice:
        text += notice

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# 🎲 Dice Game
# ---------------------------------------------------------------------------

async def dice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    await update.message.reply_text(
        f"🎲 *Dice Game*\nआपके पास 💰{user['coins']} coins हैं।\nकितना bet लगाना चाहते हैं?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=keyboards.dice_bet_kb()
    )


async def dice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = database.get_user(user_id)
    bet = int(query.data.split(":", 1)[1])

    if user["coins"] < bet:
        await query.answer("❌ पर्याप्त Coins नहीं हैं!", show_alert=True)
        return

    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)

    if player_roll > bot_roll:
        winnings = bet
        database.add_coins(user_id, winnings)
        database.update_mission_progress(user_id, "earn_coins", winnings)
        result_text = f"🎉 आप जीत गए! +{winnings} 💰"
    elif player_roll < bot_roll:
        database.add_coins(user_id, -bet)
        result_text = f"💀 आप हार गए! -{bet} 💰"
    else:
        result_text = "🤝 बराबरी! Bet वापस।"

    database.update_mission_progress(user_id, "play_dice")
    newly = achievements.check_and_unlock(user_id)
    notice = achievements.format_achievement_notice(newly)

    await query.edit_message_text(
        f"🎲 आपका Roll: *{player_roll}*  |  🤖 Bot का Roll: *{bot_roll}*\n\n{result_text}{notice}",
        parse_mode=ParseMode.MARKDOWN
    )


# ---------------------------------------------------------------------------
# 🎖️ Achievements
# ---------------------------------------------------------------------------

async def achievements_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = ensure_user(update)
    unlocked = set(database.get_unlocked_achievements(user["user_id"]))
    lines = ["🎖️ *Achievements*\n"]
    for key, info in game_data.ACHIEVEMENTS.items():
        tag = "✅" if key in unlocked else "🔒"
        lines.append(f"{tag} {info['name']} — {info['desc']}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ---------------------------------------------------------------------------
# 👑 Admin Panel / 📢 Broadcast
# ---------------------------------------------------------------------------

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ यह कमांड सिर्फ Admin के लिए है।")
        return
    await update.message.reply_text("👑 *Admin Panel*", parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=keyboards.admin_panel_kb())


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ अनुमति नहीं है।", show_alert=True)
        return
    await query.answer()
    data = query.data

    if data == "admin_stats":
        user_ids = database.get_all_user_ids()
        with database.get_conn() as conn:
            total_coins = conn.execute("SELECT SUM(coins) as s FROM users").fetchone()["s"] or 0
            total_clans = conn.execute("SELECT COUNT(*) as c FROM clans").fetchone()["c"]
        text = (f"📊 *Bot Stats*\n\n👥 कुल Users: {len(user_ids)}\n"
                f"💰 कुल Coins (सब players): {total_coins}\n👥 कुल Clans: {total_clans}")
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "admin_broadcast_help":
        await query.edit_message_text(
            "📢 सभी users को message भेजने के लिए:\n`/broadcast आपका message यहाँ`",
            parse_mode=ParseMode.MARKDOWN)
        return

    if data == "admin_givecoins_help":
        await query.edit_message_text(
            "💰 किसी user को coins देने के लिए:\n`/givecoins USER_ID AMOUNT`",
            parse_mode=ParseMode.MARKDOWN)
        return

    if data == "admin_ban_help":
        await query.edit_message_text(
            "🚫 Ban/Unban करने के लिए:\n`/ban USER_ID`\n`/unban USER_ID`",
            parse_mode=ParseMode.MARKDOWN)
        return


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ यह कमांड सिर्फ Admin के लिए है।")
        return
    if not context.args:
        await update.message.reply_text("उपयोग: /broadcast आपका message")
        return
    text = "📢 " + " ".join(context.args)
    user_ids = database.get_all_user_ids()
    sent, failed = 0, 0
    status_msg = await update.message.reply_text(f"📤 Broadcast भेजा जा रहा है... (0/{len(user_ids)})")
    for i, uid in enumerate(user_ids, 1):
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        if i % 25 == 0:
            try:
                await status_msg.edit_text(f"📤 भेजा जा रहा है... ({i}/{len(user_ids)})")
            except Exception:
                pass
    await status_msg.edit_text(f"✅ Broadcast पूरा हुआ!\nसफल: {sent} | असफल: {failed}")


async def givecoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ यह कमांड सिर्फ Admin के लिए है।")
        return
    if len(context.args) != 2:
        await update.message.reply_text("उपयोग: /givecoins USER_ID AMOUNT")
        return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("⚠️ USER_ID और AMOUNT numbers होने चाहिए।")
        return
    if not database.get_user(target_id):
        await update.message.reply_text("⚠️ यह user नहीं मिला।")
        return
    database.add_coins(target_id, amount)
    await update.message.reply_text(f"✅ {target_id} को {amount} 💰 coins दिए गए।")
    try:
        await context.bot.send_message(target_id, f"🎁 Admin ने आपको {amount} 💰 coins दिए हैं!")
    except Exception:
        pass


async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ यह कमांड सिर्फ Admin के लिए है।")
        return
    if not context.args:
        await update.message.reply_text("उपयोग: /ban USER_ID")
        return
    target_id = int(context.args[0])
    database.set_ban(target_id, True)
    await update.message.reply_text(f"🚫 User {target_id} को Ban कर दिया गया।")


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ यह कमांड सिर्फ Admin के लिए है।")
        return
    if not context.args:
        await update.message.reply_text("उपयोग: /unban USER_ID")
        return
    target_id = int(context.args[0])
    database.set_ban(target_id, False)
    await update.message.reply_text(f"✅ User {target_id} को Unban कर दिया गया।")


# ---------------------------------------------------------------------------
# Text menu router (Reply Keyboard बटन दबाने पर)
# ---------------------------------------------------------------------------

MENU_ROUTES = {
    "👤 Profile": profile_cmd,
    "⚔️ Fight": fight_cmd,
    "🥊 PvP Fight": pvp_info_cmd,
    "🎒 Inventory": inventory_cmd,
    "💎 Shop": shop_cmd,
    "🎁 Daily Reward": daily_cmd,
    "🎯 Daily Missions": missions_cmd,
    "🏆 Leaderboard": leaderboard_cmd,
    "👥 Clan": clan_cmd,
    "🎰 Lucky Spin": spin_cmd,
    "🎲 Dice Game": dice_cmd,
    "🎖️ Achievements": achievements_cmd,
    "ℹ️ Help": help_cmd,
    "👑 Admin Panel": admin_cmd,
}


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    handled = await text_router_clan_name(update, context)
    if handled:
        return
    handler = MENU_ROUTES.get(text)
    if handler:
        await handler(update, context)
    # अगर कोई menu match ना हो तो कुछ नहीं (chit-chat को ignore करें ताकि group में spam ना हो)


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    database.init_db()

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("fight", fight_cmd))
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("inventory", inventory_cmd))
    app.add_handler(CommandHandler("shop", shop_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("missions", missions_cmd))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(CommandHandler("clan", clan_cmd))
    app.add_handler(CommandHandler("spin", spin_cmd))
    app.add_handler(CommandHandler("dice", dice_cmd))
    app.add_handler(CommandHandler("achievements", achievements_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("givecoins", givecoins_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    # Callback queries
    app.add_handler(CallbackQueryHandler(pvp_callback, pattern=r"^pvp_(accept|decline):"))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern=r"^(shop_|buy_|equip_)"))
    app.add_handler(CallbackQueryHandler(claim_mission_callback, pattern=r"^claim_mission:"))
    app.add_handler(CallbackQueryHandler(clan_callback, pattern=r"^clan_"))
    app.add_handler(CallbackQueryHandler(dice_callback, pattern=r"^dice_bet:"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin_"))

    # Reply-keyboard menu text router (must come after commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    app.add_error_handler(error_handler)

    logger.info("🎮 Bot शुरू हो रहा है...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
