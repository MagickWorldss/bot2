"""Menu navigation handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.location_service import LocationService
from utils.keyboards import quests_menu_keyboard, profile_menu_keyboard, shop_menu_keyboard

logger = logging.getLogger(__name__)

router = Router(name='menu_handlers')


@router.message(F.text == "🛍 Магазин")
async def show_shop_menu(message: Message, user: User, session: AsyncSession):
    """Show shop menu."""
    from services.price_service import price_service
    # ВАЖНО: balance_eur хранит EUR, НЕ КОНВЕРТИРУЕМ!
    balance_eur = user.balance_eur
    
    text = f"""
🛍 **Магазин**

Выберите раздел:

━━━━━━━━━━━━━━━━━━━━

🛍 **Каталог товаров**
Цифровые товары за деньги
• Товары по региону (Литва)
• Оплата: € (евро)
• Моментальная покупка

🎁 **Стафф (за баллы)**
Эксклюзивные товары за баллы
• Промокоды, бонусы, контент
• Оплата: ✨ баллы
• Нельзя купить за деньги!

━━━━━━━━━━━━━━━━━━━━

💶 Ваш баланс: {price_service.format_eur(balance_eur)}
✨ Ваши баллы: **{user.achievement_points}**
    """
    
    await message.answer(text, reply_markup=shop_menu_keyboard(user_role=user.role), parse_mode="Markdown")


@router.callback_query(F.data == "all_districts_menu")
async def all_districts_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show all districts with product counts."""
    from services.district_service import district_service
    from services.image_service import ImageService
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    # Get user's city (if set)
    if user.city_id:
        city = await LocationService.get_city_by_id(session, user.city_id)
        city_name = city.name if city else "вашем городе"
        districts = await district_service.get_districts_by_city(session, user.city_id, active_only=True)
    else:
        # Show all districts from first region
        regions = await LocationService.get_all_regions(session)
        if regions:
            cities = await LocationService.get_cities_by_region(session, regions[0].id)
            if cities:
                city_name = "всех городах"
                # Get districts from all cities
                all_districts = []
                for city in cities:
                    city_districts = await district_service.get_districts_by_city(session, city.id, active_only=True)
                    all_districts.extend(city_districts)
                districts = all_districts
            else:
                districts = []
        else:
            districts = []
            city_name = ""
    
    text = f"🏘 **Все районы в {city_name}:**\n\n"
    
    if not districts:
        text += "📭 Нет доступных районов.\n\nВыберите регион и город сначала."
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="back_to_shop_menu")
        builder.adjust(1)
        
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await callback.answer()
        return
    
    # Count products in each district
    builder = InlineKeyboardBuilder()
    
    for district in districts[:30]:  # Show first 30
        # Count products in this district
        district_products = await ImageService.get_available_images(
            session,
            region_id=user.region_id,
            city_id=district.city_id,
            limit=1000
        )
        # Filter by district_id
        count = sum(1 for img in district_products if img.district_id == district.id)
        
        text += f"📍 **{district.name}**: {count} товар(ов)\n"
        
        if count > 0:
            builder.button(
                text=f"📍 {district.name} ({count})",
                callback_data=f"view_district_{district.id}"
            )
    
    builder.button(text="🔙 Назад к магазину", callback_data="back_to_shop_menu")
    builder.adjust(2)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("view_district_"))
