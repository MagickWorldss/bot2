"""Seasonal events service."""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import SeasonalEvent

logger = logging.getLogger(__name__)


class SeasonalService:
    """Service for managing seasonal events."""
    
    @staticmethod
    async def get_active_events(session: AsyncSession) -> list[SeasonalEvent]:
        """Get all active seasonal events."""
        now = datetime.utcnow()
        stmt = select(SeasonalEvent).where(
            SeasonalEvent.is_active == True,
            SeasonalEvent.starts_at <= now,
            SeasonalEvent.ends_at > now
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def apply_event_discount(
        session: AsyncSession,
        original_price: float
    ) -> tuple[float, SeasonalEvent | None]:
        """
        Apply seasonal event discount to price.
        Returns: (final_price, applied_event)
        """
        events = await SeasonalService.get_active_events(session)
        
        best_discount = 0
        best_event = None
        
        for event in events:
            if event.event_type == 'sale' and event.discount_percent:
                if event.discount_percent > best_discount:
                    best_discount = event.discount_percent
                    best_event = event
        
        if best_event:
            discount = original_price * (best_discount / 100)
            final_price = original_price - discount
            return final_price, best_event
        
        return original_price, None
    
    @staticmethod
    async def get_bonus_multiplier(session: AsyncSession) -> tuple[float, SeasonalEvent | None]:
        """
        Get bonus multiplier from active events.
        Returns: (multiplier, event)
        """
        events = await SeasonalService.get_active_events(session)
        
        best_multiplier = 1.0
        best_event = None
        
        for event in events:
            if event.event_type == 'bonus' and event.bonus_multiplier:
                if event.bonus_multiplier > best_multiplier:
                    best_multiplier = event.bonus_multiplier
                    best_event = event
        
        return best_multiplier, best_event
    
    @staticmethod
    async def create_seasonal_event(
        session: AsyncSession,
        name_ru: str,
        name_en: str,
        description_ru: str,
        description_en: str,
        event_type: str,  # sale, bonus, special
        discount_percent: float = None,
        bonus_multiplier: float = None,
        starts_at: datetime = None,
        ends_at: datetime = None
    ) -> SeasonalEvent:
        """Create a new seasonal event."""
        event = SeasonalEvent(
            name_ru=name_ru,
            name_en=name_en,
            description_ru=description_ru,
            description_en=description_en,
            event_type=event_type,
            discount_percent=discount_percent,
            bonus_multiplier=bonus_multiplier,
            starts_at=starts_at or datetime.utcnow(),
            ends_at=ends_at,
            is_active=True
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        logger.info(f"Seasonal event created: {name_ru}")
        return event


# Global instance
seasonal_service = SeasonalService()

