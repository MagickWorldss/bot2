"""Price list service."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import PriceList


class PriceListService:
    """Service for managing price lists."""
    
    @staticmethod
    async def get_price_list(
        session: AsyncSession,
        language: str = 'ru'
    ) -> Optional[str]:
        """Get price list for language."""
        result = await session.execute(
            select(PriceList)
            .where(PriceList.language == language)
            .order_by(PriceList.updated_at.desc())
        )
        
        price_list = result.scalar_one_or_none()
        
        if price_list:
            return price_list.content
        
        # Return default if not found
        return PriceListService._get_default_price_list(language)
    
    @staticmethod
    def _get_default_price_list(language: str) -> str:
        """Get default price list text."""
        defaults = {
            'ru': """💵 **Прайс-лист**

📦 Цифровые товары

🖼 Изображения:
• Стандартное - от €5.00
• Премиум - от €10.00
• Эксклюзив - от €20.00

📍 Цены зависят от региона и города

⚠️ Цены указаны в евро (€)
Оплата в криптовалюте SOL по текущему курсу.

Для просмотра каталога: 🛍 Каталог
""",
            'en': """💵 **Price List**

📦 Digital Products

🖼 Images:
• Standard - from €5.00
• Premium - from €10.00
• Exclusive - from €20.00

📍 Prices depend on region and city

⚠️ Prices are in euros (€)
Payment in SOL cryptocurrency at current rate.

To view catalog: 🛍 Catalog
""",
            'lt': """💵 **Kainų Sąrašas**

📦 Skaitmeniniai Produktai

🖼 Paveikslėliai:
• Standartinis - nuo €5.00
• Premium - nuo €10.00
• Ekskluzyvus - nuo €20.00

📍 Kainos priklauso nuo regiono ir miesto

⚠️ Kainos eurais (€)
Mokėjimas SOL kriptovaliuta pagal dabartinį kursą.

Katalogas: 🛍 Katalogas
""",
            'pl': """💵 **Cennik**

📦 Produkty Cyfrowe

🖼 Obrazy:
• Standardowy - od €5.00
• Premium - od €10.00
• Ekskluzywny - od €20.00

📍 Ceny zależą od regionu i miasta

⚠️ Ceny w euro (€)
Płatność w kryptowalucie SOL po aktualnym kursie.

Katalog: 🛍 Katalog
""",
            'de': """💵 **Preisliste**

📦 Digitale Produkte

🖼 Bilder:
• Standard - ab €5.00
• Premium - ab €10.00
• Exklusiv - ab €20.00

📍 Preise hängen von Region und Stadt ab

⚠️ Preise in Euro (€)
Zahlung in SOL-Kryptowährung zum aktuellen Kurs.

Katalog: 🛍 Katalog
""",
            'cs': """💵 **Ceník**

📦 Digitální Produkty

🖼 Obrázky:
• Standardní - od €5.00
• Premium - od €10.00
• Exkluzivní - od €20.00

📍 Ceny závisí na regionu a městě

⚠️ Ceny v eurech (€)
Platba v kryptoměně SOL podle aktuálního kurzu.

Katalog: 🛍 Katalog
"""
        }
        
        return defaults.get(language, defaults['ru'])
    
    @staticmethod
    async def update_price_list(
        session: AsyncSession,
        language: str,
        content: str,
        admin_id: int
    ) -> PriceList:
        """Update or create price list."""
        # Try to get existing
        result = await session.execute(
            select(PriceList).where(PriceList.language == language)
        )
        price_list = result.scalar_one_or_none()
        
        if price_list:
            # Update existing
            price_list.content = content
            price_list.updated_by = admin_id
        else:
            # Create new
            price_list = PriceList(
                language=language,
                content=content,
                updated_by=admin_id
            )
            session.add(price_list)
        
        await session.commit()
        await session.refresh(price_list)
        
        return price_list
    
    @staticmethod
    async def get_all_price_lists(session: AsyncSession) -> dict:
        """Get all price lists."""
        result = await session.execute(
            select(PriceList).order_by(PriceList.language)
        )
        
        price_lists = result.scalars().all()
        
        return {pl.language: pl.content for pl in price_lists}


# Global price list service
pricelist_service = PriceListService()

