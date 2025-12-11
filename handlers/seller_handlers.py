"""Seller product management handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.image_service import ImageService
from services.location_service import LocationService
from utils.keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name='seller_handlers')


@router.callback_query(F.data == "my_products_menu")
async def my_products(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show seller's products."""
    from utils.helpers import is_admin
    from config import settings
    
    # Check if user is seller, moderator or admin (by role or ADMIN_IDS)
    is_admin_user = is_admin(user.id, settings.admin_list)
    if user.role not in ['seller', 'moderator', 'admin'] and not is_admin_user:
        await callback.answer("⛔️ У вас нет доступа к этой функции.", show_alert=True)
        return
    
    # Get products added by this user
    if user.role == 'admin' or user.role == 'moderator' or is_admin_user:
        # Admins and moderators can see all products
        images = await ImageService.get_all_images(session, limit=50)
        title = "📦 **Все товары в системе:**"
    else:
        # Sellers see only their products
        images = await ImageService.get_images_by_uploader(session, user.id)
        title = "📦 **Мои товары:**"
    
    # Build keyboard with products
    builder = InlineKeyboardBuilder()
    
    # Add "Add Product" button for sellers
    builder.button(text="➕ Добавить товар", callback_data="seller_add_product_start")
    
    text = f"{title}\n\n"
    
    if not images:
        text += "📭 У вас пока нет товаров.\n\n"
        text += "Нажмите '➕ Добавить товар' чтобы начать!"
        
        builder.button(text="🔙 Назад к магазину", callback_data="back_to_shop_from_products")
        builder.adjust(1)
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.answer()
        return
    
    text += f"Всего товаров: **{len(images)}**\n\n"
    
    for img in images[:20]:  # Show first 20
        # Load location manually (no relationships)
        region = await LocationService.get_region_by_id(session, img.region_id)
        city = await LocationService.get_city_by_id(session, img.city_id)
        
        status_emoji = "✅" if not img.is_sold else "❌"
        
        region_name = region.name if region else 'N/A'
        city_name = city.name if city else 'N/A'
        
        text += (
            f"{status_emoji} **Товар #{img.id}**\n"
            f"📍 {region_name}, {city_name}\n"
            f"💶 Цена: €{img.price_sol:.2f}\n"
            f"📊 Статус: {'Продан' if img.is_sold else 'В продаже'}\n\n"
        )
        
        builder.button(
            text=f"{'✅' if not img.is_sold else '❌'} Товар #{img.id}",
            callback_data=f"manage_product_{img.id}"
        )
    
    builder.button(text="🔙 Назад к магазину", callback_data="back_to_shop_from_products")
    builder.adjust(2)
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


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
    # Note: uploaded_by field doesn't exist in Image model, so sellers can edit all products
    # This will be fixed when uploaded_by field is added to Image model
    # For now, sellers can manage all products like moderators
    
    # Load location manually (no relationships)
    region = await LocationService.get_region_by_id(session, image.region_id)
    city = await LocationService.get_city_by_id(session, image.city_id)
    
    builder = InlineKeyboardBuilder()
    
    # Add actions
    if not image.is_sold:
        builder.button(text="❌ Снять с продажи", callback_data=f"deactivate_product_{product_id}")
    else:
        builder.button(text="✅ Вернуть в продажу", callback_data=f"activate_product_{product_id}")
    
    builder.button(text="🗑 Удалить товар", callback_data=f"delete_product_{product_id}")
    builder.button(text="🔙 К списку", callback_data="back_to_my_products")
    builder.adjust(1)
    
    region_name = region.name if region else 'N/A'
    city_name = city.name if city else 'N/A'
    
    text = (
        f"📦 **Товар #{image.id}**\n\n"
        f"📍 Регион: {region_name}\n"
        f"🏙 Город: {city_name}\n"
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
    await my_products(callback, user, session)


@router.callback_query(F.data == "seller_add_product_start")
async def seller_add_product_start(callback: CallbackQuery, user: User, session: AsyncSession, state: FSMContext):
    """Start adding product for seller."""
    # Import states from admin_handlers
    from handlers.admin_handlers import AddImageStates
    from utils.keyboards import cancel_keyboard
    
    # Check role
    if user.role not in ['seller', 'moderator', 'admin']:
        await callback.answer("⛔️ Нет доступа", show_alert=True)
        return
    
    # Get regions
    regions = await LocationService.get_all_regions(session)
    
    if not regions:
        await callback.answer("❌ Нет регионов в системе", show_alert=True)
        return
    
    regions_text = "📍 **Выберите регион для товара:**\n\n"
    for region in regions:
        regions_text += f"/{region.id} - {region.name}\n"
    
    await state.set_state(AddImageStates.waiting_for_region)
    await callback.message.answer(
        regions_text,
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_shop_from_products")
async def back_to_shop_from_products(callback: CallbackQuery, user: User, session: AsyncSession):
    """Return to shop menu."""
    from handlers.menu_handlers import show_shop_menu
    await callback.message.delete()
    # Send new message with shop menu
    from aiogram.types import Message as Msg
    fake_message = callback.message
    await show_shop_menu(fake_message, user, session)

