"""Quiz handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.quiz_service import quiz_service

logger = logging.getLogger(__name__)

router = Router(name='quiz_handlers')


@router.message(Command("quiz"))
async def start_quiz(message: Message, user: User, session: AsyncSession):
    """Start a random quiz."""
    # Get random quiz
    quiz = await quiz_service.get_random_quiz(session, user.id)
    
    if not quiz:
        # Get stats
        stats = await quiz_service.get_user_quiz_stats(session, user.id)
        
        text = f"""
🧩 **Квизы и загадки**

📭 Ты ответил на все доступные вопросы!

━━━━━━━━━━━━━━━━━━━━

📊 **Твоя статистика:**
├ Всего ответов: **{stats['total_answered']}**
├ Правильных: **{stats['correct_answers']}**
└ Точность: **{stats['accuracy']:.1f}%**

🔔 Ждите новых вопросов!
        """
        await message.answer(text, parse_mode="Markdown")
        return
    
    # Show quiz
    difficulty_emoji = {"easy": "😊", "medium": "🤔", "hard": "🧠"}
    
    text = f"""
🧩 **Квиз**

{difficulty_emoji.get(quiz.difficulty, '🤔')} Сложность: **{quiz.difficulty.upper()}**

━━━━━━━━━━━━━━━━━━━━

**Вопрос:**
{quiz.question_ru}

━━━━━━━━━━━━━━━━━━━━

🎁 Награда за правильный ответ: **{quiz.reward_value}** {'SOL' if quiz.reward_type == 'sol' else 'баллов'}
    """
    
    # Build answer buttons
    builder = InlineKeyboardBuilder()
    
    answers = quiz.answers if isinstance(quiz.answers, list) else []
    for idx, answer in enumerate(answers):
        builder.button(text=answer, callback_data=f"quiz_answer_{quiz.id}_{idx}")
    
    builder.adjust(1)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("quiz_answer_"))
async def submit_quiz_answer(callback: CallbackQuery, user: User, session: AsyncSession):
    """Submit quiz answer."""
    parts = callback.data.split("_")
    quiz_id = int(parts[2])
    answer_idx = int(parts[3])
    
    # Submit answer
    is_correct, message_text, reward = await quiz_service.submit_answer(
        session, quiz_id, user.id, answer_idx
    )
    
    if is_correct:
        text = f"""
✅ **Правильно!**

{message_text}

🎉 Отличная работа!

━━━━━━━━━━━━━━━━━━━━

💡 Хочешь ещё? Используй /quiz
        """
    else:
        text = f"""
❌ **Неправильно!**

Правильный ответ был другим.

💪 Не сдавайся! Попробуй ещё раз с другим вопросом.

━━━━━━━━━━━━━━━━━━━━

🎯 Используй /quiz для следующего вопроса
        """
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == "🧩 Квиз")
async def quiz_button_handler(message: Message, user: User, session: AsyncSession):
    """Handle quiz button press."""
    await start_quiz(message, user, session)

