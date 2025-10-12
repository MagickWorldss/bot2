"""Database models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Float, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model."""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Wallet
    wallet_address: Mapped[str] = mapped_column(String(255), unique=True)
    wallet_private_key: Mapped[str] = mapped_column(Text)  # Encrypted
    balance_sol: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Location
    region_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('regions.id'), nullable=True)
    city_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('cities.id'), nullable=True)
    
    # Settings
    language: Mapped[str] = mapped_column(String(10), default='ru')  # ru, en, lt, pl, de, cs
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    region: Mapped[Optional["Region"]] = relationship("Region", back_populates="users")
    city: Mapped[Optional["City"]] = relationship("City", back_populates="users")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user")
    purchases: Mapped[list["Purchase"]] = relationship("Purchase", back_populates="user")


class Region(Base):
    """Region (Country) model."""
    __tablename__ = 'regions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)  # ISO country code
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    cities: Mapped[list["City"]] = relationship("City", back_populates="region", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship("User", back_populates="region")
    images: Mapped[list["Image"]] = relationship("Image", back_populates="region")


class City(Base):
    """City model."""
    __tablename__ = 'cities'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey('regions.id'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="cities")
    users: Mapped[list["User"]] = relationship("User", back_populates="city")
    images: Mapped[list["Image"]] = relationship("Image", back_populates="city")


class Image(Base):
    """Image (Product) model."""
    __tablename__ = 'images'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(255), unique=True)  # Telegram file ID
    file_path: Mapped[str] = mapped_column(String(500))  # Local file path
    
    # Pricing
    price_sol: Mapped[float] = mapped_column(Float)
    
    # Location
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey('regions.id'))
    city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.id'))
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[int] = mapped_column(BigInteger)  # Admin user ID
    
    # Status
    is_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="images")
    city: Mapped["City"] = relationship("City", back_populates="images")
    purchase: Mapped[Optional["Purchase"]] = relationship("Purchase", back_populates="image", uselist=False)


class Transaction(Base):
    """Transaction model for deposits and withdrawals."""
    __tablename__ = 'transactions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    
    # Transaction details
    tx_type: Mapped[str] = mapped_column(String(20))  # deposit, withdrawal, purchase
    amount_sol: Mapped[float] = mapped_column(Float)
    fee_sol: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Blockchain
    tx_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    from_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    to_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default='pending')  # pending, completed, failed
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")


class Purchase(Base):
    """Purchase model."""
    __tablename__ = 'purchases'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey('images.id'), unique=True)
    
    price_paid_sol: Mapped[float] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="purchases")
    image: Mapped["Image"] = relationship("Image", back_populates="purchase")


class DepositRequest(Base):
    """Deposit request with reserved exchange rate."""
    __tablename__ = 'deposit_requests'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    
    # Amounts
    eur_amount: Mapped[float] = mapped_column(Float)  # Amount in EUR
    sol_amount: Mapped[float] = mapped_column(Float)  # Required SOL amount
    reserved_rate: Mapped[float] = mapped_column(Float)  # SOL/EUR rate at creation
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default='pending')  # pending, completed, expired, cancelled
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)  # created_at + 30 minutes
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PriceList(Base):
    """Price list text (editable by admin)."""
    __tablename__ = 'price_lists'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    language: Mapped[str] = mapped_column(String(10), default='ru')  # ru, en, lt, pl, de, cs
    content: Mapped[str] = mapped_column(Text)
    
    updated_by: Mapped[int] = mapped_column(BigInteger)  # Admin who updated
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class AdminLog(Base):
    """Admin action log."""
    __tablename__ = 'admin_logs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

