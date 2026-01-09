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

class DeleteItem(StatesGroup):
    waiting_for_id = State()

def load_items():
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_items(items):
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

@router.message(Command("delete"))
@router.message(F.text == "❌ Удалить товар")
async def cmd_delete(message: Message, state: FSMContext):
    await message.answer(
        "❌ *Удаление товара*\n\n"
        "Введите ID товара, который хотите удалить:\n"
        "(ID можно узнать через 'Мой список')",
        parse_mode="Markdown"
    )
    await state.set_state(DeleteItem.waiting_for_id)

@router.message(DeleteItem.waiting_for_id)
async def process_delete(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        item_id = int(message.text.strip())
        
        items = load_items()
        initial_count = len(items)
        
        # Удаляем товар только если он принадлежит пользователю
        items = [item for item in items if not (
            item.get('id') == item_id and item.get('owner_id') == user_id
        )]
        
        if len(items) < initial_count:
            save_items(items)
            await message.answer("✅ Товар успешно удалён!")
        else:
            await message.answer("❌ Товар не найден или не принадлежит вам.")
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный ID (число).")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()