"""Notification service."""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Notification, User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""
    
    @staticmethod
    async def create_notification(
        session: AsyncSession,
        message: str,
        notification_type: str,  # new_product, news, promo
        user_id: int = None,  # None = all users
        region_id: int = None  # None = all regions
    ) -> Notification:
        """Create a notification."""
        notification = Notification(
            user_id=user_id,
            region_id=region_id,
            message=message,
            notification_type=notification_type
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        logger.info(f"Notification created: {notification_type} - {message[:50]}")
        return notification
    
    @staticmethod
    async def get_pending_notifications(session: AsyncSession) -> list[Notification]:
        """Get all pending notifications."""
        stmt = select(Notification).where(Notification.sent == False)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_users_to_notify(
        session: AsyncSession,
        notification: Notification
    ) -> list[int]:
        """Get list of user IDs to notify."""
        # Build query
        stmt = select(User.id).where(
            User.notifications_enabled == True,
            User.is_blocked == False
        )
        
        # Filter by specific user
        if notification.user_id:
            stmt = stmt.where(User.id == notification.user_id)
        
        # Filter by region
        if notification.region_id:
            stmt = stmt.where(User.region_id == notification.region_id)
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def mark_as_sent(session: AsyncSession, notification_id: int):
        """Mark notification as sent."""
        stmt = update(Notification).where(Notification.id == notification_id).values(
            sent=True,
            sent_at=datetime.now(timezone.utc)
        )
        await session.execute(stmt)
        await session.commit()
    
    @staticmethod
    async def send_new_product_notification(
        session: AsyncSession,
        image_id: int,
        region_id: int,
        city_name: str,
        price_sol: float
    ):
        """Send notification about new product."""
        message = f"🆕 Новый товар в {city_name}!\n💰 Цена: {price_sol} SOL\n\n📍 Перейдите в каталог чтобы купить!"
        await NotificationService.create_notification(
            session,
            message,
            'new_product',
            region_id=region_id
        )


# Global instance
notification_service = NotificationService()

