"""Shopping cart service."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database.models import Cart, Image

logger = logging.getLogger(__name__)


class CartService:
    """Service for managing shopping cart."""
    
    @staticmethod
    async def add_to_cart(session: AsyncSession, user_id: int, image_id: int) -> bool:
        """Add item to cart."""
        # Check if already in cart
        stmt = select(Cart).where(
            Cart.user_id == user_id,
            Cart.image_id == image_id
        )
        result = await session.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            return False  # Already in cart
        
        # Check if item is available
        stmt = select(Image.is_sold).where(Image.id == image_id)
        result = await session.execute(stmt)
        is_sold = result.scalar_one_or_none()
        
        if is_sold:
            return False  # Item already sold
        
        # Add to cart
        cart_item = Cart(user_id=user_id, image_id=image_id)
        session.add(cart_item)
        await session.commit()
        logger.info(f"Item {image_id} added to cart for user {user_id}")
        return True
    
    @staticmethod
    async def remove_from_cart(session: AsyncSession, user_id: int, image_id: int) -> bool:
        """Remove item from cart."""
        stmt = delete(Cart).where(
            Cart.user_id == user_id,
            Cart.image_id == image_id
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def get_cart(session: AsyncSession, user_id: int) -> list[Image]:
        """Get user's cart items."""
        stmt = select(Image).join(Cart).where(
            Cart.user_id == user_id,
            Image.is_sold == False
        ).order_by(Cart.added_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_cart_total(session: AsyncSession, user_id: int) -> float:
        """Get total price of cart."""
        items = await CartService.get_cart(session, user_id)
        return sum(item.price_sol for item in items)
    
    @staticmethod
    async def clear_cart(session: AsyncSession, user_id: int):
        """Clear user's cart."""
        stmt = delete(Cart).where(Cart.user_id == user_id)
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Cart cleared for user {user_id}")


# Global instance
cart_service = CartService()

