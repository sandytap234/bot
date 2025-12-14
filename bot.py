import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = "8306901903:AAEvWnCMfvzXHUsf_5gZ0ZVs-pdZLQM2LRs"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("Бот работает на Render 🚀")

if __name__ == "__main__":
    executor.start_polling(dp)
