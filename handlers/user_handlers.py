"""User handlers for basic commands."""
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.user_service import UserService
from services.location_service import LocationService
from utils.keyboards import main_menu_keyboard, admin_menu_keyboard, regions_keyboard, cities_keyboard
from utils.helpers import format_sol_amount, truncate_address, is_admin
from config import settings


router = Router(name='user_handlers')


@router.message(Command("start"))
async def cmd_start(message: Message, user: User, session: AsyncSession):
    """Handle /start command."""
    from services.price_service import price_service
    balance_eur = await price_service.sol_to_eur(user.balance_sol)
    
    welcome_text = f"""
👋 **Добро пожаловать, {user.first_name or 'пользователь'}!**

Я бот для покупки цифровых товаров 🛍

━━━━━━━━━━━━━━━━━━━━

💶 Баланс: {price_service.format_eur(balance_eur)}
✨ Баллы: **{user.achievement_points}**

━━━━━━━━━━━━━━━━━━━━

**Главное меню:**

🛍 **Каталог** - товары по вашему региону
🎯 **Квесты** - активности и награды
👤 **Профиль** - ваш баланс, статистика, настройки
ℹ️ **Помощь** - инструкции и поддержка
    """
    
    keyboard = main_menu_keyboard()
    
    # Add admin hint for admins
    if is_admin(user.id, settings.admin_list):
        welcome_text += "\n\n━━━━━━━━━━━━━━━━━━━━\n👑 Вам доступен GOD режим: /god"
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """Handle /help command."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    help_text = """
ℹ️ **Помощь**

━━━━━━━━━━━━━━━━━━━━

**🛍 Каталог**
Цифровые товары по вашему региону.
• Выберите свой регион и город
• Пополните баланс (€)
• Покупайте товары моментально

**🎯 Квесты**
Активности для заработка баллов:
• Ежедневный бонус
• Квесты и задания
• Квизы
• Колесо фортуны

**👤 Профиль**
Ваш аккаунт:
• Баланс и пополнение
• Реферальная программа (10% бонус)
• Достижения (ачивки)
• История покупок
• Настройки языка

**💡 Как зарабатывать:**
✨ Ежедневный бонус: +10-35 баллов
🏆 Достижения: +10-300 баллов
🎯 Квесты: награды за задания
🧩 Квизы: баллы за правильные ответы
🎰 Колесо фортуны: до 100 баллов
🎁 Рефералы: 10% от покупок друзей

**💰 Куда тратить баллы:**
🎁 Стафф - эксклюзивные товары только за баллы!

━━━━━━━━━━━━━━━━━━━━

**Команды:**
/start - главное меню
/help - эта справка
/god - админ-панель (для админов)

━━━━━━━━━━━━━━━━━━━━

По вопросам: @support
    """
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🎫 Написать в поддержку", callback_data="support_ticket")
    builder.button(text="🛍 Перейти в каталог", callback_data="goto_catalog")
    builder.adjust(1)
    
    await message.answer(help_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data == "support_ticket")
async def support_from_help(callback: CallbackQuery, user: User, session: AsyncSession):
    """Open support from help."""
    from handlers.ticket_handlers import support_menu
    await support_menu(callback.message, user, session)
    await callback.answer()


@router.callback_query(F.data == "goto_catalog")
async def goto_catalog(callback: CallbackQuery, user: User, session: AsyncSession):
    """Go to catalog from help."""
    from handlers.catalog_handlers import show_catalog
    await show_catalog(callback.message, user, session)
    await callback.answer()


@router.message(F.text == "💰 Мой баланс")
async def show_balance_redirect(message: Message, user: User, session: AsyncSession):
    """Redirect to wallet balance with EUR display."""
    from services.price_service import price_service
    from services.deposit_service import deposit_service
    
    # Get current rate
    rate = await price_service.get_sol_eur_rate()
    balance_eur = await price_service.sol_to_eur(user.balance_sol)
    
    # Check for active deposit request
    active_deposit = await deposit_service.get_active_deposit(session, user.id)
    
    # Get rating info
    from services.rating_service import rating_service
    rating_info = await rating_service.get_user_rating_info(session, user.id)
    
    balance_text = f"""
💰 **Ваш баланс**

💶 Баланс: {price_service.format_eur(balance_eur)}
✨ Баллы: **{user.achievement_points}** баллов

━━━━━━━━━━━━━━━━━━━━

{rating_info['emoji']} **Ваш рейтинг: {rating_info['rating']:+.1f}**
{rating_info['bar']} {rating_info['level']}

📊 Статистика:
├ Покупок: {rating_info['total_purchases']}
├ Потрачено: {price_service.format_eur(await price_service.sol_to_eur(rating_info['total_spent_sol']))}
└ Возвратов: {rating_info['refunds_count']}

━━━━━━━━━━━━━━━━━━━━

💡 Баллы можно потратить в разделе "🎁 Стафф"
    """
    
    if active_deposit:
        # Calculate remaining time
        remaining = active_deposit.expires_at - datetime.utcnow()
        if remaining.total_seconds() > 0:
            minutes = int(remaining.total_seconds() / 60)
            seconds = int(remaining.total_seconds() % 60)
            
            balance_text += f"""
