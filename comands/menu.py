from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json
from pathlib import Path
import os

router = Router()

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
ITEMS_FILE = DATA_DIR / "items.json"
IMAGE_PATH = Path("pigs/Sakura.png")  # Путь к картинке

# ============ СОСТОЯНИЯ ДЛЯ РАЗНЫХ КОМАНД ============
class AddItems(StatesGroup):
    waiting_for_items = State()

class DeleteItem(StatesGroup):
    waiting_for_id = State()

class ReserveItem(StatesGroup):
    waiting_for_id = State()

class UnreserveItem(StatesGroup):
    waiting_for_id = State()

# ============ ОБЫЧНОЕ МЕНЮ (кнопки внизу) ============
def get_main_menu():
    """Создает главное меню внизу экрана"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Добавить"), KeyboardButton(text="📋 Мой список")],
            [KeyboardButton(text="🔗 Поделиться"), KeyboardButton(text="❌ Удалить")],
            [KeyboardButton(text="🔒 Бронь"), KeyboardButton(text="🔓 Снять бронь")],
            [KeyboardButton(text="ℹ️ Помощь"), KeyboardButton(text="📊 Статистика")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# ============ ИНЛАЙН МЕНЮ (кнопки в сообщении) ============
def get_inline_menu():
    """Создает инлайн меню внутри сообщения"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Добавить товары", callback_data="add_items"),
                InlineKeyboardButton(text="📋 Мой список", callback_data="my_list")
            ],
            [
                InlineKeyboardButton(text="🔗 Поделиться списком", callback_data="share_list"),
                InlineKeyboardButton(text="❌ Удалить товар", callback_data="delete_item")
            ],
            [
                InlineKeyboardButton(text="🔒 Забронировать товар", callback_data="reserve_item"),
                InlineKeyboardButton(text="🔓 Снять бронь", callback_data="unreserve_item")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton(text="🔄 Обновить меню", callback_data="refresh_menu"),
                InlineKeyboardButton(text="⚙️ О боте", callback_data="about")
            ]
        ]
    )
    return keyboard

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ JSON ============
def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_items():
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_items(items):
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def get_user_items(user_id):
    items = load_items()
    return [item for item in items if item.get('owner_id') == user_id]

def get_next_item_id():
    items = load_items()
    if not items:
        return 1
    return max(item.get('id', 0) for item in items) + 1

def get_item(item_id):
    items = load_items()
    for item in items:
        if item.get('id') == item_id:
            return item
    return None

def get_total_users():
    users = load_users()
    return len(users)

