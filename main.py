import asyncio
import json
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from BANNED_FILES.config import telegram_bot

# Создаем папку data если ее нет
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
ITEMS_FILE = DATA_DIR / "items.json"

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=telegram_bot)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Импорт команд из папки comands
    from comands.menu import router as menu_router
    from comands.add import router as add_router
    from comands.list import router as list_router
    from comands.share import router as share_router
    from comands.delete import router as delete_router
    from comands.reserve import router as reserve_router
    from comands.unreserve import router as unreserve_router
    
    # Регистрация всех роутеров
    dp.include_router(menu_router)
    dp.include_router(add_router)
    dp.include_router(list_router)
    dp.include_router(share_router)
    dp.include_router(delete_router)
    dp.include_router(reserve_router)
    dp.include_router(unreserve_router)
    
    print("Бот запущен и готов к работе!")
    print("Данные хранятся в папке data/")
    print("Бот находится в процессе разработки")
    
    # Создаем JSON файлы если их нет
    if not USERS_FILE.exists():
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        print("Создан файл users.json")
    
    if not ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print("Создан файл items.json")
    
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())