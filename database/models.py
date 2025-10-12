"""Database models for Telegram Shop Bot."""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Float, DateTime, Integer, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model."""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Wallet
    wallet_address: Mapped[str] = mapped_column(String(255), unique=True)
    wallet_private_key: Mapped[str] = mapped_column(Text)  # Encrypted
    balance_sol: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Admin & Roles
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(50), default='user')  # user, seller, moderator, admin
    
    # Location
    region_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('regions.id'), nullable=True)
    city_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('cities.id'), nullable=True)
    
    # Settings
    language: Mapped[str] = mapped_column(String(10), default='ru')  # ru, en, lt, pl, de, cs
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Rating
    rating: Mapped[float] = mapped_column(Float, default=0.0)  # User rating (-100 to +100)
    total_purchases: Mapped[int] = mapped_column(Integer, default=0)
    total_spent_sol: Mapped[float] = mapped_column(Float, default=0.0)
    refunds_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Referral system
    referral_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    referred_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    referral_earnings_sol: Mapped[float] = mapped_column(Float, default=0.0)
    total_referrals: Mapped[int] = mapped_column(Integer, default=0)
    
    # Achievements & Gamification
    achievement_points: Mapped[int] = mapped_column(Integer, default=0)
    daily_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_bonus: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Region(Base):
    """Region model."""
    __tablename__ = 'regions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class City(Base):
    """City model."""
    __tablename__ = 'cities'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey('regions.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Image(Base):
    """Image/Product model."""
    __tablename__ = 'images'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price_sol: Mapped[float] = mapped_column(Float)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey('regions.id'))
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.id'))
    
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    sold_to: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Pre-order functionality
    is_preorder: Mapped[bool] = mapped_column(Boolean, default=False)
    available_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Auction functionality
    is_auction: Mapped[bool] = mapped_column(Boolean, default=False)
    auction_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    starting_price_sol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_bid_sol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    highest_bidder_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    
    # Stock & urgency
    stock_count: Mapped[int] = mapped_column(Integer, default=1)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Transaction(Base):
    """Transaction model."""
    __tablename__ = 'transactions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    tx_type: Mapped[str] = mapped_column(String(50))  # deposit, withdrawal, purchase, refund, referral_bonus
    amount_sol: Mapped[float] = mapped_column(Float)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Purchase(Base):
    """Purchase history model."""
    __tablename__ = 'purchases'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey('images.id'))
    price_sol: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AdminLog(Base):
    """Admin action log."""
    __tablename__ = 'admin_logs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DepositRequest(Base):
    """Deposit request with reserved exchange rate."""
    __tablename__ = 'deposit_requests'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    eur_amount: Mapped[float] = mapped_column(Float)
    sol_amount: Mapped[float] = mapped_column(Float)
    reserved_rate: Mapped[float] = mapped_column(Float)  # SOL/EUR rate at time of request
    status: Mapped[str] = mapped_column(String(50), default='pending')  # pending, completed, expired
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PriceList(Base):
    """Editable price list content."""
    __tablename__ = 'price_lists'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language: Mapped[str] = mapped_column(String(10), unique=True)  # ru, en, lt, pl, de, cs
    content: Mapped[str] = mapped_column(Text)
    updated_by: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Promocode(Base):
    """Promocode model."""
    __tablename__ = 'promocodes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    discount_type: Mapped[str] = mapped_column(String(20))  # percent, fixed, free_item
    discount_value: Mapped[float] = mapped_column(Float)  # percentage or SOL amount
    
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = unlimited
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PromocodeUsage(Base):
    """Promocode usage tracking."""
    __tablename__ = 'promocode_usage'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    promocode_id: Mapped[int] = mapped_column(Integer, ForeignKey('promocodes.id'))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    used_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Cart(Base):
    """Shopping cart model."""
    __tablename__ = 'carts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey('images.id'))
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Achievement(Base):
    """Achievement definitions."""
    __tablename__ = 'achievements'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name_ru: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    description_ru: Mapped[str] = mapped_column(Text)
    description_en: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(10))  # emoji
    points: Mapped[int] = mapped_column(Integer)
    condition_type: Mapped[str] = mapped_column(String(50))  # purchases, spending, referrals, streak
    condition_value: Mapped[int] = mapped_column(Integer)


class UserAchievement(Base):
    """User achievements tracking."""
    __tablename__ = 'user_achievements'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    achievement_id: Mapped[int] = mapped_column(Integer, ForeignKey('achievements.id'))
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Quest(Base):
    """Quest/Challenge definitions."""
    __tablename__ = 'quests'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_ru: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    description_ru: Mapped[str] = mapped_column(Text)
    description_en: Mapped[str] = mapped_column(Text)
    
    quest_type: Mapped[str] = mapped_column(String(50))  # daily, weekly, monthly, special
    condition_type: Mapped[str] = mapped_column(String(50))  # purchases, spending, items
    condition_value: Mapped[int] = mapped_column(Integer)
    
    reward_type: Mapped[str] = mapped_column(String(50))  # sol, points, promocode
    reward_value: Mapped[float] = mapped_column(Float)
    
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserQuest(Base):
    """User quest progress."""
    __tablename__ = 'user_quests'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    quest_id: Mapped[int] = mapped_column(Integer, ForeignKey('quests.id'))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SupportTicket(Base):
    """Support ticket system."""
    __tablename__ = 'support_tickets'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    subject: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default='open')  # open, in_progress, closed
    priority: Mapped[str] = mapped_column(String(50), default='normal')  # low, normal, high
    assigned_to: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class TicketMessage(Base):
    """Support ticket messages."""
    __tablename__ = 'ticket_messages'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey('support_tickets.id'))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    message: Mapped[str] = mapped_column(Text)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SeasonalEvent(Base):
    """Seasonal events (New Year, Black Friday, etc)."""
    __tablename__ = 'seasonal_events'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_ru: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    description_ru: Mapped[str] = mapped_column(Text)
    description_en: Mapped[str] = mapped_column(Text)
    
    event_type: Mapped[str] = mapped_column(String(50))  # sale, bonus, special
    discount_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bonus_multiplier: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ends_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Quiz(Base):
    """Quiz/Riddle definitions."""
    __tablename__ = 'quizzes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_ru: Mapped[str] = mapped_column(Text)
    question_en: Mapped[str] = mapped_column(Text)
    
    answers: Mapped[str] = mapped_column(JSON)  # List of answer options
    correct_answer_index: Mapped[int] = mapped_column(Integer)
    
    reward_type: Mapped[str] = mapped_column(String(50))  # sol, points, promocode
    reward_value: Mapped[float] = mapped_column(Float)
    
    difficulty: Mapped[str] = mapped_column(String(50))  # easy, medium, hard
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserQuiz(Base):
    """User quiz attempts."""
    __tablename__ = 'user_quizzes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    quiz_id: Mapped[int] = mapped_column(Integer, ForeignKey('quizzes.id'))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Notification(Base):
    """Notification queue for users."""
    __tablename__ = 'notifications'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)  # None = all users
    region_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('regions.id'), nullable=True)
    
    message: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(String(50))  # new_product, news, promo
    
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AuctionBid(Base):
    """Auction bids."""
    __tablename__ = 'auction_bids'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey('images.id'))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    bid_amount_sol: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
