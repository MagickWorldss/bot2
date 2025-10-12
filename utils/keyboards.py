"""Keyboard layouts for the bot."""
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from typing import List, Optional
from database.models import Region, City, Image


def main_menu_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    from services.language_service import language_service
    
    builder = ReplyKeyboardBuilder()
    # Row 1
    builder.button(text=language_service.get_text(language, 'catalog'))
    builder.button(text="🛒 Корзина")
    # Row 2
    builder.button(text=language_service.get_text(language, 'balance'))
    builder.button(text="🎁 Стафф")
    # Row 3
    builder.button(text=language_service.get_text(language, 'select_region'))
    builder.button(text="🎁 Реферальная программа")
    # Row 4
    builder.button(text="🏆 Достижения")
    builder.button(text="🎁 Ежедневный бонус")
    # Row 5
    builder.button(text="🎯 Квесты")
    builder.button(text="🧩 Квиз")
    # Row 6
    builder.button(text="🎫 Поддержка")
    builder.button(text=language_service.get_text(language, 'purchase_history'))
    # Row 7
    builder.button(text=language_service.get_text(language, 'price_list'))
    builder.button(text=language_service.get_text(language, 'language'))
    # Row 8
    builder.button(text=language_service.get_text(language, 'help'))
    
    builder.adjust(2, 2, 2, 2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Admin menu keyboard."""
    builder = ReplyKeyboardBuilder()
    # Row 1
    builder.button(text="➕ Добавить товар")
    builder.button(text="📊 Статистика")
    # Row 2
    builder.button(text="🗂 Управление регионами")
    builder.button(text="👥 Управление пользователями")
    # Row 3
    builder.button(text="🎫 Промокоды")
    builder.button(text="🎁 Стафф товары")
    # Row 4
    builder.button(text="🎯 Квесты")
    builder.button(text="🧩 Квизы")
    # Row 5
    builder.button(text="📢 Рассылка")
    builder.button(text="🎄 События")
    # Row 6
    builder.button(text="🎫 Тикеты поддержки")
    builder.button(text="✏️ Редактировать прайс-лист")
    # Row 7
    builder.button(text="🔙 Главное меню")
    
    builder.adjust(2, 2, 2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Cancel keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отмена")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def regions_keyboard(regions: List[Region]) -> InlineKeyboardMarkup:
    """Inline keyboard with regions."""
    builder = InlineKeyboardBuilder()
    for region in regions:
        builder.button(
            text=f"{region.name}",
            callback_data=f"region_{region.id}"
        )
    builder.adjust(2)
    return builder.as_markup()


def cities_keyboard(cities: List[City], back_to_regions: bool = True) -> InlineKeyboardMarkup:
    """Inline keyboard with cities."""
    builder = InlineKeyboardBuilder()
    for city in cities:
        builder.button(
            text=f"{city.name}",
            callback_data=f"city_{city.id}"
        )
    
    if back_to_regions:
        builder.button(
            text="◀️ Назад к регионам",
            callback_data="back_to_regions"
        )
    
    builder.adjust(2)
    return builder.as_markup()


def districts_keyboard(districts: List, back_callback: str = "back_to_cities") -> InlineKeyboardMarkup:
    """Inline keyboard with districts."""
    from database.models import District
    builder = InlineKeyboardBuilder()
    
    for district in districts:
        builder.button(
            text=f"📍 {district.name}",
            callback_data=f"district_{district.id}"
        )
    
    builder.button(
        text="◀️ Назад",
        callback_data=back_callback
    )
    
    builder.adjust(2)
    return builder.as_markup()


def catalog_keyboard(
    images: List[Image],
    page: int = 0,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """Inline keyboard for catalog."""
    builder = InlineKeyboardBuilder()
    
    for image in images:
        builder.button(
            text=f"🖼 Товар #{image.id} - {image.price_sol} SOL",
            callback_data=f"view_image_{image.id}"
        )
    
    # Pagination
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Пред.",
                callback_data=f"catalog_page_{page-1}"
            ))
        
        nav_buttons.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}",
            callback_data="current_page"
        ))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="След. ▶️",
                callback_data=f"catalog_page_{page+1}"
            ))
        
        builder.row(*nav_buttons)
    
    builder.adjust(1)
    return builder.as_markup()


def image_view_keyboard(image_id: int, price: float) -> InlineKeyboardMarkup:
    """Inline keyboard for viewing image."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💳 Купить за {price} SOL",
        callback_data=f"buy_image_{image_id}"
    )
    builder.button(
        text="◀️ Назад к каталогу",
        callback_data="back_to_catalog"
    )
    builder.adjust(1)
    return builder.as_markup()


def confirm_purchase_keyboard(image_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for purchase confirmation."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить покупку",
        callback_data=f"confirm_buy_{image_id}"
    )
    builder.button(
        text="❌ Отменить",
        callback_data="cancel_purchase"
    )
    builder.adjust(1)
    return builder.as_markup()


def wallet_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for wallet operations."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💵 Пополнить баланс",
        callback_data="deposit"
    )
    builder.button(
        text="📋 История транзакций",
        callback_data="transaction_history"
    )
    builder.adjust(1)
    return builder.as_markup()


def admin_region_management_keyboard(regions: List[Region]) -> InlineKeyboardMarkup:
    """Admin keyboard for region management."""
    builder = InlineKeyboardBuilder()
    
    for region in regions:
        status = "✅" if region.is_active else "❌"
        builder.button(
            text=f"{status} {region.name}",
            callback_data=f"admin_region_{region.id}"
        )
    
    builder.button(
        text="➕ Добавить регион",
        callback_data="admin_add_region"
    )
    
    builder.adjust(2)
    return builder.as_markup()


def admin_region_actions_keyboard(region_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Admin keyboard for region actions."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🏙 Управление городами",
        callback_data=f"admin_cities_{region_id}"
    )
    
    toggle_text = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    builder.button(
        text=toggle_text,
        callback_data=f"admin_toggle_region_{region_id}"
    )
    
    builder.button(
        text="🗑 Удалить регион",
        callback_data=f"admin_delete_region_{region_id}"
    )
    
    builder.button(
        text="◀️ Назад",
        callback_data="admin_regions"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def admin_district_management_keyboard(districts: List, city_id: int) -> InlineKeyboardMarkup:
    """Admin keyboard for district management."""
    builder = InlineKeyboardBuilder()
    
    for district in districts:
        status = "✅" if district.is_active else "❌"
        builder.button(
            text=f"{status} {district.name}",
            callback_data=f"admin_district_{district.id}"
        )
    
    builder.button(
        text="➕ Добавить микрорайон",
        callback_data=f"admin_add_district_{city_id}"
    )
    
    builder.button(
        text="◀️ Назад к городу",
        callback_data=f"admin_back_to_city_{city_id}"
    )
    
    builder.adjust(2)
    return builder.as_markup()


def admin_city_management_keyboard(
    cities: List[City],
    region_id: int
) -> InlineKeyboardMarkup:
    """Admin keyboard for city management."""
    builder = InlineKeyboardBuilder()
    
    for city in cities:
        status = "✅" if city.is_active else "❌"
        builder.button(
            text=f"{status} {city.name}",
            callback_data=f"admin_city_{city.id}"
        )
    
    builder.button(
        text="➕ Добавить город",
        callback_data=f"admin_add_city_{region_id}"
    )
    
    builder.button(
        text="◀️ Назад к регионам",
        callback_data="admin_regions"
    )
    
    builder.adjust(2)
    return builder.as_markup()


def back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
    """Simple back button."""
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data=callback_data)
    return builder.as_markup()

