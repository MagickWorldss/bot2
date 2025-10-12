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
    from services.location_service import LocationService
    
    logger.info("Checking database initialization...")
    
    # Check if regions exist
    async for session in db.get_session():
        regions = await LocationService.get_all_regions(session, active_only=False)
        
        if regions:
            logger.info("Database already initialized. Skipping...")
            return
        
        logger.info("Initializing database with default regions...")
        
        # EU Countries with major cities
        default_data = [
            {'name': 'Germany', 'code': 'DE', 'cities': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne', 'Stuttgart']},
            {'name': 'France', 'code': 'FR', 'cities': ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice', 'Nantes']},
            {'name': 'Spain', 'code': 'ES', 'cities': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Bilbao', 'Malaga']},
            {'name': 'Italy', 'code': 'IT', 'cities': ['Rome', 'Milan', 'Naples', 'Turin', 'Florence', 'Venice']},
            {'name': 'Netherlands', 'code': 'NL', 'cities': ['Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht', 'Eindhoven']},
            {'name': 'Belgium', 'code': 'BE', 'cities': ['Brussels', 'Antwerp', 'Ghent', 'Bruges', 'Liege']},
            {'name': 'Poland', 'code': 'PL', 'cities': ['Warsaw', 'Krakow', 'Wroclaw', 'Poznan', 'Gdansk']},
            {'name': 'Austria', 'code': 'AT', 'cities': ['Vienna', 'Salzburg', 'Innsbruck', 'Graz', 'Linz']},
            {'name': 'Czech Republic', 'code': 'CZ', 'cities': ['Prague', 'Brno', 'Ostrava', 'Plzen', 'Liberec']},
            {'name': 'Portugal', 'code': 'PT', 'cities': ['Lisbon', 'Porto', 'Braga', 'Coimbra', 'Faro']},
            {'name': 'Sweden', 'code': 'SE', 'cities': ['Stockholm', 'Gothenburg', 'Malmo', 'Uppsala', 'Vasteras']},
            {'name': 'Denmark', 'code': 'DK', 'cities': ['Copenhagen', 'Aarhus', 'Odense', 'Aalborg', 'Esbjerg']},
        ]
        
        for region_data in default_data:
            try:
                region = await LocationService.create_region(session, name=region_data['name'], code=region_data['code'])
                logger.info(f"✓ Created region: {region.name}")
                
                for city_name in region_data['cities']:
                    city = await LocationService.create_city(session, name=city_name, region_id=region.id)
                    logger.info(f"  ✓ Created city: {city.name}")
            except Exception as e:
                logger.error(f"✗ Error creating region {region_data['name']}: {e}")
        
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

