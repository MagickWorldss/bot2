"""Admin handlers for staff shop management."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.staff_service import staff_service
from services.role_service import role_service
from utils.keyboards import cancel_keyboard, admin_menu_keyboard
from utils.helpers import is_admin
from config import settings

logger = logging.getLogger(__name__)

router = Router(name='admin_staff_handlers')


class AddStaffItemStates(StatesGroup):
    """States for adding staff item."""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_type = State()
    waiting_for_content = State()
    waiting_for_stock = State()


@router.message(F.text == "🎁 Стафф товары")
async def staff_items_menu(message: Message, user: User, session: AsyncSession):
    """Show staff items management menu."""
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ Нет доступа")
        return
    
    # Get all staff items
    items = await staff_service.get_all_items(session, active_only=False)
    
    text = "🎁 **Управление товарами за баллы**\n\n"
    
    if not items:
        text += "📭 Товаров пока нет\n\n"
    else:
        for item in items[:10]:
            status = "✅" if item.is_active else "❌"
            available = item.stock_count - item.sold_count
            text += f"{status} **{item.name}**\n"
            text += f"   💰 {item.price_points} баллов | Остаток: {available}/{item.stock_count}\n"
            text += f"   Продано: {item.sold_count}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить товар", callback_data="create_staff_item")
    
    if items:
        builder.button(text="📋 Все товары", callback_data="list_all_staff_items")
    
    builder.button(text="🔙 Назад", callback_data="back_to_admin")
    builder.adjust(1)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data == "create_staff_item")
async def create_staff_item_init(callback: CallbackQuery, user: User, state: FSMContext):
    """Start staff item creation."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    text = """
➕ **Добавление товара за баллы**

Введите название товара:

Например: Промокод SALE50
    """
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AddStaffItemStates.waiting_for_name)
    await callback.answer()


@router.message(AddStaffItemStates.waiting_for_name)
async def staff_receive_name(message: Message, state: FSMContext):
    """Receive item name."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=admin_menu_keyboard())
        return
    
    await state.update_data(name=message.text.strip())
    await message.answer(
        "📝 Введите описание товара:\n(Или '-' чтобы пропустить)",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AddStaffItemStates.waiting_for_description)


@router.message(AddStaffItemStates.waiting_for_description)
async def staff_receive_description(message: Message, state: FSMContext):
    """Receive description."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=admin_menu_keyboard())
        return
    
    description = None if message.text == '-' else message.text
    await state.update_data(description=description)
    
    await message.answer("💰 Введите цену в баллах:\n(Например: 100)")
    await state.set_state(AddStaffItemStates.waiting_for_price)


@router.message(AddStaffItemStates.waiting_for_price)
async def staff_receive_price(message: Message, state: FSMContext):
    """Receive price."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=admin_menu_keyboard())
        return
    
    try:
        price = int(message.text)
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0")
            return
        
        await state.update_data(price_points=price)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="📄 Цифровой товар", callback_data="staff_type_digital")
        builder.button(text="🎫 Промокод", callback_data="staff_type_promocode")
        builder.button(text="💎 Бонус", callback_data="staff_type_bonus")
        builder.adjust(1)
        
        await message.answer(
            "📦 Выберите тип товара:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(AddStaffItemStates.waiting_for_type)
        
    except ValueError:
        await message.answer("❌ Введите число")


@router.callback_query(F.data.startswith("staff_type_"))
async def staff_receive_type(callback: CallbackQuery, user: User, state: FSMContext):
    """Receive item type."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    item_type = callback.data.split("_")[2]  # digital, promocode, bonus
    
    await state.update_data(item_type=item_type)
    
    if item_type == 'digital':
        text = "📄 Отправьте файл/фото товара или введите текст:"
    elif item_type == 'promocode':
        text = "🎫 Введите промокод (например: SALE50):"
    else:
        text = "💎 Введите описание бонуса:"
    
    await callback.message.edit_text(text)
    await state.set_state(AddStaffItemStates.waiting_for_content)
    await callback.answer()


@router.message(AddStaffItemStates.waiting_for_content)
async def staff_receive_content(message: Message, session: AsyncSession, user: User, state: FSMContext):
    """Receive content and ask for stock."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=admin_menu_keyboard())
        return
    
    # Save content
    file_id = None
    item_data = None
    
    if message.photo:
        file_id = message.photo[-1].file_id
        item_data = message.caption if message.caption else None
    elif message.document:
        file_id = message.document.file_id
        item_data = message.caption if message.caption else None
    else:
        item_data = message.text
    
    await state.update_data(file_id=file_id, item_data=item_data)
    
    await message.answer(
        "📦 Введите количество на складе:\n(Например: 10, или 0 для безлимита)"
    )
    await state.set_state(AddStaffItemStates.waiting_for_stock)


@router.message(AddStaffItemStates.waiting_for_stock)
async def staff_receive_stock(message: Message, session: AsyncSession, user: User, state: FSMContext):
    """Receive stock and create item."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=admin_menu_keyboard())
        return
    
    try:
        stock = int(message.text)
        stock = 999999 if stock == 0 else stock
        
        # Get all data
        data = await state.get_data()
        
        # Create item
        item = await staff_service.create_staff_item(
            session=session,
            name=data['name'],
            price_points=data['price_points'],
            description=data.get('description'),
            file_id=data.get('file_id'),
            item_type=data['item_type'],
            item_data=data.get('item_data'),
            stock_count=stock
        )
        
        text = f"""
✅ **Товар создан!**

🎁 Название: {item.name}
💰 Цена: {item.price_points} баллов
📦 Тип: {item.item_type}
📊 Остаток: {item.stock_count}

Пользователи увидят этот товар в разделе "🎁 Стафф"
        """
        
        await message.answer(text, parse_mode="Markdown", reply_markup=admin_menu_keyboard())
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число")


@router.callback_query(F.data == "list_all_staff_items")
async def list_all_staff_items(callback: CallbackQuery, user: User, session: AsyncSession):
    """List all staff items."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    items = await staff_service.get_all_items(session, active_only=False)
    
    text = "📋 **Все товары за баллы:**\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for item in items:
        status = "✅" if item.is_active else "❌"
        available = item.stock_count - item.sold_count
        text += f"{status} **{item.name}** ({item.price_points} баллов) - {available} шт.\n"
        
        if item.is_active:
            builder.button(text=f"❌ {item.name}", callback_data=f"deactivate_staff_{item.id}")
        else:
            builder.button(text=f"✅ {item.name}", callback_data=f"activate_staff_{item.id}")
    
    builder.button(text="🔙 Назад", callback_data="back_to_staff_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("deactivate_staff_"))
async def deactivate_staff_item(callback: CallbackQuery, user: User, session: AsyncSession):
    """Deactivate staff item."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    item_id = int(callback.data.split("_")[2])
    
    await staff_service.toggle_item_active(session, item_id, False)
    await callback.answer("✅ Товар деактивирован")
    await list_all_staff_items(callback, user, session)


@router.callback_query(F.data.startswith("activate_staff_"))
async def activate_staff_item(callback: CallbackQuery, user: User, session: AsyncSession):
    """Activate staff item."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    item_id = int(callback.data.split("_")[2])
    
    await staff_service.toggle_item_active(session, item_id, True)
    await callback.answer("✅ Товар активирован")
    await list_all_staff_items(callback, user, session)


@router.callback_query(F.data == "back_to_staff_menu")
async def back_to_staff_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Return to staff menu."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    """Return to staff menu."""
    await staff_items_menu(callback.message, user, session)
    await callback.message.delete()

