"""Catalog handlers for browsing and purchasing products."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.image_service import ImageService
from services.user_service import UserService
from services.transaction_service import TransactionService
from services.location_service import LocationService
from utils.keyboards import catalog_keyboard, image_view_keyboard, confirm_purchase_keyboard
from utils.helpers import format_sol_amount, paginate_list
from utils.preview_categories import format_category_display


router = Router(name='catalog_handlers')


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message, user: User, session: AsyncSession, state: FSMContext):
    """Show catalog of available products."""
    # Check if user selected location
    if not user.city_id:
        await message.answer(
            "⚠️ Сначала выберите ваш регион и город.\n"
            "Используйте кнопку '📍 Выбрать регион'"
        )
        return
    
    # Get available images for user's location
    images = await ImageService.get_available_images(
        session,
        region_id=user.region_id,
        city_id=user.city_id
    )
    
    if not images:
        await message.answer(
            "😔 К сожалению, в вашем регионе сейчас нет доступных товаров.\n"
            "Попробуйте зайти позже."
        )
        return
    
    # Paginate
    page_images, total_pages = paginate_list(images, 0, items_per_page=5)
    
    # Save state for pagination
    await state.update_data(catalog_page=0)
    
    keyboard = catalog_keyboard(page_images, page=0, total_pages=total_pages)
    
    await message.answer(
        f"🛍 **Каталог товаров**\n\n"
        f"Найдено товаров: {len(images)}\n"
        f"💶 Ваш баланс: €{user.balance_sol:.2f}\n\n"
        f"Выберите товар для просмотра:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("catalog_page_"))
async def catalog_page(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext
):
    """Handle catalog pagination."""
    page = int(callback.data.split("_")[2])
    
    # Get available images
    images = await ImageService.get_available_images(
        session,
        region_id=user.region_id,
        city_id=user.city_id
    )
    
    # Paginate
    page_images, total_pages = paginate_list(images, page, items_per_page=5)
    
    # Update state
    await state.update_data(catalog_page=page)
    
    keyboard = catalog_keyboard(page_images, page=page, total_pages=total_pages)
    
    await callback.message.edit_text(
        f"🛍 **Каталог товаров**\n\n"
        f"Найдено товаров: {len(images)}\n"
        f"💶 Ваш баланс: €{user.balance_sol:.2f}\n\n"
        f"Выберите товар для просмотра:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_image_"))
async def view_image(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show image details."""
    image_id = int(callback.data.split("_")[2])
    
    image = await ImageService.get_image_by_id(session, image_id)
    
    if not image or image.is_sold:
        await callback.answer(
            "❌ Этот товар уже продан.",
            show_alert=True
        )
        return
    
    # Load location manually (no relationships)
    region = await LocationService.get_region_by_id(session, image.region_id)
    city = await LocationService.get_city_by_id(session, image.city_id)
    
    region_name = region.name if region else 'N/A'
    city_name = city.name if city else 'N/A'
    
    description = f"""
🖼 **Товар #{image.id}**

📂 Категория: {format_category_display(image.category) if image.category else 'Не указана'}
📍 Регион: {region_name}
🏙 Город: {city_name}

💶 Цена: €{image.price_sol:.2f}
💰 Ваш баланс: €{user.balance_sol:.2f}
"""
    
    if image.description:
        description += f"\n📝 Описание: {image.description}"
    
    keyboard = image_view_keyboard(image_id, image.price_sol)
    
    # Try to send the preview image (or main image if no preview)
    try:
        await callback.message.delete()
        
        # Use preview if available, otherwise use main image
        photo_to_send = image.preview_file_id if image.preview_file_id else image.file_id
        
        await callback.bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=photo_to_send,
            caption=description,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending image: {e}")
        await callback.message.answer(
            description,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    await callback.answer()


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext
):
    """Go back to catalog."""
    # Get current page from state
    data = await state.get_data()
    page = data.get('catalog_page', 0)
    
    # Get available images
    images = await ImageService.get_available_images(
        session,
        region_id=user.region_id,
        city_id=user.city_id
    )
    
    if not images:
        await callback.message.edit_text(
            "😔 К сожалению, в вашем регионе сейчас нет доступных товаров."
        )
        await callback.answer()
        return
    
    # Paginate
    page_images, total_pages = paginate_list(images, page, items_per_page=5)
    
    keyboard = catalog_keyboard(page_images, page=page, total_pages=total_pages)
    
    await callback.message.edit_text(
        f"🛍 **Каталог товаров**\n\n"
        f"Найдено товаров: {len(images)}\n"
        f"💶 Ваш баланс: €{user.balance_sol:.2f}\n\n"
        f"Выберите товар для просмотра:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_image_"))
