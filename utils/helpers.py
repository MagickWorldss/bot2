"""Helper functions."""
from typing import Optional
from datetime import datetime


def format_sol_amount(amount: float) -> str:
    """Format SOL amount for display."""
    return f"{amount:.4f} SOL"


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%d.%m.%Y %H:%M")


def truncate_address(address: str, start: int = 6, end: int = 4) -> str:
    """Truncate wallet address for display."""
    if len(address) <= start + end:
        return address
    return f"{address[:start]}...{address[-end:]}"


def is_admin(user_id: int, admin_ids: list[int]) -> bool:
    """Check if user is admin."""
    return user_id in admin_ids


def validate_sol_amount(amount_str: str) -> Optional[float]:
    """Validate and parse SOL amount."""
    try:
        amount = float(amount_str.replace(',', '.'))
        if amount <= 0:
            return None
        return amount
    except ValueError:
        return None


def paginate_list(items: list, page: int, items_per_page: int = 5) -> tuple[list, int]:
    """
    Paginate a list.
    
    Returns:
        Tuple of (page_items, total_pages)
    """
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    
    return items[start_idx:end_idx], total_pages

