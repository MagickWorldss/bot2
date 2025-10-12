"""Deposit service for managing EUR deposits with rate reservation."""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import DepositRequest, User
from services.price_service import price_service
import logging

logger = logging.getLogger(__name__)


class DepositService:
    """Service for deposit operations with EUR."""
    
    @staticmethod
    async def create_deposit_request(
        session: AsyncSession,
        user_id: int,
        eur_amount: float
    ) -> DepositRequest:
        """
        Create deposit request with reserved exchange rate.
        
        Args:
            session: Database session
            user_id: User ID
            eur_amount: Amount in EUR
            
        Returns:
            Created deposit request
        """
        # Get current SOL/EUR rate
        rate = await price_service.get_sol_eur_rate()
        
        # Calculate required SOL amount
        sol_amount = eur_amount / rate
        
        # Create deposit request
        deposit = DepositRequest(
            user_id=user_id,
            eur_amount=eur_amount,
            sol_amount=sol_amount,
            reserved_rate=rate,
            status='pending',
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        
        session.add(deposit)
        await session.commit()
        await session.refresh(deposit)
        
        logger.info(
            f"Created deposit request: {eur_amount} EUR = {sol_amount} SOL "
            f"(rate: {rate}) for user {user_id}"
        )
        
        return deposit
    
    @staticmethod
    async def get_active_deposit(
        session: AsyncSession,
        user_id: int
    ) -> Optional[DepositRequest]:
        """Get user's active (pending, not expired) deposit request."""
        result = await session.execute(
            select(DepositRequest)
            .where(
                and_(
                    DepositRequest.user_id == user_id,
                    DepositRequest.status == 'pending',
                    DepositRequest.expires_at > datetime.utcnow()
                )
            )
            .order_by(DepositRequest.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def complete_deposit(
        session: AsyncSession,
        deposit_id: int
    ) -> bool:
        """Mark deposit as completed."""
        result = await session.execute(
            select(DepositRequest).where(DepositRequest.id == deposit_id)
        )
        deposit = result.scalar_one_or_none()
        
        if not deposit:
            return False
        
        deposit.status = 'completed'
        deposit.completed_at = datetime.utcnow()
        
        await session.commit()
        return True
    
    @staticmethod
    async def expire_old_deposits(session: AsyncSession) -> int:
        """Expire all old pending deposits. Returns count of expired."""
        result = await session.execute(
            select(DepositRequest)
            .where(
                and_(
                    DepositRequest.status == 'pending',
                    DepositRequest.expires_at <= datetime.utcnow()
                )
            )
        )
        
        deposits = result.scalars().all()
        count = 0
        
        for deposit in deposits:
            deposit.status = 'expired'
            count += 1
        
        if count > 0:
            await session.commit()
            logger.info(f"Expired {count} old deposit requests")
        
        return count
    
    @staticmethod
    async def cancel_deposit(
        session: AsyncSession,
        deposit_id: int
    ) -> bool:
        """Cancel deposit request."""
        result = await session.execute(
            select(DepositRequest).where(DepositRequest.id == deposit_id)
        )
        deposit = result.scalar_one_or_none()
        
        if not deposit:
            return False
        
        deposit.status = 'cancelled'
        await session.commit()
        return True
    
    @staticmethod
    async def get_user_deposit_history(
        session: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[DepositRequest]:
        """Get user's deposit request history."""
        result = await session.execute(
            select(DepositRequest)
            .where(DepositRequest.user_id == user_id)
            .order_by(DepositRequest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# Global deposit service instance
deposit_service = DepositService()

