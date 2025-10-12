"""District (microdistrict) service."""
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from database.models import District

logger = logging.getLogger(__name__)


class DistrictService:
    """Service for district operations."""
    
    @staticmethod
    async def create_district(
        session: AsyncSession,
        name: str,
        city_id: int
    ) -> District:
        """Create new district."""
        district = District(name=name, city_id=city_id, is_active=True)
        session.add(district)
        await session.commit()
        await session.refresh(district)
        logger.info(f"Created district: {name} in city {city_id}")
        return district
    
    @staticmethod
    async def get_district_by_id(session: AsyncSession, district_id: int) -> Optional[District]:
        """Get district by ID."""
        stmt = select(District).where(District.id == district_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_districts_by_city(
        session: AsyncSession,
        city_id: int,
        active_only: bool = True
    ) -> List[District]:
        """Get all districts in a city."""
        query = select(District).where(District.city_id == city_id)
        if active_only:
            query = query.where(District.is_active == True)
        query = query.order_by(District.name)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def toggle_district_active(
        session: AsyncSession,
        district_id: int,
        is_active: bool
    ) -> bool:
        """Toggle district active status."""
        stmt = update(District).where(District.id == district_id).values(is_active=is_active)
        await session.execute(stmt)
        await session.commit()
        logger.info(f"District {district_id} active status set to {is_active}")
        return True
    
    @staticmethod
    async def delete_district(session: AsyncSession, district_id: int) -> bool:
        """Delete district."""
        stmt = delete(District).where(District.id == district_id)
        result = await session.execute(stmt)
        await session.commit()
        logger.info(f"District {district_id} deleted")
        return result.rowcount > 0


# Global instance
district_service = DistrictService()

