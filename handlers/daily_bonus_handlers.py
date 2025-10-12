"""Daily bonus handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.daily_bonus_service import daily_bonus_service

logger = logging.getLogger(__name__)

router = Router(name='daily_bonus_handlers')


@router.message(Command("daily"))
async def claim_daily_bonus(message: Message, user: User, session: AsyncSession):
    """Claim daily bonus."""
    # Get status first
    status = await daily_bonus_service.get_daily_bonus_status(session, user.id)
    
    if not status['can_claim']:
        text = f"""
🎁 **Ежедневный бонус**

⏰ Уже получен сегодня!

Следующий бонус через: **{status['hours_until_next']} часов**

🔥 Текущая серия: **{status['streak']} дней**
💎 Баллов: **{status['points']}**

━━━━━━━━━━━━━━━━━━━━

💡 **Как это работает:**
• Заходи каждый день
• Получай баллы
• Серия растет → бонус больше!

🎯 За 7 дней подряд - достижение!
        """
        await message.answer(text, parse_mode="Markdown")
        return
    
    # Claim bonus
    result = await daily_bonus_service.claim_daily_bonus(session, user.id)
    
    if result['success']:
        streak_emoji = "🔥" if result['streak'] >= 7 else "✨"
        text = f"""
✅ **Ежедневный бонус получен!**

{streak_emoji} **+{result['points']} баллов!**

🔥 Серия: **{result['streak']} дней**

━━━━━━━━━━━━━━━━━━━━

💡 Продолжай заходить каждый день:
• 1-6 дней: +10 баллов
• 7-13 дней: +15 баллов  
• 14-20 дней: +20 баллов
• 21+ дней: +35 баллов

🏆 Серия 7 дней = достижение!
🏆 Серия 30 дней = особое достижение!
        """
    else:
        text = f"❌ {result['message']}"
    
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "🎁 Ежедневный бонус")
async def daily_bonus_button_handler(message: Message, user: User, session: AsyncSession):
    """Handle daily bonus button press."""
    await claim_daily_bonus(message, user, session)

