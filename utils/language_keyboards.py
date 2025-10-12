"""Keyboards for language selection."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.language_service import LANGUAGE_NAMES


def language_selection_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard."""
    builder = InlineKeyboardBuilder()
    
    for code, name in LANGUAGE_NAMES.items():
        builder.button(
            text=name,
            callback_data=f"lang_{code}"
        )
    
    builder.adjust(2)
    return builder.as_markup()


def admin_pricelist_keyboard() -> InlineKeyboardMarkup:
    """Admin keyboard for price list management."""
    builder = InlineKeyboardBuilder()
    
    for code, name in LANGUAGE_NAMES.items():
        builder.button(
            text=f"{name} ✏️",
            callback_data=f"edit_pricelist_{code}"
        )
    
    builder.adjust(2)
    return builder.as_markup()

