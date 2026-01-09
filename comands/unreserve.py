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

class UnreserveItem(StatesGroup):
    waiting_for_id = State()

def load_items():
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_items(items):
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

@router.message(Command("unreserve"))
@router.message(F.text == "🔓 Снять бронь")
async def cmd_unreserve(message: Message, state: FSMContext):
    await message.answer(
        "🔓 *Снятие брони*\n\n"
        "Введите ID товара, с которого хотите снять бронь:",
        parse_mode="Markdown"
    )
    await state.set_state(UnreserveItem.waiting_for_id)

@router.message(UnreserveItem.waiting_for_id)
async def process_unreserve(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        item_id = int(message.text.strip())
        
        items = load_items()
        item_found = False
        
        for item in items:
            if item.get('id') == item_id:
                item_found = True
                if item.get('reserved_by') != user_id:
                    await message.answer("❌ Вы не можете снять бронь с чужого товара.")
                    break
                
                item['reserved_by'] = None
                save_items(items)
                await message.answer("✅ Бронь успешно снята!")
                break
        
        if not item_found:
            await message.answer("❌ Товар с таким ID не найден.")
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID (число).")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()