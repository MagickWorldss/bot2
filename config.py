"""Configuration settings for the bot."""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Telegram
    bot_token: str = Field(..., alias='BOT_TOKEN')
    admin_ids: str = Field(..., alias='ADMIN_IDS')
    
    # Database
    database_url: str = Field(default='sqlite+aiosqlite:///./bot.db', alias='DATABASE_URL')
    
    # Solana
    solana_rpc_url: str = Field(default='https://api.devnet.solana.com', alias='SOLANA_RPC_URL')
    master_wallet_private_key: str = Field(..., alias='MASTER_WALLET_PRIVATE_KEY')
    master_wallet_public_key: str = Field(..., alias='MASTER_WALLET_PUBLIC_KEY')
    
    # App Settings
    min_deposit_sol: float = Field(default=0.01, alias='MIN_DEPOSIT_SOL')
    image_price_sol: float = Field(default=0.05, alias='IMAGE_PRICE_SOL')
    withdrawal_fee_percent: float = Field(default=2.0, alias='WITHDRAWAL_FEE_PERCENT')
    
    class Config:
        env_file = '.env'
        case_sensitive = False
    
    @property
    def admin_list(self) -> List[int]:
        """Get list of admin IDs."""
        return [int(admin_id.strip()) for admin_id in self.admin_ids.split(',') if admin_id.strip()]


# Global settings instance
settings = Settings()

