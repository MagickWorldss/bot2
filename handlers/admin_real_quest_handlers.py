"""Admin handlers for real quest management."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import User
from services.real_quest_service import RealQuestService
from utils.keyboards import admin_menu_keyboard, cancel_inline_keyboard
from utils.helpers import is_admin
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)
router = Router()


class AddRealQuestTaskStates(StatesGroup):
    """States for adding task."""
    waiting_for_number = State()
    waiting_for_text_ru = State()
    waiting_for_text_en = State()
    waiting_for_code = State()
    waiting_for_hint_ru = State()
    waiting_for_hint_en = State()


class AddRealQuestPrizeStates(StatesGroup):
    """States for adding prize."""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_location = State()
    waiting_for_image = State()


def admin_real_quest_menu_keyboard():
    """Real quest management menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Задания", callback_data="admin_real_quest_tasks")
    builder.button(text="🎁 Призы", callback_data="admin_real_quest_prizes")
    builder.button(text="📊 Статистика", callback_data="admin_real_quest_stats")
    builder.button(text="🔙 Назад", callback_data="admin_quests_menu")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def admin_real_quest_tasks_keyboard():
    """Tasks management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить задание", callback_data="admin_add_real_quest_task")
    builder.button(text="📋 Список заданий", callback_data="admin_list_real_quest_tasks")
    builder.button(text="🔙 Назад", callback_data="admin_real_quest_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_real_quest_prizes_keyboard():
    """Prizes management keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить приз", callback_data="admin_add_real_quest_prize")
    builder.button(text="📋 Список призов", callback_data="admin_list_real_quest_prizes")
    builder.button(text="🔙 Назад", callback_data="admin_real_quest_menu")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "admin_real_quest_menu")