# ============ КОМАНДА START С КАРТИНКОЙ ============
@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Загружаем или создаем запись пользователя
    users = load_users()
    user_str = str(user_id)
    
    if user_str not in users:
        users[user_str] = {
            'username': username or f"user_{user_id}",
            'full_name': full_name,
            'items_count': 0,
            'join_date': message.date.strftime("%d.%m.%Y %H:%M")
        }
        save_users(users)
        new_user = True
    else:
        # Обновляем имя если изменилось
        users[user_str]['full_name'] = full_name
        if username:
            users[user_str]['username'] = username
        save_users(users)
        new_user = False
    
    # Получаем статистику
    user_items = get_user_items(user_id)
    all_items = load_items()
    total_items = len(all_items)
    total_users = get_total_users()
    
    # Текст приветствия
    welcome_text = (
        "🎉 *Добро пожаловать в бот для управления товарами!*\n\n"
        
        "✨ *Что это за бот?*\n"
        "Это бот для создания и управления списками товаров с возможностью "
        "делиться ими с друзьями и бронировать товары из чужих списков.\n\n"
        
        "🛠️ *Возможности:*\n"
        "• 📝 Добавлять товары со ссылками\n"
        "• 📋 Вести свой список товаров\n"
        "• 🔗 Делиться списком с друзьями\n"
        "• 🔒 Бронировать товары других пользователей\n"
        "• ❌ Удалять и редактировать свои товары\n\n"
        
        "📊 *Статистика:*\n"
        f"👤 Ваших товаров: *{len(user_items)}*\n"
        f"📦 Всего товаров в системе: *{total_items}*\n"
        f"👥 Пользователей в боте: *{total_users}*\n\n"
        
        "⚠️ *Внимание!*\n"
        "🚧 Бот находится в процессе активной разработки!\n"
        "Функции могут добавляться и изменяться.\n\n"
        
        "👇 *Выберите действие из меню ниже*\n"
        "Или нажмите ℹ️ Помощь для подробной информации"
    )
    
    # Приветствие для нового пользователя
    if new_user:
        welcome_text = (
            "🎊 *Добро пожаловать в наш бот!*\n\n"
            "Мы рады приветствовать нового пользователя!\n\n"
        ) + welcome_text
    
    # Пробуем отправить с картинкой
    try:
        if IMAGE_PATH.exists():
            # Проверяем размер картинки
            file_size = os.path.getsize(IMAGE_PATH)
            if file_size < 10 * 1024 * 1024:  # 10 MB лимит
                photo = FSInputFile(IMAGE_PATH)
                await message.answer_photo(
                    photo=photo,
                    caption=welcome_text,
                    parse_mode="Markdown",
                    reply_markup=get_inline_menu()
                )
            else:
                # Картинка слишком большая, отправляем без нее
                await message.answer(
                    "🖼️ *Картинка приветствия*\n\n" + welcome_text,
                    parse_mode="Markdown",
                    reply_markup=get_inline_menu()
                )
                await message.answer(
                    "⚠️ Картинка приветствия слишком большая для отправки.\n"
                    "Максимальный размер: 10 MB",
                    parse_mode="Markdown"
                )
        else:
            # Картинки нет, отправляем только текст
            await message.answer(
                welcome_text,
                parse_mode="Markdown",
                reply_markup=get_inline_menu()
            )
            print(f"⚠️ Картинка не найдена по пути: {IMAGE_PATH}")
    except Exception as e:
        # Если ошибка при отправке с картинкой
        print(f"⚠️ Ошибка при отправке картинки: {e}")
        await message.answer(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=get_inline_menu()
        )
    
    # Отправляем обычное меню отдельным сообщением
    await message.answer(
        "💡 *Быстрый доступ через кнопки внизу:*",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

# ============ ОБРАБОТКА ИНЛАЙН КНОПОК ============
@router.callback_query(F.data == "add_items")
async def inline_add_items(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 *Добавление товаров*\n\n"
        "Введите товары в формате:\n"
        "`Название - Ссылка`\n\n"
        "Пример:\n"
        "`Телефон - https://example.com/phone`\n\n"
        "📌 Можно ввести несколько товаров, каждый с новой строки.\n\n"
        "🚧 *Примечание:* Функция в разработке, возможны улучшения.",
        parse_mode="Markdown"
    )
    await state.set_state(AddItems.waiting_for_items)
    await callback.answer()

@router.callback_query(F.data == "my_list")
async def inline_my_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    items = get_user_items(user_id)
    
    if not items:
        await callback.message.answer(
            "📭 *Ваш список товаров пока пуст.*\n\n"
            "Добавьте первый товар через кнопку '📝 Добавить товары'!",
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    response = "📋 *Ваш список товаров:*\n\n"
    
    for item in items:
        item_id = item.get('id')
        name = item.get('name')
        link = item.get('link')
        reserved_by = item.get('reserved_by')
        
        if reserved_by:
            status = f"🔒 Забронирован (ID пользователя: {reserved_by})"
        else:
            status = "✅ Свободен"
        
        response += f"*{item_id}.* {name}\n{link}\n{status}\n\n"
    
    response += "🔗 Чтобы поделиться этим списком, нажмите '🔗 Поделиться списком'"
    await callback.message.answer(response, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "share_list")
async def inline_share_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    share_command = f"/share_{user_id}"
    
    # Проверяем есть ли товары
    items = get_user_items(user_id)
    
    if not items:
        await callback.message.answer(
            "📭 *Нечего делиться!*\n\n"
            "Ваш список товаров пуст. Сначала добавьте товары через '📝 Добавить товары'.",
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    await callback.message.answer(
        f"🔗 *Поделиться списком*\n\n"
        f"У вас {len(items)} товаров.\n\n"
        f"Передайте эту команду другому пользователю:\n\n"
        f"`{share_command}`\n\n"
        f"Он сможет увидеть ваш список товаров и забронировать то, что понравится!\n\n"
        f"🚧 *Примечание:* Функция шеринга в процессе улучшения.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "delete_item")
async def inline_delete_item(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "❌ *Удаление товара*\n\n"
        "Введите ID товара, который хотите удалить:\n\n"
        "ℹ️ *ID можно узнать через '📋 Мой список'*\n\n"
        "🚧 *Примечание:* Функция в разработке.",
        parse_mode="Markdown"
    )
    await state.set_state(DeleteItem.waiting_for_id)
    await callback.answer()

@router.callback_query(F.data == "reserve_item")
async def inline_reserve_item(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔒 *Бронирование товара*\n\n"
        "Введите ID товара, который хотите забронировать:\n\n"
        "ℹ️ *Чтобы получить ID товара, попросите у друга команду для просмотра его списка*\n\n"
        "🚧 *Примечание:* Система бронирования в активной разработке.",
        parse_mode="Markdown"
    )
    await state.set_state(ReserveItem.waiting_for_id)
    await callback.answer()

@router.callback_query(F.data == "unreserve_item")
async def inline_unreserve_item(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🔓 *Снятие брони*\n\n"
        "Введите ID товара, с которого хотите снять бронь:\n\n"
        "ℹ️ *Можно снять бронь только со своих забронированных товаров*\n\n"
        "🚧 *Примечание:* Функция в разработке.",
        parse_mode="Markdown"
    )
    await state.set_state(UnreserveItem.waiting_for_id)
    await callback.answer()

@router.callback_query(F.data == "help")
async def inline_help(callback: CallbackQuery):
    help_text = (
        "📚 *Справка по боту*\n\n"
        
        "🎯 *Основные возможности:*\n"
        "• 📝 Добавлять товары со ссылками\n"
        "• 📋 Вести свой список товаров\n"
        "• 🔗 Делиться списком с друзьями\n"
        "• 🔒 Бронировать товары других пользователей\n"
        "• ❌ Удалять свои товары\n\n"
        
        "⚡ *Быстрые команды:*\n"
        "`/add` - добавить товары\n"
        "`/list` - мой список\n"
        "`/share` - поделиться\n"
        "`/delete` - удалить товар\n"
        "`/reserve` - забронировать\n"
        "`/unreserve` - снять бронь\n"
        "`/stats` - статистика\n"
        "`/menu` - показать меню\n"
        "`/help` - эта справка\n\n"
        
        "🔍 *Как это работает:*\n"
        "1. Добавьте товары через '📝 Добавить товары'\n"
        "2. Поделитесь списком через '🔗 Поделиться списком'\n"
        "3. Другой пользователь сможет посмотреть ваш список\n"
        "4. Он может забронировать понравившийся товар\n\n"
        
        "⚠️ *Важная информация:*\n"
        "🚧 Бот находится в процессе разработки!\n"
        "Функции могут меняться и улучшаться.\n"
        "Сообщайте об ошибках разработчику.\n\n"
        
        "💡 *Советы:*\n"
        "• Используйте инлайн-меню для удобства\n"
        "• ID товара можно узнать в 'Мой список'\n"
        "• Для бронирования нужен ID товара другого пользователя"
    )
    await callback.message.answer(help_text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "stats")
async def inline_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_items = get_user_items(user_id)
    all_items = load_items()
    users = load_users()
    
    # Считаем статистику
    reserved_count = sum(1 for item in user_items if item.get('reserved_by'))
    total_reserved = sum(1 for item in all_items if item.get('reserved_by'))
    
    stats_text = (
        "📊 *Статистика бота*\n\n"
        
        "👤 *Ваша статистика:*\n"
        f"• Ваших товаров: *{len(user_items)}*\n"
        f"• Забронировано ваших товаров: *{reserved_count}*\n"
        f"• Свободных ваших товаров: *{len(user_items) - reserved_count}*\n\n"
        
        "🌐 *Общая статистика:*\n"
        f"• Всего товаров в системе: *{len(all_items)}*\n"
        f"• Всего пользователей: *{len(users)}*\n"
        f"• Всего забронированных товаров: *{total_reserved}*\n\n"
        
        "📈 *Активность:*\n"
    )
    
    if user_items:
        # Находим самый старый и новый товар
        if len(all_items) > 0:
            oldest = min(all_items, key=lambda x: x.get('id', 0))
            newest = max(all_items, key=lambda x: x.get('id', 0))
            stats_text += f"• Первый товар добавлен: ID {oldest.get('id')}\n"
            stats_text += f"• Последний товар добавлен: ID {newest.get('id')}\n"
    else:
        stats_text += "У вас пока нет товаров. Добавьте первый! 📝\n"
    
    stats_text += "\n🚧 *Статистика в разработке, будут новые метрики*"
    
    await callback.message.answer(stats_text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "about")
async def inline_about(callback: CallbackQuery):
    about_text = (
        "🤖 *Информация о боте*\n\n"
        
        "📱 *Название:* WishKeep Bot\n"
        "🎯 *Цель:* Управление списками товаров\n"
        "👨‍💻 *Статус:* В активной разработке\n\n"
        
        "📅 *История версий:*\n"
        "• v0.1 - Базовая функциональность\n"
        "• v0.2 - Добавлено бронирование\n"
        "• v0.3 - Система шеринга\n"
        "• v0.4 - JSON хранилище\n"
        "• v0.5 - Инлайн меню\n\n"
        
        "🛠️ *Технологии:*\n"
        "• Python 3.11+\n"
        "• Aiogram 3.x\n"
        "• JSON для хранения данных\n"
        "• FSM для многошаговых операций\n\n"
        
        "🚀 *Планы на будущее:*\n"
        "• Уведомления о бронировании\n"
        "• Категории товаров\n"
        "• Поиск по товарам\n"
        "• Рейтинги и отзывы\n"
        "• Веб-интерфейс\n\n"
        
        "⚠️ *Важно знать:*\n"
        "Бот находится в стадии активной разработки!\n"
        "Некоторые функции могут работать нестабильно.\n"
        "Данные могут сбрасываться при обновлениях.\n\n"
        
        "📞 *Обратная связь:*\n"
        "Сообщайте об ошибках и предложениях разработчику."
    )
    await callback.message.answer(about_text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "refresh_menu")
async def inline_refresh_menu(callback: CallbackQuery):
    await callback.message.edit_reply_markup(
        reply_markup=get_inline_menu()
    )
    await callback.answer("✅ Меню обновлено!")

# ============ ОБРАБОТКА ОБЫЧНЫХ КНОПОК ============
@router.message(F.text == "📝 Добавить")
async def button_add(message: Message, state: FSMContext):
    await message.answer(
        "📝 *Добавление товаров*\n\n"
        "Введите товары в формате:\n"
        "`Название - Ссылка`\n\n"
        "Пример:\n"
        "`Телефон - https://example.com/phone`\n\n"
        "📌 Можно ввести несколько товаров, каждый с новой строки.\n\n"
        "🚧 *Примечание:* Функция в разработке.",
        parse_mode="Markdown"
    )
    await state.set_state(AddItems.waiting_for_items)

@router.message(F.text == "📋 Мой список")
async def button_list(message: Message):
    user_id = message.from_user.id
    items = get_user_items(user_id)
    
    if not items:
        await message.answer(
            "📭 *Ваш список товаров пока пуст.*\n\n"
            "Добавьте первый товар через кнопку '📝 Добавить'!",
            parse_mode="Markdown"
        )
        return
    
    response = "📋 *Ваш список товаров:*\n\n"
    
    for item in items:
        item_id = item.get('id')
        name = item.get('name')
        link = item.get('link')
        reserved_by = item.get('reserved_by')
        
        if reserved_by:
            status = f"🔒 Забронирован (ID: {reserved_by})"
        else:
            status = "✅ Свободен"
        
        response += f"*{item_id}.* {name}\n{link}\n{status}\n\n"
    
    response += "🔗 Чтобы поделиться списком, нажмите '🔗 Поделиться'"
    await message.answer(response, parse_mode="Markdown")

@router.message(F.text == "🔗 Поделиться")
async def button_share(message: Message):
    user_id = message.from_user.id
    share_command = f"/share_{user_id}"
    
    # Проверяем есть ли товары
    items = get_user_items(user_id)
    
    if not items:
        await message.answer(
            "📭 *Нечего делиться!*\n\n"
            "Ваш список товаров пуст. Сначала добавьте товары.",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        f"🔗 *Поделиться списком*\n\n"
        f"У вас {len(items)} товаров.\n\n"
        f"Передайте эту команду другому пользователю:\n\n"
        f"`{share_command}`\n\n"
        f"🚧 *Система шеринга в разработке*",
        parse_mode="Markdown"
    )

@router.message(F.text == "❌ Удалить")
async def button_delete(message: Message, state: FSMContext):
    await message.answer(
        "❌ *Удаление товара*\n\n"
        "Введите ID товара, который хотите удалить:\n"
        "(ID можно узнать через '📋 Мой список')\n\n"
        "🚧 *Функция в разработке*",
        parse_mode="Markdown"
    )
    await state.set_state(DeleteItem.waiting_for_id)

@router.message(F.text == "🔒 Бронь")
async def button_reserve(message: Message, state: FSMContext):
    await message.answer(
        "🔒 *Бронирование товара*\n\n"
        "Введите ID товара, который хотите забронировать:\n\n"
        "🚧 *Система бронирования в активной разработке*",
        parse_mode="Markdown"
    )
    await state.set_state(ReserveItem.waiting_for_id)

@router.message(F.text == "🔓 Снять бронь")
async def button_unreserve(message: Message, state: FSMContext):
    await message.answer(
        "🔓 *Снятие брони*\n\n"
        "Введите ID товара, с которого хотите снять бронь:\n\n"
        "🚧 *Функция в разработке*",
        parse_mode="Markdown"
    )
    await state.set_state(UnreserveItem.waiting_for_id)

@router.message(F.text == "ℹ️ Помощь")
async def button_help(message: Message):
    help_text = (
        "📚 *Справка по боту*\n\n"
        
        "🎯 *Основные кнопки:*\n"
        "`📝 Добавить` - добавить товары\n"
        "`📋 Мой список` - просмотреть свои товары\n"
        "`🔗 Поделиться` - поделиться своим списком\n"
        "`❌ Удалить` - удалить товар по ID\n"
        "`🔒 Бронь` - забронировать товар\n"
        "`🔓 Снять бронь` - отменить бронирование\n"
        "`📊 Статистика` - общая статистика\n\n"
        
        "⚠️ *Внимание!*\n"
        "🚧 Бот находится в процессе разработки!\n"
        "Некоторые функции могут работать нестабильно.\n\n"
        
        "💡 *Подсказки:*\n"
        "• Используйте инлайн-меню (/menu) для удобства\n"
        "• Все данные хранятся в JSON файлах\n"
        "• Сообщайте об ошибках разработчику"
    )
    await message.answer(help_text, parse_mode="Markdown")

@router.message(F.text == "📊 Статистика")
async def button_stats(message: Message):
    user_id = message.from_user.id
    user_items = get_user_items(user_id)
    all_items = load_items()
    users = load_users()
    
    # Считаем топ пользователей
    users_items = {}
    for item in all_items:
        owner_id = item.get('owner_id')
        if owner_id not in users_items:
            users_items[owner_id] = 0
        users_items[owner_id] += 1
    
    stats_text = (
        "📊 *Общая статистика бота*\n\n"
        
        f"👤 Всего пользователей: *{len(users)}*\n"
        f"📦 Всего товаров: *{len(all_items)}*\n"
        f"🎯 Ваших товаров: *{len(user_items)}*\n\n"
        
        "🏆 *Топ пользователей по количеству товаров:*\n"
    )
    
    if users_items:
        sorted_users = sorted(users_items.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for i, (owner_id, count) in enumerate(sorted_users, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🎖️"
            if owner_id == user_id:
                stats_text += f"{emoji} 👑 ВЫ: {count} товаров\n"
            else:
                stats_text += f"{emoji} Пользователь {owner_id}: {count} товаров\n"
    else:
        stats_text += "Пока нет данных о пользователях\n"
    
    stats_text += "\n🚧 *Статистика собирается в тестовом режиме*"
    
    await message.answer(stats_text, parse_mode="Markdown")

# ============ ОБРАБОТКА СОСТОЯНИЙ (FSM) ============
@router.message(AddItems.waiting_for_items)
async def process_add_items(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    lines = text.split('\n')
    
    success_count = 0
    fail_count = 0
    added_items = []
    
    items = load_items()
    next_id = get_next_item_id()
    
    for line in lines:
        try:
            if ' - ' not in line:
                raise ValueError("Неверный формат")
            
            name, link = line.split(' - ', 1)
            name = name.strip()
            link = link.strip()
            
            if not name or not link:
                raise ValueError("Пустые поля")
            
            # Проверяем ссылку
            if not link.startswith(('http://', 'https://')):
                link = 'https://' + link
            
            item = {
                'id': next_id,
                'name': name,
                'link': link,
                'reserved_by': None,
                'owner_id': user_id,
                'added_date': message.date.strftime("%d.%m.%Y %H:%M")
            }
            
            items.append(item)
            added_items.append((next_id, name, link))
            next_id += 1
            success_count += 1
        except Exception as e:
            print(f"Ошибка при добавлении товара: {e}")
            fail_count += 1
    
    save_items(items)
    
    # Обновляем счетчик товаров пользователя
    users = load_users()
    user_str = str(user_id)
    if user_str in users:
        users[user_str]['items_count'] = len(get_user_items(user_id))
        save_users(users)
    
    response = f"✅ *Добавление завершено*\n\n"
    response += f"📊 Результат:\n"
    response += f"• Успешно добавлено: *{success_count}*\n"
    response += f"• Не удалось добавить: *{fail_count}*\n\n"
    
    if added_items:
        response += "📝 *Добавленные товары:*\n"
        for item_id, name, link in added_items[:3]:  # Показываем первые 3
            response += f"• ID {item_id}: {name}\n"
        if len(added_items) > 3:
            response += f"• ... и еще {len(added_items) - 3} товаров\n"
    
    if fail_count > 0:
        response += "\n❌ *Возможные причины ошибок:*\n"
        response += "• Неверный формат (нужно: Название - Ссылка)\n"
        response += "• Пустое название или ссылка\n"
        response += "• Слишком длинная строка\n"
    
    response += "\n🚧 *Система добавления в разработке*"
    
    await message.answer(response, parse_mode="Markdown")
    await state.clear()

@router.message(DeleteItem.waiting_for_id)
async def process_delete_item(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        item_id = int(message.text.strip())
        
        items = load_items()
        item_to_delete = None
        
        # Ищем товар
        for item in items:
            if item.get('id') == item_id and item.get('owner_id') == user_id:
                item_to_delete = item
                break
        
        if item_to_delete:
            # Удаляем товар
            items = [item for item in items if not (
                item.get('id') == item_id and item.get('owner_id') == user_id
            )]
            save_items(items)
            
            # Обновляем счетчик
            users = load_users()
            user_str = str(user_id)
            if user_str in users:
                users[user_str]['items_count'] = len(get_user_items(user_id))
                save_users(users)
            
            response = (
                f"✅ *Товар успешно удалён!*\n\n"
                f"🗑️ Удален товар:\n"
                f"• ID: {item_id}\n"
                f"• Название: {item_to_delete.get('name')}\n"
                f"• Ссылка: {item_to_delete.get('link')}\n\n"
                f"🚧 *Функция удаления в разработке*"
            )
            await message.answer(response, parse_mode="Markdown")
        else:
            await message.answer(
                "❌ *Товар не найден или не принадлежит вам!*\n\n"
                "Проверьте:\n"
                "• Правильность ID\n"
                "• Принадлежит ли товар вам\n\n"
                "ℹ️ ID можно узнать в '📋 Мой список'",
                parse_mode="Markdown"
            )
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат ID!*\n\n"
            "Введите корректный номер ID (только цифры).\n"
            "Пример: 1, 15, 42",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(
            f"❌ *Ошибка при удалении!*\n\n"
            f"Техническая информация: {str(e)[:100]}\n\n"
            "🚧 *Система в разработке, возможны ошибки*",
            parse_mode="Markdown"
        )
    
    await state.clear()

@router.message(ReserveItem.waiting_for_id)
async def process_reserve_item(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        item_id = int(message.text.strip())
        
        items = load_items()
        item_found = None
        
        for item in items:
            if item.get('id') == item_id:
                item_found = item
                break
        
        if not item_found:
            await message.answer(
                "❌ *Товар не найден!*\n\n"
                "Проверьте правильность ID товара.",
                parse_mode="Markdown"
            )
            return
        
        if item_found.get('reserved_by'):
            await message.answer(
                "❌ *Товар уже забронирован!*\n\n"
                f"Этот товар забронирован пользователем ID: {item_found.get('reserved_by')}\n\n"
                "Попробуйте другой товар.",
                parse_mode="Markdown"
            )
            return
        
        if item_found.get('owner_id') == user_id:
            await message.answer(
                "❌ *Нельзя бронировать свои товары!*\n\n"
                "Вы можете бронировать только товары других пользователей.",
                parse_mode="Markdown"
            )
            return
        
        # Бронируем товар
        item_found['reserved_by'] = user_id
        item_found['reserved_date'] = message.date.strftime("%d.%m.%Y %H:%M")
        save_items(items)
        
        response = (
            f"✅ *Товар успешно забронирован!*\n\n"
            f"🔒 Забронирован товар:\n"
            f"• ID: {item_id}\n"
            f"• Название: {item_found.get('name')}\n"
            f"• Владелец: ID {item_found.get('owner_id')}\n"
            f"• Ссылка: {item_found.get('link')}\n\n"
            f"⚠️ *Помните:*\n"
            f"• Бронь действует до снятия\n"
            f"• Владелец может отменить бронь\n\n"
            f"🚧 *Система бронирования в активной разработке*"
        )
        await message.answer(response, parse_mode="Markdown")
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат ID!*\n\n"
            "Введите корректный номер ID (только цифры).",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(
            f"❌ *Ошибка при бронировании!*\n\n"
            f"Техническая информация: {str(e)[:100]}\n\n"
            "🚧 *Система в разработке*",
            parse_mode="Markdown"
        )
    
    await state.clear()

@router.message(UnreserveItem.waiting_for_id)
async def process_unreserve_item(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        item_id = int(message.text.strip())
        
        items = load_items()
        item_found = None
        
        for item in items:
            if item.get('id') == item_id:
                item_found = item
                break
        
        if not item_found:
            await message.answer(
                "❌ *Товар не найден!*\n\n"
                "Проверьте правильность ID товара.",
                parse_mode="Markdown"
            )
            return
        
        if not item_found.get('reserved_by'):
            await message.answer(
                "❌ *Товар не забронирован!*\n\n"
                "Этот товар и так свободен.",
                parse_mode="Markdown"
            )
            return
        
        if item_found.get('reserved_by') != user_id:
            await message.answer(
                "❌ *Нельзя снять чужую бронь!*\n\n"
                "Вы можете снять только свою бронь.\n"
                f"Этот товар забронирован пользователем ID: {item_found.get('reserved_by')}",
                parse_mode="Markdown"
            )
            return
        
        # Снимаем бронь
        reserved_date = item_found.get('reserved_date', 'неизвестно')
        item_found['reserved_by'] = None
        item_found.pop('reserved_date', None)
        save_items(items)
        
        response = (
            f"✅ *Бронь успешно снята!*\n\n"
            f"🔓 Снята бронь с товара:\n"
            f"• ID: {item_id}\n"
            f"• Название: {item_found.get('name')}\n"
            f"• Дата брони: {reserved_date}\n"
            f"• Ссылка: {item_found.get('link')}\n\n"
            f"🚧 *Система в разработке*"
        )
        await message.answer(response, parse_mode="Markdown")
        
    except ValueError:
        await message.answer(
            "❌ *Неверный формат ID!*\n\n"
            "Введите корректный номер ID (только цифры).",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(
            f"❌ *Ошибка при снятии брони!*\n\n"
            f"Техническая информация: {str(e)[:100]}\n\n"
            "🚧 *Система в разработке*",
            parse_mode="Markdown"
        )
    
    await state.clear()

# ============ КОМАНДА /SHARE_ ============
@router.message(F.text.startswith("/share_"))
async def cmd_view_shared(message: Message):
    try:
        text = message.text.strip()
        
        if not text.startswith("/share_"):
            return
        
        owner_id_str = text[7:]
        
        if not owner_id_str.isdigit():
            await message.answer(
                "❌ *Неверный формат команды!*\n\n"
                "Используйте: `/share_123456789`\n"
                "Где 123456789 - ID пользователя",
                parse_mode="Markdown"
            )
            return
        
        owner_id = int(owner_id_str)
        current_user_id = message.from_user.id
        
        # Нельзя смотреть свой список через эту команду
        if owner_id == current_user_id:
            await message.answer(
                "ℹ️ *Это ваш собственный список!*\n\n"
                "Для просмотра своего списка используйте кнопку '📋 Мой список' "
                "или команду `/list`",
                parse_mode="Markdown"
            )
            return
        
        items = load_items()
        user_items = [item for item in items if item.get('owner_id') == owner_id]
        
        if not user_items:
            await message.answer(
                "📭 *Список пользователя пуст или недоступен!*\n\n"
                f"Пользователь ID {owner_id} пока не добавил товаров "
                "или список недоступен для просмотра.",
                parse_mode="Markdown"
            )
            return
        
        response = f"📋 *Список товаров пользователя ID {owner_id}:*\n\n"
        
        for item in user_items:
            item_id = item.get('id')
            name = item.get('name')
            link = item.get('link')
            reserved_by = item.get('reserved_by')
            
            if reserved_by:
                if reserved_by == current_user_id:
                    status = "🔒 Забронирован ВАМИ"
                else:
                    status = f"🔒 Забронирован (ID: {reserved_by})"
            else:
                status = "✅ Свободен"
            
            response += f"*{item_id}.* {name}\n{link}\n{status}\n\n"
        
        response += (
            "🔒 *Чтобы забронировать товар:*\n"
            "1. Скопируйте ID нужного товара\n"
            "2. Нажмите '🔒 Бронь'\n"
            "3. Введите ID товара\n\n"
            "🚧 *Система шеринга в разработке*"
        )
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(
            f"❌ *Произошла ошибка!*\n\n"
            f"Техническая информация: {str(e)[:100]}\n\n"
            "Проверьте правильность команды.",
            parse_mode="Markdown"
        )

# ============ КОМАНДА MENU ============
@router.message(Command("menu"))
async def cmd_menu(message: Message):
    menu_text = (
        "🎛️ *Главное меню*\n\n"
        "Выберите действие из меню ниже:\n\n"
        "🚧 *Бот в разработке, меню может меняться*"
    )
    await message.answer(menu_text, parse_mode="Markdown", reply_markup=get_inline_menu())

# ============ КОМАНДА INFO ============
@router.message(Command("info"))
async def cmd_info(message: Message):
    info_text = (
        "🤖 *Информация о боте WishKeep*\n\n"
        
        "🎯 *Назначение:*\n"
        "Бот для создания и управления списками товаров "
        "с возможностью делиться ими и бронировать товары.\n\n"
        
        "🔄 *Текущая версия:* 0.5 (Beta)\n"
        "📅 *Статус:* В активной разработке\n\n"
        
        "⚠️ *Предупреждение:*\n"
        "• Бот находится в стадии тестирования\n"
        "• Функции могут меняться\n"
        "• Возможны сбои в работе\n"
        "• Данные могут быть сброшены\n\n"
        
        "📞 *Обратная связь:*\n"
        "Сообщайте о проблемах и предложениях разработчику.\n\n"
        
        "💾 *Хранение данных:*\n"
        "Все данные хранятся в JSON файлах в папке `data/`\n\n"
        
        "🚀 *Планы развития:*\n"
        "• Уведомления\n• Категории\n• Поиск\n• Веб-интерфейс"
    )
    await message.answer(info_text, parse_mode="Markdown")

# ============ ОБРАБОТКА НЕИЗВЕСТНЫХ КОМАНД ============
@router.message()
async def unknown_command(message: Message):
    if message.text and message.text.startswith('/'):
        await message.answer(
            "❓ *Неизвестная команда!*\n\n"
            "Используйте кнопки меню или команды:\n"
            "`/start` - начало работы\n"
            "`/menu` - показать меню\n"
            "`/help` - справка\n"
            "`/info` - информация о боте\n\n"
            "🚧 *Бот в разработке, команды могут меняться*",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )