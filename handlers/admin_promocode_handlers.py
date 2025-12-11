"""Admin handlers for promocode management."""
import logging
from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.promocode_service import promocode_service
from services.role_service import role_service
from utils.helpers import is_admin
from config import settings

logger = logging.getLogger(__name__)

router = Router(name='admin_promocode_handlers')


class PromocodeStates(StatesGroup):
    """States for promocode creation."""
    waiting_for_code = State()
    waiting_for_type = State()
    waiting_for_value = State()
    waiting_for_max_uses = State()
    waiting_for_duration = State()


@router.message(F.text == "🎫 Промокоды")
async def promocodes_menu(message: Message, user: User, session: AsyncSession):
    """Show promocodes management menu."""
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ Нет доступа")
        return
    
    # Get all promocodes
    promocodes = await promocode_service.get_all_promocodes(session)
    
    text = "🎫 **Управление промокодами**\n\n"
    
    if not promocodes:
        text += "📭 Промокодов пока нет\n\n"
    else:
        for promo in promocodes[:10]:  # Show last 10
            status = "✅" if promo.is_active else "❌"
            text += f"{status} **{promo.code}**\n"
            text += f"   Тип: {promo.discount_type} | Значение: {promo.discount_value}\n"
            text += f"   Использовано: {promo.used_count}"
            if promo.max_uses:
                text += f"/{promo.max_uses}"
            text += "\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать промокод", callback_data="create_promocode")
    
    if promocodes:
        builder.button(text="📋 Все промокоды", callback_data="list_all_promocodes")
    
    builder.button(text="🔙 Назад", callback_data="back_to_admin")
    builder.adjust(1)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data == "create_promocode")
async def create_promocode_init(callback: CallbackQuery, user: User, state: FSMContext):
    """Start promocode creation."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    text = """
➕ **Создание промокода**

Введите код промокода (например: SALE20)

━━━━━━━━━━━━━━━━━━━━

Требования:
• Только латинские буквы и цифры
• Не более 20 символов
• Без пробелов
    """
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(PromocodeStates.waiting_for_code)
    await callback.answer()


@router.message(PromocodeStates.waiting_for_code)
async def promocode_receive_code(message: Message, state: FSMContext):
    """Receive promocode code."""
    code = message.text.upper().strip()
    
    # Validate
    if not code.isalnum() or len(code) > 20:
        await message.answer("❌ Неверный формат. Попробуйте снова:")
        return
    
    await state.update_data(code=code)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="% Процент", callback_data="promo_type_percent")
    builder.button(text="💰 Фикс. сумма", callback_data="promo_type_fixed")
    builder.button(text="🎁 Бесплатно", callback_data="promo_type_free")
    builder.adjust(1)
    
    await message.answer(
        f"✅ Код: **{code}**\n\nВыберите тип скидки:",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await state.set_state(PromocodeStates.waiting_for_type)


@router.callback_query(F.data.startswith("promo_type_"))
async def promocode_receive_type(callback: CallbackQuery, user: User, state: FSMContext):
    """Receive discount type."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    discount_type = callback.data.split("_")[2]  # percent, fixed, free
    
    await state.update_data(discount_type=discount_type)
    
    if discount_type == "free":
        # Free item - skip value input
        await state.update_data(discount_value=0)
        await callback.message.edit_text(
            "Максимальное количество использований?\n(Введите число или 0 для безлимита)"
        )
        await state.set_state(PromocodeStates.waiting_for_max_uses)
    else:
        if discount_type == "percent":
            text = "Введите процент скидки (1-100):"
        else:
            text = "Введите сумму скидки в SOL (например: 0.05):"
        
        await callback.message.edit_text(text)
        await state.set_state(PromocodeStates.waiting_for_value)
    
    await callback.answer()


@router.message(PromocodeStates.waiting_for_value)
async def promocode_receive_value(message: Message, state: FSMContext):
    """Receive discount value."""
    try:
        value = float(message.text)
        
        data = await state.get_data()
        if data['discount_type'] == 'percent' and (value < 1 or value > 100):
            await message.answer("❌ Процент должен быть от 1 до 100")
            return
        
        await state.update_data(discount_value=value)
        await message.answer("Максимальное количество использований?\n(Введите число или 0 для безлимита)")
        await state.set_state(PromocodeStates.waiting_for_max_uses)
    except ValueError:
        await message.answer("❌ Введите число")


@router.message(PromocodeStates.waiting_for_max_uses)
async def promocode_receive_max_uses(message: Message, state: FSMContext, user: User, session: AsyncSession):
    """Receive max uses and create promocode."""
    try:
        max_uses = int(message.text)
        max_uses = None if max_uses == 0 else max_uses
        
        data = await state.get_data()
        
        # Create promocode
        valid_until = datetime.now(timezone.utc) + timedelta(days=30)  # 30 days default
        
        promocode = await promocode_service.create_promocode(
            session=session,
            code=data['code'],
            discount_type=data['discount_type'],
            discount_value=data['discount_value'],
            created_by=user.id,
            max_uses=max_uses,
            valid_until=valid_until
        )
        
        text = f"""
✅ **Промокод создан!**

🎫 Код: **{promocode.code}**
📊 Тип: {promocode.discount_type}
💰 Значение: {promocode.discount_value}
🔢 Макс. использований: {max_uses or '∞'}
📅 Действует до: {valid_until.strftime('%d.%m.%Y')}

━━━━━━━━━━━━━━━━━━━━

Пользователи могут использовать этот промокод при покупке!
        """
        
        await message.answer(text, parse_mode="Markdown")
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число")


@router.callback_query(F.data == "list_all_promocodes")
async def list_all_promocodes(callback: CallbackQuery, user: User, session: AsyncSession):
    """List all promocodes with management options."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    promocodes = await promocode_service.get_all_promocodes(session)
    
    text = "📋 **Все промокоды:**\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for promo in promocodes:
        status = "✅" if promo.is_active else "❌"
        text += f"{status} **{promo.code}** ({promo.discount_type}: {promo.discount_value})\n"
        
        if promo.is_active:
            builder.button(text=f"❌ Деактивировать {promo.code}", callback_data=f"deactivate_promo_{promo.id}")
    
    builder.button(text="🔙 Назад", callback_data="back_to_promocodes")
    builder.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("deactivate_promo_"))
async def deactivate_promocode(callback: CallbackQuery, user: User, session: AsyncSession):
    """Deactivate promocode."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    """Deactivate promocode."""
    promo_id = int(callback.data.split("_")[2])
    
    await promocode_service.deactivate_promocode(session, promo_id)
    
    await callback.answer("✅ Промокод деактивирован")
    await list_all_promocodes(callback, callback.from_user, session)


@router.callback_query(F.data == "back_to_promocodes")
async def back_to_promocodes(callback: CallbackQuery, user: User, session: AsyncSession):
    """Return to promocodes menu."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    """Return to promocodes menu."""
    await promocodes_menu(callback.message, user, session)
    await callback.message.delete()

