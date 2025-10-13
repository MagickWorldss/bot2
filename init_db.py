"""Database initialization script for Lithuania structure."""
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
        
        # Initialize default quests
        await init_default_quests(session)
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        await session.rollback()
        raise


async def init_default_quests(session: AsyncSession):
    """Initialize default quests."""
    from database.models import Quest
    from datetime import datetime, timedelta
    
    # Check if quests already exist
    stmt = select(Quest)
    result = await session.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        logger.info("Квесты уже существуют, пропускаем инициализацию")
        return
    
    logger.info("Создаю стандартные квесты...")
    
    now = datetime.utcnow()
    
    # 1. Daily quest
    daily_quest = Quest(
        name_ru="Первая покупка дня",
        name_en="First Purchase of the Day",
        description_ru="Совершите хотя бы одну покупку сегодня и получите бонус!",
        description_en="Make at least one purchase today and get a bonus!",
        quest_type="daily",
        condition_type="purchases",
        condition_value=1,
        reward_type="sol",
        reward_value=5.0,
        starts_at=now,
        ends_at=now + timedelta(days=365),  # Active for a year
        is_active=True
    )
    session.add(daily_quest)
    logger.info("  ✅ Создан ежедневный квест: Первая покупка дня")
    
    # 2. Weekly quest
    weekly_quest = Quest(
        name_ru="Активный покупатель",
        name_en="Active Buyer",
        description_ru="Совершите 10 покупок за неделю и получите щедрую награду!",
        description_en="Make 10 purchases in a week and get a generous reward!",
        quest_type="weekly",
        condition_type="purchases",
        condition_value=10,
        reward_type="sol",
        reward_value=50.0,
        starts_at=now,
        ends_at=now + timedelta(days=365),
        is_active=True
    )
    session.add(weekly_quest)
    logger.info("  ✅ Создан еженедельный квест: Активный покупатель")
    
    # 3. Monthly quest
    monthly_quest = Quest(
        name_ru="Большой спендер",
        name_en="Big Spender",
        description_ru="Потратьте 500 EUR за месяц и получите 100 баллов достижений!",
        description_en="Spend 500 EUR in a month and get 100 achievement points!",
        quest_type="monthly",
        condition_type="spending",
        condition_value=500,
        reward_type="points",
        reward_value=100.0,
        starts_at=now,
        ends_at=now + timedelta(days=365),
        is_active=True
    )
    session.add(monthly_quest)
    logger.info("  ✅ Создан месячный квест: Большой спендер")
    
    await session.commit()
    logger.info("✅ Стандартные квесты созданы!")


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
