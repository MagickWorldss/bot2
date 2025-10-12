"""Seller product management handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.image_service import ImageService
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name='seller_handlers')


@router.message(F.text == "📦 Мои товары")
async def my_products(message: Message, user: User, session: AsyncSession):
    """Show seller's products."""
    # Check if user is seller, moderator or admin
    if user.role not in ['seller', 'moderator', 'admin']:
        await message.answer("⛔️ У вас нет доступа к этой функции.")
        return
    
    # Get products added by this user
    if user.role == 'admin' or user.role == 'moderator':
        # Admins and moderators can see all products
        images = await ImageService.get_all_images(session, limit=50)
        title = "📦 **Все товары в системе:**"
    else:
        # Sellers see only their products
        images = await ImageService.get_images_by_uploader(session, user.id)
        title = "📦 **Мои товары:**"
    
    if not images:
        await message.answer(
            "📭 У вас пока нет добавленных товаров.\n\n"
            "Используйте: /god → ➕ Добавить товар",
            reply_markup=main_menu_keyboard(user_role=user.role)
        )
        return
    
    # Build keyboard with products
    builder = InlineKeyboardBuilder()
    
    text = f"{title}\n\n"
    
    for img in images[:20]:  # Show first 20
        await session.refresh(img, ['region', 'city'])
        status_emoji = "✅" if not img.is_sold else "❌"
        
        text += (
            f"{status_emoji} **Товар #{img.id}**\n"
            f"📍 {img.region.name}, {img.city.name}\n"
            f"💶 Цена: €{img.price_sol:.2f}\n"
            f"📊 Статус: {'Продан' if img.is_sold else 'В продаже'}\n\n"
        )
        
        builder.button(
            text=f"{'✅' if not img.is_sold else '❌'} Товар #{img.id}",
            callback_data=f"manage_product_{img.id}"
        )
    
    builder.button(text="🔙 Назад", callback_data="back_to_main_from_products")
    builder.adjust(2)
    
    await message.answer(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("manage_product_"))
async def manage_product(callback: CallbackQuery, user: User, session: AsyncSession):
    """Manage specific product."""
    product_id = int(callback.data.split("_")[2])
    
    # Check access
    if user.role not in ['seller', 'moderator', 'admin']:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    # Get product
    image = await ImageService.get_image_by_id(session, product_id)
    
    if not image:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    # Check if seller owns this product (except for admins/moderators)
    if user.role == 'seller' and image.uploaded_by != user.id:
        await callback.answer("⛔️ Это не ваш товар", show_alert=True)
        return
    
    await session.refresh(image, ['region', 'city'])
    
    builder = InlineKeyboardBuilder()
    
    # Add actions
    if not image.is_sold:
        builder.button(text="❌ Снять с продажи", callback_data=f"deactivate_product_{product_id}")
    else:
        builder.button(text="✅ Вернуть в продажу", callback_data=f"activate_product_{product_id}")
    
    builder.button(text="🗑 Удалить товар", callback_data=f"delete_product_{product_id}")
    builder.button(text="🔙 К списку", callback_data="back_to_my_products")
    builder.adjust(1)
    
    text = (
        f"📦 **Товар #{image.id}**\n\n"
        f"📍 Регион: {image.region.name}\n"
        f"🏙 Город: {image.city.name}\n"
        f"💶 Цена: €{image.price_sol:.2f}\n"
        f"📊 Статус: {'❌ Продан' if image.is_sold else '✅ В продаже'}\n"
        f"📅 Добавлен: {image.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    )
    
    if image.description:
        text += f"\n📝 Описание: {image.description}"
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("deactivate_product_"))
async def deactivate_product(callback: CallbackQuery, user: User, session: AsyncSession):
    """Mark product as sold (deactivate)."""
    product_id = int(callback.data.split("_")[2])
    
    image = await ImageService.get_image_by_id(session, product_id)
    
    if not image or (user.role == 'seller' and image.uploaded_by != user.id):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    image.is_sold = True
    await session.commit()
    
    await callback.answer("✅ Товар снят с продажи", show_alert=True)
    
    # Refresh view
    await manage_product(callback, user, session)


@router.callback_query(F.data.startswith("activate_product_"))
async def activate_product(callback: CallbackQuery, user: User, session: AsyncSession):
    """Mark product as available (activate)."""
    product_id = int(callback.data.split("_")[2])
    
    image = await ImageService.get_image_by_id(session, product_id)
    
    if not image or (user.role == 'seller' and image.uploaded_by != user.id):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    image.is_sold = False
    image.sold_at = None
    await session.commit()
    
    await callback.answer("✅ Товар возвращен в продажу", show_alert=True)
    
    # Refresh view
    await manage_product(callback, user, session)


@router.callback_query(F.data.startswith("delete_product_"))
async def delete_product(callback: CallbackQuery, user: User, session: AsyncSession):
    """Delete product."""
    product_id = int(callback.data.split("_")[2])
    
    image = await ImageService.get_image_by_id(session, product_id)
    
    if not image or (user.role == 'seller' and image.uploaded_by != user.id):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    # Delete product
    await session.delete(image)
    await session.commit()
    
    await callback.answer("🗑 Товар удален", show_alert=True)
    await callback.message.delete()


@router.callback_query(F.data == "back_to_my_products")
async def back_to_my_products(callback: CallbackQuery, user: User, session: AsyncSession):
    """Return to products list."""
    await my_products(callback.message, user, session)
    await callback.message.delete()


@router.callback_query(F.data == "back_to_main_from_products")
async def back_to_main_from_products(callback: CallbackQuery, user: User):
    """Return to main menu."""
    await callback.message.edit_text("🏠 Главное меню")
    await callback.answer()

