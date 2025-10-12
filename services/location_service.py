"""Location service for managing regions and cities."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Region, City


class LocationService:
    """Service for location operations."""
    
    @staticmethod
    async def create_region(
        session: AsyncSession,
        name: str,
        code: str
    ) -> Region:
        """Create new region."""
        region = Region(name=name, code=code)
        session.add(region)
        await session.commit()
        await session.refresh(region)
        return region
    
    @staticmethod
    async def get_region_by_id(session: AsyncSession, region_id: int) -> Optional[Region]:
        """Get region by ID."""
        result = await session.execute(
            select(Region).where(Region.id == region_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_regions(session: AsyncSession, active_only: bool = True) -> List[Region]:
        """Get all regions."""
        query = select(Region)
        if active_only:
            query = query.where(Region.is_active == True)
        query = query.order_by(Region.name)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def create_city(
        session: AsyncSession,
        name: str,
        region_id: int
    ) -> City:
        """Create new city."""
        city = City(name=name, region_id=region_id)
        session.add(city)
        await session.commit()
        await session.refresh(city)
        return city
    
    @staticmethod
    async def get_city_by_id(session: AsyncSession, city_id: int) -> Optional[City]:
        """Get city by ID."""
        result = await session.execute(
            select(City).where(City.id == city_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_cities_by_region(
        session: AsyncSession,
        region_id: int,
        active_only: bool = True
    ) -> List[City]:
        """Get all cities in a region."""
        query = select(City).where(City.region_id == region_id)
        if active_only:
            query = query.where(City.is_active == True)
        query = query.order_by(City.name)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def toggle_region_active(
        session: AsyncSession,
        region_id: int,
        is_active: bool
    ) -> bool:
        """Toggle region active status."""
        region = await LocationService.get_region_by_id(session, region_id)
        if not region:
            return False
        
        region.is_active = is_active
        await session.commit()
        return True
    
    @staticmethod
    async def toggle_city_active(
        session: AsyncSession,
        city_id: int,
        is_active: bool
    ) -> bool:
        """Toggle city active status."""
        city = await LocationService.get_city_by_id(session, city_id)
        if not city:
            return False
        
        city.is_active = is_active
        await session.commit()
        return True
    
    @staticmethod
    async def delete_city(session: AsyncSession, city_id: int) -> bool:
        """Delete city."""
        city = await LocationService.get_city_by_id(session, city_id)
        if not city:
            return False
        
        await session.delete(city)
        await session.commit()
        return True
    
    @staticmethod
    async def delete_region(session: AsyncSession, region_id: int) -> bool:
        """Delete region and all its cities."""
        region = await LocationService.get_region_by_id(session, region_id)
        if not region:
            return False
        
        await session.delete(region)
        await session.commit()
        return True