async def view_district_products(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show products in specific district."""
    district_id = int(callback.data.split("_")[2])
    
    from services.district_service import district_service
    from services.image_service import ImageService
    from utils.keyboards import catalog_keyboard
    from utils.helpers import paginate_list
    
    district = await district_service.get_district_by_id(session, district_id)
    
    if not district:
        await callback.answer("❌ Район не найден", show_alert=True)
        return
    
    # Get products in this district
    all_products = await ImageService.get_available_images(
        session,
        region_id=user.region_id,
        city_id=district.city_id,
        limit=1000
    )
    # Filter by district_id
    district_products = [img for img in all_products if img.district_id == district.id]
    
    if not district_products:
        await callback.answer("😔 В этом районе нет товаров", show_alert=True)
        return
    
    # Show products
    page_size = 5
    current_page, total_pages = paginate_list(district_products, 0, page_size)
    
    text = f"🏘 **Район: {district.name}**\n\n"
    text += f"Найдено товаров: **{len(district_products)}**\n\n"
    text += "Выберите товар:"
    
    keyboard = catalog_keyboard(current_page, page=0, total_pages=total_pages)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "back_to_shop_menu")
async def back_to_shop_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Return to shop menu."""
    await show_shop_menu(callback.message, user, session)


@router.callback_query(F.data == "change_region_menu")
async def change_region_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Change region from shop menu."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    regions = await LocationService.get_all_regions(session)
    
    builder = InlineKeyboardBuilder()
    for region in regions:
        builder.button(
            text=f"{region.name}",
            callback_data=f"region_{region.id}"  # Исправлено: используем существующий handler
        )
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📍 **Выберите регион:**",
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "catalog_menu")
async def catalog_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show catalog from menu."""
    # Check if user selected location
    if not user.city_id:
        await callback.message.edit_text(
            "⚠️ **Сначала выберите ваш регион!**\n\n"
            "Используйте: 👤 Профиль → настройте локацию",
            parse_mode="Markdown"
        )
        await callback.answer("⚠️ Выберите регион!", show_alert=True)
        return
    
    # Get available images for user's location
    from services.image_service import ImageService
    images = await ImageService.get_available_images(
        session,
        region_id=user.region_id,
        city_id=user.city_id
    )
    
    if not images:
        await callback.message.edit_text(
            "😔 К сожалению, в вашем регионе сейчас нет доступных товаров.\n\n"
            "Попробуйте зайти позже.",
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Show first page
    from utils.keyboards import catalog_keyboard
    from utils.helpers import paginate_list
    
    page_size = 5
    current_page, total_pages = paginate_list(images, 0, page_size)
    
    # Load location manually (no relationships in User model)
    region_name = "не указан"
    city_name = "не указан"
    
    if user.region_id and user.city_id:
        region = await LocationService.get_region_by_id(session, user.region_id)
        city = await LocationService.get_city_by_id(session, user.city_id)
        region_name = region.name if region else "не указан"
        city_name = city.name if city else "не указан"
    
    catalog_text = f"🛍 **Каталог товаров**\n\n"
    catalog_text += f"📍 Ваш регион: {region_name}\n"
    catalog_text += f"🏙 Ваш город: {city_name}\n\n"
    catalog_text += f"Найдено товаров: **{len(images)}**\n\n"
    catalog_text += "Выберите товар для просмотра:"
    
    keyboard = catalog_keyboard(current_page, page=0, total_pages=total_pages)
    
    await callback.message.edit_text(
        catalog_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "staff_menu")
async def staff_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show staff shop from menu."""
    from handlers.staff_handlers import show_staff_shop
    await show_staff_shop(callback.message, user, session)
    await callback.answer()


@router.message(F.text == "🎯 Квесты")
async def show_quests_menu(message: Message):
    """Show quests menu."""
    text = """
🎯 **Квесты и активности**

Выберите раздел:

🎁 **Ежедневный бонус** - получай баллы каждый день
🎯 **Квесты** - выполняй задания, получай награды
🧩 **Квиз** - отвечай на вопросы, зарабатывай баллы
🎰 **Колесо фортуны** - испытай удачу!

━━━━━━━━━━━━━━━━━━━━

💡 Все активности дают баллы!
Баллы можно потратить в магазине "🎁 Стафф"
    """
    
    await message.answer(text, reply_markup=quests_menu_keyboard(), parse_mode="Markdown")


@router.message(F.text == "👤 Профиль")
async def show_profile_menu(message: Message, user: User, session: AsyncSession):
    """Show profile menu."""
    from services.price_service import price_service
    # ВАЖНО: balance_eur хранит EUR, НЕ КОНВЕРТИРУЕМ!
    balance_eur = user.balance_eur
    
    text = f"""
👤 **Ваш профиль**

👋 {user.first_name or 'Пользователь'}
🆔 ID: `{user.id}`

💶 Баланс: {price_service.format_eur(balance_eur)}
✨ Баллы: **{user.achievement_points}**

━━━━━━━━━━━━━━━━━━━━

Выберите раздел:

💰 **Мой баланс** - пополнить, посмотреть
🎁 **Реферальная программа** - приглашай друзей
🏆 **Достижения** - твои ачивки
📜 **История покупок** - что купил
🌐 **Язык** - изменить язык бота
    """
    
    await message.answer(text, reply_markup=profile_menu_keyboard(), parse_mode="Markdown")


