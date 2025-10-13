"""Admin handlers for bot management."""
import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, AdminLog
from services.image_service import ImageService
from services.location_service import LocationService
from services.user_service import UserService
from services.transaction_service import TransactionService
from utils.keyboards import (
    admin_region_management_keyboard,
    admin_region_actions_keyboard,
    admin_city_management_keyboard,
    cancel_keyboard,
    admin_menu_keyboard
)
from utils.helpers import format_sol_amount, is_admin
from config import settings


router = Router(name='admin_handlers')
logger = logging.getLogger(__name__)


class AddImageStates(StatesGroup):
    """States for adding image."""
    waiting_for_region = State()
    waiting_for_city = State()
    waiting_for_district = State()  # Новый state для микрорайона
    waiting_for_image = State()
    waiting_for_price = State()
    waiting_for_description = State()


class AddRegionStates(StatesGroup):
    """States for adding region."""
    waiting_for_name = State()
    waiting_for_code = State()


class AddCityStates(StatesGroup):
    """States for adding city."""
    waiting_for_name = State()


class AddDistrictStates(StatesGroup):
    """States for adding district."""
    waiting_for_name = State()


class AddBalanceState(StatesGroup):
    """State for adding balance."""
    waiting_for_amount = State()


# Admin check filter
async def is_admin_filter(message: Message, user: User) -> bool:
    """Check if user is admin."""
    return is_admin(user.id, settings.admin_list)


@router.message(F.text == "➕ Добавить товар")
async def add_product_start(message: Message, user: User, session: AsyncSession, state: FSMContext):
    """Start adding product."""
    # Check role: admin (by ADMIN_IDS), moderator, seller can add products
    from services.role_service import role_service
    allowed_roles = ['admin', 'moderator', 'seller']
    
    # Also check if user is in ADMIN_IDS (even if role not set)
    is_admin_user = is_admin(user.id, settings.admin_list)
    
    if user.role not in allowed_roles and not is_admin_user:
        await message.answer("⛔️ У вас нет доступа к этой функции.\n\nДобавлять товары могут только продавцы, модераторы и администраторы.")
        return
    
    # Get regions
    regions = await LocationService.get_all_regions(session)
    
    if not regions:
        await message.answer(
            "❌ Сначала нужно добавить регионы.\n"
            "Используйте '🗂 Управление регионами'"
        )
        return
    
    regions_text = "📍 **Выберите регион для товара:**\n\n"
    for region in regions:
        regions_text += f"/{region.id} - {region.name}\n"
    
    await state.set_state(AddImageStates.waiting_for_region)
    await message.answer(
        regions_text,
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )


@router.message(AddImageStates.waiting_for_region)
async def add_product_region(message: Message, session: AsyncSession, state: FSMContext):
    """Process region selection."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    try:
        region_id = int(message.text.strip('/'))
        region = await LocationService.get_region_by_id(session, region_id)
        
        if not region:
            await message.answer("❌ Регион не найден. Попробуйте еще раз.")
            return
        
        # Get cities in region
        cities = await LocationService.get_cities_by_region(session, region_id)
        
        if not cities:
            await message.answer(
                f"❌ В регионе '{region.name}' нет городов.\n"
                f"Добавьте города через 'Управление регионами'."
            )
            return
        
        cities_text = f"🏙 **Выберите город в {region.name}:**\n\n"
        for city in cities:
            cities_text += f"/{city.id} - {city.name}\n"
        
        await state.update_data(region_id=region_id)
        await state.set_state(AddImageStates.waiting_for_city)
        
        await message.answer(cities_text, parse_mode="Markdown")
        
    except ValueError:
        await message.answer("❌ Введите номер региона (например: /1)")


@router.message(AddImageStates.waiting_for_city)
async def add_product_city(message: Message, session: AsyncSession, state: FSMContext):
    """Process city selection."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    try:
        city_id = int(message.text.strip('/'))
        city = await LocationService.get_city_by_id(session, city_id)
        
        if not city:
            await message.answer("❌ Город не найден. Попробуйте еще раз.")
            return
        
        await state.update_data(city_id=city_id)
        
        # Get districts in city
        from services.district_service import district_service
        districts = await district_service.get_districts_by_city(session, city_id)
        
        if not districts or len(districts) == 0:
            # No districts - go to image
            await state.set_state(AddImageStates.waiting_for_image)
            await message.answer(
                "🖼 **Отправьте изображение товара:**\n\n"
                "Это изображение будет продаваться пользователям."
            )
            return
        
        # Show districts
        districts_text = f"📍 **Выберите микрорайон в {city.name}:**\n\n"
        for district in districts[:20]:  # Show first 20
            districts_text += f"/{district.id} - {district.name}\n"
        
        districts_text += f"\n/0 - Все микрорайоны (без привязки)"
        
        await state.set_state(AddImageStates.waiting_for_district)
        await message.answer(districts_text, parse_mode="Markdown")
        
    except ValueError:
        await message.answer("❌ Введите номер города (например: /1)")


