from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from config import BOT_TOKEN
from database import add_user, get_user


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    add_user(
        user.id,
        user.username or "",
        user.first_name
    )

    text = f"""
🚩 *Jai Shree Ram* 🚩

🙏 Swagat hai *{user.first_name}*!

🕉️ Hindu Community Bot me aapka hardik swagat hai.

Available Commands:
/help
/profile

Sanatan Dharma ki Jai! 🚩
"""

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
"""
📖 Commands

/start
/help
/profile

🚩 Aur naye features jaldi aa rahe hain.
"""
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)

    if not user:
        await update.message.reply_text("Pehle /start karein.")
        return

    await update.message.reply_text(
f"""
👤 Profile

🪪 Name : {user[2]}
⭐ Level : {user[5]}
⚡ XP : {user[3]}
💰 Coins : {user[4]}
"""
    )


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("profile", profile))

print("🚩 Hindu Community Bot Started...")
app.run_polling()