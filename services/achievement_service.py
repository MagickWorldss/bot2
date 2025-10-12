"""Achievement service."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Achievement, UserAchievement, User

logger = logging.getLogger(__name__)


class AchievementService:
    """Service for managing achievements."""
    
    @staticmethod
    async def check_and_unlock_achievements(session: AsyncSession, user_id: int):
        """Check and unlock new achievements for user."""
        # Get user stats
        stmt = select(
            User.total_purchases,
            User.total_spent_sol,
            User.total_referrals,
            User.daily_streak
        ).where(User.id == user_id)
        result = await session.execute(stmt)
        user_stats = result.one_or_none()
        
        if not user_stats:
            return
        
        purchases, spent, referrals, streak = user_stats
        
        # Get all achievements
        stmt = select(Achievement)
        result = await session.execute(stmt)
        all_achievements = result.scalars().all()
        
        # Get already unlocked achievements
        stmt = select(Achievement.id).join(UserAchievement).where(
            UserAchievement.user_id == user_id
        )
        result = await session.execute(stmt)
        unlocked_ids = set(result.scalars().all())
        
        # Check each achievement
        newly_unlocked = []
        for ach in all_achievements:
            if ach.id in unlocked_ids:
                continue  # Already unlocked
            
            # Check condition
            should_unlock = False
            if ach.condition_type == 'purchases':
                should_unlock = purchases >= ach.condition_value
            elif ach.condition_type == 'spending':
                should_unlock = spent >= ach.condition_value
            elif ach.condition_type == 'referrals':
                should_unlock = referrals >= ach.condition_value
            elif ach.condition_type == 'streak':
                should_unlock = streak >= ach.condition_value
            
            if should_unlock:
                # Unlock achievement
                user_ach = UserAchievement(user_id=user_id, achievement_id=ach.id)
                session.add(user_ach)
                
                # Give points
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                user = result.scalars().first()
                if user:
                    user.achievement_points += ach.points
                
                newly_unlocked.append(ach)
                logger.info(f"User {user_id} unlocked achievement: {ach.code}")
        
        await session.commit()
        return newly_unlocked
    
    @staticmethod
    async def get_user_achievements(session: AsyncSession, user_id: int) -> dict:
        """Get user's achievements."""
        # Get all achievements
        stmt = select(Achievement)
        result = await session.execute(stmt)
        all_achievements = list(result.scalars().all())
        
        # Get unlocked achievement IDs
        stmt = select(Achievement.id).join(UserAchievement).where(
            UserAchievement.user_id == user_id
        )
        result = await session.execute(stmt)
        unlocked_ids = set(result.scalars().all())
        
        return {
            'all': all_achievements,
            'unlocked_ids': unlocked_ids,
            'total': len(all_achievements),
            'unlocked_count': len(unlocked_ids)
        }
    
    @staticmethod
    async def init_default_achievements(session: AsyncSession):
        """Initialize default achievements."""
        achievements = [
            {
                'code': 'first_purchase',
                'name_ru': '🎉 Первая покупка',
                'name_en': '🎉 First Purchase',
                'description_ru': 'Совершите первую покупку',
                'description_en': 'Make your first purchase',
                'icon': '🎉',
                'points': 10,
                'condition_type': 'purchases',
                'condition_value': 1
            },
            {
                'code': 'buyer_10',
                'name_ru': '⭐ 10 покупок',
                'name_en': '⭐ 10 Purchases',
                'description_ru': 'Совершите 10 покупок',
                'description_en': 'Make 10 purchases',
                'icon': '⭐',
                'points': 50,
                'condition_type': 'purchases',
                'condition_value': 10
            },
            {
                'code': 'buyer_50',
                'name_ru': '🌟 50 покупок',
                'name_en': '🌟 50 Purchases',
                'description_ru': 'Совершите 50 покупок',
                'description_en': 'Make 50 purchases',
                'icon': '🌟',
                'points': 200,
                'condition_type': 'purchases',
                'condition_value': 50
            },
            {
                'code': 'spender_100',
                'name_ru': '💰 Потратил €100',
                'name_en': '💰 Spent €100',
                'description_ru': 'Потратьте €100',
                'description_en': 'Spend €100',
                'icon': '💰',
                'points': 100,
                'condition_type': 'spending',
                'condition_value': 1  # 1 SOL ≈ €150 (adjust)
            },
            {
                'code': 'referrer',
                'name_ru': '🎁 Пригласил друга',
                'name_en': '🎁 Invited a Friend',
                'description_ru': 'Пригласите первого друга',
                'description_en': 'Invite your first friend',
                'icon': '🎁',
                'points': 50,
                'condition_type': 'referrals',
                'condition_value': 1
            },
            {
                'code': 'referrer_10',
                'name_ru': '👥 10 рефералов',
                'name_en': '👥 10 Referrals',
                'description_ru': 'Пригласите 10 друзей',
                'description_en': 'Invite 10 friends',
                'icon': '👥',
                'points': 200,
                'condition_type': 'referrals',
                'condition_value': 10
            },
            {
                'code': 'streak_7',
                'name_ru': '🔥 7 дней подряд',
                'name_en': '🔥 7 Day Streak',
                'description_ru': 'Заходите 7 дней подряд',
                'description_en': 'Login 7 days in a row',
                'icon': '🔥',
                'points': 70,
                'condition_type': 'streak',
                'condition_value': 7
            },
            {
                'code': 'streak_30',
                'name_ru': '🏆 30 дней подряд',
                'name_en': '🏆 30 Day Streak',
                'description_ru': 'Заходите 30 дней подряд',
                'description_en': 'Login 30 days in a row',
                'icon': '🏆',
                'points': 300,
                'condition_type': 'streak',
                'condition_value': 30
            }
        ]
        
        for ach_data in achievements:
            # Check if exists
            stmt = select(Achievement).where(Achievement.code == ach_data['code'])
            result = await session.execute(stmt)
            existing = result.scalars().first()
            
            if not existing:
                ach = Achievement(**ach_data)
                session.add(ach)
        
        await session.commit()
        logger.info("Default achievements initialized")


# Global instance
achievement_service = AchievementService()

