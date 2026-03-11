import os

from aiogram import Bot

from dotenv import load_dotenv

load_dotenv()

async def send_message(post):
    bot = Bot(token=os.getenv("BOT_TOKEN"))

    msg = await bot.send_message(
        chat_id=int(os.getenv("CHAT_ID")),
        text=post
    )
    await bot.session.close()
    return msg.message_id


async def delete_message(message_id):
    bot = Bot(token=os.getenv("BOT_TOKEN"))

    await bot.delete_message(
        chat_id=int(os.getenv("CHAT_ID")),
        message_id=message_id,
    )
