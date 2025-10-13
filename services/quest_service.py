"""Quest and challenge service."""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Quest, UserQuest, User

logger = logging.getLogger(__name__)


class QuestService:
    """Service for managing quests and challenges."""
    
    @staticmethod
    async def get_active_quests(session: AsyncSession) -> list[Quest]:
        """Get all active quests."""
        now = datetime.utcnow()
        stmt = select(Quest).where(
            Quest.is_active == True,
            Quest.starts_at <= now,
            Quest.ends_at > now
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_user_quests(session: AsyncSession, user_id: int) -> list[dict]:
        """Get user's quest progress."""
        active_quests = await QuestService.get_active_quests(session)
        
        # Get user quest progress
        stmt = select(UserQuest).where(UserQuest.user_id == user_id)
        result = await session.execute(stmt)
        user_quests = {uq.quest_id: uq for uq in result.scalars().all()}
        
        result_list = []
        for quest in active_quests:
            user_quest = user_quests.get(quest.id)
            result_list.append({
                'quest': quest,
                'progress': user_quest.progress if user_quest else 0,
                'completed': user_quest.completed if user_quest else False
            })
        
        return result_list
    
    @staticmethod
    async def update_quest_progress(
        session: AsyncSession,
        user_id: int,
        condition_type: str,  # purchases, spending, items
        value: float
    ):
        """Update user's quest progress."""
        active_quests = await QuestService.get_active_quests(session)
        
        for quest in active_quests:
            if quest.condition_type != condition_type:
                continue
            
            # Get or create user quest
            stmt = select(UserQuest).where(
                UserQuest.user_id == user_id,
                UserQuest.quest_id == quest.id
            )
            result = await session.execute(stmt)
            user_quest = result.scalars().first()
            
            if not user_quest:
                user_quest = UserQuest(
                    user_id=user_id,
                    quest_id=quest.id,
                    progress=0
                )
                session.add(user_quest)
            
            if user_quest.completed:
                continue  # Already completed
            
            # Update progress
            user_quest.progress += int(value)
            
            # Check completion
            if user_quest.progress >= quest.condition_value:
                user_quest.completed = True
                user_quest.completed_at = datetime.utcnow()
                
                # Give reward
                await QuestService._give_reward(session, user_id, quest)
                logger.info(f"User {user_id} completed quest {quest.id}")
        
        await session.commit()
    
    @staticmethod
    async def _give_reward(session: AsyncSession, user_id: int, quest: Quest):
        """Give quest reward to user."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return
        
        if quest.reward_type == 'sol':
            user.balance_eur += quest.reward_value
        elif quest.reward_type == 'points':
            user.achievement_points += int(quest.reward_value)
        elif quest.reward_type == 'promocode':
            # Create personal promocode for user
            pass  # Can implement later
        
        logger.info(f"Quest reward given to user {user_id}: {quest.reward_type} = {quest.reward_value}")
    
    # === ADMIN METHODS ===
    
    @staticmethod
    async def get_all_quests(session: AsyncSession) -> list[Quest]:
        """Get all quests (for admin)."""
        stmt = select(Quest).order_by(Quest.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_quest_by_id(session: AsyncSession, quest_id: int) -> Quest | None:
        """Get quest by ID."""
        stmt = select(Quest).where(Quest.id == quest_id)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def create_quest(
        session: AsyncSession,
        name_ru: str,
        name_en: str,
        description_ru: str,
        description_en: str,
        quest_type: str,
        condition_type: str,
        condition_value: int,
        reward_type: str,
        reward_value: float,
        starts_at: datetime,
        ends_at: datetime
    ) -> Quest:
        """Create new quest."""
        quest = Quest(
            name_ru=name_ru,
            name_en=name_en,
            description_ru=description_ru,
            description_en=description_en,
            quest_type=quest_type,
            condition_type=condition_type,
            condition_value=condition_value,
            reward_type=reward_type,
            reward_value=reward_value,
            starts_at=starts_at,
            ends_at=ends_at,
            is_active=True
        )
        session.add(quest)
        await session.commit()
        await session.refresh(quest)
        logger.info(f"Quest created: {quest.name_ru} (ID: {quest.id})")
        return quest
    
    @staticmethod
    async def update_quest(
        session: AsyncSession,
        quest_id: int,
        **kwargs
    ) -> bool:
        """Update quest fields."""
        stmt = update(Quest).where(Quest.id == quest_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Quest {quest_id} updated: {kwargs}")
        return True
    
    @staticmethod
    async def delete_quest(session: AsyncSession, quest_id: int) -> bool:
        """Delete quest."""
        quest = await QuestService.get_quest_by_id(session, quest_id)
        if quest:
            await session.delete(quest)
            await session.commit()
            logger.info(f"Quest {quest_id} deleted")
            return True
        return False
    
    @staticmethod
    async def toggle_quest_status(session: AsyncSession, quest_id: int) -> bool:
        """Toggle quest active status."""
        quest = await QuestService.get_quest_by_id(session, quest_id)
        if quest:
            quest.is_active = not quest.is_active
            await session.commit()
            logger.info(f"Quest {quest_id} status toggled to {quest.is_active}")
            return True
        return False


# Global instance
quest_service = QuestService()

