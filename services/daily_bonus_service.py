"""Daily bonus service."""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User

logger = logging.getLogger(__name__)


class DailyBonusService:
    """Service for daily bonus system."""
    
    DAILY_BONUS_POINTS = 10  # Base points for daily login
    STREAK_BONUS_MULTIPLIER = 1.5  # Multiplier per streak week
    
    @staticmethod
    async def claim_daily_bonus(session: AsyncSession, user_id: int) -> dict:
        """
        Claim daily bonus.
        Returns: {
            'success': bool,
            'points': int,
            'streak': int,
            'message': str
        }
        """
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        now = datetime.now(timezone.utc)
        last_claim = user.last_daily_bonus
        
        # Check if already claimed today
        if last_claim and (now - last_claim).days < 1:
            hours_left = 24 - (now - last_claim).seconds // 3600
            return {
                'success': False,
                'message': f'⏰ Следующий бонус через {hours_left} часов'
            }
        
        # Check streak
        if last_claim:
            days_since = (now - last_claim).days
            if days_since == 1:
                # Continue streak
                user.daily_streak += 1
            elif days_since > 1:
                # Streak broken
                user.daily_streak = 1
        else:
            # First claim
            user.daily_streak = 1
        
        # Calculate bonus
        streak_weeks = user.daily_streak // 7
        multiplier = 1 + (streak_weeks * DailyBonusService.STREAK_BONUS_MULTIPLIER)
        points = int(DailyBonusService.DAILY_BONUS_POINTS * multiplier)
        
        # Give bonus
        user.achievement_points += points
        user.last_daily_bonus = now
        
        await session.commit()
        logger.info(f"User {user_id} claimed daily bonus: {points} points, streak: {user.daily_streak}")
        
        return {
            'success': True,
            'points': points,
            'streak': user.daily_streak,
            'message': f'🎁 Получено {points} баллов! Серия: {user.daily_streak} дней'
        }
    
    @staticmethod
    async def get_daily_bonus_status(session: AsyncSession, user_id: int) -> dict:
        """Get daily bonus status for user."""
        stmt = select(
            User.last_daily_bonus,
            User.daily_streak,
            User.achievement_points
        ).where(User.id == user_id)
        result = await session.execute(stmt)
        row = result.one_or_none()
        
        if not row:
            return {
                'can_claim': True,
                'streak': 0,
                'points': 0,
                'hours_until_next': 0
            }
        
        last_claim, streak, points = row
        now = datetime.now(timezone.utc)
        
        if not last_claim:
            can_claim = True
            hours_until_next = 0
        else:
            hours_since = (now - last_claim).total_seconds() / 3600
            can_claim = hours_since >= 24
            hours_until_next = max(0, int(24 - hours_since))
        
        return {
            'can_claim': can_claim,
            'streak': streak or 0,
            'points': points or 0,
            'hours_until_next': hours_until_next
        }


# Global instance
daily_bonus_service = DailyBonusService()

