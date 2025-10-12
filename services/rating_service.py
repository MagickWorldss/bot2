"""Rating service for user reputation system."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.user_service import UserService


class RatingService:
    """Service for managing user ratings."""
    
    @staticmethod
    def calculate_rating(
        total_purchases: int,
        total_spent_sol: float,
        refunds_count: int
    ) -> float:
        """
        Calculate user rating.
        
        Formula:
        - Base: purchases * 10
        - Bonus: total_spent * 20
        - Penalty: refunds * -50
        - Range: -100 to +100
        
        Returns:
            Rating value (-100 to +100)
        """
        # Base score from purchases
        purchase_score = min(total_purchases * 10, 50)
        
        # Bonus for spending
        spending_score = min(total_spent_sol * 20, 50)
        
        # Penalty for refunds
        refund_penalty = refunds_count * 50
        
        # Calculate total
        rating = purchase_score + spending_score - refund_penalty
        
        # Clamp to -100 to +100
        rating = max(-100, min(100, rating))
        
        return rating
    
    @staticmethod
    def get_rating_level(rating: float) -> str:
        """Get rating level name."""
        if rating >= 80:
            return "⭐⭐⭐ VIP"
        elif rating >= 50:
            return "⭐⭐ Отличный"
        elif rating >= 20:
            return "⭐ Хороший"
        elif rating >= 0:
            return "😐 Нейтральный"
        elif rating >= -30:
            return "⚠️ Сомнительный"
        else:
            return "❌ Плохой"
    
    @staticmethod
    def get_rating_bar(rating: float, length: int = 10) -> str:
        """
        Get visual rating bar.
        
        Args:
            rating: Rating value (-100 to +100)
            length: Bar length (default 10)
            
        Returns:
            Visual bar like: ▓▓▓▓▓░░░░░
        """
        # Normalize rating to 0-length scale
        normalized = ((rating + 100) / 200) * length
        filled = int(normalized)
        empty = length - filled
        
        # Create bar
        bar = "▓" * filled + "░" * empty
        
        return bar
    
    @staticmethod
    def get_rating_emoji(rating: float) -> str:
        """Get emoji for rating."""
        if rating >= 80:
            return "🌟"
        elif rating >= 50:
            return "⭐"
        elif rating >= 20:
            return "✨"
        elif rating >= 0:
            return "😐"
        elif rating >= -30:
            return "⚠️"
        else:
            return "❌"
    
    @staticmethod
    async def update_rating_after_purchase(
        session: AsyncSession,
        user_id: int,
        amount_sol: float
    ) -> float:
        """
        Update user rating after successful purchase.
        
        Returns:
            New rating value
        """
        user = await UserService.get_user(session, user_id)
        
        if not user:
            return 0.0
        
        # Update stats
        user.total_purchases += 1
        user.total_spent_sol += amount_sol
        
        # Recalculate rating
        user.rating = RatingService.calculate_rating(
            user.total_purchases,
            user.total_spent_sol,
            user.refunds_count
        )
        
        await session.commit()
        
        return user.rating
    
    @staticmethod
    async def update_rating_after_refund(
        session: AsyncSession,
        user_id: int
    ) -> float:
        """
        Update user rating after refund.
        
        Returns:
            New rating value
        """
        user = await UserService.get_user(session, user_id)
        
        if not user:
            return 0.0
        
        # Increment refunds
        user.refunds_count += 1
        
        # Recalculate rating
        user.rating = RatingService.calculate_rating(
            user.total_purchases,
            user.total_spent_sol,
            user.refunds_count
        )
        
        await session.commit()
        
        return user.rating
    
    @staticmethod
    async def get_user_rating_info(
        session: AsyncSession,
        user_id: int
    ) -> Optional[dict]:
        """Get full rating info for user."""
        user = await UserService.get_user(session, user_id)
        
        if not user:
            return None
        
        return {
            'rating': user.rating,
            'level': RatingService.get_rating_level(user.rating),
            'bar': RatingService.get_rating_bar(user.rating),
            'emoji': RatingService.get_rating_emoji(user.rating),
            'total_purchases': user.total_purchases,
            'total_spent_sol': user.total_spent_sol,
            'refunds_count': user.refunds_count
        }


# Global rating service
rating_service = RatingService()

