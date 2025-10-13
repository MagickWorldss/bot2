"""Transaction service for managing financial operations."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Transaction


class TransactionService:
    """Service for transaction operations."""
    
    @staticmethod
    async def create_transaction(
        session: AsyncSession,
        user_id: int,
        tx_type: str,
        amount_sol: float,
        tx_hash: Optional[str] = None,
        description: Optional[str] = None,
        status: str = 'pending'
    ) -> Transaction:
        """Create new transaction record."""
        transaction = Transaction(
            user_id=user_id,
            tx_type=tx_type,
            amount_sol=amount_sol,
            tx_hash=tx_hash,
            description=description,
            status=status
        )
        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)
        return transaction
    
    @staticmethod
    async def update_transaction_status(
        session: AsyncSession,
        transaction_id: int,
        status: str,
        tx_hash: Optional[str] = None
    ) -> bool:
        """Update transaction status."""
        result = await session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            return False
        
        transaction.status = status
        if tx_hash:
            transaction.tx_hash = tx_hash
        
        if status == 'completed':
            transaction.completed_at = datetime.utcnow()
        
        await session.commit()
        return True
    
    @staticmethod
    async def get_user_transactions(
        session: AsyncSession,
        user_id: int,
        tx_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Transaction]:
        """Get user's transaction history."""
        query = select(Transaction).where(Transaction.user_id == user_id)
        
        if tx_type:
            query = query.where(Transaction.tx_type == tx_type)
        
        query = query.order_by(Transaction.created_at.desc()).limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_pending_transactions(session: AsyncSession) -> List[Transaction]:
        """Get all pending transactions."""
        result = await session.execute(
            select(Transaction)
            .where(Transaction.status == 'pending')
            .order_by(Transaction.created_at.asc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_transaction_by_id(
        session: AsyncSession,
        transaction_id: int
    ) -> Optional[Transaction]:
        """Get transaction by ID."""
        result = await session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

