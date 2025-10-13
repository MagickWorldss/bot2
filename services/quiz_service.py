"""Quiz and riddle service."""
import logging
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Quiz, UserQuiz, User

logger = logging.getLogger(__name__)


class QuizService:
    """Service for managing quizzes and riddles."""
    
    @staticmethod
    async def get_random_quiz(session: AsyncSession, user_id: int) -> Quiz | None:
        """Get a random quiz that user hasn't answered yet."""
        # Get all active quizzes
        stmt = select(Quiz).where(Quiz.is_active == True)
        result = await session.execute(stmt)
        all_quizzes = list(result.scalars().all())
        
        if not all_quizzes:
            return None
        
        # Get quizzes user already answered
        stmt = select(UserQuiz.quiz_id).where(UserQuiz.user_id == user_id)
        result = await session.execute(stmt)
        answered_ids = set(result.scalars().all())
        
        # Filter unanswered
        unanswered = [q for q in all_quizzes if q.id not in answered_ids]
        
        if not unanswered:
            return None  # User answered all quizzes
        
        return random.choice(unanswered)
    
    @staticmethod
    async def submit_answer(
        session: AsyncSession,
        quiz_id: int,
        user_id: int,
        answer_index: int
    ) -> tuple[bool, str, float]:
        """
        Submit answer to quiz.
        Returns: (is_correct, message, reward_amount)
        """
        # Get quiz
        stmt = select(Quiz).where(Quiz.id == quiz_id)
        result = await session.execute(stmt)
        quiz = result.scalars().first()
        
        if not quiz:
            return False, "❌ Квиз не найден", 0.0
        
        # Check if already answered
        stmt = select(UserQuiz).where(
            UserQuiz.user_id == user_id,
            UserQuiz.quiz_id == quiz_id
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            return False, "❌ Вы уже отвечали на этот вопрос", 0.0
        
        # Check answer
        is_correct = answer_index == quiz.correct_answer_index
        
        # Record attempt
        user_quiz = UserQuiz(
            user_id=user_id,
            quiz_id=quiz_id,
            is_correct=is_correct
        )
        session.add(user_quiz)
        
        reward = 0.0
        if is_correct:
            # Give reward
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if user:
                if quiz.reward_type == 'sol':
                    user.balance_eur += quiz.reward_value
                    reward = quiz.reward_value
                elif quiz.reward_type == 'points':
                    user.achievement_points += int(quiz.reward_value)
                    reward = quiz.reward_value
            
            await session.commit()
            logger.info(f"User {user_id} answered quiz {quiz_id} correctly, reward: {reward}")
            return True, f"✅ Правильно! Награда: {reward} {'SOL' if quiz.reward_type == 'sol' else 'баллов'}", reward
        else:
            await session.commit()
            logger.info(f"User {user_id} answered quiz {quiz_id} incorrectly")
            return False, "❌ Неправильный ответ!", 0.0
    
    @staticmethod
    async def create_quiz(
        session: AsyncSession,
        question_ru: str,
        question_en: str,
        answers: list[str],
        correct_answer_index: int,
        reward_type: str,  # sol, points, promocode
        reward_value: float,
        difficulty: str = 'medium'
    ) -> Quiz:
        """Create a new quiz."""
        quiz = Quiz(
            question_ru=question_ru,
            question_en=question_en,
            answers=answers,
            correct_answer_index=correct_answer_index,
            reward_type=reward_type,
            reward_value=reward_value,
            difficulty=difficulty,
            is_active=True
        )
        session.add(quiz)
        await session.commit()
        await session.refresh(quiz)
        logger.info(f"Quiz created: {question_ru[:50]}")
        return quiz
    
    @staticmethod
    async def get_user_quiz_stats(session: AsyncSession, user_id: int) -> dict:
        """Get user's quiz statistics."""
        stmt = select(UserQuiz).where(UserQuiz.user_id == user_id)
        result = await session.execute(stmt)
        all_attempts = list(result.scalars().all())
        
        total = len(all_attempts)
        correct = sum(1 for a in all_attempts if a.is_correct)
        
        return {
            'total_answered': total,
            'correct_answers': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0
        }


# Global instance
quiz_service = QuizService()

