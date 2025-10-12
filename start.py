"""Startup script with automatic database initialization."""
import asyncio
import logging
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_database():
    """Initialize database with default data if needed."""
    from database.database import db
    from init_db import init_db_data
    
    logger.info("Checking database initialization...")
    
    # Check if regions exist
    async for session in db.get_session():
        from services.location_service import LocationService
        regions = await LocationService.get_all_regions(session, active_only=False)
        
        if regions:
            logger.info("Database already initialized. Skipping...")
            return
        
        logger.info("Initializing database with Lithuania structure...")
        
        # Use init_db_data which has Lithuania with districts
        await init_db_data(session)
        
        logger.info("✅ Database initialization complete!")


async def main():
    """Main function to start the bot with initialization."""
    from aiogram import Bot, Dispatcher
    from aiogram.fsm.storage.memory import MemoryStorage
    from config import settings
    from database.database import db
    from handlers import setup_routers
    from middleware.user_middleware import UserMiddleware
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Setup middleware
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    
    # Setup routers
    router = setup_routers()
    dp.include_router(router)
    
    # Create database tables
    logger.info("Creating database tables...")
    await db.create_tables()
    logger.info("Database tables created successfully")
    
    # Initialize database with default data
    await initialize_database()
    
    # Start polling
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        from services.wallet_service import wallet_service
        await wallet_service.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)

