"""Shopping cart handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.cart_service import cart_service
from services.price_service import price_service
from services.user_service import UserService
from services.image_service import ImageService
from services.transaction_service import TransactionService
from services.quest_service import quest_service
from services.achievement_service import achievement_service
from services.referral_service import referral_service
from services.rating_service import rating_service

logger = logging.getLogger(__name__)

router = Router(name='cart_handlers')


@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Add item to cart."""
    image_id = int(callback.data.split("_")[3])
    
    success = await cart_service.add_to_cart(session, user.id, image_id)
    
    if success:
        await callback.answer("✅ Товар добавлен в корзину!", show_alert=True)
    else:
        await callback.answer("❌ Товар уже в корзине или продан", show_alert=True)


@router.callback_query(F.data == "view_cart")
async def view_cart_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """View shopping cart."""
    await view_cart(callback.message, user, session, edit=True)
    await callback.answer()


@router.message(F.text == "🛒 Корзина")
async def view_cart_button(message: Message, user: User, session: AsyncSession):
    """View shopping cart via button."""
    await view_cart(message, user, session)


async def view_cart(message: Message, user: User, session: AsyncSession, edit: bool = False):
    """Display shopping cart."""
    # Get cart items
    items = await cart_service.get_cart(session, user.id)
    
    if not items:
        text = "🛒 **Корзина пуста**\n\nДобавьте товары из каталога!"
        if edit:
            await message.edit_text(text, parse_mode="Markdown")
        else:
            await message.answer(text, parse_mode="Markdown")
        return
    
    # Calculate total
    total_sol = await cart_service.get_cart_total(session, user.id)
    total_eur = await price_service.sol_to_eur(total_sol)
    
    # Build message
    text = "🛒 **Твоя корзина**\n\n"
    
    for idx, item in enumerate(items, 1):
        item_eur = await price_service.sol_to_eur(item.price_sol)
        text += f"{idx}. {item.description or 'Товар'}\n"
        text += f"   💰 {price_service.format_sol(item.price_sol)} ({price_service.format_eur(item_eur)})\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"💵 **Итого:** {price_service.format_sol(total_sol)}\n"
    text += f"💶 **В евро:** {price_service.format_eur(total_eur)}\n\n"
    text += f"💰 **Твой баланс:** {price_service.format_sol(user.balance_sol)}\n"
    
    # Build keyboard
    builder = InlineKeyboardBuilder()
    
    # Remove buttons for each item
    for item in items:
        builder.button(text=f"❌ Удалить #{item.id}", callback_data=f"remove_from_cart_{item.id}")
    
    builder.adjust(2)
    
    # Buy all button
    if user.balance_sol >= total_sol:
        builder.button(text="💳 Купить всё", callback_data="buy_cart")
    else:
        deficit = total_sol - user.balance_sol
        deficit_eur = await price_service.sol_to_eur(deficit)
        builder.button(text=f"💳 Не хватает {price_service.format_eur(deficit_eur)}", callback_data="need_balance")
    
    builder.button(text="🗑 Очистить корзину", callback_data="clear_cart")
    builder.button(text="🔙 Назад", callback_data="back_to_catalog")
    
    builder.adjust(1)
    
    if edit:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("remove_from_cart_"))
async def remove_from_cart_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Remove item from cart."""
    image_id = int(callback.data.split("_")[3])
    
    success = await cart_service.remove_from_cart(session, user.id, image_id)
    
    if success:
        await callback.answer("✅ Товар удален из корзины")
        await view_cart(callback.message, user, session, edit=True)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Clear shopping cart."""
    await cart_service.clear_cart(session, user.id)
    await callback.answer("✅ Корзина очищена")
    await view_cart(callback.message, user, session, edit=True)


@router.callback_query(F.data == "buy_cart")
async def buy_cart_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Buy all items in cart."""
    # Get cart items
    items = await cart_service.get_cart(session, user.id)
    
    if not items:
        await callback.answer("❌ Корзина пуста", show_alert=True)
        return
    
    # Calculate total
    total_sol = sum(item.price_sol for item in items)
    
    # Check balance
    if user.balance_sol < total_sol:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return
    
    # Process purchases
    purchased_count = 0
    for item in items:
        # Check if still available
        if item.is_sold:
            continue
        
        # Deduct from balance
        await UserService.update_balance(session, user.id, -item.price_sol)
        
        # Mark as sold
        await ImageService.mark_as_sold(session, item.id, user.id, item.price_sol)
        
        # Create transaction
        await TransactionService.create_transaction(
            session=session,
            user_id=user.id,
            tx_type='purchase',
            amount_sol=item.price_sol,
            description=f"Покупка из корзины: {item.description or f'Товар #{item.id}'}",
            status='completed'
        )
        
        purchased_count += 1
    
    # Update quest progress
    await quest_service.update_quest_progress(session, user.id, 'purchases', purchased_count)
    await quest_service.update_quest_progress(session, user.id, 'spending', total_sol)
    
    # Check achievements
    new_achievements = await achievement_service.check_and_unlock_achievements(session, user.id)
    
    # Process referral bonus
    referral_bonus = await referral_service.process_referral_bonus(session, user.id, total_sol)
    
    # Update rating
    new_rating = await rating_service.update_rating_after_purchase(session, user.id, total_sol)
    
    # Clear cart
    await cart_service.clear_cart(session, user.id)
    
    # Success message
    total_eur = await price_service.sol_to_eur(total_sol)
    text = f"""
✅ **Покупка успешна!**

📦 Куплено товаров: **{purchased_count}**
💰 Потрачено: **{price_service.format_sol(total_sol)}** ({price_service.format_eur(total_eur)})
    """
    
    if new_achievements:
        text += f"\n🏆 **Новые достижения:** {len(new_achievements)}"
    
    if referral_bonus > 0:
        text += f"\n🎁 Ваш реферер получил бонус: {price_service.format_sol(referral_bonus)}"
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.message.delete()
    await callback.answer("✅ Покупка завершена!")

