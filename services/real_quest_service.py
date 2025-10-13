"""Real-life quest service for treasure hunt."""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import RealQuestTask, RealQuestPrize, UserRealQuest, User

logger = logging.getLogger(__name__)


class RealQuestService:
    """Service for managing real-life treasure hunt quest."""
    
    @staticmethod
    async def get_user_quest_progress(session: AsyncSession, user_id: int) -> UserRealQuest | None:
        """Get user's quest progress."""
        stmt = select(UserRealQuest).where(UserRealQuest.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def start_quest(session: AsyncSession, user_id: int) -> UserRealQuest:
        """Start quest for user."""
        # Check if user already has quest
        existing = await RealQuestService.get_user_quest_progress(session, user_id)
        if existing:
            return existing
        
        # Assign unclaimed prize
        prize = await RealQuestService._get_unclaimed_prize(session)
        if not prize:
            raise ValueError("No prizes available")
        
        # Create quest progress
        quest_progress = UserRealQuest(
            user_id=user_id,
            current_task=1,
            prize_id=prize.id,
            is_completed=False
        )
        session.add(quest_progress)
        await session.commit()
        await session.refresh(quest_progress)
        
        logger.info(f"User {user_id} started real quest, assigned prize {prize.id}")
        return quest_progress
    
    @staticmethod
    async def get_current_task(session: AsyncSession, user_id: int) -> dict | None:
        """Get current task for user."""
        progress = await RealQuestService.get_user_quest_progress(session, user_id)
        if not progress or progress.is_completed:
            return None
        
        stmt = select(RealQuestTask).where(
            RealQuestTask.task_number == progress.current_task,
            RealQuestTask.is_active == True
        )
        result = await session.execute(stmt)
        task = result.scalars().first()
        
        if not task:
            return None
        
        return {
            'task_number': task.task_number,
            'task_text_ru': task.task_text_ru,
            'task_text_en': task.task_text_en,
            'hint_ru': task.hint_ru,
            'hint_en': task.hint_en,
            'total_tasks': 20,
            'current_progress': progress.current_task
        }
    
    @staticmethod
    async def submit_code(session: AsyncSession, user_id: int, code: str) -> dict:
        """Submit code for current task."""
        progress = await RealQuestService.get_user_quest_progress(session, user_id)
        if not progress:
            return {'success': False, 'error': 'quest_not_started'}
        
        if progress.is_completed:
            return {'success': False, 'error': 'quest_already_completed'}
        
        # Get current task
        stmt = select(RealQuestTask).where(
            RealQuestTask.task_number == progress.current_task,
            RealQuestTask.is_active == True
        )
        result = await session.execute(stmt)
        task = result.scalars().first()
        
        if not task:
            return {'success': False, 'error': 'task_not_found'}
        
        # Check code
        if code.strip().lower() != task.correct_code.strip().lower():
            return {'success': False, 'error': 'incorrect_code'}
        
        # Move to next task
        progress.current_task += 1
        
        # Check if quest completed
        if progress.current_task > 20:
            progress.is_completed = True
            progress.completed_at = datetime.utcnow()
            
            # Mark prize as claimed
            if progress.prize_id:
                stmt_prize = select(RealQuestPrize).where(RealQuestPrize.id == progress.prize_id)
                result_prize = await session.execute(stmt_prize)
                prize = result_prize.scalars().first()
                if prize:
                    prize.is_claimed = True
                    prize.claimed_by = user_id
                    prize.claimed_at = datetime.utcnow()
            
            await session.commit()
            logger.info(f"User {user_id} completed real quest!")
            
            return {
                'success': True,
                'completed': True,
                'prize_id': progress.prize_id
            }
        
        await session.commit()
        logger.info(f"User {user_id} completed task {progress.current_task - 1}")
        
        return {
            'success': True,
            'completed': False,
            'next_task': progress.current_task
        }
    
    @staticmethod
    async def get_prize_info(session: AsyncSession, prize_id: int) -> RealQuestPrize | None:
        """Get prize information."""
        stmt = select(RealQuestPrize).where(RealQuestPrize.id == prize_id)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def _get_unclaimed_prize(session: AsyncSession) -> RealQuestPrize | None:
        """Get first unclaimed prize."""
        stmt = select(RealQuestPrize).where(RealQuestPrize.is_claimed == False).limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    # === ADMIN METHODS ===
    
    @staticmethod
    async def get_all_tasks(session: AsyncSession) -> list[RealQuestTask]:
        """Get all tasks (for admin)."""
        stmt = select(RealQuestTask).order_by(RealQuestTask.task_number)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_task_by_number(session: AsyncSession, task_number: int) -> RealQuestTask | None:
        """Get task by number."""
        stmt = select(RealQuestTask).where(RealQuestTask.task_number == task_number)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def create_task(
        session: AsyncSession,
        task_number: int,
        task_text_ru: str,
        task_text_en: str,
        correct_code: str,
        hint_ru: str = None,
        hint_en: str = None
    ) -> RealQuestTask:
        """Create new task."""
        task = RealQuestTask(
            task_number=task_number,
            task_text_ru=task_text_ru,
            task_text_en=task_text_en,
            correct_code=correct_code,
            hint_ru=hint_ru,
            hint_en=hint_en,
            is_active=True
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        logger.info(f"Real quest task {task_number} created")
        return task
    
    @staticmethod
    async def update_task(
        session: AsyncSession,
        task_id: int,
        **kwargs
    ) -> bool:
        """Update task fields."""
        stmt = update(RealQuestTask).where(RealQuestTask.id == task_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Real quest task {task_id} updated: {kwargs}")
        return True
    
    @staticmethod
    async def delete_task(session: AsyncSession, task_id: int) -> bool:
        """Delete task."""
        stmt = select(RealQuestTask).where(RealQuestTask.id == task_id)
        result = await session.execute(stmt)
        task = result.scalars().first()
        if task:
            await session.delete(task)
            await session.commit()
            logger.info(f"Real quest task {task_id} deleted")
            return True
        return False
    
    @staticmethod
    async def get_all_prizes(session: AsyncSession) -> list[RealQuestPrize]:
        """Get all prizes (for admin)."""
        stmt = select(RealQuestPrize).order_by(RealQuestPrize.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def create_prize(
        session: AsyncSession,
        prize_name: str,
        prize_description: str,
        pickup_location: str,
        prize_image_file_id: str = None
    ) -> RealQuestPrize:
        """Create new prize."""
        prize = RealQuestPrize(
            prize_name=prize_name,
            prize_description=prize_description,
            pickup_location=pickup_location,
            prize_image_file_id=prize_image_file_id,
            is_claimed=False
        )
        session.add(prize)
        await session.commit()
        await session.refresh(prize)
        logger.info(f"Real quest prize created: {prize_name} (ID: {prize.id})")
        return prize
    
    @staticmethod
    async def update_prize(
        session: AsyncSession,
        prize_id: int,
        **kwargs
    ) -> bool:
        """Update prize fields."""
        stmt = update(RealQuestPrize).where(RealQuestPrize.id == prize_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Real quest prize {prize_id} updated: {kwargs}")
        return True
    
    @staticmethod
    async def delete_prize(session: AsyncSession, prize_id: int) -> bool:
        """Delete prize."""
        stmt = select(RealQuestPrize).where(RealQuestPrize.id == prize_id)
        result = await session.execute(stmt)
        prize = result.scalars().first()
        if prize:
            await session.delete(prize)
            await session.commit()
            logger.info(f"Real quest prize {prize_id} deleted")
            return True
        return False
    
    @staticmethod
    async def get_quest_statistics(session: AsyncSession) -> dict:
        """Get quest statistics."""
        stmt_total = select(func.count(UserRealQuest.id))
        result_total = await session.execute(stmt_total)
        total_participants = result_total.scalar()
        
        stmt_completed = select(func.count(UserRealQuest.id)).where(UserRealQuest.is_completed == True)
        result_completed = await session.execute(stmt_completed)
        completed = result_completed.scalar()
        
        stmt_prizes = select(func.count(RealQuestPrize.id))
        result_prizes = await session.execute(stmt_prizes)
        total_prizes = result_prizes.scalar()
        
        stmt_claimed = select(func.count(RealQuestPrize.id)).where(RealQuestPrize.is_claimed == True)
        result_claimed = await session.execute(stmt_claimed)
        claimed_prizes = result_claimed.scalar()
        
        return {
            'total_participants': total_participants,
            'completed_quests': completed,
            'total_prizes': total_prizes,
            'claimed_prizes': claimed_prizes,
            'available_prizes': total_prizes - claimed_prizes
        }


# Global instance
real_quest_service = RealQuestService()