@router.message(AddImageStates.waiting_for_district)
async def add_product_district(message: Message, session: AsyncSession, state: FSMContext):
    """Process district selection."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    try:
        district_id = int(message.text.strip('/'))
        
        # 0 means "all districts"
        if district_id == 0:
            district_id = None
        elif district_id > 0:
            # Verify district exists
            from services.district_service import district_service
            district = await district_service.get_district_by_id(session, district_id)
            if not district:
                await message.answer("❌ Микрорайон не найден. Попробуйте еще раз.")
                return
        
        await state.update_data(district_id=district_id)
        await state.set_state(AddImageStates.waiting_for_image)
        
        await message.answer(
            "🖼 **Отправьте изображение товара:**\n\n"
            "Это изображение будет продаваться пользователям."
        )
        
    except ValueError:
        await message.answer("❌ Введите номер микрорайона (например: /1 или /0 для всех)")


@router.message(AddImageStates.waiting_for_image, F.photo)
async def add_product_image(message: Message, state: FSMContext):
    """Process image upload."""
    # Get the best quality photo
    photo = message.photo[-1]
    file_id = photo.file_id
    
    await state.update_data(file_id=file_id)
    await state.set_state(AddImageStates.waiting_for_price)
    
    await message.answer(
        "💰 **Укажите цену в EUR (€):**\n\n"
        "Например: 5.00 или 10"
    )


@router.message(AddImageStates.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    """Process price input."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверная цена. Введите число больше 0.\n"
            "Например: 5.00 или 10"
        )
        return
    
    await state.update_data(price=price)
    await state.set_state(AddImageStates.waiting_for_description)
    
    await message.answer(
        "📝 **Введите описание товара:**\n\n"
        "Или отправьте '-' чтобы пропустить."
    )


@router.message(AddImageStates.waiting_for_description)
async def add_product_description(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext
):
    """Process description and save product."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    description = None if message.text == '-' else message.text
    
    # Get data from state
    data = await state.get_data()
    region_id = data.get('region_id')
    city_id = data.get('city_id')
    district_id = data.get('district_id')  # Может быть None
    file_id = data.get('file_id')
    price = data.get('price')
    
    # Log for debugging
    logger.info(f"Adding product: region_id={region_id}, city_id={city_id}, district_id={district_id}, price={price}")
    
    # Debug: check if all data is present
    if not region_id or not city_id or not file_id or not price:
        await message.answer(
            f"❌ Ошибка: отсутствуют данные.\n"
            f"region_id: {region_id}, city_id: {city_id}\n"
            f"file_id: {file_id}, price: {price}\n"
            f"Попробуйте добавить товар заново.",
            reply_markup=admin_menu_keyboard()
        )
        await state.clear()
        return
    
    # Try-catch для отлова ошибок
    try:
        # Download and save image file
        file = await message.bot.get_file(file_id)
    
        # Create images directory if not exists
        os.makedirs('images', exist_ok=True)
        
        # Generate unique filename
        import uuid
        filename = f"images/{uuid.uuid4()}.jpg"
        
        # Download file
        await message.bot.download_file(file.file_path, filename)
        
        # Save to database
        image = await ImageService.add_image(
            session=session,
            file_id=file_id,
            file_path=filename,
            price_sol=price,
            region_id=region_id,
            city_id=city_id,
            uploaded_by=user.id,
            description=description,
            district_id=district_id
        )
        
        # Log admin action
        log = AdminLog(
            admin_id=user.id,
            action="add_product",
            details=f"Added product #{image.id}, price: €{price}"
        )
        session.add(log)
        await session.commit()
        
        await state.clear()
        
        # Load location info manually (no relationships in Image model)
        region = await LocationService.get_region_by_id(session, region_id)
        city = await LocationService.get_city_by_id(session, city_id)
        
        district_info = ""
        if district_id:
            from services.district_service import district_service
            district = await district_service.get_district_by_id(session, district_id)
            if district:
                district_info = f"📍 Микрорайон: {district.name}\n"
        
        await message.answer(
            f"✅ **Товар успешно добавлен!**\n\n"
            f"ID: #{image.id}\n"
            f"Регион: {region.name if region else 'N/A'}\n"
            f"Город: {city.name if city else 'N/A'}\n"
            f"{district_info}"
            f"💶 Цена: €{image.price_sol:.2f}\n"
            f"📝 Описание: {image.description or 'Нет'}",
            reply_markup=admin_menu_keyboard(),
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Product #{image.id} added successfully by user {user.id}")
        
    except Exception as e:
        logger.error(f"Error adding product: {e}", exc_info=True)
        await message.answer(
            f"❌ Ошибка при добавлении товара:\n{str(e)}\n\n"
            f"Попробуйте еще раз.",
            reply_markup=admin_menu_keyboard()
        )
        await state.clear()


@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message, user: User, session: AsyncSession):
    """Show bot statistics."""
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ У вас нет доступа к этой функции.")
        return
    
    # Get statistics
    stats = await ImageService.get_statistics(session)
    
    # Get user count
    from sqlalchemy import func, select
    result = await session.execute(select(func.count(User.id)))
    user_count = result.scalar() or 0
    
    stats_text = f"""
📊 **Статистика бота**

