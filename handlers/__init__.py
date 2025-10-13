"""Handlers package."""
from aiogram import Router
from handlers import (
    user_handlers,
    admin_handlers,
    catalog_handlers,
    wallet_handlers,
    language_handlers,
    referral_handlers,
    cart_handlers,
    achievement_handlers,
    daily_bonus_handlers,
    quest_handlers,
    quiz_handlers,
    ticket_handlers,
    admin_promocode_handlers,
    staff_handlers,
    admin_staff_handlers,
    menu_handlers,
    admin_support_handlers,
    user_promocode_handlers,
    seller_handlers,
    admin_quest_handlers,
    roulette_handlers,
    admin_roulette_handlers,
    real_quest_handlers,
    admin_real_quest_handlers,
)


def setup_routers() -> Router:
    """Setup all routers."""
    router = Router()
    
    # Include sub-routers
    router.include_router(user_handlers.router)
    router.include_router(admin_handlers.router)
    router.include_router(catalog_handlers.router)
    router.include_router(wallet_handlers.router)
    router.include_router(language_handlers.router)
    router.include_router(referral_handlers.router)
    router.include_router(cart_handlers.router)
    router.include_router(achievement_handlers.router)
    router.include_router(daily_bonus_handlers.router)
    router.include_router(quest_handlers.router)
    router.include_router(quiz_handlers.router)
    router.include_router(ticket_handlers.router)
    router.include_router(admin_promocode_handlers.router)
    router.include_router(staff_handlers.router)
    router.include_router(admin_staff_handlers.router)
    router.include_router(menu_handlers.router)
    router.include_router(admin_support_handlers.router)
    router.include_router(user_promocode_handlers.router)
    router.include_router(seller_handlers.router)
    router.include_router(admin_quest_handlers.router)
    router.include_router(roulette_handlers.router)
    router.include_router(admin_roulette_handlers.router)
    router.include_router(real_quest_handlers.router)
    router.include_router(admin_real_quest_handlers.router)
    
    return router


__all__ = ['setup_routers']

