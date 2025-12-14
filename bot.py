import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from database import Database

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 6851306933
OWNER_CHANNEL = "https://t.me/Lydkastarz"

db = Database()

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# ======================= FSM =======================
class AddChannel(StatesGroup):
    chat_id = State()
    url = State()
    btn_text = State()


# ======================= SUBSCRIPTION CHECK (OLD WORKING LOGIC) =======================
async def is_subscribed(user_id: int, chat_id: int) -> bool:
    """
    Проверка подписки — точная логика старого бота:
    - если Telegram выдаёт исключение → пользователь НЕ подписан
    - если исключения нет → пользователь подписан
    """
    try:
        member = await bot.get_chat_member(chat_id, user_id)

        # Если явно "left" — точно нет подписки
        if member.status == "left":
            return False

        # ВСЁ остальное — member, admin, creator → подписан
        return True

    except Exception as e:
        # В старом боте ошибка == НЕ подписан
        print(f"[SUB CHECK ERROR] user={user_id}, chat={chat_id} → {e}")
        return False


# ======================= FILE DELIVERY =======================
async def process_file_request(msg: Message, file_id: int):
    channels = db.get_channels()

    # Проверяем подписку на каждый канал
    for _, chat_id, url, btn_text in channels:
        subscribed = await is_subscribed(msg.from_user.id, int(chat_id))

        if not subscribed:
            kb = InlineKeyboardBuilder()

            for _, _, link, name in channels:
                kb.button(text=name, url=link)

            kb.button(
                text="Проверить подписку ✅",
                callback_data=f"checksub:{file_id}"
            )
            kb.adjust(1)

            return await msg.answer(
                "Чтобы получить файл — подпишись на каналы спонсоров:",
                reply_markup=kb.as_markup()
            )

    # Все подписки пройдены → выдаём файл
    file = db.get_file(file_id)
    if not file:
        return await msg.answer("Файл не найден.")

    file_tg, caption = file
    await msg.answer_document(file_tg, caption=caption)


# ======================= CALLBACK =======================
@dp.callback_query(F.data.startswith("checksub:"))
async def check_subscription(callback: CallbackQuery):
    file_id = int(callback.data.split(":")[1])
    await process_file_request(callback.message, file_id)


# ======================= START =======================
@dp.message(Command("start"))
async def start_cmd(msg: Message):
    args = msg.text.split()

    # Если пользователь пришёл по ссылке file123
    if len(args) > 1 and args[1].startswith("file"):
        return await process_file_request(msg, int(args[1].replace("file", "")))

    db.add_user(msg.from_user.id)
    await msg.answer(
        f"👋 Привет! Я храню файлы с канала <b>Мега</b>!\n\n"
        f"<a href='{OWNER_CHANNEL}'>Наш канал 🌟</a>"
    )


# ======================= ADMIN PANEL =======================
@dp.message(Command("admin"))
async def admin_panel(msg: Message):
    if msg.from_user.id != OWNER_ID and not db.is_admin(msg.from_user.id):
        return

    text = (
        "<b>👑 Админ-панель</b>\n\n"
        "<b>/addadmin user_id</b> — добавить админа\n"
        "<b>/remadmin user_id</b> — удалить админа\n"
        "<b>/addfile</b> — добавить файл ответом на файл\n"
        "<b>/list</b> — список файлов\n"
        "<b>/stats</b> — статистика\n"
        "<b>/addchannel</b> — добавить канал спонсора\n"
        "<b>/channels</b> — список каналов\n"
        "<b>/delchannel id</b> — удалить канал\n"
        "<code>file123</code> — получить файл вручную"
    )

    await msg.answer(text)


# ======================= ADD CHANNEL =======================
@dp.message(Command("addchannel"))
async def add_channel_start(msg: Message, state: FSMContext):
    if not db.is_admin(msg.from_user.id):
        return
    await msg.answer("Введите chat_id канала (-100xxxxxxxxxx):")
    await state.set_state(AddChannel.chat_id)


@dp.message(AddChannel.chat_id)
async def step1(msg: Message, state: FSMContext):
    await state.update_data(chat_id=msg.text)
    await msg.answer("Теперь отправьте ссылку на канал:")
    await state.set_state(AddChannel.url)


