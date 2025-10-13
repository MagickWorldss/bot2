"""Roulette wheel handlers."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.roulette_service import RouletteService
from utils.keyboards import quests_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "roulette_spin")
async def roulette_spin(callback: CallbackQuery, user: User, session: AsyncSession):
    """Spin the roulette wheel."""
    # Check if user can spin today
    can_spin = await RouletteService.can_spin_today(session, user.id)
    
    if not can_spin:
        await callback.message.edit_text(
            "🎰 **Колесо рулетки**\n\n"
            "❌ Вы уже крутили колесо сегодня!\n\n"
            "Возвращайтесь завтра за новым призом! 🎁",
            reply_markup=quests_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("❌ Уже использовано сегодня")
        return
    
    # Spin the wheel
    result = await RouletteService.spin_wheel(session, user.id)
    
    if not result['success']:
        error_messages = {
            'no_prizes': "😔 К сожалению, сейчас нет доступных призов. Попробуйте позже!",
            'already_spun_today': "❌ Вы уже крутили колесо сегодня!"
        }
        error_msg = error_messages.get(result.get('error'), "❌ Произошла ошибка")
        
        await callback.message.edit_text(
            f"🎰 **Колесо рулетки**\n\n{error_msg}",
            reply_markup=quests_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("❌ Ошибка")
        return
    
    # Format prize message
    prize_name = result['prize_name']
    prize_type = result['prize_type']
    prize_value = result['prize_value']
    
    prize_emoji = {
        'eur': '💶',
        'points': '⭐',
        'promocode': '🎟',
        'nothing': '😔'
    }
    
    prize_text = {
        'eur': f"💶 **{prize_value} EUR** добавлено на ваш баланс!",
        'points': f"⭐ **{int(prize_value)} баллов** добавлено!",
        'promocode': f"🎟 **Промокод**: {prize_value}",
        'nothing': "😔 К сожалению, в этот раз ничего не выпало. Попробуйте завтра!"
    }
    
    emoji = prize_emoji.get(prize_type, '🎁')
    text = prize_text.get(prize_type, f"🎁 {prize_name}")
    
    await callback.message.edit_text(
        f"🎰 **Колесо рулетки**\n\n"
        f"🎉 **Поздравляем!**\n\n"
        f"{emoji} Вы выиграли: **{prize_name}**\n\n"
        f"{text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 Возвращайтесь завтра за новым призом!",
        reply_markup=quests_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer(f"🎉 Выиграли: {prize_name}!")
    
    logger.info(f"User {user.id} won roulette prize: {prize_name}")


@router.callback_query(F.data == "roulette_history")
async def roulette_history(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show user's roulette spin history."""
    history = await RouletteService.get_user_spin_history(session, user.id, limit=10)
    
    if not history:
        await callback.message.edit_text(
            "🎰 **История рулетки**\n\n"
            "📭 У вас пока нет истории вращений.\n\n"
            "Крутите колесо каждый день и выигрывайте призы!",
            reply_markup=quests_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    text = "🎰 **История рулетки**\n\n"
    text += "Последние 10 вращений:\n\n"
    
    for spin in history:
        date = spin.created_at.strftime("%d.%m.%Y")
        text += f"• {date} - {spin.prize_won}\n"
    
    text += f"\n━━━━━━━━━━━━━━━━━━━━\n"
    text += f"\n📊 Всего вращений: {len(history)}"
    
    await callback.message.edit_text(
        text,
        reply_markup=quests_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

