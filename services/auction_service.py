"""Auction service."""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Image, AuctionBid, User

logger = logging.getLogger(__name__)


class AuctionService:
    """Service for managing auctions."""
    
    @staticmethod
    async def place_bid(
        session: AsyncSession,
        image_id: int,
        user_id: int,
        bid_amount_sol: float
    ) -> tuple[bool, str]:
        """
        Place a bid on auction item.
        Returns: (success, message)
        """
        # Get auction item
        stmt = select(Image).where(Image.id == image_id)
        result = await session.execute(stmt)
        item = result.scalars().first()
        
        if not item or not item.is_auction:
            return False, "❌ Это не аукционный товар"
        
        if item.is_sold:
            return False, "❌ Аукцион завершен"
        
        # Check if auction ended
        if item.auction_ends_at and datetime.now(timezone.utc) > item.auction_ends_at:
            return False, "❌ Аукцион завершен"
        
        # Check bid amount
        min_bid = item.current_bid_sol or item.starting_price_sol
        if bid_amount_sol <= min_bid:
            return False, f"❌ Ставка должна быть больше {min_bid} SOL"
        
        # Check user balance
        stmt = select(User.balance_eur).where(User.id == user_id)
        result = await session.execute(stmt)
        balance = result.scalar_one_or_none()
        
        if balance < bid_amount_sol:
            return False, "❌ Недостаточно средств"
        
        # Return previous bidder's money
        if item.highest_bidder_id and item.highest_bidder_id != user_id:
            stmt = update(User).where(User.id == item.highest_bidder_id).values(
                balance_eur=User.balance_eur + item.current_bid_sol
            )
            await session.execute(stmt)
        
        # Reserve new bidder's money
        stmt = update(User).where(User.id == user_id).values(
            balance_eur=User.balance_eur - bid_amount_sol
        )
        await session.execute(stmt)
        
        # Update auction
        item.current_bid_sol = bid_amount_sol
        item.highest_bidder_id = user_id
        
        # Record bid
        bid = AuctionBid(
            image_id=image_id,
            user_id=user_id,
            bid_amount_sol=bid_amount_sol
        )
        session.add(bid)
        
        await session.commit()
        logger.info(f"User {user_id} placed bid {bid_amount_sol} SOL on item {image_id}")
        
        return True, f"✅ Ставка принята: {bid_amount_sol} SOL"
    
    @staticmethod
    async def complete_auction(session: AsyncSession, image_id: int) -> bool:
        """Complete auction and transfer item to winner."""
        stmt = select(Image).where(Image.id == image_id)
        result = await session.execute(stmt)
        item = result.scalars().first()
        
        if not item or not item.is_auction or item.is_sold:
            return False
        
        if not item.highest_bidder_id:
            # No bids, auction failed
            item.is_sold = False
            await session.commit()
            return False
        
        # Transfer item to winner
        item.is_sold = True
        item.sold_to = item.highest_bidder_id
        item.sold_at = datetime.now(timezone.utc)
        
        # Money already reserved, just log it
        logger.info(f"Auction completed: item {image_id} won by user {item.highest_bidder_id} for {item.current_bid_sol} SOL")
        
        await session.commit()
        return True
    
    @staticmethod
    async def get_auction_info(session: AsyncSession, image_id: int) -> dict | None:
        """Get auction information."""
        stmt = select(Image).where(Image.id == image_id, Image.is_auction == True)
        result = await session.execute(stmt)
        item = result.scalars().first()
        
        if not item:
            return None
        
        # Get bid history
        stmt = select(AuctionBid).where(AuctionBid.image_id == image_id).order_by(AuctionBid.created_at.desc()).limit(5)
        result = await session.execute(stmt)
        recent_bids = list(result.scalars().all())
        
        now = datetime.now(timezone.utc)
        time_left = (item.auction_ends_at - now).total_seconds() if item.auction_ends_at else None
        
        return {
            'item': item,
            'current_bid': item.current_bid_sol or item.starting_price_sol,
            'highest_bidder_id': item.highest_bidder_id,
            'time_left_seconds': time_left,
            'recent_bids': recent_bids,
            'is_ended': time_left and time_left <= 0
        }


# Global instance
auction_service = AuctionService()

