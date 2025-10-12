"""Database initialization script for Lithuania structure."""
import asyncio
import logging
from database.database import db
from database.models import Region, City, District
from services.location_service import LocationService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Lithuania cities and districts structure
LITHUANIA_STRUCTURE = {
    "Вильнюс": [
        "Антакальнис",
        "Вяркяй",
        "Жирмунай",
        "Жвиряй",
        "Каролинишкес",
        "Лаздинай",
        "Науйининкай",
        "Науяместис",
        "Панеряй",
        "Пашилайчяй",
        "Пилайте",
        "Расос",
        "Сенаместис (Старый город)",
        "Шешкине",
        "Шнипишкес",
        "Ужупис",
        "Фабийонишкес"
    ],
    "Каунас": [
        "Алексотас",
        "Виляймполе",
        "Дайнава",
        "Жалякальнис",
        "Центр",
        "Паняряй",
        "Петрашюнай",
        "Шанчяй",
        "Шилайняй",
        "Эйгуляй"
    ],
    "Клайпеда": [
        "Банга",
        "Вите",
        "Жардининкай",
        "Майронис",
        "Мелнраге",
        "Науйойи Клайпеда",
        "Паупяй",
        "Смелте",
        "Центр",
        "Швянтойи"
    ],
    "Шяуляй": [
        "Баублис",
        "Гинкунай",
        "Говерос",
        "Дубравос",
        "Ежерас",
        "Таленай",
        "Центр"
    ],
    "Паневежис": [
        "Алкснупяй",
        "Драугисте",
        "Екимишкис",
        "Книйшес",
        "Маргис",
        "Парко",
        "Центр"
    ],
    "Алитус": [
        "Аникщяй",
        "Дайнава",
        "Миронас",
        "Науяместис",
        "Сенаместис",
        "Центр"
    ],
    "Мариямполе": [
        "Гудишкес",
        "Дегучай",
        "Сасначука",
        "Саулес",
        "Центр"
    ],
    "Тельшяй": [
        "Гадунава",
        "Джукстай",
        "Жемайчю",
        "Центр"
    ],
    "Утена": [
        "Даугайляй",
        "Крошняй",
        "Науяместис",
        "Вякшняй",
        "Центр"
    ],
    "Таураге": [
        "Лауко",
        "Даужай",
        "Полесе",
        "Центр"
    ]
}


async def init_db_data(session):
    """Initialize database with Lithuania data."""
    try:
        # Check if Lithuania already exists
        regions = await LocationService.get_all_regions(session, active_only=False)
        lithuania = next((r for r in regions if r.name == "Литва"), None)
        
        if lithuania:
            logger.info("Литва уже существует, пропускаю инициализацию")
            return
        
        # Create Lithuania region
        logger.info("Создаю регион: Литва")
        lithuania = await LocationService.create_region(
            session=session,
            name="Литва",
            code="LT"
        )
        
        # Create cities and districts
        for city_name, districts in LITHUANIA_STRUCTURE.items():
            logger.info(f"Создаю город: {city_name}")
            city = await LocationService.create_city(
                session=session,
                name=city_name,
                region_id=lithuania.id
            )
            
            # Create districts
            for district_name in districts:
                logger.info(f"  Создаю микрорайон: {district_name}")
                district = District(
                    name=district_name,
                    city_id=city.id,
                    is_active=True
                )
                session.add(district)
        
        await session.commit()
        logger.info("✅ База данных инициализирована: Литва, 10 городов, все микрорайоны")
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        await session.rollback()
        raise


async def main():
    """Main initialization function."""
    logger.info("Creating database tables...")
    
    # Create tables
    async with db.engine.begin() as conn:
        from database.models import Base
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")
    
    # Initialize data
    async for session in db.get_session():
        await init_db_data(session)
        break
    
    logger.info("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