async def admin_real_quest_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show real quest management menu."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    stats = await RealQuestService.get_quest_statistics(session)
    
    await callback.message.edit_text(
        "🗺 **Управление квестом поиска**\n\n"
        f"📊 **Статистика:**\n"
        f"• Участников: {stats['total_participants']}\n"
        f"• Завершили: {stats['completed_quests']}\n"
        f"• Всего призов: {stats['total_prizes']}\n"
        f"• Выдано: {stats['claimed_prizes']}\n"
        f"• Доступно: {stats['available_prizes']}\n\n"
        "Выберите действие:",
        reply_markup=admin_real_quest_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_real_quest_tasks")
async def admin_real_quest_tasks(callback: CallbackQuery, user: User):
    """Show tasks management."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "📋 **Управление заданиями**\n\n"
        "Здесь вы можете создавать и редактировать задания квеста.\n\n"
        "**Всего заданий:** 20\n"
        "Каждое задание должно иметь:\n"
        "• Номер (1-20)\n"
        "• Текст задания (RU/EN)\n"
        "• Правильный код\n"
        "• Подсказку (опционально)",
        reply_markup=admin_real_quest_tasks_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_real_quest_prizes")
async def admin_real_quest_prizes(callback: CallbackQuery, user: User):
    """Show prizes management."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "🎁 **Управление призами**\n\n"
        "Здесь вы можете добавлять физические призы.\n\n"
        "Каждый приз должен быть уникальным!\n"
        "После завершения квеста участник получит:\n"
        "• Название приза\n"
        "• Описание\n"
        "• Место получения\n"
        "• Фото (если есть)",
        reply_markup=admin_real_quest_prizes_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_real_quest_stats")
async def admin_real_quest_stats(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show detailed statistics."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    stats = await RealQuestService.get_quest_statistics(session)
    tasks = await RealQuestService.get_all_tasks(session)
    prizes = await RealQuestService.get_all_prizes(session)
    
    await callback.message.edit_text(
        "📊 **Подробная статистика**\n\n"
        f"👥 **Участники:**\n"
        f"• Всего: {stats['total_participants']}\n"
        f"• Завершили: {stats['completed_quests']}\n"
        f"• В процессе: {stats['total_participants'] - stats['completed_quests']}\n\n"
        f"📋 **Задания:**\n"
        f"• Создано: {len(tasks)}/20\n\n"
        f"🎁 **Призы:**\n"
        f"• Всего: {stats['total_prizes']}\n"
        f"• Выдано: {stats['claimed_prizes']}\n"
        f"• Доступно: {stats['available_prizes']}",
        reply_markup=admin_real_quest_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_real_quest_task")
async def admin_add_task_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new task."""
    await state.set_state(AddRealQuestTaskStates.waiting_for_number)
    await callback.message.edit_text(
        "➕ **Создание нового задания**\n\n"
        "Шаг 1/6: Введите номер задания (1-20):",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AddRealQuestTaskStates.waiting_for_number)
async def admin_add_task_number(message: Message, state: FSMContext):
    """Process task number."""
    try:
        number = int(message.text)
        if number < 1 or number > 20:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число от 1 до 20")
        return
    
    await state.update_data(task_number=number)
    await state.set_state(AddRealQuestTaskStates.waiting_for_text_ru)
    await message.answer(
        f"Шаг 2/6: Введите текст задания #{number} (на русском):",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRealQuestTaskStates.waiting_for_text_ru)
async def admin_add_task_text_ru(message: Message, state: FSMContext):
    """Process task text (RU)."""
    await state.update_data(task_text_ru=message.text)
    await state.set_state(AddRealQuestTaskStates.waiting_for_text_en)
    await message.answer(
        "Шаг 3/6: Введите текст задания (на английском):",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRealQuestTaskStates.waiting_for_text_en)
async def admin_add_task_text_en(message: Message, state: FSMContext):
    """Process task text (EN)."""
    await state.update_data(task_text_en=message.text)
    await state.set_state(AddRealQuestTaskStates.waiting_for_code)
    await message.answer(
        "Шаг 4/6: Введите правильный код для этого задания:",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRealQuestTaskStates.waiting_for_code)
async def admin_add_task_code(message: Message, state: FSMContext):
    """Process correct code."""
    await state.update_data(correct_code=message.text)
    await state.set_state(AddRealQuestTaskStates.waiting_for_hint_ru)
    await message.answer(
        "Шаг 5/6: Введите подсказку (на русском) или '-' чтобы пропустить:",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRealQuestTaskStates.waiting_for_hint_ru)
async def admin_add_task_hint_ru(message: Message, state: FSMContext):
    """Process hint (RU)."""
    hint = None if message.text == '-' else message.text
    await state.update_data(hint_ru=hint)
    await state.set_state(AddRealQuestTaskStates.waiting_for_hint_en)
    await message.answer(
        "Шаг 6/6: Введите подсказку (на английском) или '-' чтобы пропустить:",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRealQuestTaskStates.waiting_for_hint_en)
async def admin_add_task_hint_en(message: Message, state: FSMContext, session: AsyncSession):
    """Process hint (EN) and create task."""
    hint = None if message.text == '-' else message.text
    
    # Get all data
    data = await state.get_data()
    
    # Create task
    task = await RealQuestService.create_task(
        session=session,
        task_number=data['task_number'],
        task_text_ru=data['task_text_ru'],
        task_text_en=data['task_text_en'],
        correct_code=data['correct_code'],
        hint_ru=data.get('hint_ru'),
        hint_en=hint
    )
    
    await state.clear()
    await message.answer(
        f"✅ **Задание #{data['task_number']} создано!**\n\n"
        f"Код: `{data['correct_code']}`",
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"Real quest task {task.id} created by admin {message.from_user.id}")


@router.callback_query(F.data == "admin_add_real_quest_prize")
async def admin_add_prize_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new prize."""
    await state.set_state(AddRealQuestPrizeStates.waiting_for_name)
    await callback.message.edit_text(
        "➕ **Добавление нового приза**\n\n"
        "Шаг 1/4: Введите название приза:",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AddRealQuestPrizeStates.waiting_for_name)
async def admin_add_prize_name(message: Message, state: FSMContext):
    """Process prize name."""
    await state.update_data(prize_name=message.text)
    await state.set_state(AddRealQuestPrizeStates.waiting_for_description)
    await message.answer(
        "Шаг 2/4: Введите описание приза:",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRealQuestPrizeStates.waiting_for_description)
async def admin_add_prize_description(message: Message, state: FSMContext):
    """Process prize description."""
    await state.update_data(prize_description=message.text)
    await state.set_state(AddRealQuestPrizeStates.waiting_for_location)
    await message.answer(
        "Шаг 3/4: Введите место получения приза:",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRealQuestPrizeStates.waiting_for_location)
async def admin_add_prize_location(message: Message, state: FSMContext):
    """Process pickup location."""
    await state.update_data(pickup_location=message.text)
    await state.set_state(AddRealQuestPrizeStates.waiting_for_image)
    await message.answer(
        "Шаг 4/4: Отправьте фото приза или '-' чтобы пропустить:",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRealQuestPrizeStates.waiting_for_image)
async def admin_add_prize_image(message: Message, state: FSMContext, session: AsyncSession):
    """Process prize image and create prize."""
    file_id = None
    
    if message.text != '-' and message.photo:
        file_id = message.photo[-1].file_id
    
    # Get all data
    data = await state.get_data()
    
    # Create prize
    prize = await RealQuestService.create_prize(
        session=session,
        prize_name=data['prize_name'],
        prize_description=data['prize_description'],
        pickup_location=data['pickup_location'],
        prize_image_file_id=file_id
    )
    
    await state.clear()
    await message.answer(
        f"✅ **Приз создан!**\n\n"
        f"**ID:** {prize.id}\n"
        f"**Название:** {prize.prize_name}",
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"Real quest prize {prize.id} created by admin {message.from_user.id}")


@router.callback_query(F.data == "admin_list_real_quest_tasks")
async def admin_list_tasks(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show list of all tasks."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    tasks = await RealQuestService.get_all_tasks(session)
    
    if not tasks:
        await callback.message.edit_text(
            "📋 **Список заданий пуст**\n\n"
            "Создайте первое задание!",
            reply_markup=admin_real_quest_tasks_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    text = f"📋 **Список заданий** ({len(tasks)}/20)\n\n"
    
    for task in tasks:
        status = "✅" if task.is_active else "❌"
        text += f"{status} **Задание {task.task_number}**\n"
        text += f"Код: `{task.correct_code}`\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_real_quest_tasks_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_list_real_quest_prizes")
async def admin_list_prizes(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show list of all prizes."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    prizes = await RealQuestService.get_all_prizes(session)
    
    if not prizes:
        await callback.message.edit_text(
            "🎁 **Список призов пуст**\n\n"
            "Добавьте первый приз!",
            reply_markup=admin_real_quest_prizes_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    text = f"🎁 **Список призов** ({len(prizes)})\n\n"
    
    for prize in prizes:
        status = "✅ Выдан" if prize.is_claimed else "📦 Доступен"
        text += f"{status} **{prize.prize_name}**\n"
        if prize.is_claimed:
            text += f"Получил: User ID {prize.claimed_by}\n"
        text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_real_quest_prizes_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

