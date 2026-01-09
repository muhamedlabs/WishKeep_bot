from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json
from pathlib import Path

router = Router()

DATA_DIR = Path("data")
ITEMS_FILE = DATA_DIR / "items.json"

class AddItems(StatesGroup):
    waiting_for_items = State()

def load_items():
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_items(items):
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def get_next_item_id():
    items = load_items()
    if not items:
        return 1
    return max(item.get('id', 0) for item in items) + 1

@router.message(Command("add"))
@router.message(F.text == "📝 Добавить товары")
async def cmd_add(message: Message, state: FSMContext):
    await message.answer(
        "📝 *Добавление товаров*\n\n"
        "Введите товары в формате:\n"
        "`Название - Ссылка`\n\n"
        "Пример:\n"
        "`Телефон - https://example.com/phone`\n\n"
        "Можно ввести несколько товаров, каждый с новой строки.",
        parse_mode="Markdown"
    )
    await state.set_state(AddItems.waiting_for_items)

@router.message(AddItems.waiting_for_items)
async def process_items(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    lines = text.split('\n')
    
    success_count = 0
    fail_count = 0
    added_items = []
    
    items = load_items()
    
    for line in lines:
        try:
            if ' - ' not in line:
                raise ValueError("Ошибка в формате")
            
            name, link = line.split(' - ', 1)
            name = name.strip()
            link = link.strip()
            
            if not name or not link:
                raise ValueError("Пустые поля")
            
            item_id = get_next_item_id() + success_count + fail_count
            
            item = {
                'id': item_id,
                'name': name,
                'link': link,
                'reserved_by': None,
                'owner_id': user_id
            }
            
            items.append(item)
            added_items.append((item_id, name))
            success_count += 1
        except Exception:
            fail_count += 1
    
    save_items(items)
    
    response = f"✅ *Групповое добавление завершено*\n\n"
    response += f"✅ Успешно: {success_count}\n"
    
    if added_items:
        response += "Добавленные товары:\n"
        for item_id, name in added_items[-5:]:
            response += f"  • {name} (ID: {item_id})\n"
    
    if fail_count > 0:
        response += f"\n❌ Ошибок: {fail_count}\n"
        response += "Проверьте формат ввода:\n`Название - Ссылка`"
    
    await message.answer(response, parse_mode="Markdown")
    await state.clear()