👥 Пользователей: {user_count}
🖼 Всего товаров: {stats['total_images']}
✅ Продано: {stats['sold_images']}
📦 Доступно: {stats['available_images']}
💶 Общая выручка: €{stats['total_revenue']:.2f}
    """
    
    await message.answer(stats_text, parse_mode="Markdown")


@router.message(F.text.in_(["🗂 Управление регионами", "🗂 Регионы и города"]))
async def manage_regions(message: Message, user: User, session: AsyncSession):
    """Manage regions."""
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ У вас нет доступа к этой функции.")
        return
    
    regions = await LocationService.get_all_regions(session, active_only=False)
    
    if not regions:
        await message.answer(
            "📍 **Управление регионами**\n\n"
            "Регионов пока нет. Добавьте первый регион.",
            reply_markup=admin_region_management_keyboard([])
        )
        return
    
    keyboard = admin_region_management_keyboard(regions)
    
    await message.answer(
        "📍 **Управление регионами**\n\n"
        "Выберите регион для управления:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("admin_region_"))
async def admin_region_actions(callback: CallbackQuery, session: AsyncSession):
    """Show region actions."""
    if callback.data == "admin_regions":
        # Back to regions list
        regions = await LocationService.get_all_regions(session, active_only=False)
        keyboard = admin_region_management_keyboard(regions)
        
        await callback.message.edit_text(
            "📍 **Управление регионами**\n\n"
            "Выберите регион для управления:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    region_id = int(callback.data.split("_")[2])
    region = await LocationService.get_region_by_id(session, region_id)
    
    if not region:
        await callback.answer("❌ Регион не найден.", show_alert=True)
        return
    
    keyboard = admin_region_actions_keyboard(region_id, region.is_active)
    
    status = "Активен" if region.is_active else "Неактивен"
    
    await callback.message.edit_text(
        f"📍 **Регион: {region.name}**\n\n"
        f"Код: {region.code}\n"
        f"Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cities_"))
async def admin_manage_cities(callback: CallbackQuery, session: AsyncSession):
    """Manage cities in region."""
    region_id = int(callback.data.split("_")[2])
    region = await LocationService.get_region_by_id(session, region_id)
    
    if not region:
        await callback.answer("❌ Регион не найден.", show_alert=True)
        return
    
    cities = await LocationService.get_cities_by_region(session, region_id, active_only=False)
    
    keyboard = admin_city_management_keyboard(cities, region_id)
    
    await callback.message.edit_text(
        f"🏙 **Города в регионе {region.name}**\n\n"
        f"Выберите город для управления:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_region_"))
async def toggle_region_status(callback: CallbackQuery, session: AsyncSession):
    """Toggle region active status."""
    region_id = int(callback.data.split("_")[3])
    region = await LocationService.get_region_by_id(session, region_id)
    
    if not region:
        await callback.answer("❌ Регион не найден.", show_alert=True)
        return
    
    # Toggle status
    await LocationService.toggle_region_active(session, region_id, not region.is_active)
    
    # Refresh region
    await session.refresh(region)
    
    keyboard = admin_region_actions_keyboard(region_id, region.is_active)
    status = "Активен" if region.is_active else "Неактивен"
    
    await callback.message.edit_text(
        f"📍 **Регион: {region.name}**\n\n"
        f"Код: {region.code}\n"
        f"Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await callback.answer(f"✅ Статус изменен на: {status}")


@router.callback_query(F.data == "admin_add_region")
async def add_region_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new region."""
    await state.set_state(AddRegionStates.waiting_for_name)
    
    await callback.message.answer(
        "➕ **Добавление региона**\n\n"
        "Введите название региона (страны):\n"
        "Например: Germany",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AddRegionStates.waiting_for_name)
async def add_region_name(message: Message, state: FSMContext):
    """Process region name."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление региона отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    name = message.text.strip()
    await state.update_data(region_name=name)
    await state.set_state(AddRegionStates.waiting_for_code)
    
    await message.answer(
        "📝 Введите ISO код страны (2 буквы):\n"
        "Например: DE для Germany"
    )


@router.message(AddRegionStates.waiting_for_code)
async def add_region_code(message: Message, session: AsyncSession, user: User, state: FSMContext):
    """Process region code and save."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление региона отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    code = message.text.strip().upper()
    
    if len(code) != 2:
        await message.answer(
            "❌ Код должен содержать 2 буквы.\n"
            "Попробуйте еще раз."
        )
        return
    
    # Get data from state
    data = await state.get_data()
    name = data['region_name']
    
    # Create region
    try:
        region = await LocationService.create_region(session, name, code)
        
        # Log admin action
        log = AdminLog(
            admin_id=user.id,
            action="add_region",
            details=f"Added region: {name} ({code})"
        )
        session.add(log)
        await session.commit()
        
        await state.clear()
        
        await message.answer(
            f"✅ **Регион успешно добавлен!**\n\n"
            f"Название: {region.name}\n"
            f"Код: {region.code}\n\n"
            f"Теперь добавьте города в этот регион.",
            reply_markup=admin_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при создании региона: {str(e)}\n"
            f"Возможно, такой регион уже существует."
        )


@router.callback_query(F.data.startswith("admin_add_city_"))
async def add_city_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new city."""
    region_id = int(callback.data.split("_")[3])
    
    await state.update_data(city_region_id=region_id)
    await state.set_state(AddCityStates.waiting_for_name)
    
    await callback.message.answer(
        "➕ **Добавление города**\n\n"
        "Введите название города:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AddCityStates.waiting_for_name)
async def add_city_name(message: Message, session: AsyncSession, user: User, state: FSMContext):
    """Process city name and save."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление города отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    name = message.text.strip()
    
    # Get region ID from state
    data = await state.get_data()
    region_id = data['city_region_id']
    
    # Create city
    try:
        city = await LocationService.create_city(session, name, region_id)
        
        # Log admin action
        log = AdminLog(
            admin_id=user.id,
            action="add_city",
            details=f"Added city: {name} (region_id: {region_id})"
        )
        session.add(log)
        await session.commit()
        
        await state.clear()
        
        # Load region manually
        region = await LocationService.get_region_by_id(session, region_id)
        
        await message.answer(
            f"✅ **Город успешно добавлен!**\n\n"
            f"Название: {city.name}\n"
            f"Регион: {region.name if region else 'N/A'}",
            reply_markup=admin_menu_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при создании города: {str(e)}"
        )


