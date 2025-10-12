"""User middleware for automatic registration and checks."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import db
from services.user_service import UserService


class UserMiddleware(BaseMiddleware):
    """Middleware to ensure user is registered."""
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Process event."""
        # Get user from event
        user = event.from_user
        
        if not user:
            return await handler(event, data)
        
        # Get database session
        async for session in db.get_session():
            # Get or create user - ALWAYS fetch fresh from DB
            db_user = await UserService.get_or_create_user(
                session=session,
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Refresh user to get latest data (role, balance, etc.)
            await session.refresh(db_user)
            
            # Check if user is blocked
            if db_user.is_blocked:
                if isinstance(event, Message):
                    await event.answer("⛔️ Ваш аккаунт заблокирован.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⛔️ Ваш аккаунт заблокирован.", show_alert=True)
                return
            
            # Add user and session to data
            data['user'] = db_user
            data['session'] = session
            
            # Call handler
            return await handler(event, data)

