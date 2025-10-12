"""Role management service."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User

logger = logging.getLogger(__name__)


class RoleService:
    """Service for managing user roles."""
    
    ROLES = {
        'user': {
            'name_ru': 'Пользователь',
            'name_en': 'User',
            'permissions': ['buy', 'view_catalog']
        },
        'seller': {
            'name_ru': 'Продавец',
            'name_en': 'Seller',
            'permissions': ['buy', 'view_catalog', 'add_product', 'edit_product', 'delete_product']
        },
        'moderator': {
            'name_ru': 'Модератор',
            'name_en': 'Moderator',
            'permissions': ['buy', 'view_catalog', 'add_product', 'edit_product', 'delete_product', 
                           'manage_users', 'view_tickets', 'reply_tickets', 'view_stats']
        },
        'admin': {
            'name_ru': 'Администратор',
            'name_en': 'Administrator',
            'permissions': ['all']
        }
    }
    
    @staticmethod
    async def set_user_role(session: AsyncSession, user_id: int, role: str) -> bool:
        """Set user role."""
        if role not in RoleService.ROLES:
            return False
        
        stmt = update(User).where(User.id == user_id).values(
            role=role,
            is_admin=(role == 'admin')
        )
        await session.execute(stmt)
        await session.commit()
        logger.info(f"User {user_id} role set to {role}")
        return True
    
    @staticmethod
    async def get_user_role(session: AsyncSession, user_id: int) -> str:
        """Get user role."""
        stmt = select(User.role).where(User.id == user_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        return role or 'user'
    
    @staticmethod
    def has_permission(role: str, permission: str) -> bool:
        """Check if role has permission."""
        if role not in RoleService.ROLES:
            return False
        
        role_permissions = RoleService.ROLES[role]['permissions']
        
        if 'all' in role_permissions:
            return True
        
        return permission in role_permissions
    
    @staticmethod
    async def check_user_permission(session: AsyncSession, user_id: int, permission: str) -> bool:
        """Check if user has permission."""
        role = await RoleService.get_user_role(session, user_id)
        return RoleService.has_permission(role, permission)
    
    @staticmethod
    def get_role_name(role: str, language: str = 'ru') -> str:
        """Get role display name."""
        if role not in RoleService.ROLES:
            return role
        
        key = 'name_ru' if language == 'ru' else 'name_en'
        return RoleService.ROLES[role][key]


# Global instance
role_service = RoleService()

