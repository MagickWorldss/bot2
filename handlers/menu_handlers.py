"""Menu navigation handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from utils.keyboards import quests_menu_keyboard, profile_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name='menu_handlers')


@router.message(F.text == "🎯 Квесты")
async def show_quests_menu(message: Message):
    """Show quests menu."""
    text = """
🎯 **Квесты и активности**

Выберите раздел:

🎁 **Ежедневный бонус** - получай баллы каждый день
🎯 **Квесты** - выполняй задания, получай награды
🧩 **Квиз** - отвечай на вопросы, зарабатывай баллы
🎰 **Колесо фортуны** - испытай удачу!

━━━━━━━━━━━━━━━━━━━━

💡 Все активности дают баллы!
Баллы можно потратить в магазине "🎁 Стафф"
    """
    
    await message.answer(text, reply_markup=quests_menu_keyboard(), parse_mode="Markdown")


@router.message(F.text == "👤 Профиль")
async def show_profile_menu(message: Message, user: User, session: AsyncSession):
    """Show profile menu."""
    from services.price_service import price_service
    balance_eur = await price_service.sol_to_eur(user.balance_sol)
    
    text = f"""
👤 **Ваш профиль**

👋 {user.first_name or 'Пользователь'}
🆔 ID: `{user.id}`

💶 Баланс: {price_service.format_eur(balance_eur)}
✨ Баллы: **{user.achievement_points}**

━━━━━━━━━━━━━━━━━━━━

Выберите раздел:

💰 **Мой баланс** - пополнить, посмотреть
🎁 **Реферальная программа** - приглашай друзей
🏆 **Достижения** - твои ачивки
📜 **История покупок** - что купил
🌐 **Язык** - изменить язык бота
    """
    
    await message.answer(text, reply_markup=profile_menu_keyboard(), parse_mode="Markdown")


# Callbacks for quests menu
@router.callback_query(F.data == "daily_bonus_menu")
async def daily_bonus_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle daily bonus from menu."""
    from handlers.daily_bonus_handlers import claim_daily_bonus
    await claim_daily_bonus(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "quests_menu")
async def quests_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle quests from menu."""
    from handlers.quest_handlers import show_quests
    await show_quests(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "quiz_menu")
async def quiz_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle quiz from menu."""
    from handlers.quiz_handlers import start_quiz
    await start_quiz(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "fortune_wheel")
async def fortune_wheel_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Fortune wheel - spin for random reward."""
    import random
    from services.daily_bonus_service import daily_bonus_service
    
    # Check if can spin (once per day, like daily bonus)
    status = await daily_bonus_service.get_daily_bonus_status(session, user.id)
    
    if not status['can_claim']:
        await callback.answer(
            f"🎰 Колесо уже было крутнуто сегодня!\n"
            f"Следующая попытка через {status['hours_until_next']} часов",
            show_alert=True
        )
        return
    
    # Spin wheel - random reward
    rewards = [
        {'type': 'points', 'value': 5, 'text': '✨ 5 баллов', 'emoji': '✨'},
        {'type': 'points', 'value': 10, 'text': '💎 10 баллов', 'emoji': '💎'},
        {'type': 'points', 'value': 25, 'text': '⭐ 25 баллов', 'emoji': '⭐'},
        {'type': 'points', 'value': 50, 'text': '🌟 50 баллов', 'emoji': '🌟'},
        {'type': 'points', 'value': 100, 'text': '🎉 100 баллов!', 'emoji': '🎉'},
        {'type': 'nothing', 'value': 0, 'text': '😅 Ничего', 'emoji': '😅'},
    ]
    
    # Weighted random
    weights = [30, 25, 20, 15, 5, 5]  # 5% chance for 100 points
    reward = random.choices(rewards, weights=weights)[0]
    
    # Give reward
    if reward['type'] == 'points' and reward['value'] > 0:
        from sqlalchemy import update
        from database.models import User as UserModel
        stmt = update(UserModel).where(UserModel.id == user.id).values(
            achievement_points=UserModel.achievement_points + reward['value']
        )
        await session.execute(stmt)
        await session.commit()
    
    # Mark as used (use daily bonus timestamp)
    from datetime import datetime
    stmt = update(UserModel).where(UserModel.id == user.id).values(
        last_daily_bonus=datetime.utcnow()
    )
    await session.execute(stmt)
    await session.commit()
    
    text = f"""
🎰 **Колесо фортуны**

🎲 Крутим колесо...

━━━━━━━━━━━━━━━━━━━━

{reward['emoji']} **{reward['text']}!**

━━━━━━━━━━━━━━━━━━━━

💫 Возвращайтесь завтра за новым вращением!
    """
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer(f"{reward['emoji']} {reward['text']}!", show_alert=True)


# Callbacks for profile menu
@router.callback_query(F.data == "my_balance")
async def my_balance_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show balance from menu."""
    from handlers.user_handlers import show_balance_redirect
    await show_balance_redirect(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "referral_menu")
async def referral_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show referral from menu."""
    from handlers.referral_handlers import show_referral_info
    await show_referral_info(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "achievements_menu")
async def achievements_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show achievements from menu."""
    from handlers.achievement_handlers import show_achievements
    await show_achievements(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "purchase_history_menu")
async def purchase_history_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show purchase history from menu."""
    from handlers.catalog_handlers import show_purchase_history
    await show_purchase_history(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "language_menu")
async def language_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show language selection from menu."""
    from services.language_service import language_service
    from utils.language_keyboards import language_selection_keyboard
    
    lang = await language_service.get_user_language(session, user.id)
    
    await callback.message.edit_text(
        language_service.get_text(lang, 'select_language'),
        reply_markup=language_selection_keyboard()
    )
    await callback.answer()

