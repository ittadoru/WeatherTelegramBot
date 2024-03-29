# Импорт библиотек
import asyncio

from config import BOT_TOKEN
from weatherApp.handlers import router, on_startup

from aiogram import Dispatcher, Bot

import logging


# Создание эксземпляров классов
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Главная функция компиляции всего бота
async def main():
    dp.include_router(router)
    await on_startup()
    await dp.start_polling(bot)


# Функция запуска
if __name__ == "__main__":
    try:
        # logging.basicConfig(level=logging.INFO) # Используется при разработке, может значительно снизить скорость
        asyncio.run(main())
    except KeyboardInterrupt:
        print("EXIT")