@router.callback_query(F.data.startswith("admin_delete_region_"))
async def delete_region_confirm(callback: CallbackQuery, session: AsyncSession):
    """Confirm region deletion."""
    region_id = int(callback.data.split("_")[3])
    region = await LocationService.get_region_by_id(session, region_id)
    
    if not region:
        await callback.answer("❌ Регион не найден.", show_alert=True)
        return
    
    # Check if region has images
    from services.image_service import ImageService
    image_count = await ImageService.get_image_count(session, region_id=region_id)
    
    if image_count > 0:
        await callback.answer(
            f"❌ Невозможно удалить регион!\n"
            f"В нем есть {image_count} товаров.\n"
            f"Сначала удалите товары.",
            show_alert=True
        )
        return
    
    # Delete region
    success = await LocationService.delete_region(session, region_id)
    
    if success:
        await callback.answer(f"✅ Регион '{region.name}' удален!", show_alert=True)
        
        # Return to regions list
        regions = await LocationService.get_all_regions(session, active_only=False)
        keyboard = admin_region_management_keyboard(regions)
        
        await callback.message.edit_text(
            "📍 **Управление регионами**\n\n"
            "Выберите регион для управления:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ошибка при удалении региона.", show_alert=True)


@router.callback_query(F.data.startswith("admin_city_"))
async def admin_city_actions(callback: CallbackQuery, session: AsyncSession):
    """Show city actions."""
    city_id = int(callback.data.split("_")[2])
    city = await LocationService.get_city_by_id(session, city_id)
    
    if not city:
        await callback.answer("❌ Город не найден.", show_alert=True)
        return
    
    # Load region
    await session.refresh(city, ['region'])
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    # Manage districts button
    builder.button(text="📍 Управление микрорайонами", callback_data=f"admin_districts_{city_id}")
    
    toggle_text = "🔴 Деактивировать" if city.is_active else "🟢 Активировать"
    builder.button(text=toggle_text, callback_data=f"admin_toggle_city_{city_id}")
    
    builder.button(text="🗑 Удалить город", callback_data=f"admin_delete_city_{city_id}")
    
    builder.button(text="◀️ Назад", callback_data=f"admin_cities_{city.region_id}")
    
    builder.adjust(1)
    
    status = "Активен" if city.is_active else "Неактивен"
    
    await callback.message.edit_text(
        f"🏙 **Город: {city.name}**\n\n"
        f"Регион: {city.region.name}\n"
        f"Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_city_"))
async def toggle_city_status(callback: CallbackQuery, session: AsyncSession):
    """Toggle city active status."""
    city_id = int(callback.data.split("_")[3])
    city = await LocationService.get_city_by_id(session, city_id)
    
    if not city:
        await callback.answer("❌ Город не найден.", show_alert=True)
        return
    
    # Toggle status
    await LocationService.toggle_city_active(session, city_id, not city.is_active)
    
    # Refresh
    await session.refresh(city)
    
    # Load region manually
    region = await LocationService.get_region_by_id(session, city.region_id)
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    toggle_text = "🔴 Деактивировать" if city.is_active else "🟢 Активировать"
    builder.button(text=toggle_text, callback_data=f"admin_toggle_city_{city_id}")
    builder.button(text="🗑 Удалить город", callback_data=f"admin_delete_city_{city_id}")
    builder.button(text="◀️ Назад", callback_data=f"admin_cities_{city.region_id}")
    builder.adjust(1)
    
    status = "Активен" if city.is_active else "Неактивен"
    
    await callback.message.edit_text(
        f"🏙 **Город: {city.name}**\n\n"
        f"Регион: {region.name if region else 'N/A'}\n"
        f"Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await callback.answer(f"✅ Статус изменен на: {status}")


@router.callback_query(F.data.startswith("admin_districts_"))
async def admin_manage_districts(callback: CallbackQuery, session: AsyncSession):
    """Manage districts in city."""
    city_id = int(callback.data.split("_")[2])
    city = await LocationService.get_city_by_id(session, city_id)
    
    if not city:
        await callback.answer("❌ Город не найден.", show_alert=True)
        return
    
    from services.district_service import district_service
    districts = await district_service.get_districts_by_city(session, city_id, active_only=False)
    
    from utils.keyboards import admin_district_management_keyboard
    keyboard = admin_district_management_keyboard(districts, city_id)
    
    await callback.message.edit_text(
        f"📍 **Микрорайоны в городе {city.name}**\n\n"
        f"Всего: {len(districts)}\n\n"
        f"Выберите микрорайон для управления:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_district_"))
