"""Roulette service for daily wheel spin."""
import logging
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from database.models import RoulettePrize, UserRouletteSpin, User, UserCoupon

logger = logging.getLogger(__name__)


class RouletteService:
    """Service for managing roulette wheel."""
    
    @staticmethod
    async def can_spin_today(session: AsyncSession, user_id: int) -> bool:
        """Check if user can spin today."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(UserRouletteSpin).where(
            UserRouletteSpin.user_id == user_id,
            UserRouletteSpin.created_at >= today_start
        )
        result = await session.execute(stmt)
        spin = result.scalars().first()
        
        return spin is None
    
    @staticmethod
    async def get_active_prizes(session: AsyncSession, user_id: int = None) -> list[RoulettePrize]:
        """Get all active prizes. Exclude discount_coupon if user already has active coupon."""
        stmt = select(RoulettePrize).where(RoulettePrize.is_active == True)
        result = await session.execute(stmt)
        prizes = list(result.scalars().all())
        
        # Если указан user_id, исключаем купон если у пользователя уже есть активный
        if user_id:
            has_active_coupon = await RouletteService.has_active_coupon(session, user_id)
            if has_active_coupon:
                prizes = [p for p in prizes if p.prize_type != 'discount_coupon']
        
        return prizes
    
    @staticmethod
    async def spin_wheel(session: AsyncSession, user_id: int) -> dict:
        """Spin the wheel and get a prize."""
        # Check if user can spin
        if not await RouletteService.can_spin_today(session, user_id):
            return {'success': False, 'error': 'already_spun_today'}
        
        # Get active prizes (excluding discount_coupon if user has active one)
        prizes = await RouletteService.get_active_prizes(session, user_id)
        
        if not prizes:
            return {'success': False, 'error': 'no_prizes'}
        
        # Normalize probabilities if needed (ensure they sum to 1.0)
        total_prob = sum(p.probability for p in prizes)
        if total_prob == 0:
            return {'success': False, 'error': 'no_prizes'}
        
        # Select prize based on probability
        rand = random.uniform(0, total_prob)
        
        current_prob = 0
        selected_prize = None
        
        for prize in prizes:
            current_prob += prize.probability
            if rand <= current_prob:
                selected_prize = prize
                break
        
        if not selected_prize:
            selected_prize = prizes[-1]  # Fallback to last prize
        
        # Record spin
        spin = UserRouletteSpin(
            user_id=user_id,
            prize_id=selected_prize.id,
            prize_won=selected_prize.name
        )
        session.add(spin)
        
        # Give prize to user
        await RouletteService._give_prize(session, user_id, selected_prize)
        
        await session.commit()
        
        logger.info(f"User {user_id} spun roulette and won: {selected_prize.name}")
        
        return {
            'success': True,
            'prize': selected_prize,
            'prize_name': selected_prize.name,
            'prize_type': selected_prize.prize_type,
            'prize_value': selected_prize.prize_value
        }
    
    @staticmethod
    async def _give_prize(session: AsyncSession, user_id: int, prize: RoulettePrize):
        """Give prize to user."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return
        
        if prize.prize_type == 'eur':
            user.balance_eur += prize.prize_value
        elif prize.prize_type == 'points':
            user.achievement_points += int(prize.prize_value)
        elif prize.prize_type == 'discount_coupon':
            # Create coupon with 10 days expiration
            expires_at = datetime.now(timezone.utc) + timedelta(days=10)
            coupon = UserCoupon(
                user_id=user_id,
                max_discount=prize.prize_value,  # 30.00 EUR
                expires_at=expires_at
            )
            session.add(coupon)
            logger.info(f"Coupon created for user {user_id}: {prize.prize_value} EUR, expires {expires_at}")
        elif prize.prize_type == 'nothing':
            pass  # No prize
        
        logger.info(f"Prize given to user {user_id}: {prize.prize_type} = {prize.prize_value}")
    
    @staticmethod
    async def get_user_spin_history(session: AsyncSession, user_id: int, limit: int = 10) -> list[UserRouletteSpin]:
        """Get user's spin history."""
        stmt = select(UserRouletteSpin).where(
            UserRouletteSpin.user_id == user_id
        ).order_by(UserRouletteSpin.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    # === ADMIN METHODS ===
    
    @staticmethod
    async def get_all_prizes(session: AsyncSession) -> list[RoulettePrize]:
        """Get all prizes (for admin)."""
        stmt = select(RoulettePrize).order_by(RoulettePrize.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_prize_by_id(session: AsyncSession, prize_id: int) -> RoulettePrize | None:
        """Get prize by ID."""
        stmt = select(RoulettePrize).where(RoulettePrize.id == prize_id)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def create_prize(
        session: AsyncSession,
        name: str,
        prize_type: str,
        prize_value: float,
        probability: float
    ) -> RoulettePrize:
        """Create new prize."""
        prize = RoulettePrize(
            name=name,
            prize_type=prize_type,
            prize_value=prize_value,
            probability=probability,
            is_active=True
        )
        session.add(prize)
        await session.commit()
        await session.refresh(prize)
        logger.info(f"Roulette prize created: {name} (ID: {prize.id})")
        return prize
    
    @staticmethod
    async def update_prize(
        session: AsyncSession,
        prize_id: int,
        **kwargs
    ) -> bool:
        """Update prize fields."""
        stmt = update(RoulettePrize).where(RoulettePrize.id == prize_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Roulette prize {prize_id} updated: {kwargs}")
        return True
    
    @staticmethod
    async def delete_prize(session: AsyncSession, prize_id: int) -> bool:
        """Delete prize."""
        prize = await RouletteService.get_prize_by_id(session, prize_id)
        if prize:
            await session.delete(prize)
            await session.commit()
            logger.info(f"Roulette prize {prize_id} deleted")
            return True
        return False
    
    @staticmethod
    async def toggle_prize_status(session: AsyncSession, prize_id: int) -> bool:
        """Toggle prize active status."""
        prize = await RouletteService.get_prize_by_id(session, prize_id)
        if prize:
            prize.is_active = not prize.is_active
            await session.commit()
            logger.info(f"Roulette prize {prize_id} status toggled to {prize.is_active}")
            return True
        return False
    
    @staticmethod
    async def has_active_coupon(session: AsyncSession, user_id: int) -> bool:
        """Check if user has active (not used, not expired) coupon."""
        now = datetime.now(timezone.utc)
        stmt = select(UserCoupon).where(
            UserCoupon.user_id == user_id,
            UserCoupon.is_used == False,
            UserCoupon.expires_at > now
        )
        result = await session.execute(stmt)
        coupon = result.scalars().first()
        return coupon is not None
    
    @staticmethod
    async def get_user_active_coupon(session: AsyncSession, user_id: int) -> UserCoupon | None:
        """Get user's active coupon if exists."""
        now = datetime.now(timezone.utc)
        stmt = select(UserCoupon).where(
            UserCoupon.user_id == user_id,
            UserCoupon.is_used == False,
            UserCoupon.expires_at > now
        ).order_by(UserCoupon.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def validate_nothing_prize_count(session: AsyncSession) -> tuple[bool, int]:
        """Validate that there is only one active 'nothing' prize. Returns (is_valid, count)."""
        stmt = select(RoulettePrize).where(
            RoulettePrize.prize_type == 'nothing',
            RoulettePrize.is_active == True
        )
        result = await session.execute(stmt)
        nothing_prizes = list(result.scalars().all())
        count = len(nothing_prizes)
        return (count <= 1, count)


# Global instance
roulette_service = RouletteService()

