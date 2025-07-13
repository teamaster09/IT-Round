import aiofiles
from aiofiles import os as aios
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from alembic import command
from alembic.config import Config

from handlers import router
from config import TELEGRAM_BOT_TOKEN
import asyncio


async def main():
    if not await aios.path.exists('events.db'):
        # Создаем файл БД и применяем миграции
        async with aiofiles.open('events.db', 'w'):
            pass

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("База данных создана и миграции применены")

    # 1. Настройка хранилища для FSM
    storage = MemoryStorage()

    # 2. Настройка параметров бота
    default = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token="8023486762:AAHTpSdWmiJYojGggafA31l2x15vQBt3680", default=default)

    # 3. Инициализация шедулера  <-- ДОБАВЛЯЕМ ЗДЕСЬ
    from reminders import setup_scheduler
    setup_scheduler(bot)  # Передаём ЭКЗЕМПЛЯР бота, а не класс

    # 4. Создаём диспетчер
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    # 5. Запуск бота
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())