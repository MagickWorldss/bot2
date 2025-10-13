"""Preview categories and icons for products."""

# Категории товаров с превью-иконками
PREVIEW_CATEGORIES = {
    "winter": {
        "name": "❄️ Зима",
        "icon": "❄️",
        "description": "Зимние пейзажи, снег, мороз"
    },
    "pharmacy": {
        "name": "💊 Фармакология", 
        "icon": "💊",
        "description": "Медицинские препараты, лекарства"
    },
    "summer": {
        "name": "☀️ Лето",
        "icon": "☀️", 
        "description": "Летние пейзажи, солнце, природа"
    },
    "nature": {
        "name": "🌿 Природа",
        "icon": "🌿",
        "description": "Природные пейзажи, растения"
    },
    "city": {
        "name": "🏙️ Город",
        "icon": "🏙️",
        "description": "Городские пейзажи, архитектура"
    },
    "food": {
        "name": "🍕 Еда",
        "icon": "🍕",
        "description": "Кулинария, рецепты, продукты"
    },
    "art": {
        "name": "🎨 Искусство",
        "icon": "🎨",
        "description": "Художественные работы, творчество"
    },
    "tech": {
        "name": "💻 Технологии",
        "icon": "💻",
        "description": "Электроника, гаджеты, IT"
    },
    "fashion": {
        "name": "👗 Мода",
        "icon": "👗",
        "description": "Одежда, аксессуары, стиль"
    },
    "sports": {
        "name": "⚽ Спорт",
        "icon": "⚽",
        "description": "Спортивные товары, активность"
    },
    "animals": {
        "name": "🐕 Животные",
        "icon": "🐕",
        "description": "Домашние животные, питомцы"
    },
    "travel": {
        "name": "✈️ Путешествия",
        "icon": "✈️",
        "description": "Туризм, достопримечательности"
    }
}

def get_category_info(category_key: str) -> dict:
    """Get category information by key."""
    return PREVIEW_CATEGORIES.get(category_key, {
        "name": "📦 Другое",
        "icon": "📦",
        "description": "Разные товары"
    })

def get_all_categories() -> dict:
    """Get all available categories."""
    return PREVIEW_CATEGORIES

def format_category_display(category_key: str) -> str:
    """Format category for display."""
    category = get_category_info(category_key)
    return f"{category['icon']} {category['name']}"

def get_category_keyboard():
    """Get keyboard for category selection."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    for key, category in PREVIEW_CATEGORIES.items():
        builder.button(
            text=f"{category['icon']} {category['name']}",
            callback_data=f"category_{key}"
        )
    
    builder.adjust(2)  # 2 columns
    return builder.as_markup()
