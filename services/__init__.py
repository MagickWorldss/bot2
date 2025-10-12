"""Services package."""
from services.wallet_service import wallet_service
from services.user_service import UserService
from services.image_service import ImageService
from services.transaction_service import TransactionService
from services.price_service import price_service
from services.deposit_service import deposit_service
from services.balance_api import balance_api
from services.language_service import language_service
from services.pricelist_service import pricelist_service
from services.rating_service import rating_service
from services.referral_service import referral_service
from services.promocode_service import promocode_service
from services.cart_service import cart_service
from services.achievement_service import achievement_service
from services.daily_bonus_service import daily_bonus_service
from services.quest_service import quest_service
from services.auction_service import auction_service
from services.notification_service import notification_service
from services.ticket_service import ticket_service
from services.seasonal_service import seasonal_service
from services.quiz_service import quiz_service
from services.role_service import role_service

__all__ = [
    'wallet_service',
    'UserService',
    'ImageService',
    'TransactionService',
    'price_service',
    'deposit_service',
    'balance_api',
    'language_service',
    'pricelist_service',
    'rating_service',
    'referral_service',
    'promocode_service',
    'cart_service',
    'achievement_service',
    'daily_bonus_service',
    'quest_service',
    'auction_service',
    'notification_service',
    'ticket_service',
    'seasonal_service',
    'quiz_service',
    'role_service',
]

