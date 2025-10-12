"""User promocode handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.promocode_service import promocode_service

logger = logging.getLogger(__name__)

router = Router(name='user_promocode_handlers')


class PromocodeInputStates(StatesGroup):
    """States for promocode input."""
    waiting_for_code = State()


@router.callback_query(F.data == "my_promocodes_menu")
async def show_my_promocodes(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show user's promocodes menu."""
    text = """
🎫 **Промокоды**

━━━━━━━━━━━━━━━━━━━━

💡 Используйте промокоды для получения скидок!

Промокоды можно получить:
• В магазине "🎁 Стафф" за баллы
• От администратора
• В акциях и конкурсах

━━━━━━━━━━━━━━━━━━━━

Введите промокод при покупке товара в каталоге!
    """
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🎫 Ввести промокод", callback_data="enter_promocode")
    builder.button(text="🔙 Назад", callback_data="back_to_profile")
    builder.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "enter_promocode")
async def enter_promocode_init(callback: CallbackQuery, state: FSMContext):
    """Start promocode input."""
    await callback.message.edit_text(
        "🎫 **Введите промокод:**\n\n"
        "Например: SALE20",
        parse_mode="Markdown"
    )
    await state.set_state(PromocodeInputStates.waiting_for_code)
    await callback.answer()


@router.message(PromocodeInputStates.waiting_for_code)
async def process_promocode_input(message: Message, user: User, session: AsyncSession, state: FSMContext):
    """Process promocode input."""
    code = message.text.strip().upper()
    
    # Validate promocode
    is_valid, error_message, promocode = await promocode_service.validate_promocode(session, code, user.id)
    
    if not is_valid:
        await message.answer(
            f"{error_message}\n\n"
            f"Попробуйте другой промокод или напишите в поддержку."
        )
        await state.clear()
        return
    
    # Save promocode to state for later use
    await state.update_data(active_promocode_id=promocode.id, active_promocode_code=code)
    
    # Calculate discount preview
    if promocode.discount_type == 'percent':
        discount_text = f"{promocode.discount_value}% скидка"
    elif promocode.discount_type == 'fixed':
        discount_text = f"{promocode.discount_value} SOL скидка"
    else:
        discount_text = "Бесплатный товар"
    
    await message.answer(
        f"✅ **Промокод активирован!**\n\n"
        f"🎫 Код: **{code}**\n"
        f"💰 Скидка: {discount_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 Промокод будет применен при следующей покупке в каталоге!\n\n"
        f"Перейдите в: 🛍 Магазин → 🛍 Каталог товаров",
        parse_mode="Markdown"
    )
    await state.clear()


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, user: User, session: AsyncSession):
    """Return to profile menu."""
    from handlers.menu_handlers import show_profile_menu
    await show_profile_menu(callback.message, user, session)
    await callback.message.delete()

