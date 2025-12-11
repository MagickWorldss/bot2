"""Admin handlers for quest management."""
import logging
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import User
from services.quest_service import QuestService
from utils.keyboards import (
    admin_quest_management_keyboard,
    admin_quests_list_keyboard,
    admin_quest_actions_keyboard,
    cancel_inline_keyboard,
    admin_menu_keyboard
)
from utils.helpers import is_admin

logger = logging.getLogger(__name__)
router = Router()


class AddQuestStates(StatesGroup):
    """States for adding quest."""
    waiting_for_name_ru = State()
    waiting_for_name_en = State()
    waiting_for_description_ru = State()
    waiting_for_description_en = State()
    waiting_for_quest_type = State()
    waiting_for_condition_type = State()
    waiting_for_condition_value = State()
    waiting_for_reward_type = State()
    waiting_for_reward_value = State()
    waiting_for_duration = State()


class EditQuestStates(StatesGroup):
    """States for editing quest."""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_condition = State()
    waiting_for_reward = State()


@router.message(F.text == "🎯 Квесты и челленджи")
async def admin_quests_menu(message: Message, user: User, session: AsyncSession):
    """Show quest management menu."""
    if not is_admin(user.id, settings.admin_list):
        return
    
    await message.answer(
        "🎯 **Управление квестами и челленджами**\n\n"
        "Здесь вы можете создавать и управлять квестами для пользователей.\n\n"
        "**Типы квестов:**\n"
        "• Ежедневные - обновляются каждый день\n"
        "• Еженедельные - обновляются каждую неделю\n"
        "• Месячные - обновляются каждый месяц\n"
        "• Специальные - разовые события\n\n"
        "**Условия:**\n"
        "• Покупки - количество покупок\n"
        "• Траты - сумма потраченных средств\n"
        "• Товары - количество купленных товаров\n\n"
        "**Награды:**\n"
        "• EUR - баланс в евро\n"
        "• Баллы - баллы достижений\n"
        "• Промокод - специальный промокод",
        reply_markup=admin_quest_management_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "admin_quests_menu")
