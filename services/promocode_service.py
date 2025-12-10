"""Promocode service."""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Promocode, PromocodeUsage

logger = logging.getLogger(__name__)


class PromocodeService:
    """Service for managing promocodes."""
    
    @staticmethod
    async def create_promocode(
        session: AsyncSession,
        code: str,
        discount_type: str,  # percent, fixed, free_item
        discount_value: float,
        created_by: int,
        max_uses: int = None,
        valid_from: datetime = None,
        valid_until: datetime = None
    ) -> Promocode:
        """Create a new promocode."""
        promocode = Promocode(
            code=code.upper(),
            discount_type=discount_type,
            discount_value=discount_value,
            max_uses=max_uses,
            valid_from=valid_from,
            valid_until=valid_until,
            created_by=created_by
        )
        session.add(promocode)
        await session.commit()
        await session.refresh(promocode)
        logger.info(f"Promocode {code} created by admin {created_by}")
        return promocode
    
    @staticmethod
    async def validate_promocode(
        session: AsyncSession,
        code: str,
        user_id: int
    ) -> tuple[bool, str, Promocode | None]:
        """
        Validate promocode.
        Returns: (is_valid, error_message, promocode_object)
        """
        # Find promocode
        stmt = select(Promocode).where(Promocode.code == code.upper())
        result = await session.execute(stmt)
        promocode = result.scalars().first()
        
        if not promocode:
            return False, "❌ Промокод не найден", None
        
        if not promocode.is_active:
            return False, "❌ Промокод деактивирован", None
        
        # Check dates
        now = datetime.now(timezone.utc)
        if promocode.valid_from and now < promocode.valid_from:
            return False, "❌ Промокод еще не активен", None
        if promocode.valid_until and now > promocode.valid_until:
            return False, "❌ Промокод истек", None
        
        # Check max uses
        if promocode.max_uses and promocode.used_count >= promocode.max_uses:
            return False, "❌ Промокод исчерпан", None
        
        # Check if user already used it
        stmt = select(PromocodeUsage).where(
            PromocodeUsage.promocode_id == promocode.id,
            PromocodeUsage.user_id == user_id
        )
        result = await session.execute(stmt)
        usage = result.scalars().first()
        
        if usage:
            return False, "❌ Вы уже использовали этот промокод", None
        
        return True, "✅ Промокод действителен", promocode
    
    @staticmethod
    async def apply_promocode(
        session: AsyncSession,
        promocode_id: int,
        user_id: int,
        original_price: float
    ) -> float:
        """
        Apply promocode and return discounted price.
        Also marks promocode as used.
        """
        # Get promocode
        stmt = select(Promocode).where(Promocode.id == promocode_id)
        result = await session.execute(stmt)
        promocode = result.scalars().first()
        
        if not promocode:
            return original_price
        
        # Calculate discount
        if promocode.discount_type == 'percent':
            discount = original_price * (promocode.discount_value / 100)
            final_price = original_price - discount
        elif promocode.discount_type == 'fixed':
            final_price = max(0, original_price - promocode.discount_value)
        elif promocode.discount_type == 'free_item':
            final_price = 0
        else:
            final_price = original_price
        
        # Mark as used
        usage = PromocodeUsage(promocode_id=promocode_id, user_id=user_id)
        session.add(usage)
        
        # Increment usage count
        stmt = update(Promocode).where(Promocode.id == promocode_id).values(
            used_count=Promocode.used_count + 1
        )
        await session.execute(stmt)
        
        await session.commit()
        logger.info(f"Promocode {promocode.code} applied by user {user_id}, discount: {original_price - final_price} SOL")
        
        return final_price
    
    @staticmethod
    async def deactivate_promocode(session: AsyncSession, promocode_id: int) -> bool:
        """Deactivate promocode."""
        stmt = update(Promocode).where(Promocode.id == promocode_id).values(is_active=False)
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Promocode #{promocode_id} deactivated")
        return True
    
    @staticmethod
    async def get_all_promocodes(session: AsyncSession) -> list[Promocode]:
        """Get all promocodes."""
        stmt = select(Promocode).order_by(Promocode.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())


# Global instance
promocode_service = PromocodeService()

