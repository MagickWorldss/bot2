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
    welcome_text = f"""
👋 Добро пожаловать, {user.first_name or 'пользователь'}!

Я бот для покупки цифровых товаров за криптовалюту (SOL).

🔹 Ваш личный кошелек:
`{user.wallet_address}`

💰 Баланс: {format_sol_amount(user.balance_sol)}

📍 Выберите регион и город, чтобы увидеть доступные товары.

Используйте меню ниже для навигации.
    """
    
    keyboard = main_menu_keyboard()
    
    # Add admin menu button for admins
    if is_admin(user.id, settings.admin_list):
        welcome_text += "\n\n👑 Вам доступен GOD режим. Команда: /god"
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message):
    """Handle /help command."""
    help_text = """
ℹ️ **Помощь**

**Как купить товар:**
1. Выберите регион и город (📍 Выбрать регион)
2. Пополните баланс (💰 Мой баланс → Пополнить)
3. Перейдите в каталог (🛍 Каталог)
4. Выберите товар и купите его

**Пополнение баланса:**
- Выберите сумму в евро (EUR)
- Курс зафиксируется на 30 минут
- Переведите SOL на ваш адрес
- Зачисление по зафиксированному курсу

**Важно:**
- Каждый товар продается только один раз
- После покупки товар сразу удаляется из каталога
- Баланс отображается в евро (€)

**Команды:**
- /start - главное меню
- /help - эта справка

По вопросам: @support
    """
    
    await message.answer(help_text, parse_mode="Markdown")


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
    
    balance_text = f"""
💰 **Ваш баланс**

💶 Баланс: {price_service.format_eur(balance_eur)}
💎 В SOL: {format_sol_amount(user.balance_sol)}

📊 Текущий курс: 1 SOL = €{rate:.2f}
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
    """Handle city selection."""
    city_id = int(callback.data.split("_")[1])
    
    # Get city details
    city = await LocationService.get_city_by_id(session, city_id)
    if not city:
        await callback.answer("❌ Город не найден.", show_alert=True)
        return
    
    # Update user location
    await UserService.set_location(session, user.id, city.region_id, city_id)
    
    # Load region
    await session.refresh(city, ['region'])
    
    await callback.message.edit_text(
        f"✅ Вы выбрали: {city.region.name}, {city.name}\n\n"
        f"Теперь вы можете просмотреть каталог товаров для вашего региона."
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