⏳ **Активная заявка на пополнение**

Сумма: {price_service.format_eur(active_deposit.eur_amount)}
Требуется: {format_sol_amount(active_deposit.sol_amount)}
Курс: 1 SOL = €{active_deposit.reserved_rate:.2f} (зарезервирован)

Осталось: {minutes} мин {seconds} сек

🔹 Переведите {format_sol_amount(active_deposit.sol_amount)} на адрес:
`{user.wallet_address}`
            """
        else:
            balance_text += "\n⚠️ Заявка истекла. Создайте новую для пополнения."
    
    balance_text += f"""
🔹 Адрес кошелька:
`{user.wallet_address}`
    """
    
    from utils.keyboards import wallet_keyboard
    await message.answer(balance_text, reply_markup=wallet_keyboard(), parse_mode="Markdown")


@router.message(F.text == "📍 Выбрать регион")
async def select_region(message: Message, session: AsyncSession):
    """Show region selection."""
    regions = await LocationService.get_all_regions(session)
    
    if not regions:
        await message.answer(
            "❌ Регионы еще не добавлены. Попробуйте позже."
        )
        return
    
    keyboard = regions_keyboard(regions)
    await message.answer(
        "📍 Выберите ваш регион:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("region_"))
async def select_region_callback(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession
):
    """Handle region selection."""
    region_id = int(callback.data.split("_")[1])
    
    # Get cities in region
    cities = await LocationService.get_cities_by_region(session, region_id)
    
    if not cities:
        await callback.answer(
            "❌ В этом регионе еще нет городов.",
            show_alert=True
        )
        return
    
    keyboard = cities_keyboard(cities, back_to_regions=True)
    await callback.message.edit_text(
        "🏙 Выберите ваш город:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("city_"))
async def select_city_callback(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession
):
    """Handle city selection - show districts."""
    city_id = int(callback.data.split("_")[1])
    
    # Get city details
    city = await LocationService.get_city_by_id(session, city_id)
    if not city:
        await callback.answer("❌ Город не найден.", show_alert=True)
        return
    
    # Get districts in city
    from services.district_service import district_service
    districts = await district_service.get_districts_by_city(session, city_id)
    
    if not districts:
        # No districts - save city directly
        await UserService.set_location(session, user.id, city.region_id, city_id)
        await session.refresh(city, ['region'])
        
        await callback.message.edit_text(
            f"✅ Вы выбрали: {city.region.name}, {city.name}\n\n"
            f"Теперь вы можете просмотреть каталог товаров."
        )
        await callback.answer("✅ Локация сохранена!")
        return
    
    # Show districts
    from utils.keyboards import districts_keyboard
    keyboard = districts_keyboard(districts, back_callback=f"region_{city.region_id}")
    
    await callback.message.edit_text(
        f"📍 Выберите микрорайон в городе {city.name}:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("district_"))
async def select_district_callback(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession
):
    """Handle district selection."""
    district_id = int(callback.data.split("_")[1])
    
    # Get district details
    from services.district_service import district_service
    district = await district_service.get_district_by_id(session, district_id)
    
    if not district:
        await callback.answer("❌ Микрорайон не найден.", show_alert=True)
        return
    
    # Get city and region
    city = await LocationService.get_city_by_id(session, district.city_id)
    region = await LocationService.get_region_by_id(session, city.region_id)
    
    # Update user location with district
    from sqlalchemy import update
    from database.models import User as UserModel
    stmt = update(UserModel).where(UserModel.id == user.id).values(
        region_id=city.region_id,
        city_id=city.id,
        district_id=district_id
    )
    await session.execute(stmt)
    await session.commit()
    
    await callback.message.edit_text(
        f"✅ Вы выбрали:\n"
        f"🌍 {region.name}\n"
        f"🏙 {city.name}\n"
        f"📍 {district.name}\n\n"
        f"Теперь вы можете просмотреть каталог товаров для вашего микрорайона."
    )
    await callback.answer("✅ Локация сохранена!")


@router.callback_query(F.data == "back_to_regions")
async def back_to_regions(callback: CallbackQuery, session: AsyncSession):
    """Go back to region selection."""
    regions = await LocationService.get_all_regions(session)
    keyboard = regions_keyboard(regions)
    
    await callback.message.edit_text(
        "📍 Выберите ваш регион:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.message(Command("god"))
async def cmd_admin(message: Message, user: User):
    """Open admin panel."""
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    admin_text = """
👑 **GOD Mode**

Добро пожаловать в режим администратора!
Выберите действие:
    """
    
    keyboard = admin_menu_keyboard()
    await message.answer(admin_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(F.text == "🔙 Главное меню")
async def back_to_main_menu(message: Message, user: User):
    """Return to main menu."""
    keyboard = main_menu_keyboard()
    await message.answer(
        "📱 Главное меню",
        reply_markup=keyboard
    )

