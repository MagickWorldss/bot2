"""Achievement handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.achievement_service import achievement_service

logger = logging.getLogger(__name__)

router = Router(name='achievement_handlers')


@router.message(Command("achievements"))
async def show_achievements(message: Message, user: User, session: AsyncSession):
    """Show user's achievements."""
    # Get achievements
    ach_data = await achievement_service.get_user_achievements(session, user.id)
    
    text = f"""
🏆 **Достижения**

📊 Открыто: **{ach_data['unlocked_count']}/{ach_data['total']}**
💎 Баллов: **{user.achievement_points}**

━━━━━━━━━━━━━━━━━━━━

**Твои достижения:**

"""
    
    # Sort achievements
    unlocked = []
    locked = []
    
    for ach in ach_data['all']:
        if ach.id in ach_data['unlocked_ids']:
            unlocked.append(ach)
        else:
            locked.append(ach)
    
    # Show unlocked
    if unlocked:
        for ach in unlocked:
            text += f"✅ {ach.icon} **{ach.name_ru}**\n"
            text += f"   _{ach.description_ru}_ (+{ach.points} баллов)\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "**Еще не открыто:**\n\n"
    
    # Show locked
    if locked:
        for ach in locked:
            text += f"🔒 {ach.icon} {ach.name_ru}\n"
            text += f"   _{ach.description_ru}_ (+{ach.points} баллов)\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "🎯 Выполняй действия и открывай достижения!"
    
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "🏆 Достижения")
async def achievements_button_handler(message: Message, user: User, session: AsyncSession):
    """Handle achievements button press."""
    await show_achievements(message, user, session)

