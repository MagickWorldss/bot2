"""Balance API service for sharing balance across multiple bots."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.user_service import UserService
from services.price_service import price_service
import logging

logger = logging.getLogger(__name__)


class BalanceAPI:
    """Service for managing unified balance across multiple bots."""
    
    @staticmethod
    async def get_user_balance(
        session: AsyncSession,
        telegram_id: int
    ) -> Optional[dict]:
        """
        Get user balance by Telegram ID.
        Works across any bot using the same database.
        
        Args:
            session: Database session
            telegram_id: User's Telegram ID
            
        Returns:
            Dict with balance info or None if user not found
        """
        user = await UserService.get_user(session, telegram_id)
        
        if not user:
            logger.info(f"User {telegram_id} not found in database")
            return None
        
        # Get balance in EUR
        balance_eur = await price_service.sol_to_eur(user.balance_sol)
        rate = await price_service.get_sol_eur_rate()
        
        return {
            'telegram_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'balance_sol': user.balance_sol,
            'balance_eur': balance_eur,
            'wallet_address': user.wallet_address,
            'current_rate': rate,
            'is_blocked': user.is_blocked
        }
    
    @staticmethod
    async def update_balance(
        session: AsyncSession,
        telegram_id: int,
        amount_sol: float,
        description: str = "Balance update from external bot"
    ) -> bool:
        """
        Update user balance from external bot.
        
        Args:
            session: Database session
            telegram_id: User's Telegram ID
            amount_sol: Amount to add (can be negative)
            description: Transaction description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update balance
            success = await UserService.update_balance(session, telegram_id, amount_sol)
            
            if success:
                # Create transaction record
                from services.transaction_service import TransactionService
                
                await TransactionService.create_transaction(
                    session=session,
                    user_id=telegram_id,
                    tx_type='external_update',
                    amount_sol=abs(amount_sol),
                    description=description,
                    status='completed'
                )
                
                logger.info(
                    f"Balance updated for user {telegram_id}: "
                    f"{amount_sol:+.6f} SOL via external bot"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating balance for {telegram_id}: {e}")
            return False
    
    @staticmethod
    async def check_user_exists(
        session: AsyncSession,
        telegram_id: int
    ) -> bool:
        """Check if user exists in database."""
        user = await UserService.get_user(session, telegram_id)
        return user is not None
    
    @staticmethod
    async def sync_user_info(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> bool:
        """
        Sync user info from external bot.
        Creates user if doesn't exist.
        """
        try:
            user = await UserService.get_or_create_user(
                session=session,
                user_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            logger.info(f"User {telegram_id} synced from external bot")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing user {telegram_id}: {e}")
            return False


# Global balance API instance
balance_api = BalanceAPI()