async def admin_quests_menu_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show quest management menu (callback)."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    # Create extended keyboard with all quest features
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Квесты", callback_data="admin_quests_submenu")
    builder.button(text="🎰 Рулетка", callback_data="admin_roulette_menu")
    builder.button(text="🗺 Квест поиска", callback_data="admin_real_quest_menu")
    builder.button(text="🎁 Ежедневный бонус", callback_data="admin_daily_bonus_menu")
    builder.button(text="🔙 Назад в админку", callback_data="back_to_admin")
    builder.adjust(2, 2, 1)
    
    await callback.message.edit_text(
        "🎯 **Управление квестами и челленджами**\n\n"
        "Полное управление всеми игровыми элементами.\n\n"
        "**📋 Квесты:**\n"
        "• Создание и редактирование квестов\n"
        "• Условия: покупки, траты, товары\n"
        "• Награды: EUR, баллы, промокоды\n\n"
        "**🎰 Рулетка:**\n"
        "• Настройка призов и вероятностей\n"
        "• Управление активностью\n\n"
        "**🗺 Квест поиска:**\n"
        "• 20 заданий в реальной жизни\n"
        "• Физические призы\n"
        "• Статистика участников\n\n"
        "**🎁 Ежедневный бонус:**\n"
        "• Настройка размера бонуса\n"
        "• Управление условиями",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_quests_submenu")
async def admin_quests_submenu(callback: CallbackQuery, user: User):
    """Show quests submenu."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать квест", callback_data="admin_add_quest")
    builder.button(text="📋 Список квестов", callback_data="admin_list_quests")
    builder.button(text="🔙 Назад", callback_data="admin_quests_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📋 **Управление квестами**\n\n"
        "Создавайте и редактируйте квесты для пользователей.\n\n"
        "**Типы квестов:**\n"
        "• Ежедневные - обновляются каждый день\n"
        "• Еженедельные - обновляются каждую неделю\n"
        "• Месячные - обновляются каждый месяц\n"
        "• Специальные - разовые события",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_list_quests")
async def admin_list_quests(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show list of all quests."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    quests = await QuestService.get_all_quests(session)
    
    if not quests:
        await callback.message.edit_text(
            "📋 **Список квестов пуст**\n\n"
            "Создайте первый квест!",
            reply_markup=admin_quest_management_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"📋 **Список квестов** ({len(quests)})\n\n"
        "Выберите квест для редактирования:",
        reply_markup=admin_quests_list_keyboard(quests),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_quest_"))
async def admin_quest_actions(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show quest actions."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен")
        return
    
    quest_id = int(callback.data.split("_")[2])
    quest = await QuestService.get_quest_by_id(session, quest_id)
    
    if not quest:
        await callback.answer("❌ Квест не найден")
        return
    
    # Format quest info
    quest_types = {
        'daily': 'Ежедневный',
        'weekly': 'Еженедельный',
        'monthly': 'Месячный',
        'special': 'Специальный'
    }
    
    condition_types = {
        'purchases': 'Покупки',
        'spending': 'Траты',
        'items': 'Товары'
    }
    
    reward_types = {
        'sol': 'EUR',
        'points': 'Баллы',
        'promocode': 'Промокод'
    }
    
    status = "✅ Активен" if quest.is_active else "❌ Неактивен"
    
    await callback.message.edit_text(
        f"🎯 **Квест: {quest.name_ru}**\n\n"
        f"**Статус:** {status}\n"
        f"**Тип:** {quest_types.get(quest.quest_type, quest.quest_type)}\n\n"
        f"**Описание (RU):**\n{quest.description_ru}\n\n"
        f"**Описание (EN):**\n{quest.description_en}\n\n"
        f"**Условие:** {condition_types.get(quest.condition_type, quest.condition_type)} - {quest.condition_value}\n"
        f"**Награда:** {reward_types.get(quest.reward_type, quest.reward_type)} - {quest.reward_value}\n\n"
        f"**Период:**\n"
        f"С: {quest.starts_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"До: {quest.ends_at.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=admin_quest_actions_keyboard(quest_id, quest.is_active),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_quest")
async def admin_add_quest_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new quest."""
    await state.set_state(AddQuestStates.waiting_for_name_ru)
    await callback.message.edit_text(
        "➕ **Создание нового квеста**\n\n"
        "Шаг 1/10: Введите название квеста (на русском):",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AddQuestStates.waiting_for_name_ru)
async def admin_add_quest_name_ru(message: Message, state: FSMContext):
    """Process quest name (RU)."""
    await state.update_data(name_ru=message.text)
    await state.set_state(AddQuestStates.waiting_for_name_en)
    await message.answer(
        "Шаг 2/10: Введите название квеста (на английском):",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddQuestStates.waiting_for_name_en)
async def admin_add_quest_name_en(message: Message, state: FSMContext):
    """Process quest name (EN)."""
    await state.update_data(name_en=message.text)
    await state.set_state(AddQuestStates.waiting_for_description_ru)
    await message.answer(
        "Шаг 3/10: Введите описание квеста (на русском):",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddQuestStates.waiting_for_description_ru)
async def admin_add_quest_desc_ru(message: Message, state: FSMContext):
    """Process quest description (RU)."""
    await state.update_data(description_ru=message.text)
    await state.set_state(AddQuestStates.waiting_for_description_en)
    await message.answer(
        "Шаг 4/10: Введите описание квеста (на английском):",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddQuestStates.waiting_for_description_en)
async def admin_add_quest_desc_en(message: Message, state: FSMContext):
    """Process quest description (EN)."""
    await state.update_data(description_en=message.text)
    await state.set_state(AddQuestStates.waiting_for_quest_type)
    await message.answer(
        "Шаг 5/10: Выберите тип квеста:\n\n"
        "Введите:\n"
        "• `daily` - Ежедневный\n"
        "• `weekly` - Еженедельный\n"
        "• `monthly` - Месячный\n"
        "• `special` - Специальный",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )


@router.message(AddQuestStates.waiting_for_quest_type)
async def admin_add_quest_type(message: Message, state: FSMContext):
    """Process quest type."""
    quest_type = message.text.lower()
    if quest_type not in ['daily', 'weekly', 'monthly', 'special']:
        await message.answer("❌ Неверный тип. Введите: daily, weekly, monthly или special")
        return
    
    await state.update_data(quest_type=quest_type)
    await state.set_state(AddQuestStates.waiting_for_condition_type)
    await message.answer(
        "Шаг 6/10: Выберите тип условия:\n\n"
        "Введите:\n"
        "• `purchases` - Количество покупок\n"
        "• `spending` - Сумма трат (EUR)\n"
        "• `items` - Количество товаров",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )


@router.message(AddQuestStates.waiting_for_condition_type)
async def admin_add_quest_condition_type(message: Message, state: FSMContext):
    """Process condition type."""
    condition_type = message.text.lower()
    if condition_type not in ['purchases', 'spending', 'items']:
        await message.answer("❌ Неверный тип. Введите: purchases, spending или items")
        return
    
    await state.update_data(condition_type=condition_type)
    await state.set_state(AddQuestStates.waiting_for_condition_value)
    await message.answer(
        "Шаг 7/10: Введите значение условия (число):\n\n"
        "Например: 5 (для 5 покупок) или 100 (для 100 EUR)",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddQuestStates.waiting_for_condition_value)
async def admin_add_quest_condition_value(message: Message, state: FSMContext):
    """Process condition value."""
    try:
        value = int(message.text)
        if value <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное целое число")
        return
    
    await state.update_data(condition_value=value)
    await state.set_state(AddQuestStates.waiting_for_reward_type)
    await message.answer(
        "Шаг 8/10: Выберите тип награды:\n\n"
        "Введите:\n"
        "• `sol` - EUR (баланс)\n"
        "• `points` - Баллы достижений\n"
        "• `promocode` - Промокод",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )


@router.message(AddQuestStates.waiting_for_reward_type)
async def admin_add_quest_reward_type(message: Message, state: FSMContext):
    """Process reward type."""
    reward_type = message.text.lower()
    if reward_type not in ['sol', 'points', 'promocode']:
        await message.answer("❌ Неверный тип. Введите: sol, points или promocode")
        return
    
    await state.update_data(reward_type=reward_type)
    await state.set_state(AddQuestStates.waiting_for_reward_value)
    await message.answer(
        "Шаг 9/10: Введите значение награды (число):\n\n"
        "Например: 10 (для 10 EUR) или 100 (для 100 баллов)",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddQuestStates.waiting_for_reward_value)
async def admin_add_quest_reward_value(message: Message, state: FSMContext):
    """Process reward value."""
    try:
        value = float(message.text)
        if value <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное число")
        return
    
    await state.update_data(reward_value=value)
    await state.set_state(AddQuestStates.waiting_for_duration)
    await message.answer(
        "Шаг 10/10: Введите длительность квеста в днях:\n\n"
        "Например: 1 (для ежедневного) или 7 (для еженедельного)",
        reply_markup=cancel_inline_keyboard()
    )


@router.message(AddQuestStates.waiting_for_duration)
async def admin_add_quest_duration(message: Message, state: FSMContext, session: AsyncSession):
    """Process duration and create or update quest."""
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите положительное целое число")
        return
    
    # Get all data
    data = await state.get_data()
    
    # Check if editing dates
    if data.get('edit_type') == 'dates':
        quest_id = data.get('quest_id')
        quest = await QuestService.get_quest_by_id(session, quest_id)
        
        if quest:
            starts_at = quest.starts_at
            ends_at = starts_at + timedelta(days=days)
            await QuestService.update_quest(session, quest_id, ends_at=ends_at)
            await state.clear()
            await message.answer(
                f"✅ **Даты квеста обновлены!**\n\n"
                f"Новый период: {days} дней",
                reply_markup=admin_menu_keyboard(),
                parse_mode="Markdown"
            )
        return
    
    # Create new quest
    starts_at = datetime.now(timezone.utc)
    ends_at = starts_at + timedelta(days=days)
    
    quest = await QuestService.create_quest(
        session=session,
        name_ru=data['name_ru'],
        name_en=data['name_en'],
        description_ru=data['description_ru'],
        description_en=data['description_en'],
        quest_type=data['quest_type'],
        condition_type=data['condition_type'],
        condition_value=data['condition_value'],
        reward_type=data['reward_type'],
        reward_value=data['reward_value'],
        starts_at=starts_at,
        ends_at=ends_at
    )
    
    await state.clear()
    await message.answer(
        f"✅ **Квест создан успешно!**\n\n"
        f"**ID:** {quest.id}\n"
        f"**Название:** {quest.name_ru}\n"
        f"**Период:** {days} дней",
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    logger.info(f"Quest {quest.id} created by admin {message.from_user.id}")


@router.callback_query(F.data.startswith("admin_activate_quest_"))
async def admin_activate_quest(callback: CallbackQuery, user: User, session: AsyncSession):
    """Activate quest."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    quest_id = int(callback.data.split("_")[3])
    await QuestService.toggle_quest_status(session, quest_id)
    
    # Refresh display
    await admin_quest_actions(callback, user, session)
    await callback.answer("✅ Квест активирован")


@router.callback_query(F.data.startswith("admin_deactivate_quest_"))
async def admin_deactivate_quest(callback: CallbackQuery, user: User, session: AsyncSession):
    """Deactivate quest."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    quest_id = int(callback.data.split("_")[3])
    await QuestService.toggle_quest_status(session, quest_id)
    
    # Refresh display
    await admin_quest_actions(callback, user, session)
    await callback.answer("🔴 Квест деактивирован")


@router.callback_query(F.data.startswith("admin_delete_quest_"))
async def admin_delete_quest(callback: CallbackQuery, user: User, session: AsyncSession):
    """Delete quest."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    quest_id = int(callback.data.split("_")[3])
    success = await QuestService.delete_quest(session, quest_id)
    
    if success:
        await callback.message.edit_text(
            "✅ Квест удален успешно!",
            reply_markup=admin_quest_management_keyboard()
        )
        await callback.answer("✅ Удалено")
    else:
        await callback.answer("❌ Ошибка удаления")


@router.callback_query(F.data == "cancel_add_quest")
async def cancel_add_quest(callback: CallbackQuery, state: FSMContext):
    """Cancel quest creation."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Создание квеста отменено."
    )
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=admin_menu_keyboard()
    )
    await callback.answer("❌ Отменено")


