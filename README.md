# 🎮 RPG Warrior Arena — Telegram Bot

एक पूरा RPG-style Telegram game bot: Fight, PvP, Weapons/Armor, Shop, Clans, Daily Missions,
Lucky Spin, Dice Game, Leaderboard, Achievements, Referral System, और Admin Panel — सब SQLite
पर आधारित।

## 📂 Files
```
config.py        → Bot token, admin IDs, game balance settings
game_data.py      → Weapons, Armor, Enemies, Missions, Achievements, Spin rewards की list
database.py       → SQLite database की सारी functions
game_logic.py     → Fight (PvE/PvP) simulation logic
achievements.py   → Achievement unlock checking
keyboards.py      → सारे Reply/Inline keyboards
main.py           → Bot entry point (सारे handlers यहीं हैं)
requirements.txt  → Python dependencies
```

## 🚀 Setup (Step by Step)

### 1. Bot Token लें
1. Telegram पर [@BotFather](https://t.me/BotFather) खोलें
2. `/newbot` भेजें और नाम/username दें
3. जो token मिले उसे कॉपी करें

### 2. अपनी Admin ID पता करें
[@userinfobot](https://t.me/userinfobot) को message करें, वो आपकी numeric user ID बता देगा।

### 3. Config भरें
`config.py` खोलें और भरें:
```python
BOT_TOKEN = "यहाँ अपना token डालें"
ADMIN_IDS = [आपकी_user_id]
```

### 4. Dependencies Install करें
```bash
pip install -r requirements.txt
```

### 5. Bot चलाएं
```bash
python main.py
```

बस! Bot अब चालू है। Telegram पर अपने bot को `/start` भेजें।

## 🎮 Features

| Feature | कैसे इस्तेमाल करें |
|---|---|
| 🚩 Welcome | `/start` |
| 👤 Profile | मेनू बटन या `/profile` |
| ⚔️ PvE Fight | मेनू बटन या `/fight` — random दुश्मन से लड़ाई |
| 🥊 PvP Fight | Group में किसी की message पर reply करके `/duel` |
| 🎒 Inventory | अपने weapons/armor देखें |
| 💎 Shop | नए weapons/armor खरीदें और equip करें |
| 🎁 Daily Reward | रोज़ाना 24 घंटे में एक बार मुफ़्त coins+xp |
| 🎯 Daily Missions | रोज़ 3 random missions, पूरा करने पर इनाम claim करें |
| 🏆 Leaderboard | टॉप 10 players (Level के आधार पर) |
| 👥 Clan System | Clan बनाएं (1000 coins), join करें, clan leaderboard देखें |
| 🎰 Lucky Spin | रोज़ाना एक free spin — coins/xp/energy/jackpot |
| 🎲 Dice Game | Coins bet लगाकर bot के खिलाफ dice खेलें |
| 🎖️ Achievements | Milestones पूरे करने पर auto-unlock होते हैं |
| 💰 Referral | `/help` से referral link लें, दोस्त join करे तो दोनों को इनाम |
| 👑 Admin Panel | सिर्फ ADMIN_IDS के लिए — `/admin` |
| 📢 Broadcast | `/broadcast आपका message` — सभी users को भेजें |
| 💰 Give Coins | `/givecoins USER_ID AMOUNT` |
| 🚫 Ban/Unban | `/ban USER_ID` / `/unban USER_ID` |

## ⚙️ Customize करना चाहें तो

- **नए Weapons/Armor जोड़ने** के लिए `game_data.py` में `WEAPONS` / `ARMORS` dict में entry डालें।
- **नए Enemies** जोड़ने के लिए `game_data.py` की `ENEMIES` list में जोड़ें।
- **Game balance** (energy cost, daily reward amount, आदि) बदलने के लिए `config.py` देखें।
- **नए Missions/Achievements** `game_data.py` में जोड़ सकते हैं (achievements के लिए
  `achievements.py` में unlock-condition भी जोड़नी होगी)।

## 📝 Notes

- Database अपने आप `game_bot.db` नाम की SQLite file में बन जाता है, कोई extra setup नहीं चाहिए।
- Bot को हमेशा चालू रखने के लिए किसी VPS/server (जैसे Railway, Render, या अपना Linux server) पर
  `python main.py` को PM2 / systemd / screen से चलाएं।
- PvP के लिए दोनों players को पहले बॉट में `/start` करना ज़रूरी है (ताकि bot उन्हें DM कर सके)।
