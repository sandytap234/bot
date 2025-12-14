import os
from aiogram import Bot, Dispatcher, executor, types

BOT_TOKEN = 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("Бот работает на Render 🚀")

if __name__ == "__main__":
    executor.start_polling(dp)