async def buy_image(callback: CallbackQuery, user: User, session: AsyncSession):
    """Initiate purchase."""
    image_id = int(callback.data.split("_")[2])
    
    image = await ImageService.get_image_by_id(session, image_id)
    
    if not image or image.is_sold:
        await callback.answer(
            "❌ Этот товар уже продан.",
            show_alert=True
        )
        return
    
    # Check balance
    if user.balance_sol < image.price_sol:
        await callback.answer(
            f"❌ Недостаточно средств.\n"
            f"Требуется: €{image.price_sol:.2f}\n"
            f"Ваш баланс: €{user.balance_sol:.2f}",
            show_alert=True
        )
        return
    
    keyboard = confirm_purchase_keyboard(image_id)
    
    await callback.message.edit_caption(
        caption=f"⚠️ **Подтверждение покупки**\n\n"
        f"Товар: #{image.id}\n"
        f"💶 Цена: €{image.price_sol:.2f}\n\n"
        f"Вы уверены, что хотите купить этот товар?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_buy_"))
async def confirm_purchase(callback: CallbackQuery, user: User, session: AsyncSession):
    """Confirm and process purchase."""
    import logging
    logger = logging.getLogger(__name__)
    
    image_id = int(callback.data.split("_")[2])
    
    image = await ImageService.get_image_by_id(session, image_id)
    
    if not image or image.is_sold:
        await callback.answer(
            "❌ Этот товар уже продан.",
            show_alert=True
        )
        return
    
    # Log balance check
    logger.info(f"Purchase attempt - User {user.id}: balance={user.balance_sol:.2f} EUR, price={image.price_sol:.2f} EUR")
    
    # Check balance again
    if user.balance_sol < image.price_sol:
        logger.warning(f"Insufficient funds - User {user.id}: balance={user.balance_sol:.2f} < price={image.price_sol:.2f}")
        await callback.answer(
            f"❌ Недостаточно средств.\nТребуется: €{image.price_sol:.2f}\nВаш баланс: €{user.balance_sol:.2f}",
            show_alert=True
        )
        return
    
    # Process purchase
    logger.info(f"Processing purchase - User {user.id}, Product {image.id}, Price: €{image.price_sol:.2f}")
    
    # 1. Deduct from balance
    success = await UserService.update_balance(session, user.id, -image.price_sol)
    
    if not success:
        logger.error(f"Failed to update balance for user {user.id}")
        await callback.answer("❌ Ошибка при обновлении баланса", show_alert=True)
        return
    
    # 2. Mark as sold
    await ImageService.mark_as_sold(session, image_id, user.id, image.price_sol)
    
    # 3. Create transaction record
    await TransactionService.create_transaction(
        session=session,
        user_id=user.id,
        tx_type='purchase',
        amount_sol=image.price_sol,
        description=f"Покупка товара #{image.id}",
        status='completed'
    )
    
    # 4. Update user rating
    from services.rating_service import rating_service
    new_rating = await rating_service.update_rating_after_purchase(
        session, user.id, image.price_sol
    )
    
    # Refresh user
    await session.refresh(user)
    
    # Send the purchased image
    try:
        await callback.message.delete()
        await callback.bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=image.file_id,
            caption=f"✅ **Покупка успешна!**\n\n"
            f"Товар: #{image.id}\n"
            f"📂 Категория: {format_category_display(image.category) if image.category else 'Не указана'}\n"
            f"💶 Оплачено: €{image.price_sol:.2f}\n"
            f"💰 Остаток баланса: €{user.balance_sol:.2f}\n\n"
            f"Спасибо за покупку! 🎉",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error sending purchased image: {e}")
        await callback.message.edit_text(
            f"✅ Покупка успешна, но не удалось отправить изображение."
        )
    
    await callback.answer("✅ Покупка завершена!", show_alert=True)


@router.callback_query(F.data == "cancel_purchase")
async def cancel_purchase(callback: CallbackQuery):
    """Cancel purchase."""
    await callback.message.edit_caption(
        caption="❌ Покупка отменена."
    )
    await callback.answer()


@router.message(F.text == "📜 История покупок")
async def purchase_history(message: Message, user: User, session: AsyncSession):
    """Show purchase history."""
    purchases = await ImageService.get_user_purchases(session, user.id, limit=10)
    
    if not purchases:
        await message.answer("📜 У вас пока нет покупок.")
        return
    
    history_text = "📜 **История ваших покупок:**\n\n"
    
    for purchase in purchases:
        # Load image
        await session.refresh(purchase, ['image'])
        image = purchase.image
        
        history_text += (
            f"🖼 Товар #{image.id}\n"
            f"💰 Цена: {format_sol_amount(purchase.price_paid_sol)}\n"
            f"📅 Дата: {purchase.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {image.region.name}, {image.city.name}\n\n"
        )
    
    await message.answer(history_text, parse_mode="Markdown")

