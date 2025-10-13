"""Admin handlers for roulette management."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import User
from services.roulette_service import RouletteService
from utils.keyboards import admin_menu_keyboard, cancel_inline_keyboard
from utils.helpers import is_admin
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)
router = Router()


class AddRoulettePrizeStates(StatesGroup):
    """States for adding roulette prize."""
    waiting_for_name = State()
    waiting_for_type = State()
    waiting_for_value = State()
    waiting_for_probability = State()


def admin_roulette_menu_keyboard():
    """Roulette management menu."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить приз", callback_data="admin_add_roulette_prize")
    builder.button(text="📋 Список призов", callback_data="admin_list_roulette_prizes")
    builder.button(text="🔙 Назад", callback_data="admin_quests_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_roulette_prizes_keyboard(prizes):
    """List of roulette prizes."""
    builder = InlineKeyboardBuilder()
    for prize in prizes:
        status = "✅" if prize.is_active else "❌"
        builder.button(
            text=f"{status} {prize.name} ({prize.probability*100:.0f}%)",
            callback_data=f"admin_roulette_prize_{prize.id}"
        )
    builder.button(text="🔙 Назад", callback_data="admin_roulette_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_roulette_prize_actions_keyboard(prize_id: int, is_active: bool):
    """Actions for specific prize."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Название", callback_data=f"admin_edit_roulette_name_{prize_id}")
    builder.button(text="💰 Значение", callback_data=f"admin_edit_roulette_value_{prize_id}")
    builder.button(text="🎲 Вероятность", callback_data=f"admin_edit_roulette_prob_{prize_id}")
    
    if is_active:
        builder.button(text="🔴 Деактивировать", callback_data=f"admin_deactivate_roulette_{prize_id}")
    else:
        builder.button(text="🟢 Активировать", callback_data=f"admin_activate_roulette_{prize_id}")
    
    builder.button(text="🗑 Удалить", callback_data=f"admin_delete_roulette_{prize_id}")
    builder.button(text="🔙 Назад", callback_data="admin_list_roulette_prizes")
    builder.adjust(2, 1, 1, 1, 1)
    return builder.as_markup()


@router.callback_query(F.data == "admin_roulette_menu")
async def admin_roulette_menu(callback: CallbackQuery, user: User):
    """Show roulette management menu."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "🎰 **Управление колесом рулетки**\n\n"
        "Здесь вы можете настроить призы и их вероятности.\n\n"
        "**Типы призов:**\n"
        "• `eur` - EUR (баланс)\n"
        "• `points` - Баллы\n"
        "• `promocode` - Промокод\n"
        "• `nothing` - Ничего\n\n"
        "**Вероятность:**\n"
        "Число от 0.0 до 1.0\n"
        "Например: 0.3 = 30% шанс",
        reply_markup=admin_roulette_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_list_roulette_prizes")
async def admin_list_prizes(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show list of all prizes."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    prizes = await RouletteService.get_all_prizes(session)
    
    if not prizes:
        await callback.message.edit_text(
            "📋 **Список призов пуст**\n\n"
            "Создайте первый приз!",
            reply_markup=admin_roulette_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    total_prob = sum(p.probability for p in prizes if p.is_active)
    
    await callback.message.edit_text(
        f"📋 **Список призов** ({len(prizes)})\n\n"
        f"Общая вероятность: {total_prob*100:.0f}%\n\n"
        f"Выберите приз для редактирования:",
        reply_markup=admin_roulette_prizes_keyboard(prizes),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_roulette_prize_"))
async def admin_prize_actions(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show prize actions."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    prize_id = int(callback.data.split("_")[3])
    prize = await RouletteService.get_prize_by_id(session, prize_id)
    
    if not prize:
        await callback.answer("❌ Приз не найден")
        return
    
    prize_types = {
        'eur': 'EUR',
        'points': 'Баллы',
        'promocode': 'Промокод',
        'nothing': 'Ничего'
    }
    
    status = "✅ Активен" if prize.is_active else "❌ Неактивен"
    
    await callback.message.edit_text(
        f"🎰 **Приз: {prize.name}**\n\n"
        f"**Статус:** {status}\n"
        f"**Тип:** {prize_types.get(prize.prize_type, prize.prize_type)}\n"
        f"**Значение:** {prize.prize_value}\n"
        f"**Вероятность:** {prize.probability*100:.1f}%",
        reply_markup=admin_roulette_prize_actions_keyboard(prize_id, prize.is_active),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_roulette_prize")
async def admin_add_prize_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new prize."""
    await state.set_state(AddRoulettePrizeStates.waiting_for_name)
    await callback.message.edit_text(
        "➕ **Создание нового приза**\n\n"
        "Шаг 1/4: Введите название приза:\n\n"
        "Например: \"10 EUR\", \"50 баллов\", \"Ничего\"",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AddRoulettePrizeStates.waiting_for_name)
async def admin_add_prize_name(message: Message, state: FSMContext):
    """Process prize name."""
    await state.update_data(name=message.text)
    await state.set_state(AddRoulettePrizeStates.waiting_for_type)
    await message.answer(
        "Шаг 2/4: Выберите тип приза:\n\n"
        "Введите:\n"
        "• `eur` - EUR (баланс)\n"
        "• `points` - Баллы\n"
        "• `promocode` - Промокод\n"
        "• `nothing` - Ничего",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )


@router.message(AddRoulettePrizeStates.waiting_for_type)
async def admin_add_prize_type(message: Message, state: FSMContext):
    """Process prize type."""
    prize_type = message.text.lower()
    if prize_type not in ['eur', 'points', 'promocode', 'nothing']:
        await message.answer("❌ Неверный тип. Введите: eur, points, promocode или nothing")
        return
    
    await state.update_data(prize_type=prize_type)
    await state.set_state(AddRoulettePrizeStates.waiting_for_value)
    await message.answer(
        "Шаг 3/4: Введите значение приза (число):\n\n"
        "Например: 10 (для 10 EUR) или 50 (для 50 баллов)\n"
        "Для 'nothing' введите 0",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRoulettePrizeStates.waiting_for_value)
async def admin_add_prize_value(message: Message, state: FSMContext):
    """Process prize value."""
    try:
        value = float(message.text)
    except ValueError:
        await message.answer("❌ Введите число")
        return
    
    await state.update_data(prize_value=value)
    await state.set_state(AddRoulettePrizeStates.waiting_for_probability)
    await message.answer(
        "Шаг 4/4: Введите вероятность (от 0.0 до 1.0):\n\n"
        "Примеры:\n"
        "• 0.1 = 10% шанс\n"
        "• 0.3 = 30% шанс\n"
        "• 0.5 = 50% шанс",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddRoulettePrizeStates.waiting_for_probability)
async def admin_add_prize_probability(message: Message, state: FSMContext, session: AsyncSession):
    """Process probability and create prize."""
    try:
        probability = float(message.text)
        if probability < 0 or probability > 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число от 0.0 до 1.0")
        return
    
    # Get all data
    data = await state.get_data()
    
    # Create prize
    prize = await RouletteService.create_prize(
        session=session,
        name=data['name'],
        prize_type=data['prize_type'],
        prize_value=data['prize_value'],
        probability=probability
    )
    
    await state.clear()
    await message.answer(
        f"✅ **Приз создан успешно!**\n\n"
        f"**ID:** {prize.id}\n"
        f"**Название:** {prize.name}\n"
        f"**Вероятность:** {probability*100:.0f}%",
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"Roulette prize {prize.id} created by admin {message.from_user.id}")


@router.callback_query(F.data.startswith("admin_activate_roulette_"))
async def admin_activate_prize(callback: CallbackQuery, session: AsyncSession):
    """Activate prize."""
    prize_id = int(callback.data.split("_")[3])
    await RouletteService.toggle_prize_status(session, prize_id)
    
    # Refresh display
    await admin_prize_actions(callback, callback.from_user, session)
    await callback.answer("✅ Приз активирован")


@router.callback_query(F.data.startswith("admin_deactivate_roulette_"))
async def admin_deactivate_prize(callback: CallbackQuery, session: AsyncSession):
    """Deactivate prize."""
    prize_id = int(callback.data.split("_")[3])
    await RouletteService.toggle_prize_status(session, prize_id)
    
    # Refresh display
    await admin_prize_actions(callback, callback.from_user, session)
    await callback.answer("🔴 Приз деактивирован")


@router.callback_query(F.data.startswith("admin_delete_roulette_"))
async def admin_delete_prize(callback: CallbackQuery, session: AsyncSession):
    """Delete prize."""
    prize_id = int(callback.data.split("_")[3])
    success = await RouletteService.delete_prize(session, prize_id)
    
    if success:
        await callback.message.edit_text(
            "✅ Приз удален успешно!",
            reply_markup=admin_roulette_menu_keyboard()
        )
        await callback.answer("✅ Удалено")
    else:
        await callback.answer("❌ Ошибка удаления")


@router.callback_query(F.data == "cancel_add_roulette_prize")
async def cancel_add_prize(callback: CallbackQuery, state: FSMContext):
    """Cancel prize creation."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание приза отменено."
    )
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=admin_menu_keyboard()
    )
    await callback.answer("❌ Отменено")

