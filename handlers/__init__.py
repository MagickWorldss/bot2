"""Handlers package."""
from aiogram import Router
from handlers import user_handlers, admin_handlers, catalog_handlers, wallet_handlers


def setup_routers() -> Router:
    """Setup all routers."""
    router = Router()
    
    # Include sub-routers
    router.include_router(user_handlers.router)
    router.include_router(admin_handlers.router)
    router.include_router(catalog_handlers.router)
    router.include_router(wallet_handlers.router)
    
    return router


__all__ = ['setup_routers']

