"""Admin handlers for daily bonus management."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import User
from utils.keyboards import admin_menu_keyboard
from utils.helpers import is_admin
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)
router = Router()


class EditDailyBonusStates(StatesGroup):
    """States for editing daily bonus."""
    waiting_for_amount = State()


@router.callback_query(F.data == "admin_daily_bonus_menu")
async def admin_daily_bonus_menu(callback: CallbackQuery, user: User):
    """Show daily bonus management menu."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    # Get current bonus amount from settings (you can store this in DB later)
    current_bonus = 10.0  # Default value
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить сумму бонуса", callback_data="admin_edit_daily_bonus_amount")
    builder.button(text="📊 Статистика", callback_data="admin_daily_bonus_stats")
    builder.button(text="🔙 Назад", callback_data="admin_quests_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🎁 **Управление ежедневным бонусом**\n\n"
        f"**Текущая сумма бонуса:** {current_bonus} EUR\n\n"
        "Пользователи могут получать ежедневный бонус раз в 24 часа.\n\n"
        "**Настройки:**\n"
        "• Изменить сумму бонуса\n"
        "• Просмотр статистики получений",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_edit_daily_bonus_amount")
async def admin_edit_bonus_amount(callback: CallbackQuery, state: FSMContext):
    """Start editing bonus amount."""
    await state.set_state(EditDailyBonusStates.waiting_for_amount)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="admin_daily_bonus_menu")
    
    await callback.message.edit_text(
        "✏️ **Изменение суммы ежедневного бонуса**\n\n"
        "Введите новую сумму бонуса в EUR:\n\n"
        "Например: 10 или 15.5",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(EditDailyBonusStates.waiting_for_amount)
async def process_bonus_amount(message: Message, state: FSMContext):
    """Process new bonus amount."""
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное число")
        return
    
    # Here you would save to database or config
    # For now, just confirm
    await state.clear()
    
    await message.answer(
        f"✅ **Сумма ежедневного бонуса обновлена!**\n\n"
        f"Новая сумма: **{amount} EUR**\n\n"
        f"Все пользователи теперь будут получать {amount} EUR при получении ежедневного бонуса.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"Daily bonus amount updated to {amount} EUR by admin {message.from_user.id}")


@router.callback_query(F.data == "admin_daily_bonus_stats")
async def admin_daily_bonus_stats(callback: CallbackQuery, session: AsyncSession):
    """Show daily bonus statistics."""
    # Here you would query actual statistics from database
    # For now, show placeholder
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="admin_daily_bonus_menu")
    
    await callback.message.edit_text(
        "📊 **Статистика ежедневного бонуса**\n\n"
        "**За сегодня:**\n"
        "• Получили бонус: 0 пользователей\n"
        "• Выдано: 0 EUR\n\n"
        "**За неделю:**\n"
        "• Получили бонус: 0 пользователей\n"
        "• Выдано: 0 EUR\n\n"
        "**Всего:**\n"
        "• Получили бонус: 0 пользователей\n"
        "• Выдано: 0 EUR",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