# Callbacks for quests menu
@router.callback_query(F.data == "daily_bonus_menu")
async def daily_bonus_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle daily bonus from menu."""
    from handlers.daily_bonus_handlers import claim_daily_bonus
    await claim_daily_bonus(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "quests_menu")
async def quests_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle quests from menu."""
    from handlers.quest_handlers import show_quests
    await show_quests(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "quiz_menu")
async def quiz_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle quiz from menu."""
    from handlers.quiz_handlers import start_quiz
    await start_quiz(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "fortune_wheel")
async def fortune_wheel_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Fortune wheel - spin for random reward."""
    import random
    from services.daily_bonus_service import daily_bonus_service
    
    # Check if can spin (once per day, like daily bonus)
    status = await daily_bonus_service.get_daily_bonus_status(session, user.id)
    
    if not status['can_claim']:
        await callback.answer(
            f"🎰 Колесо уже было крутнуто сегодня!\n"
            f"Следующая попытка через {status['hours_until_next']} часов",
            show_alert=True
        )
        return
    
    # Spin wheel - random reward
    rewards = [
        {'type': 'points', 'value': 5, 'text': '✨ 5 баллов', 'emoji': '✨'},
        {'type': 'points', 'value': 10, 'text': '💎 10 баллов', 'emoji': '💎'},
        {'type': 'points', 'value': 25, 'text': '⭐ 25 баллов', 'emoji': '⭐'},
        {'type': 'points', 'value': 50, 'text': '🌟 50 баллов', 'emoji': '🌟'},
        {'type': 'points', 'value': 100, 'text': '🎉 100 баллов!', 'emoji': '🎉'},
        {'type': 'nothing', 'value': 0, 'text': '😅 Ничего', 'emoji': '😅'},
    ]
    
    # Weighted random
    weights = [30, 25, 20, 15, 5, 5]  # 5% chance for 100 points
    reward = random.choices(rewards, weights=weights)[0]
    
    # Give reward
    if reward['type'] == 'points' and reward['value'] > 0:
        from sqlalchemy import update
        from database.models import User as UserModel
        stmt = update(UserModel).where(UserModel.id == user.id).values(
            achievement_points=UserModel.achievement_points + reward['value']
        )
        await session.execute(stmt)
        await session.commit()
    
    # Mark as used (use daily bonus timestamp)
    from datetime import datetime
    stmt = update(UserModel).where(UserModel.id == user.id).values(
        last_daily_bonus=datetime.utcnow()
    )
    await session.execute(stmt)
    await session.commit()
    
    text = f"""
🎰 **Колесо фортуны**

🎲 Крутим колесо...

━━━━━━━━━━━━━━━━━━━━

{reward['emoji']} **{reward['text']}!**

━━━━━━━━━━━━━━━━━━━━

💫 Возвращайтесь завтра за новым вращением!
    """
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer(f"{reward['emoji']} {reward['text']}!", show_alert=True)


# Callbacks for profile menu
@router.callback_query(F.data == "my_balance")
async def my_balance_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show balance from menu."""
    from handlers.user_handlers import show_balance_redirect
    await show_balance_redirect(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "referral_menu")
async def referral_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show referral from menu."""
    from handlers.referral_handlers import show_referral_info
    await show_referral_info(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "achievements_menu")
async def achievements_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show achievements from menu."""
    from handlers.achievement_handlers import show_achievements
    await show_achievements(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "purchase_history_menu")
async def purchase_history_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show purchase history from menu."""
    from handlers.catalog_handlers import show_purchase_history
    await show_purchase_history(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "language_menu")
async def language_from_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show language selection from menu."""
    from services.language_service import language_service
    from utils.language_keyboards import language_selection_keyboard
    
    lang = await language_service.get_user_language(session, user.id)
    
    await callback.message.edit_text(
        language_service.get_text(lang, 'select_language'),
        reply_markup=language_selection_keyboard()
    )
    await callback.answer()

