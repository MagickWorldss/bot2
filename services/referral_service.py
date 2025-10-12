"""Referral system service."""
import secrets
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import User, Transaction
from services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class ReferralService:
    """Service for managing referral system."""
    
    REFERRAL_BONUS_PERCENT = 10  # 10% of friend's first purchase
    
    @staticmethod
    def generate_referral_code() -> str:
        """Generate unique referral code."""
        return secrets.token_urlsafe(8)
    
    @staticmethod
    async def get_or_create_referral_code(session: AsyncSession, user_id: int) -> str:
        """Get existing or create new referral code for user."""
        stmt = select(User.referral_code).where(User.id == user_id)
        result = await session.execute(stmt)
        code = result.scalar_one_or_none()
        
        if not code:
            # Generate new code
            code = ReferralService.generate_referral_code()
            stmt = update(User).where(User.id == user_id).values(referral_code=code)
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Created referral code {code} for user {user_id}")
        
        return code
    
    @staticmethod
    async def get_referral_link(session: AsyncSession, user_id: int, bot_username: str) -> str:
        """Get referral link for user."""
        code = await ReferralService.get_or_create_referral_code(session, user_id)
        return f"https://t.me/{bot_username}?start=ref_{code}"
    
    @staticmethod
    async def register_referral(session: AsyncSession, new_user_id: int, referral_code: str) -> bool:
        """Register new user as referral."""
        # Find referrer by code
        stmt = select(User.id).where(User.referral_code == referral_code)
        result = await session.execute(stmt)
        referrer_id = result.scalar_one_or_none()
        
        if not referrer_id or referrer_id == new_user_id:
            return False
        
        # Update new user
        stmt = update(User).where(User.id == new_user_id).values(referred_by=referrer_id)
        await session.execute(stmt)
        
        # Update referrer stats
        stmt = update(User).where(User.id == referrer_id).values(
            total_referrals=User.total_referrals + 1
        )
        await session.execute(stmt)
        
        await session.commit()
        logger.info(f"User {new_user_id} registered as referral of {referrer_id}")
        return True
    
    @staticmethod
    async def process_referral_bonus(
        session: AsyncSession,
        user_id: int,
        purchase_amount_sol: float
    ) -> float:
        """
        Process referral bonus after user's first purchase.
        Returns bonus amount given to referrer.
        """
        # Check if user was referred
        stmt = select(User.referred_by, User.total_purchases).where(User.id == user_id)
        result = await session.execute(stmt)
        row = result.one_or_none()
        
        if not row or not row[0] or row[1] > 1:  # Not referred or not first purchase
            return 0.0
        
        referrer_id = row[0]
        bonus_amount = purchase_amount_sol * (ReferralService.REFERRAL_BONUS_PERCENT / 100)
        
        # Give bonus to referrer
        stmt = update(User).where(User.id == referrer_id).values(
            balance_sol=User.balance_sol + bonus_amount,
            referral_earnings_sol=User.referral_earnings_sol + bonus_amount
        )
        await session.execute(stmt)
        
        # Create transaction record
        await TransactionService.create_transaction(
            session=session,
            user_id=referrer_id,
            tx_type='referral_bonus',
            amount_sol=bonus_amount,
            description=f"Реферальный бонус за покупку друга (User #{user_id})",
            status='completed'
        )
        
        await session.commit()
        logger.info(f"Referral bonus {bonus_amount} SOL given to user {referrer_id}")
        return bonus_amount
    
    @staticmethod
    async def get_referral_stats(session: AsyncSession, user_id: int) -> dict:
        """Get user's referral statistics."""
        stmt = select(
            User.total_referrals,
            User.referral_earnings_sol
        ).where(User.id == user_id)
        result = await session.execute(stmt)
        row = result.one_or_none()
        
        if not row:
            return {
                'total_referrals': 0,
                'total_earnings_sol': 0.0
            }
        
        return {
            'total_referrals': row[0],
            'total_earnings_sol': row[1]
        }


# Global instance
referral_service = ReferralService()

