import os
from datetime import datetime
from telegram import Bot

from dotenv import load_dotenv

load_dotenv()

telegram_bot = Bot(token=os.getenv("TELEGRAM_API_KEY"))


def _format_message(user_input: str, ia_output: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"🧠 *IA Interaction*\n"
        f"🕒 *Time*: `{timestamp}`\n\n"
        f"👤 *Input*:\n`{user_input}`\n\n"
        f"🤖 *Output*:\n`{ia_output}`"
    )


async def log_to_telegram(user_input: str, ia_output: str):
    try:
        message = _format_message(user_input, ia_output)
        await telegram_bot.send_message(
            chat_id=os.getenv("TELEGRAM_CHAT_ID"), text=message, parse_mode="Markdown"
        )
    except Exception as e:
        print(f"[Telegram Log Error] {e}")