@dp.message(AddChannel.url)
async def step2(msg: Message, state: FSMContext):
    await state.update_data(url=msg.text)
    await msg.answer("Введите текст кнопки:")
    await state.set_state(AddChannel.btn_text)


@dp.message(AddChannel.btn_text)
async def step3(msg: Message, state: FSMContext):
    data = await state.get_data()
    db.add_channel(data["chat_id"], data["url"], msg.text)
    await msg.answer("Канал добавлен! 🎉")
    await state.clear()


# ======================= DELETE CHANNEL =======================
@dp.message(Command("delchannel"))
async def delete_channel(msg: Message):
    if not db.is_admin(msg.from_user.id):
        return

    parts = msg.text.split()
    if len(parts) != 2:
        return await msg.answer("Использование: /delchannel <id>")

    db.del_channel(int(parts[1]))
    await msg.answer("Канал удалён! ❌")


# ======================= LIST CHANNELS =======================
@dp.message(Command("channels"))
async def list_channels(msg: Message):
    if not db.is_admin(msg.from_user.id):
        return

    channels = db.get_channels()
    if not channels:
        return await msg.answer("Каналов нет.")

    txt = "<b>📡 Каналы-спонсоры:</b>\n\n"
    for cid, chat_id, url, name in channels:
        txt += (
            f"<b>ID записи:</b> {cid}\n"
            f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
            f"<b>URL:</b> {url}\n"
            f"<b>Название кнопки:</b> {name}\n\n"
        )

    await msg.answer(txt)


# ======================= ADD FILE =======================
@dp.message(Command("addfile"))
async def add_file(msg: Message):
    if not db.is_admin(msg.from_user.id):
        return

    if not msg.reply_to_message:
        return await msg.answer("Используй команду ответом на файл.")

    rep = msg.reply_to_message

    if rep.document:
        media = rep.document
    elif rep.video:
        media = rep.video
    elif rep.photo:
        media = rep.photo[-1]
    else:
        return await msg.answer("Это не файл!")

    new_id = db.add_file(media.file_id, rep.caption or "Без названия")
    bot_username = (await bot.get_me()).username

    link = f"https://t.me/{bot_username}?start=file{new_id}"

    await msg.answer(f"Файл добавлен!\nID: {new_id}\n🔗 {link}")


# ======================= ADMIN CONTROL =======================
@dp.message(Command("addadmin"))
async def add_admin(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return

    parts = msg.text.split()
    if len(parts) == 2 and parts[1].isdigit():
        db.add_admin(int(parts[1]))
        return await msg.answer("Админ добавлен!")

    if msg.reply_to_message:
        db.add_admin(msg.reply_to_message.from_user.id)
        return await msg.answer("Админ добавлен!")

    await msg.answer("Использование: /addadmin user_id")


@dp.message(Command("remadmin"))
async def rem_admin(msg: Message):
    if msg.from_user.id != OWNER_ID:
        return

    parts = msg.text.split()
    if len(parts) == 2 and parts[1].isdigit():
        db.remove_admin(int(parts[1]))
        return await msg.answer("Админ удалён!")

    if msg.reply_to_message:
        db.remove_admin(msg.reply_to_message.from_user.id)
        return await msg.answer("Админ удалён!")

    await msg.answer("Использование: /remadmin user_id")


# ======================= LIST FILES =======================
@dp.message(Command("list"))
async def list_files(msg: Message):
    if not db.is_admin(msg.from_user.id):
        return

    files = db.list_files()
    if not files:
        return await msg.answer("Файлов нет.")

    txt = "<b>📁 Файлы:</b>\n\n"
    for fid, caption in files:
        txt += f"ID {fid}: {caption}\n"

    await msg.answer(txt)


# ======================= STATS =======================
@dp.message(Command("stats"))
async def stats(msg: Message):
    if not db.is_admin(msg.from_user.id):
        return
    await msg.answer(f"📊 Пользователей: {db.users_count()}")


# ======================= MANUAL FILE GET =======================
@dp.message(F.text.regexp(r"^file(\d+)$"))
async def manual_file(msg: Message):
    file_id = int(msg.text.replace("file", ""))
    file = db.get_file(file_id)

    if not file:
        return await msg.answer("Файл не найден.")

    file_tg, caption = file
    await msg.answer_document(file_tg, caption=caption)


# ======================= RUN =======================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
