"""Quest handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.quest_service import quest_service

logger = logging.getLogger(__name__)

router = Router(name='quest_handlers')


@router.message(Command("quests"))
async def show_quests(message: Message, user: User, session: AsyncSession):
    """Show active quests and user progress."""
    # Get quests
    quests = await quest_service.get_user_quests(session, user.id)
    
    if not quests:
        text = """
🎯 **Квесты и челленджи**

📭 Сейчас нет активных квестов

━━━━━━━━━━━━━━━━━━━━

💡 **Что такое квесты?**
Выполняй задания и получай награды!

Примеры:
• Купи 3 товара за неделю → бонус
• Потрать 0.5 SOL → награда
• Пригласи 5 друзей → приз

🔔 Следи за обновлениями!
        """
        await message.answer(text, parse_mode="Markdown")
        return
    
    text = "🎯 **Активные квесты**\n\n"
    
    active_count = 0
    completed_count = 0
    
    for q in quests:
        quest = q['quest']
        progress = q['progress']
        completed = q['completed']
        
        if completed:
            completed_count += 1
            status_icon = "✅"
            progress_text = f"**Выполнено!**"
        else:
            active_count += 1
            status_icon = "🔄"
            progress_percent = min(100, int(progress / quest.condition_value * 100))
            progress_text = f"Прогресс: **{progress}/{quest.condition_value}** ({progress_percent}%)"
        
        text += f"{status_icon} **{quest.name_ru}**\n"
        text += f"   _{quest.description_ru}_\n"
        text += f"   {progress_text}\n"
        
        # Format reward
        if quest.reward_type == 'sol':
            reward_text = f"{quest.reward_value} EUR"
        elif quest.reward_type == 'points':
            reward_text = f"{int(quest.reward_value)} баллов"
        else:
            reward_text = quest.reward_value
        
        text += f"   🎁 Награда: {reward_text}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"📊 Активных: **{active_count}** | Выполнено: **{completed_count}**"
    
    # Add buttons for roulette, real quest, and daily bonus
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🎰 Колесо рулетки", callback_data="roulette_spin")
    builder.button(text="🗺 Квест поиска", callback_data="real_quest_menu")
    builder.button(text="🎁 Ежедневный бонус", callback_data="daily_bonus_menu")
    builder.adjust(1)
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(F.text == "🎯 Квесты")
async def quests_button_handler(message: Message, user: User, session: AsyncSession):
    """Handle quests button press."""
    await show_quests(message, user, session)

