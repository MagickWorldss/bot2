"""Staff shop handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.staff_service import staff_service

logger = logging.getLogger(__name__)

router = Router(name='staff_handlers')


@router.message(F.text == "🎁 Стафф")
async def show_staff_shop(message: Message, user: User, session: AsyncSession):
    """Show staff shop."""
    # Get all active items
    items = await staff_service.get_all_items(session, active_only=True)
    
    if not items:
        text = """
🎁 **Магазин за баллы**

📭 Пока нет доступных товаров

━━━━━━━━━━━━━━━━━━━━

💡 Здесь появятся эксклюзивные товары,
которые можно купить за баллы!

Баллы можно получить:
• Ежедневный бонус (/daily)
• Достижения
• Квесты
• Квизы
• Акции
        """
        await message.answer(text, parse_mode="Markdown")
        return
    
    text = f"""
🎁 **Магазин за баллы**

✨ Ваши баллы: **{user.achievement_points}**

━━━━━━━━━━━━━━━━━━━━

**Доступные товары:**

"""
    
    builder = InlineKeyboardBuilder()
    
    for item in items:
        # Check stock
        available = item.stock_count - item.sold_count
        stock_text = f"(осталось: {available})" if available > 0 else "(нет в наличии)"
        
        text += f"🎁 **{item.name}**\n"
        text += f"   💰 {item.price_points} баллов {stock_text}\n"
        if item.description:
            text += f"   _{item.description}_\n"
        text += "\n"
        
        if available > 0:
            builder.button(
                text=f"🎁 {item.name} - {item.price_points} баллов",
                callback_data=f"buy_staff_{item.id}"
            )
    
    builder.adjust(1)
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "💡 Нажмите на товар чтобы купить"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("buy_staff_"))
async def buy_staff_item(callback: CallbackQuery, user: User, session: AsyncSession):
    """Purchase staff item."""
    item_id = int(callback.data.split("_")[2])
    
    # Purchase
    success, message_text, item = await staff_service.purchase_staff_item(session, user.id, item_id)
    
    if not success:
        await callback.answer(message_text, show_alert=True)
        return
    
    # Send item
    text = f"""
✅ **Покупка успешна!**

🎁 Товар: **{item.name}**
💰 Потрачено: **{item.price_points}** баллов

"""
    
    if item.item_type == 'promocode' and item.item_data:
        text += f"🎫 Ваш промокод: `{item.item_data}`\n\n"
    elif item.item_type == 'bonus' and item.item_data:
        text += f"💎 Бонус: {item.item_data}\n\n"
    
    if item.file_id:
        # Send file/image
        await callback.message.answer_photo(
            photo=item.file_id,
            caption=text,
            parse_mode="Markdown"
        )
    elif item.item_data and item.item_type == 'digital':
        text += f"📄 Контент:\n{item.item_data}"
        await callback.message.answer(text, parse_mode="Markdown")
    else:
        await callback.message.answer(text, parse_mode="Markdown")
    
    await callback.message.delete()
    await callback.answer("✅ Покупка завершена!")