async def admin_district_actions(callback: CallbackQuery, session: AsyncSession):
    """Show district actions."""
    district_id = int(callback.data.split("_")[2])
    
    from services.district_service import district_service
    district = await district_service.get_district_by_id(session, district_id)
    
    if not district:
        await callback.answer("❌ Микрорайон не найден.", show_alert=True)
        return
    
    # Get city
    city = await LocationService.get_city_by_id(session, district.city_id)
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    toggle_text = "🔴 Деактивировать" if district.is_active else "🟢 Активировать"
    builder.button(text=toggle_text, callback_data=f"admin_toggle_district_{district_id}")
    
    builder.button(text="🗑 Удалить микрорайон", callback_data=f"admin_delete_district_{district_id}")
    
    builder.button(text="◀️ Назад", callback_data=f"admin_districts_{district.city_id}")
    
    builder.adjust(1)
    
    status = "Активен" if district.is_active else "Неактивен"
    
    await callback.message.edit_text(
        f"📍 **Микрорайон: {district.name}**\n\n"
        f"Город: {city.name}\n"
        f"Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_toggle_district_"))
async def toggle_district_status(callback: CallbackQuery, session: AsyncSession):
    """Toggle district active status."""
    district_id = int(callback.data.split("_")[3])
    
    from services.district_service import district_service
    district = await district_service.get_district_by_id(session, district_id)
    
    if not district:
        await callback.answer("❌ Микрорайон не найден.", show_alert=True)
        return
    
    # Toggle status
    await district_service.toggle_district_active(session, district_id, not district.is_active)
    
    # Refresh and show again
    district = await district_service.get_district_by_id(session, district_id)
    city = await LocationService.get_city_by_id(session, district.city_id)
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    toggle_text = "🔴 Деактивировать" if district.is_active else "🟢 Активировать"
    builder.button(text=toggle_text, callback_data=f"admin_toggle_district_{district_id}")
    builder.button(text="🗑 Удалить микрорайон", callback_data=f"admin_delete_district_{district_id}")
    builder.button(text="◀️ Назад", callback_data=f"admin_districts_{district.city_id}")
    builder.adjust(1)
    
    status = "Активен" if district.is_active else "Неактивен"
    
    await callback.message.edit_text(
        f"📍 **Микрорайон: {district.name}**\n\n"
        f"Город: {city.name}\n"
        f"Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer(f"✅ Статус изменен на: {status}")


@router.callback_query(F.data.startswith("admin_add_district_"))
async def add_district_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new district."""
    city_id = int(callback.data.split("_")[3])
    
    await state.update_data(city_id=city_id)
    await state.set_state(AddDistrictStates.waiting_for_name)
    
    await callback.message.answer(
        "➕ **Добавление микрорайона**\n\n"
        "Введите название микрорайона:\n"
        "Например: Антакальнис",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AddDistrictStates.waiting_for_name)
async def add_district_name(message: Message, session: AsyncSession, user: User, state: FSMContext):
    """Process district name and save."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление микрорайона отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    name = message.text.strip()
    
    # Get data from state
    data = await state.get_data()
    city_id = data['city_id']
    
    # Create district
    from services.district_service import district_service
    from database.models import AdminLog
    
    try:
        district = await district_service.create_district(session, name, city_id)
        
        # Log admin action
        log = AdminLog(
            admin_id=user.id,
            action="add_district",
            details=f"Added district: {name} to city {city_id}"
        )
        session.add(log)
        await session.commit()
        
        await message.answer(
            f"✅ Микрорайон '{name}' успешно добавлен!",
            reply_markup=admin_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error adding district: {e}")
        await message.answer(
            f"❌ Ошибка при добавлении микрорайона.",
            reply_markup=admin_menu_keyboard()
        )
    
    await state.clear()


@router.callback_query(F.data.startswith("admin_delete_district_"))
async def delete_district_confirm(callback: CallbackQuery, session: AsyncSession):
    """Delete district."""
    district_id = int(callback.data.split("_")[3])
    
    from services.district_service import district_service
    district = await district_service.get_district_by_id(session, district_id)
    
    if not district:
        await callback.answer("❌ Микрорайон не найден.", show_alert=True)
        return
    
    city_id = district.city_id
    district_name = district.name
    
    # Check if district has images
    from services.image_service import ImageService
    from sqlalchemy import select
    from database.models import Image
    stmt = select(Image).where(Image.district_id == district_id)
    result = await session.execute(stmt)
    images = result.scalars().all()
    image_count = len(images)
    
    if image_count > 0:
        await callback.answer(
            f"❌ Невозможно удалить микрорайон!\n"
            f"В нем есть {image_count} товаров.\n"
            f"Сначала удалите товары.",
            show_alert=True
        )
        return
    
    # Delete district
    success = await district_service.delete_district(session, district_id)
    
    if success:
        await callback.answer(f"✅ Микрорайон '{district_name}' удален!", show_alert=True)
        
        # Return to districts list
        districts = await district_service.get_districts_by_city(session, city_id, active_only=False)
        from utils.keyboards import admin_district_management_keyboard
        keyboard = admin_district_management_keyboard(districts, city_id)
        
        city = await LocationService.get_city_by_id(session, city_id)
        
        await callback.message.edit_text(
            f"📍 **Микрорайоны в городе {city.name}**\n\n"
            f"Выберите микрорайон для управления:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ошибка при удалении микрорайона.", show_alert=True)


@router.callback_query(F.data.startswith("admin_back_to_city_"))
async def admin_back_to_city(callback: CallbackQuery, session: AsyncSession):
    """Return to city menu."""
    city_id = int(callback.data.split("_")[4])
    await admin_city_actions(callback, session)


@router.callback_query(F.data.startswith("admin_delete_city_"))
async def delete_city_confirm(callback: CallbackQuery, session: AsyncSession):
    """Delete city."""
    city_id = int(callback.data.split("_")[3])
    city = await LocationService.get_city_by_id(session, city_id)
    
    if not city:
        await callback.answer("❌ Город не найден.", show_alert=True)
        return
    
    region_id = city.region_id
    city_name = city.name
    
    # Check if city has images
    from services.image_service import ImageService
    image_count = await ImageService.get_image_count(session, city_id=city_id)
    
    if image_count > 0:
        await callback.answer(
            f"❌ Невозможно удалить город!\n"
            f"В нем есть {image_count} товаров.\n"
            f"Сначала удалите товары.",
            show_alert=True
        )
        return
    
    # Delete city
    success = await LocationService.delete_city(session, city_id)
    
    if success:
        await callback.answer(f"✅ Город '{city_name}' удален!", show_alert=True)
        
        # Return to cities list
        cities = await LocationService.get_cities_by_region(session, region_id, active_only=False)
        keyboard = admin_city_management_keyboard(cities, region_id)
        
        region = await LocationService.get_region_by_id(session, region_id)
        
        await callback.message.edit_text(
            f"🏙 **Города в регионе {region.name}**\n\n"
            f"Выберите город для управления:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ошибка при удалении города.", show_alert=True)


@router.message(F.text.in_(["👥 Управление пользователями", "👥 Пользователи"]))
async def manage_users(message: Message, user: User, session: AsyncSession):
    """Show user management options."""
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ У вас нет доступа к этой функции.")
        return
    
    users = await UserService.get_all_users(session, limit=20)
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    for u in users:
        status = "🚫" if u.is_blocked else "✅"
        username = f"@{u.username}" if u.username else u.first_name or "User"
        builder.button(
            text=f"{status} {username} (ID: {u.id})",
            callback_data=f"admin_user_{u.id}"
        )
    
    builder.adjust(1)
    
    await message.answer(
        "👥 **Управление пользователями**\n\n"
        "Выберите пользователя для управления:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("admin_user_"))
async def admin_user_actions(callback: CallbackQuery, session: AsyncSession):
    """Show user actions."""
    # Parse user_id correctly for different callback patterns
    parts = callback.data.split("_")
    if len(parts) == 3:
        # admin_user_12345
        user_id = int(parts[2])
    else:
        # Should not happen, but handle gracefully
        logger.error(f"Unexpected callback_data format: {callback.data}")
        await callback.answer("❌ Ошибка парсинга", show_alert=True)
        return
    target_user = await UserService.get_user_with_location(session, user_id)
    
    if not target_user:
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    # Block/Unblock button
    if target_user.is_blocked:
        builder.button(text="🟢 Разблокировать", callback_data=f"admin_unblock_{user_id}")
    else:
        builder.button(text="🔴 Заблокировать", callback_data=f"admin_block_{user_id}")
    
    # View purchases
    builder.button(text="📜 История покупок", callback_data=f"admin_purchases_{user_id}")
    
    # View transactions
    builder.button(text="💸 История транзакций", callback_data=f"admin_transactions_{user_id}")
    
    # Add balance
    builder.button(text="💰 Добавить баланс", callback_data=f"admin_add_balance_{user_id}")
    
    # Reset balance
    builder.button(text="🔄 Обнулить баланс", callback_data=f"admin_reset_balance_{user_id}")
    
    # Change role
    builder.button(text="👑 Изменить роль", callback_data=f"admin_change_role_{user_id}")
    
    # Back button
    builder.button(text="◀️ Назад к списку", callback_data="admin_users_list")
    
    builder.adjust(2, 2, 2, 1, 1)
    
    # User info
    status = "🚫 Заблокирован" if target_user.is_blocked else "✅ Активен"
    location = "Не указана"
    
    # Load region and city if exist
    if target_user.region_id and target_user.city_id:
        region = await LocationService.get_region_by_id(session, target_user.region_id)
        city = await LocationService.get_city_by_id(session, target_user.city_id)
        if region and city:
            location = f"{region.name}, {city.name}"
    
    # Get user role
    from services.role_service import role_service
    role_name = role_service.get_role_name(target_user.role, 'ru')
    
    # Escape special characters for Markdown
    first_name = target_user.first_name or 'N/A'
    first_name = first_name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
    
    if target_user.username:
        username_escaped = target_user.username.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
        username_display = f"@{username_escaped}"
    else:
        username_display = 'N/A'
    
    user_info = (
        f"👤 *Пользователь*\n\n"
        f"ID: `{target_user.id}`\n"
        f"Имя: {first_name}\n"
        f"Username: {username_display}\n"
        f"Статус: {status}\n"
        f"👑 Роль: *{role_name}*\n\n"
        f"💶 Баланс: €{target_user.balance_sol:.2f}\n"
        f"📍 Локация: {location}\n"
        f"📅 Регистрация: {target_user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Выберите действие:"
    )
    
    await callback.message.edit_text(
        user_info,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_block_"))
async def admin_block_user(callback: CallbackQuery, session: AsyncSession, user: User):
    """Block user."""
    user_id = int(callback.data.split("_")[2])
    
    success = await UserService.block_user(session, user_id, blocked=True)
    
    if success:
        # Log action
        log = AdminLog(
            admin_id=user.id,
            action="block_user",
            details=f"Blocked user {user_id}"
        )
        session.add(log)
        await session.commit()
        
        await callback.answer("✅ Пользователь заблокирован!", show_alert=True)
        
        # Create new callback with correct data
        from aiogram.types import CallbackQuery as CQ
        new_callback = CQ(
            id=callback.id,
            from_user=callback.from_user,
            message=callback.message,
            chat_instance=callback.chat_instance,
            data=f"admin_user_{user_id}"
        )
        
        # Refresh user info
        await admin_user_actions(new_callback, session)
        return
        
        status = "🚫 Заблокирован"
        location = "Не указана"
        if target_user.region and target_user.city:
            location = f"{target_user.region.name}, {target_user.city.name}"
        
        user_info = (
            f"👤 **Пользователь**\n\n"
            f"ID: `{target_user.id}`\n"
            f"Имя: {target_user.first_name or 'N/A'}\n"
            f"Username: @{target_user.username or 'N/A'}\n"
            f"Статус: {status}\n\n"
            f"💰 Баланс: {format_sol_amount(target_user.balance_sol)}\n"
            f"📍 Локация: {location}\n"
            f"📅 Регистрация: {target_user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Выберите действие:"
        )
        
        await callback.message.edit_text(
            user_info,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ошибка при блокировке пользователя.", show_alert=True)


@router.callback_query(F.data.startswith("admin_unblock_"))
async def admin_unblock_user(callback: CallbackQuery, session: AsyncSession, user: User):
    """Unblock user."""
    user_id = int(callback.data.split("_")[2])
    
    success = await UserService.block_user(session, user_id, blocked=False)
    
    if success:
        # Log action
        log = AdminLog(
            admin_id=user.id,
            action="unblock_user",
            details=f"Unblocked user {user_id}"
        )
        session.add(log)
        await session.commit()
        
        await callback.answer("✅ Пользователь разблокирован!", show_alert=True)
        
        # Create new callback with correct data
        from aiogram.types import CallbackQuery as CQ
        new_callback = CQ(
            id=callback.id,
            from_user=callback.from_user,
            message=callback.message,
            chat_instance=callback.chat_instance,
            data=f"admin_user_{user_id}"
        )
        
        # Refresh user info
        await admin_user_actions(new_callback, session)
        return
        
        status = "✅ Активен"
        location = "Не указана"
        if target_user.region and target_user.city:
            location = f"{target_user.region.name}, {target_user.city.name}"
        
        user_info = (
            f"👤 **Пользователь**\n\n"
            f"ID: `{target_user.id}`\n"
            f"Имя: {target_user.first_name or 'N/A'}\n"
            f"Username: @{target_user.username or 'N/A'}\n"
            f"Статус: {status}\n\n"
            f"💰 Баланс: {format_sol_amount(target_user.balance_sol)}\n"
            f"📍 Локация: {location}\n"
            f"📅 Регистрация: {target_user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Выберите действие:"
        )
        
        await callback.message.edit_text(
            user_info,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Ошибка при разблокировке пользователя.", show_alert=True)


@router.callback_query(F.data.startswith("admin_purchases_"))
async def admin_view_purchases(callback: CallbackQuery, session: AsyncSession):
    """View user's purchase history."""
    user_id = int(callback.data.split("_")[2])
    
    from services.image_service import ImageService
    purchases = await ImageService.get_user_purchases(session, user_id, limit=10)
    
    if not purchases:
        await callback.answer("У пользователя нет покупок.", show_alert=True)
        return
    
    history_text = f"📜 **История покупок пользователя {user_id}:**\n\n"
    
    for purchase in purchases:
        await session.refresh(purchase, ['image'])
        image = purchase.image
        
        # Load location manually (no relationships)
        region = await LocationService.get_region_by_id(session, image.region_id)
        city = await LocationService.get_city_by_id(session, image.city_id)
        
        region_name = region.name if region else 'N/A'
        city_name = city.name if city else 'N/A'
        
        history_text += (
            f"🖼 Товар #{image.id}\n"
            f"💶 Цена: €{purchase.price_sol:.2f}\n"
            f"📅 Дата: {purchase.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {region_name}, {city_name}\n\n"
        )
    
    await callback.message.answer(history_text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_transactions_"))
async def admin_view_transactions(callback: CallbackQuery, session: AsyncSession):
    """View user's transaction history."""
    user_id = int(callback.data.split("_")[2])
    
    transactions = await TransactionService.get_user_transactions(session, user_id, limit=10)
    
    if not transactions:
        await callback.answer("У пользователя нет транзакций.", show_alert=True)
        return
    
    history_text = f"💸 **История транзакций пользователя {user_id}:**\n\n"
    
    for tx in transactions:
        type_emoji = {
            'deposit': '💵',
            'withdrawal': '💸',
            'purchase': '🛍'
        }.get(tx.tx_type, '💰')
        
        status_emoji = {
            'completed': '✅',
            'pending': '⏳',
            'failed': '❌'
        }.get(tx.status, '❓')
        
        history_text += (
            f"{type_emoji} *{tx.tx_type.capitalize()}* {status_emoji}\n"
            f"💶 Сумма: €{tx.amount_sol:.2f}\n"
        )
        
        if tx.fee_sol > 0:
            history_text += f"Комиссия: {format_sol_amount(tx.fee_sol)}\n"
        
        history_text += f"Дата: {tx.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        
        if tx.description:
            history_text += f"Описание: {tx.description}\n"
        
        history_text += "\n"
    
    await callback.message.answer(history_text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_add_balance_"))
async def admin_add_balance_init(callback: CallbackQuery, state: FSMContext):
    """Initialize balance addition."""
    user_id = int(callback.data.split("_")[3])
    
    await state.update_data(target_user_id=user_id)
    await state.set_state(AddBalanceState.waiting_for_amount)
    
    await callback.message.answer(
        "💰 **Добавление баланса**\n\n"
        "Введите сумму в EUR (€) для добавления:\n"
        "(может быть отрицательной для списания)\n\n"
        "Например: 10.00 или -5.00",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AddBalanceState.waiting_for_amount)
async def admin_add_balance_amount(
    message: Message,
    session: AsyncSession,
    user: User,
    state: FSMContext
):
    """Process balance addition."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Добавление баланса отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    # Validate amount
    try:
        amount = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("❌ Неверная сумма. Введите число.")
        return
    
    # Get target user
    data = await state.get_data()
    target_user_id = data['target_user_id']
    
    # Update balance
    success = await UserService.update_balance(session, target_user_id, amount)
    
    if success:
        # Log action
        log = AdminLog(
            admin_id=user.id,
            action="modify_balance",
            details=f"Added €{amount} to user {target_user_id}"
        )
        session.add(log)
        await session.commit()
        
        await state.clear()
        
        target_user = await UserService.get_user(session, target_user_id)
        
        operation = "добавлено" if amount >= 0 else "списано"
        
        # Refresh user to get updated balance
        await session.refresh(target_user)
        
        await message.answer(
            f"✅ *Баланс изменен!*\n\n"
            f"Пользователь: {target_user_id}\n"
            f"{operation.capitalize()}: €{abs(amount):.2f}\n"
            f"💶 Новый баланс: €{target_user.balance_sol:.2f}",
            reply_markup=admin_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Ошибка при изменении баланса.")


@router.callback_query(F.data == "admin_users_list")
async def admin_users_list_callback(callback: CallbackQuery, session: AsyncSession):
    """Return to users list."""
    users = await UserService.get_all_users(session, limit=20)
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    
    for u in users:
        status = "🚫" if u.is_blocked else "✅"
        username = f"@{u.username}" if u.username else u.first_name or "User"
        builder.button(
            text=f"{status} {username} (ID: {u.id})",
            callback_data=f"admin_user_{u.id}"
        )
    
    builder.adjust(1)
    
    await callback.message.edit_text(
        "👥 **Управление пользователями**\n\n"
        "Выберите пользователя для управления:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_reset_balance_"))
async def admin_reset_balance(callback: CallbackQuery, user: User, session: AsyncSession):
    """Reset user balance to zero."""
    user_id = int(callback.data.split("_")[3])
    
    # Get user
    target_user = await UserService.get_user(session, user_id)
    
    if not target_user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    old_balance = target_user.balance_sol
    
    # Reset balance
    target_user.balance_sol = 0.0
    await session.commit()
    
    # Log action
    log = AdminLog(
        admin_id=user.id,
        action="reset_balance",
        details=f"Reset balance for user {user_id} (was €{old_balance:.2f})"
    )
    session.add(log)
    await session.commit()
    
    await callback.answer(f"✅ Баланс обнулен! (было €{old_balance:.2f})", show_alert=True)
    
    # Create new callback with correct data for admin_user_actions
    from aiogram.types import CallbackQuery as CQ
    new_callback = CQ(
        id=callback.id,
        from_user=callback.from_user,
        message=callback.message,
        chat_instance=callback.chat_instance,
        data=f"admin_user_{user_id}"  # Правильный формат!
    )
    
    # Refresh user info
    await admin_user_actions(new_callback, session)


@router.callback_query(F.data.startswith("admin_change_role_"))
async def admin_change_role(callback: CallbackQuery, session: AsyncSession):
    """Show role selection menu."""
    user_id = int(callback.data.split("_")[3])
    
    from services.role_service import role_service
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    roles = ['user', 'seller', 'moderator', 'admin']
    for role in roles:
        role_name = role_service.get_role_name(role, 'ru')
        builder.button(text=f"👑 {role_name}", callback_data=f"set_role_{user_id}_{role}")
    
    builder.button(text="◀️ Назад", callback_data=f"admin_user_{user_id}")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "👑 **Выберите новую роль:**",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_role_"))
async def set_user_role(callback: CallbackQuery, session: AsyncSession):
    """Set user role."""
    parts = callback.data.split("_")
    user_id = int(parts[2])
    new_role = parts[3]
    
    from services.role_service import role_service
    
    success = await role_service.set_user_role(session, user_id, new_role)
    
    if success:
        role_name = role_service.get_role_name(new_role, 'ru')
        await callback.answer(f"✅ Роль изменена на: {role_name}", show_alert=True)
        
        # Create new callback with correct data
        from aiogram.types import CallbackQuery as CQ
        new_callback = CQ(
            id=callback.id,
            from_user=callback.from_user,
            message=callback.message,
            chat_instance=callback.chat_instance,
            data=f"admin_user_{user_id}"
        )
        
        # Return to user info
        await admin_user_actions(new_callback, session)
    else:
        await callback.answer("❌ Ошибка при изменении роли", show_alert=True)

