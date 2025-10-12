"""Admin handlers for bot management."""
import os
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


class AddImageStates(StatesGroup):
    """States for adding image."""
    waiting_for_region = State()
    waiting_for_city = State()
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
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ У вас нет доступа к этой функции.")
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
        await state.set_state(AddImageStates.waiting_for_image)
        
        await message.answer(
            "🖼 **Отправьте изображение товара:**\n\n"
            "Это изображение будет продаваться пользователям."
        )
        
    except ValueError:
        await message.answer("❌ Введите номер города (например: /1)")


@router.message(AddImageStates.waiting_for_image, F.photo)
async def add_product_image(message: Message, state: FSMContext):
    """Process image upload."""
    # Get the best quality photo
    photo = message.photo[-1]
    file_id = photo.file_id
    
    await state.update_data(file_id=file_id)
    await state.set_state(AddImageStates.waiting_for_price)
    
    await message.answer(
        "💰 **Укажите цену в SOL:**\n\n"
        "Например: 0.05"
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
    
    from utils.helpers import validate_sol_amount
    
    price = validate_sol_amount(message.text)
    if not price:
        await message.answer(
            "❌ Неверная цена. Введите число больше 0.\n"
            "Например: 0.05"
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
    region_id = data['region_id']
    city_id = data['city_id']
    file_id = data['file_id']
    price = data['price']
    
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
        description=description
    )
    
    # Log admin action
    log = AdminLog(
        admin_id=user.id,
        action="add_product",
        details=f"Added product #{image.id}, price: {price} SOL"
    )
    session.add(log)
    await session.commit()
    
    await state.clear()
    
    # Load location info
    await session.refresh(image, ['region', 'city'])
    
    await message.answer(
        f"✅ **Товар успешно добавлен!**\n\n"
        f"ID: #{image.id}\n"
        f"Регион: {image.region.name}\n"
        f"Город: {image.city.name}\n"
        f"Цена: {format_sol_amount(image.price_sol)}\n"
        f"Описание: {image.description or 'Нет'}",
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )


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
💰 Общая выручка: {format_sol_amount(stats['total_revenue'])}
    """
    
    await message.answer(stats_text, parse_mode="Markdown")


@router.message(F.text == "🗂 Управление регионами")
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
        
        # Load region
        await session.refresh(city, ['region'])
        
        await message.answer(
            f"✅ **Город успешно добавлен!**\n\n"
            f"Название: {city.name}\n"
            f"Регион: {city.region.name}",
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
    await session.refresh(city, ['region'])
    
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
        f"Регион: {city.region.name}\n"
        f"Статус: {status}\n\n"
        f"Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await callback.answer(f"✅ Статус изменен на: {status}")


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


@router.message(F.text == "👥 Управление пользователями")
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
    user_id = int(callback.data.split("_")[2])
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
    
    # Back button
    builder.button(text="◀️ Назад к списку", callback_data="admin_users_list")
    
    builder.adjust(2, 2, 1, 1)
    
    # User info
    status = "🚫 Заблокирован" if target_user.is_blocked else "✅ Активен"
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
        
        # Refresh user info
        target_user = await UserService.get_user_with_location(session, user_id)
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🟢 Разблокировать", callback_data=f"admin_unblock_{user_id}")
        builder.button(text="📜 История покупок", callback_data=f"admin_purchases_{user_id}")
        builder.button(text="💸 История транзакций", callback_data=f"admin_transactions_{user_id}")
        builder.button(text="💰 Добавить баланс", callback_data=f"admin_add_balance_{user_id}")
        builder.button(text="◀️ Назад к списку", callback_data="admin_users_list")
        builder.adjust(2, 2, 1, 1)
        
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
        
        # Refresh user info
        target_user = await UserService.get_user_with_location(session, user_id)
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🔴 Заблокировать", callback_data=f"admin_block_{user_id}")
        builder.button(text="📜 История покупок", callback_data=f"admin_purchases_{user_id}")
        builder.button(text="💸 История транзакций", callback_data=f"admin_transactions_{user_id}")
        builder.button(text="💰 Добавить баланс", callback_data=f"admin_add_balance_{user_id}")
        builder.button(text="◀️ Назад к списку", callback_data="admin_users_list")
        builder.adjust(2, 2, 1, 1)
        
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
        await session.refresh(image, ['region', 'city'])
        
        history_text += (
            f"🖼 Товар #{image.id}\n"
            f"💰 Цена: {format_sol_amount(purchase.price_paid_sol)}\n"
            f"📅 Дата: {purchase.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📍 {image.region.name}, {image.city.name}\n\n"
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
            f"{type_emoji} **{tx.tx_type.capitalize()}** {status_emoji}\n"
            f"Сумма: {format_sol_amount(tx.amount_sol)}\n"
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
        "Введите сумму в SOL для добавления:\n"
        "(может быть отрицательной для списания)\n\n"
        "Например: 0.1 или -0.05",
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
            details=f"Added {amount} SOL to user {target_user_id}"
        )
        session.add(log)
        await session.commit()
        
        await state.clear()
        
        target_user = await UserService.get_user(session, target_user_id)
        
        operation = "добавлено" if amount >= 0 else "списано"
        
        await message.answer(
            f"✅ **Баланс изменен!**\n\n"
            f"Пользователь: {target_user_id}\n"
            f"{operation.capitalize()}: {format_sol_amount(abs(amount))}\n"
            f"Новый баланс: {format_sol_amount(target_user.balance_sol)}",
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

