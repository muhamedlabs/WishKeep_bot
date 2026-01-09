from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import json
from pathlib import Path
import re

router = Router()

DATA_DIR = Path("data")
ITEMS_FILE = DATA_DIR / "items.json"

def load_items():
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@router.message(Command("share"))
@router.message(F.text == "🔗 Поделиться списком")
async def cmd_share(message: Message):
    user_id = message.from_user.id
    share_command = f"/share_{user_id}"
    
    await message.answer(
        f"🔗 *Поделиться списком*\n\n"
        f"Передайте эту команду другому пользователю:\n\n"
        f"`{share_command}`\n\n"
        f"Он сможет увидеть ваш список товаров.",
        parse_mode="Markdown"
    )

# Способ 1: Используем F.text.startswith для перехвата команды
@router.message(F.text.startswith("/share_"))
async def cmd_view_shared(message: Message):
    try:
        # Извлекаем ID из команды
        text = message.text.strip()
        
        # Проверяем формат команды
        if not text.startswith("/share_"):
            return
        
        # Извлекаем ID
        owner_id_str = text[7:]  # Убираем "/share_"
        
        if not owner_id_str.isdigit():
            await message.answer("❌ Неверный формат команды. Используйте: /share_123456789")
            return
        
        owner_id = int(owner_id_str)
        
        # Загружаем товары
        items = load_items()
        user_items = [item for item in items if item.get('owner_id') == owner_id]
        
        if not user_items:
            await message.answer("📭 Список пользователя пуст или недоступен.")
            return
        
        # Формируем ответ
        response = "📋 *Список товаров пользователя:*\n\n"
        
        for item in user_items:
            item_id = item.get('id')
            name = item.get('name')
            link = item.get('link')
            reserved_by = item.get('reserved_by')
            
            if reserved_by:
                status = f"🔒 Забронирован"
            else:
                status = "✅ Свободен"
            
            response += f"*{item_id}.* {name}\n{link}\n{status}\n\n"
        
        response += "🔒 Чтобы забронировать товар, укажите его ID через команду /reserve"
        await message.answer(response, parse_mode="Markdown")
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Используйте: /share_123456789")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

# Способ 2: Добавляем команду /stats для проверки
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Показать статистику"""
    items = load_items()
    
    if not items:
        await message.answer("📊 В базе данных пока нет товаров.")
        return
    
    # Группируем по владельцам
    owners = {}
    for item in items:
        owner_id = item.get('owner_id')
        if owner_id not in owners:
            owners[owner_id] = 0
        owners[owner_id] += 1
    
    response = "📊 *Статистика товаров:*\n\n"
    for owner_id, count in owners.items():
        response += f"👤 Пользователь {owner_id}: {count} товаров\n"
        response += f"   Команда для просмотра: `/share_{owner_id}`\n\n"
    
    response += f"📦 Всего товаров: {len(items)}"
    await message.answer(response, parse_mode="Markdown")