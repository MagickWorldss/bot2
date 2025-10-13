"""Wallet handlers for balance operations."""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.transaction_service import TransactionService
from utils.keyboards import wallet_keyboard, cancel_keyboard, main_menu_keyboard
from utils.helpers import format_sol_amount, validate_sol_amount


router = Router(name='wallet_handlers')


class WithdrawStates(StatesGroup):
    """States for withdrawal process."""
    waiting_for_address = State()
    waiting_for_amount = State()


class DepositStates(StatesGroup):
    """States for deposit process."""
    waiting_for_eur_amount = State()


@router.callback_query(F.data == "deposit")
async def deposit_init(callback: CallbackQuery, user: User, session: AsyncSession, state: FSMContext):
    """Initialize deposit with EUR amount."""
    from services.price_service import price_service
    from services.deposit_service import deposit_service
    
    # Check for active deposit
    active_deposit = await deposit_service.get_active_deposit(session, user.id)
    
    if active_deposit:
        # Show existing deposit
        remaining = active_deposit.expires_at - datetime.utcnow()
        minutes = int(remaining.total_seconds() / 60)
        seconds = int(remaining.total_seconds() % 60)
        
        deposit_text = f"""
⏳ **У вас уже есть активная заявка**

Сумма: {price_service.format_eur(active_deposit.eur_amount)}
Требуется: {price_service.format_sol(active_deposit.sol_amount)}
Курс: 1 SOL = €{active_deposit.reserved_rate:.2f}

Осталось времени: {minutes} мин {seconds} сек

🔹 Переведите {price_service.format_sol(active_deposit.sol_amount)} на адрес:
`{user.wallet_address}`

После перевода средства зачислятся автоматически по курсу €{active_deposit.reserved_rate:.2f} за 1 SOL.
        """
        
        await callback.message.answer(deposit_text, parse_mode="Markdown")
        await callback.answer()
        return
    
    # Get current rate
    rate = await price_service.get_sol_eur_rate()
    
    await state.set_state(DepositStates.waiting_for_eur_amount)
    
    deposit_text = f"""
💵 **Пополнение баланса**

📊 Текущий курс: 1 SOL = €{rate:.2f}

Введите сумму для пополнения в **евро (EUR)**:

Например: 5 или 10 или 20

⚠️ **Важно:**
- Курс зафиксируется на 30 минут
- У вас будет 30 минут для перевода SOL
- Зачисление по зафиксированному курсу
- Минимум: €5
    """
    
    from utils.keyboards import cancel_keyboard
    await callback.message.answer(deposit_text, reply_markup=cancel_keyboard(), parse_mode="Markdown")
    await callback.answer()


