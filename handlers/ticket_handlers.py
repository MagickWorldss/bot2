"""Support ticket handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.ticket_service import ticket_service

logger = logging.getLogger(__name__)

router = Router(name='ticket_handlers')


class TicketStates(StatesGroup):
    """States for ticket creation."""
    waiting_for_subject = State()
    waiting_for_message = State()
    waiting_for_reply = State()


@router.message(Command("support"))
async def support_menu(message: Message, user: User, session: AsyncSession):
    """Show support menu."""
    # Get user's tickets
    tickets = await ticket_service.get_user_tickets(session, user.id)
    
    text = """
🎫 **Поддержка**

━━━━━━━━━━━━━━━━━━━━

💡 Выберите действие:
    """
    
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать обращение", callback_data="create_ticket")
    
    if tickets:
        builder.button(text="📋 Мои обращения", callback_data="my_tickets")
    
    builder.button(text="🔙 Главное меню", callback_data="back_to_main")
    builder.adjust(1)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data == "create_ticket")
async def create_ticket_init(callback: CallbackQuery, state: FSMContext):
    """Start ticket creation."""
    text = """
📝 **Создание обращения**

Опишите вашу проблему или вопрос одним сообщением.

Администратор ответит вам в ближайшее время.

━━━━━━━━━━━━━━━━━━━━

✍️ Напишите сообщение:
    """
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(TicketStates.waiting_for_message)
    await callback.answer()


@router.message(TicketStates.waiting_for_message)
async def create_ticket_message(message: Message, user: User, session: AsyncSession, state: FSMContext):
    """Receive ticket message."""
    subject = "Обращение в поддержку"
    text = message.text
    
    # Create ticket
    ticket = await ticket_service.create_ticket(session, user.id, subject, text)
    
    response = f"""
✅ **Обращение создано!**

🎫 Номер: **#{ticket.id}**

━━━━━━━━━━━━━━━━━━━━

Администратор ответит вам в ближайшее время.

Вы получите уведомление когда будет ответ.

━━━━━━━━━━━━━━━━━━━━

📋 Посмотреть обращения: /support
    """
    
    await message.answer(response, parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data == "my_tickets")
async def show_my_tickets(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show user's tickets."""
    tickets = await ticket_service.get_user_tickets(session, user.id)
    
    if not tickets:
        text = "📭 У вас нет обращений"
        await callback.message.edit_text(text)
        await callback.answer()
        return
    
    text = "📋 **Ваши обращения:**\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for ticket in tickets:
        status_emoji = {
            'open': '🆕',
            'in_progress': '⏳',
            'closed': '✅'
        }.get(ticket.status, '❓')
        
        text += f"{status_emoji} **#{ticket.id}** - {ticket.subject}\n"
        text += f"   Статус: {ticket.status}\n"
        text += f"   Создано: {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        builder.button(text=f"Открыть #{ticket.id}", callback_data=f"view_ticket_{ticket.id}")
    
    builder.adjust(1)
    builder.button(text="🔙 Назад", callback_data="back_to_support")
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("view_ticket_"))
async def view_ticket(callback: CallbackQuery, user: User, session: AsyncSession):
    """View ticket messages."""
    ticket_id = int(callback.data.split("_")[2])
    
    # Get messages
    messages = await ticket_service.get_ticket_messages(session, ticket_id)
    
    if not messages:
        await callback.answer("❌ Обращение не найдено", show_alert=True)
        return
    
    text = f"🎫 **Обращение #{ticket_id}**\n\n"
    
    for msg in messages:
        sender = "👤 Вы" if not msg.is_admin else "👑 Администратор"
        time = msg.created_at.strftime('%d.%m %H:%M')
        text += f"**{sender}** _{time}_:\n{msg.message}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Ответить", callback_data=f"reply_ticket_{ticket_id}")
    builder.button(text="🔙 Назад", callback_data="my_tickets")
    builder.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_ticket_init(callback: CallbackQuery, state: FSMContext):
    """Start reply to ticket."""
    ticket_id = int(callback.data.split("_")[2])
    
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(TicketStates.waiting_for_reply)
    
    text = "✍️ **Напишите ваше сообщение:**"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()


@router.message(TicketStates.waiting_for_reply)
async def reply_ticket_message(message: Message, user: User, session: AsyncSession, state: FSMContext):
    """Receive reply message."""
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    
    if not ticket_id:
        await message.answer("❌ Ошибка")
        await state.clear()
        return
    
    # Add message
    await ticket_service.add_message(session, ticket_id, user.id, message.text, is_admin=False)
    
    text = f"""
✅ **Сообщение отправлено!**

Администратор получит уведомление.

━━━━━━━━━━━━━━━━━━━━

📋 Ваши обращения: /support
    """
    
    await message.answer(text, parse_mode="Markdown")
    await state.clear()


@router.message(F.text == "🎫 Поддержка")
async def support_button_handler(message: Message, user: User, session: AsyncSession):
    """Handle support button press."""
    await support_menu(message, user, session)


@router.callback_query(F.data == "back_to_support")
async def back_to_support_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Return to support menu."""
    await support_menu(callback.message, user, session)
    await callback.message.delete()

