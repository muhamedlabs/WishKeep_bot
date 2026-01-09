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

class ReserveItem(StatesGroup):
    waiting_for_id = State()

def load_items():
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_items(items):
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

@router.message(Command("reserve"))
@router.message(F.text == "🔒 Забронировать")
async def cmd_reserve(message: Message, state: FSMContext):
    await message.answer(
        "🔒 *Бронирование товара*\n\n"
        "Введите ID товара, который хотите забронировать:",
        parse_mode="Markdown"
    )
    await state.set_state(ReserveItem.waiting_for_id)

@router.message(ReserveItem.waiting_for_id)
async def process_reserve(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        item_id = int(message.text.strip())
        
        items = load_items()
        item_found = False
        
        for item in items:
            if item.get('id') == item_id:
                item_found = True
                if item.get('reserved_by'):
                    await message.answer("❌ Этот товар уже забронирован.")
                    break
                
                item['reserved_by'] = user_id
                save_items(items)
                await message.answer("✅ Вы успешно забронировали товар!")
                break
        
        if not item_found:
            await message.answer("❌ Товар с таким ID не найден.")
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID (число).")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()