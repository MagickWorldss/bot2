"""User service for managing users."""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, Region, City
from services.wallet_service import wallet_service

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations."""
    
    @staticmethod
    async def get_or_create_user(
        session: AsyncSession,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Get existing user or create new one."""
        # Try to get existing user
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update user info if changed
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            await session.commit()
            return user
        
        # Create new wallet for user
        public_key, encrypted_private_key = wallet_service.create_wallet()
        
        # Create new user
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            wallet_address=public_key,
            wallet_private_key=encrypted_private_key,
            balance_eur=0.0
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_balance(session: AsyncSession, user_id: int, amount: float) -> bool:
        """Update user balance."""
        user = await UserService.get_user(session, user_id)
        if not user:
            return False
        
        user.balance_eur += amount
        await session.commit()
        await session.refresh(user)  # Refresh to ensure changes are saved
        logger.info(f"User {user_id} balance updated: {amount:+.2f}, new balance: {user.balance_eur:.2f}")
        return True
    
    @staticmethod
    async def set_location(
        session: AsyncSession,
        user_id: int,
        region_id: Optional[int] = None,
        city_id: Optional[int] = None
    ) -> bool:
        """Set user location."""
        user = await UserService.get_user(session, user_id)
        if not user:
            return False
        
        user.region_id = region_id
        user.city_id = city_id
        await session.commit()
        return True
    
    @staticmethod
    async def get_user_with_location(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user with loaded location relationships."""
        result = await session.execute(
            select(User)
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Load relationships
            if user.region_id:
                await session.refresh(user, ['region'])
            if user.city_id:
                await session.refresh(user, ['city'])
        
        return user
    
    @staticmethod
    async def get_all_users(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination."""
        result = await session.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def block_user(session: AsyncSession, user_id: int, blocked: bool = True) -> bool:
        """Block or unblock user."""
        user = await UserService.get_user(session, user_id)
        if not user:
            return False
        
        user.is_blocked = blocked
        await session.commit()
        return True