# Edit quest handlers
@router.callback_query(F.data.startswith("admin_edit_quest_name_"))
async def admin_edit_quest_name(callback: CallbackQuery, user: User, state: FSMContext, session: AsyncSession):
    """Start editing quest name."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    quest_id = int(callback.data.split("_")[4])
    quest = await QuestService.get_quest_by_id(session, quest_id)
    
    if not quest:
        await callback.answer("❌ Квест не найден", show_alert=True)
        return
    
    await state.set_state(EditQuestStates.waiting_for_name)
    await state.update_data(quest_id=quest_id, edit_type='name')
    
    await callback.message.edit_text(
        f"✏️ **Редактирование названия квеста**\n\n"
        f"Текущее название (RU): {quest.name_ru}\n"
        f"Текущее название (EN): {quest.name_en}\n\n"
        f"Введите новое название на русском:",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(EditQuestStates.waiting_for_name)
async def admin_save_quest_name(message: Message, state: FSMContext, session: AsyncSession):
    """Save quest name."""
    data = await state.get_data()
    quest_id = data.get('quest_id')
    edit_type = data.get('edit_type')
    
    if edit_type == 'name':
        # First name (RU), then ask for EN
        if 'name_ru' not in data:
            await state.update_data(name_ru=message.text)
            await message.answer(
                "Теперь введите название на английском:",
                reply_markup=cancel_inline_keyboard()
            )
        else:
            # Save both names
            name_ru = data['name_ru']
            name_en = message.text
            
            await QuestService.update_quest(session, quest_id, name_ru=name_ru, name_en=name_en)
            await state.clear()
            
            await message.answer(
                "✅ Название квеста обновлено!",
                reply_markup=admin_menu_keyboard()
            )


@router.callback_query(F.data.startswith("admin_edit_quest_desc_"))
async def admin_edit_quest_desc(callback: CallbackQuery, user: User, state: FSMContext, session: AsyncSession):
    """Start editing quest description."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    quest_id = int(callback.data.split("_")[4])
    quest = await QuestService.get_quest_by_id(session, quest_id)
    
    if not quest:
        await callback.answer("❌ Квест не найден", show_alert=True)
        return
    
    await state.set_state(EditQuestStates.waiting_for_description)
    await state.update_data(quest_id=quest_id, edit_type='description')
    
    await callback.message.edit_text(
        f"📝 **Редактирование описания квеста**\n\n"
        f"Текущее описание (RU): {quest.description_ru[:100]}...\n\n"
        f"Введите новое описание на русском:",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(EditQuestStates.waiting_for_description)
async def admin_save_quest_desc(message: Message, state: FSMContext, session: AsyncSession):
    """Save quest description."""
    data = await state.get_data()
    quest_id = data.get('quest_id')
    edit_type = data.get('edit_type')
    
    if edit_type == 'description':
        if 'description_ru' not in data:
            await state.update_data(description_ru=message.text)
            await message.answer(
                "Теперь введите описание на английском:",
                reply_markup=cancel_inline_keyboard()
            )
        else:
            description_ru = data['description_ru']
            description_en = message.text
            
            await QuestService.update_quest(session, quest_id, description_ru=description_ru, description_en=description_en)
            await state.clear()
            
            await message.answer(
                "✅ Описание квеста обновлено!",
                reply_markup=admin_menu_keyboard()
            )


@router.callback_query(F.data.startswith("admin_edit_quest_cond_"))
async def admin_edit_quest_cond(callback: CallbackQuery, user: User, state: FSMContext, session: AsyncSession):
    """Start editing quest condition."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    quest_id = int(callback.data.split("_")[4])
    quest = await QuestService.get_quest_by_id(session, quest_id)
    
    if not quest:
        await callback.answer("❌ Квест не найден", show_alert=True)
        return
    
    await state.set_state(EditQuestStates.waiting_for_condition)
    await state.update_data(quest_id=quest_id)
    
    await callback.message.edit_text(
        f"🎯 **Редактирование условия квеста**\n\n"
        f"Текущее условие: {quest.condition_type} - {quest.condition_value}\n\n"
        f"Введите тип условия (purchases/spending/items):",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(EditQuestStates.waiting_for_condition)
async def admin_save_quest_cond(message: Message, state: FSMContext, session: AsyncSession):
    """Save quest condition."""
    data = await state.get_data()
    quest_id = data.get('quest_id')
    
    condition_type = message.text.lower()
    if condition_type not in ['purchases', 'spending', 'items']:
        await message.answer("❌ Неверный тип. Введите: purchases, spending или items")
        return
    
    if 'condition_type' not in data:
        await state.update_data(condition_type=condition_type)
        await message.answer(
            "Введите значение условия (число):",
            reply_markup=cancel_inline_keyboard()
        )
    else:
        try:
            condition_value = int(message.text)
            if condition_value <= 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ Введите положительное целое число")
            return
        
        condition_type = data['condition_type']
        await QuestService.update_quest(session, quest_id, condition_type=condition_type, condition_value=condition_value)
        await state.clear()
        
        await message.answer(
            "✅ Условие квеста обновлено!",
            reply_markup=admin_menu_keyboard()
        )


@router.callback_query(F.data.startswith("admin_edit_quest_reward_"))
async def admin_edit_quest_reward(callback: CallbackQuery, user: User, state: FSMContext, session: AsyncSession):
    """Start editing quest reward."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    quest_id = int(callback.data.split("_")[4])
    quest = await QuestService.get_quest_by_id(session, quest_id)
    
    if not quest:
        await callback.answer("❌ Квест не найден", show_alert=True)
        return
    
    await state.set_state(EditQuestStates.waiting_for_reward)
    await state.update_data(quest_id=quest_id)
    
    await callback.message.edit_text(
        f"🎁 **Редактирование награды квеста**\n\n"
        f"Текущая награда: {quest.reward_type} - {quest.reward_value}\n\n"
        f"Введите тип награды (sol/points/promocode):",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(EditQuestStates.waiting_for_reward)
async def admin_save_quest_reward(message: Message, state: FSMContext, session: AsyncSession):
    """Save quest reward."""
    data = await state.get_data()
    quest_id = data.get('quest_id')
    
    reward_type = message.text.lower()
    if reward_type not in ['sol', 'points', 'promocode']:
        await message.answer("❌ Неверный тип. Введите: sol, points или promocode")
        return
    
    if 'reward_type' not in data:
        await state.update_data(reward_type=reward_type)
        await message.answer(
            "Введите значение награды (число):",
            reply_markup=cancel_inline_keyboard()
        )
    else:
        try:
            reward_value = float(message.text)
            if reward_value <= 0:
                raise ValueError
        except ValueError:
            await message.answer("❌ Введите положительное число")
            return
        
        reward_type = data['reward_type']
        await QuestService.update_quest(session, quest_id, reward_type=reward_type, reward_value=reward_value)
        await state.clear()
        
        await message.answer(
            "✅ Награда квеста обновлена!",
            reply_markup=admin_menu_keyboard()
        )


@router.callback_query(F.data.startswith("admin_edit_quest_dates_"))
async def admin_edit_quest_dates(callback: CallbackQuery, user: User, state: FSMContext, session: AsyncSession):
    """Start editing quest dates."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    quest_id = int(callback.data.split("_")[4])
    quest = await QuestService.get_quest_by_id(session, quest_id)
    
    if not quest:
        await callback.answer("❌ Квест не найден", show_alert=True)
        return
    
    await state.set_state(AddQuestStates.waiting_for_duration)
    await state.update_data(quest_id=quest_id, edit_type='dates')
    
    await callback.message.edit_text(
        f"📅 **Редактирование дат квеста**\n\n"
        f"Текущий период:\n"
        f"С: {quest.starts_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"До: {quest.ends_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Введите новую длительность в днях:",
        reply_markup=cancel_inline_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()