@router.message(DepositStates.waiting_for_eur_amount)
async def deposit_amount(message: Message, user: User, session: AsyncSession, state: FSMContext):
    """Process EUR amount for deposit."""
    if message.text == "❌ Отмена":
        await state.clear()
        from utils.keyboards import main_menu_keyboard
        await message.answer(
            "❌ Пополнение отменено.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Validate amount
    try:
        eur_amount = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("❌ Неверная сумма. Введите число (например: 10)")
        return
    
    if eur_amount < 5:
        await message.answer("❌ Минимальная сумма пополнения: €5")
        return
    
    # Create deposit request
    from services.deposit_service import deposit_service
    from services.price_service import price_service
    
    deposit = await deposit_service.create_deposit_request(
        session, user.id, eur_amount
    )
    
    await state.clear()
    
    # Calculate time remaining
    expires_in_minutes = 30
    
    deposit_text = f"""
✅ **Заявка на пополнение создана!**

💶 Сумма: {price_service.format_eur(deposit.eur_amount)}
💎 Требуется: {price_service.format_sol(deposit.sol_amount)}
📊 Зарезервированный курс: 1 SOL = €{deposit.reserved_rate:.2f}

⏳ У вас есть **{expires_in_minutes} минут** для перевода!

🔹 Переведите **{price_service.format_sol(deposit.sol_amount)}** на адрес:
`{user.wallet_address}`

⚠️ **Важно:**
- Переведите ТОЧНУЮ сумму: {deposit.sol_amount:.6f} SOL
- Курс зафиксирован на 30 минут
- После перевода зачисление автоматическое
- Зачислится: {price_service.format_eur(deposit.eur_amount)}

📅 Действительно до: {deposit.expires_at.strftime('%H:%M:%S')} UTC
    """
    
    from utils.keyboards import main_menu_keyboard
    await message.answer(deposit_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == "withdraw")
async def withdraw_init(callback: CallbackQuery, user: User, state: FSMContext):
    """Initialize withdrawal."""
    if user.balance_sol <= 0:
        await callback.answer(
            "❌ Недостаточно средств для вывода.",
            show_alert=True
        )
        return
    
    await callback.message.answer(
        f"💸 **Вывод средств**\n\n"
        f"Доступно для вывода: {format_sol_amount(user.balance_sol)}\n"
        f"Комиссия: 2%\n\n"
        f"Введите адрес кошелька SOL для вывода:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    
    await state.set_state(WithdrawStates.waiting_for_address)
    await callback.answer()


@router.message(WithdrawStates.waiting_for_address)
async def withdraw_address(message: Message, state: FSMContext):
    """Process withdrawal address."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Вывод средств отменен.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Basic validation
    address = message.text.strip()
    if len(address) < 32 or len(address) > 44:
        await message.answer(
            "❌ Неверный формат адреса. Попробуйте еще раз."
        )
        return
    
    await state.update_data(withdraw_address=address)
    await state.set_state(WithdrawStates.waiting_for_amount)
    
    await message.answer(
        "💰 Введите сумму для вывода (в SOL):"
    )


@router.message(WithdrawStates.waiting_for_amount)
async def withdraw_amount(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext
):
    """Process withdrawal amount."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Вывод средств отменен.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    # Validate amount
    amount = validate_sol_amount(message.text)
    if not amount:
        await message.answer(
            "❌ Неверная сумма. Введите число больше 0."
        )
        return
    
    # Calculate fee
    fee = amount * 0.02  # 2% fee
    total = amount + fee
    
    # Check balance
    if total > user.balance_sol:
        await message.answer(
            f"❌ Недостаточно средств.\n\n"
            f"Требуется: {format_sol_amount(total)} (включая комиссию {format_sol_amount(fee)})\n"
            f"Ваш баланс: {format_sol_amount(user.balance_sol)}"
        )
        return
    
    # Get withdrawal address from state
    data = await state.get_data()
    withdraw_address = data.get('withdraw_address')
    
    # Create withdrawal transaction
    from services.user_service import UserService
    
    # Deduct from balance
    await UserService.update_balance(session, user.id, -total)
    
    # Create transaction record
    await TransactionService.create_transaction(
        session=session,
        user_id=user.id,
        tx_type='withdrawal',
        amount_sol=amount,
        description=f"Вывод средств на {withdraw_address} (комиссия: {fee:.2f} EUR)",
        status='pending'
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ **Заявка на вывод создана**\n\n"
        f"Сумма: {format_sol_amount(amount)}\n"
        f"Комиссия: {format_sol_amount(fee)}\n"
        f"Итого: {format_sol_amount(total)}\n"
        f"Адрес: `{withdraw_address}`\n\n"
        f"Средства будут отправлены в течение 24 часов.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "transaction_history")
async def transaction_history(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession
):
    """Show transaction history."""
    transactions = await TransactionService.get_user_transactions(
        session,
        user.id,
        limit=10
    )
    
    if not transactions:
        await callback.message.answer(
            "📋 У вас пока нет транзакций."
        )
        await callback.answer()
        return
    
    history_text = "📋 **История транзакций:**\n\n"
    
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

