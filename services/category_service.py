"""Category service for managing product categories."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from database.models import Category


class CategoryService:
    """Service for category operations."""
    
    @staticmethod
    async def get_all_categories(session: AsyncSession) -> List[Category]:
        """Get all active categories ordered by sort_order."""
        stmt = select(Category).where(Category.is_active == True).order_by(Category.sort_order, Category.name)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_category_by_key(session: AsyncSession, key: str) -> Optional[Category]:
        """Get category by key."""
        stmt = select(Category).where(Category.key == key)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_category_by_id(session: AsyncSession, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        stmt = select(Category).where(Category.id == category_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_category(
        session: AsyncSession,
        key: str,
        name: str,
        icon: str,
        description: Optional[str] = None,
        sort_order: int = 0
    ) -> Category:
        """Create new category."""
        category = Category(
            key=key,
            name=name,
            icon=icon,
            description=description,
            sort_order=sort_order
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category
    
    @staticmethod
    async def update_category(
        session: AsyncSession,
        category_id: int,
        key: Optional[str] = None,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update category."""
        update_data = {}
        if key is not None:
            update_data['key'] = key
        if name is not None:
            update_data['name'] = name
        if icon is not None:
            update_data['icon'] = icon
        if description is not None:
            update_data['description'] = description
        if sort_order is not None:
            update_data['sort_order'] = sort_order
        if is_active is not None:
            update_data['is_active'] = is_active
        
        if not update_data:
            return False
        
        update_data['updated_at'] = func.now()
        
        stmt = update(Category).where(Category.id == category_id).values(**update_data)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def delete_category(session: AsyncSession, category_id: int) -> bool:
        """Delete category (soft delete - set is_active=False)."""
        stmt = update(Category).where(Category.id == category_id).values(
            is_active=False,
            updated_at=func.now()
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def initialize_default_categories(session: AsyncSession):
        """Initialize default categories from preview_categories.py."""
        from utils.preview_categories import PREVIEW_CATEGORIES
        
        for key, category_data in PREVIEW_CATEGORIES.items():
            # Check if category already exists
            existing = await CategoryService.get_category_by_key(session, key)
            if not existing:
                await CategoryService.create_category(
                    session=session,
                    key=key,
                    name=category_data['name'],
                    icon=category_data['icon'],
                    description=category_data['description']
                )


# Create service instance
category_service = CategoryService()
