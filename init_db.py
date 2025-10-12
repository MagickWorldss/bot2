"""Initialize database with default data."""
import asyncio
from database.database import db
from database.models import Region, City
from services.location_service import LocationService
from sqlalchemy.ext.asyncio import AsyncSession


async def init_default_regions():
    """Initialize default EU regions and cities."""
    async for session in db.get_session():
        # Check if regions already exist
        regions = await LocationService.get_all_regions(session, active_only=False)
        
        if regions:
            print("Database already has regions. Skipping initialization.")
            return
        
        print("Initializing default regions and cities...")
        
        # EU Countries with major cities
        default_data = [
            {
                'name': 'Germany',
                'code': 'DE',
                'cities': ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne', 'Stuttgart']
            },
            {
                'name': 'France',
                'code': 'FR',
                'cities': ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice', 'Nantes']
            },
            {
                'name': 'Spain',
                'code': 'ES',
                'cities': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Bilbao', 'Malaga']
            },
            {
                'name': 'Italy',
                'code': 'IT',
                'cities': ['Rome', 'Milan', 'Naples', 'Turin', 'Florence', 'Venice']
            },
            {
                'name': 'Netherlands',
                'code': 'NL',
                'cities': ['Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht', 'Eindhoven']
            },
            {
                'name': 'Belgium',
                'code': 'BE',
                'cities': ['Brussels', 'Antwerp', 'Ghent', 'Bruges', 'Liege']
            },
            {
                'name': 'Poland',
                'code': 'PL',
                'cities': ['Warsaw', 'Krakow', 'Wroclaw', 'Poznan', 'Gdansk']
            },
            {
                'name': 'Austria',
                'code': 'AT',
                'cities': ['Vienna', 'Salzburg', 'Innsbruck', 'Graz', 'Linz']
            },
            {
                'name': 'Czech Republic',
                'code': 'CZ',
                'cities': ['Prague', 'Brno', 'Ostrava', 'Plzen', 'Liberec']
            },
            {
                'name': 'Portugal',
                'code': 'PT',
                'cities': ['Lisbon', 'Porto', 'Braga', 'Coimbra', 'Faro']
            },
            {
                'name': 'Sweden',
                'code': 'SE',
                'cities': ['Stockholm', 'Gothenburg', 'Malmo', 'Uppsala', 'Vasteras']
            },
            {
                'name': 'Denmark',
                'code': 'DK',
                'cities': ['Copenhagen', 'Aarhus', 'Odense', 'Aalborg', 'Esbjerg']
            },
        ]
        
        for region_data in default_data:
            try:
                # Create region
                region = await LocationService.create_region(
                    session,
                    name=region_data['name'],
                    code=region_data['code']
                )
                print(f"✓ Created region: {region.name}")
                
                # Create cities
                for city_name in region_data['cities']:
                    city = await LocationService.create_city(
                        session,
                        name=city_name,
                        region_id=region.id
                    )
                    print(f"  ✓ Created city: {city.name}")
                
            except Exception as e:
                print(f"✗ Error creating region {region_data['name']}: {e}")
        
        print("\n✅ Database initialization complete!")


async def main():
    """Main initialization function."""
    print("Creating database tables...")
    await db.create_tables()
    print("✓ Database tables created")
    
    print("\nInitializing default data...")
    await init_default_regions()


if __name__ == '__main__':
    asyncio.run(main())

