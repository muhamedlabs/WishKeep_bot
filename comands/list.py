from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import json
from pathlib import Path

router = Router()

DATA_DIR = Path("data")
ITEMS_FILE = DATA_DIR / "items.json"

def load_items():
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@router.message(Command("list"))
@router.message(F.text == "📋 Мой список")
async def cmd_list(message: Message):
    user_id = message.from_user.id
    items = load_items()
    user_items = [item for item in items if item.get('owner_id') == user_id]
    
    if not user_items:
        await message.answer("📭 Ваш список товаров пока пуст.")
        return
    
    response = "📋 *Ваш список товаров:*\n\n"
    
    for item in user_items:
        item_id = item.get('id')
        name = item.get('name')
        link = item.get('link')
        reserved_by = item.get('reserved_by')
        
        if reserved_by:
            status = f"🔒 Забронирован (пользователем {reserved_by})"
        else:
            status = "✅ Свободен"
        
        response += f"*{item_id}.* {name}\n{link}\n{status}\n\n"
    
    response += "🔗 Чтобы поделиться списком, нажмите 'Поделиться списком'"
    await message.answer(response, parse_mode="Markdown")