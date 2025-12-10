"""Price service for getting SOL/EUR rate."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import aiohttp
from pycoingecko import CoinGeckoAPI

logger = logging.getLogger(__name__)


class PriceService:
    """Service for managing cryptocurrency prices."""
    
    def __init__(self):
        self.cg = CoinGeckoAPI()
        self.current_rate: Optional[float] = None
        self.last_update: Optional[datetime] = None
        self.update_interval = 60  # Update every 60 seconds
    
    async def get_sol_eur_rate(self) -> float:
        """
        Get current SOL/EUR exchange rate.
        
        Returns:
            Current rate (1 SOL = X EUR)
        """
        # Check if we have cached rate (less than 60 seconds old)
        if self.current_rate and self.last_update:
            if datetime.now(timezone.utc) - self.last_update < timedelta(seconds=self.update_interval):
                return self.current_rate
        
        try:
            # Get price from CoinGecko
            price_data = await asyncio.to_thread(
                self.cg.get_price,
                ids='solana',
                vs_currencies='eur'
            )
            
            rate = price_data['solana']['eur']
            self.current_rate = rate
            self.last_update = datetime.now(timezone.utc)
            
            logger.info(f"Updated SOL/EUR rate: {rate}")
            return rate
            
        except Exception as e:
            logger.error(f"Error getting SOL/EUR rate: {e}")
            
            # Fallback to default rate if API fails
            if self.current_rate:
                return self.current_rate
            
            # Default fallback (примерный курс)
            return 150.0  # 1 SOL ≈ 150 EUR (примерно)
    
    async def sol_to_eur(self, sol_amount: float) -> float:
        """Convert SOL to EUR."""
        rate = await self.get_sol_eur_rate()
        return sol_amount * rate
    
    async def eur_to_sol(self, eur_amount: float) -> float:
        """Convert EUR to SOL."""
        rate = await self.get_sol_eur_rate()
        return eur_amount / rate
    
    def format_eur(self, amount: float) -> str:
        """Format EUR amount for display."""
        return f"€{amount:.2f}"
    
    def format_sol(self, amount: float) -> str:
        """Format SOL amount for display."""
        return f"{amount:.4f} SOL"


# Global price service instance
price_service = PriceService()

