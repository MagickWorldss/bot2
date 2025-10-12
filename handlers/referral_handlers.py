"""Referral system handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.referral_service import referral_service
from services.price_service import price_service

logger = logging.getLogger(__name__)

router = Router(name='referral_handlers')


@router.message(Command("referral"))
async def show_referral_info(message: Message, user: User, session: AsyncSession):
    """Show referral system information and user's referral link."""
    # Get referral link
    bot_info = await message.bot.get_me()
    referral_link = await referral_service.get_referral_link(session, user.id, bot_info.username)
    
    # Get stats
    stats = await referral_service.get_referral_stats(session, user.id)
    
    # ВАЖНО: total_earnings_sol уже в EUR! НЕ КОНВЕРТИРУЕМ!
    earnings_eur = stats['total_earnings_sol']
    
    text = f"""
🎁 **Реферальная программа**

👥 Приглашай друзей и получай бонусы!

━━━━━━━━━━━━━━━━━━━━

📊 **Твоя статистика:**
├ Приглашено друзей: **{stats['total_referrals']}**
└ Заработано: **€{earnings_eur:.2f}**

━━━━━━━━━━━━━━━━━━━━

🔗 **Твоя реферальная ссылка:**
`{referral_link}`

━━━━━━━━━━━━━━━━━━━━

💰 **Как это работает:**

1️⃣ Отправь ссылку другу
2️⃣ Друг регистрируется по ссылке
3️⃣ Друг делает первую покупку
4️⃣ Ты получаешь **10% от суммы** на баланс!

━━━━━━━━━━━━━━━━━━━━

✨ **Преимущества:**
• Бонус зачисляется автоматически
• Без ограничений по количеству рефералов
• Деньги можно тратить на покупки

━━━━━━━━━━━━━━━━━━━━

🎯 Пригласи 10 друзей и получи достижение!
    """
    
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "🎁 Реферальная программа")
async def referral_button_handler(message: Message, user: User, session: AsyncSession):
    """Handle referral button press."""
    await show_referral_info(message, user, session)

