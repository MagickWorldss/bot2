"""Staff shop service."""
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import StaffItem, StaffPurchase, User

logger = logging.getLogger(__name__)


class StaffService:
    """Service for managing staff shop items."""
    
    @staticmethod
    async def create_staff_item(
        session: AsyncSession,
        name: str,
        price_points: int,
        description: str = None,
        file_id: str = None,
        item_type: str = 'digital',
        item_data: str = None,
        stock_count: int = 1
    ) -> StaffItem:
        """Create a new staff item."""
        item = StaffItem(
            name=name,
            description=description,
            price_points=price_points,
            file_id=file_id,
            item_type=item_type,
            item_data=item_data,
            stock_count=stock_count,
            is_active=True
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        logger.info(f"Created staff item: {name} for {price_points} points")
        return item
    
    @staticmethod
    async def get_all_items(session: AsyncSession, active_only: bool = True) -> List[StaffItem]:
        """Get all staff items."""
        query = select(StaffItem)
        if active_only:
            query = query.where(StaffItem.is_active == True)
        query = query.order_by(StaffItem.price_points)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_item_by_id(session: AsyncSession, item_id: int) -> Optional[StaffItem]:
        """Get staff item by ID."""
        stmt = select(StaffItem).where(StaffItem.id == item_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def purchase_staff_item(
        session: AsyncSession,
        user_id: int,
        item_id: int
    ) -> tuple[bool, str, StaffItem | None]:
        """
        Purchase staff item with points.
        Returns: (success, message, item)
        """
        # Get item
        item = await StaffService.get_item_by_id(session, item_id)
        
        if not item or not item.is_active:
            return False, "❌ Товар не найден или недоступен", None
        
        # Check stock
        if item.stock_count <= item.sold_count:
            return False, "❌ Товар закончился", None
        
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "❌ Пользователь не найден", None
        
        # Check balance
        if user.achievement_points < item.price_points:
            return False, f"❌ Недостаточно баллов! Нужно: {item.price_points}, у вас: {user.achievement_points}", None
        
        # Deduct points
        user.achievement_points -= item.price_points
        
        # Increment sold count
        item.sold_count += 1
        
        # Create purchase record
        purchase = StaffPurchase(
            user_id=user_id,
            staff_item_id=item_id,
            points_spent=item.price_points
        )
        session.add(purchase)
        
        await session.commit()
        logger.info(f"User {user_id} purchased staff item {item_id} for {item.price_points} points")
        
        return True, "✅ Покупка успешна!", item
    
    @staticmethod
    async def get_user_purchases(session: AsyncSession, user_id: int) -> List[StaffPurchase]:
        """Get user's staff purchases."""
        stmt = select(StaffPurchase).where(StaffPurchase.user_id == user_id).order_by(StaffPurchase.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def toggle_item_active(session: AsyncSession, item_id: int, is_active: bool) -> bool:
        """Toggle item active status."""
        stmt = update(StaffItem).where(StaffItem.id == item_id).values(is_active=is_active)
        await session.execute(stmt)
        await session.commit()
        return True
    
    @staticmethod
    async def delete_item(session: AsyncSession, item_id: int) -> bool:
        """Delete staff item."""
        item = await StaffService.get_item_by_id(session, item_id)
        if not item:
            return False
        
        await session.delete(item)
        await session.commit()
        logger.info(f"Deleted staff item {item_id}")
        return True


# Global instance
staff_service = StaffService()

