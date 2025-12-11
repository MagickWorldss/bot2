"""Admin support/tickets handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.ticket_service import ticket_service
from services.role_service import role_service
from utils.keyboards import admin_menu_keyboard
from utils.helpers import is_admin
from config import settings

logger = logging.getLogger(__name__)

router = Router(name='admin_support_handlers')


class AdminReplyStates(StatesGroup):
    """States for admin reply to ticket."""
    waiting_for_reply = State()


@router.message(F.text.in_(["🎫 Тикеты поддержки", "🎫 Поддержка"]))
async def admin_tickets_menu(message: Message, user: User, session: AsyncSession):
    """Show tickets management for admin."""
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ Нет доступа")
        return
    
    # Get open tickets
    tickets = await ticket_service.get_open_tickets(session)
    
    text = "🎫 **Тикеты поддержки**\n\n"
    
    if not tickets:
        text += "📭 Нет открытых тикетов\n\n"
        text += "Все обращения обработаны! ✅"
    else:
        text += f"📋 Открытых тикетов: **{len(tickets)}**\n\n"
        
        for ticket in tickets[:10]:
            status_emoji = {
                'open': '🆕',
                'in_progress': '⏳'
            }.get(ticket.status, '❓')
            
            text += f"{status_emoji} **#{ticket.id}** - {ticket.subject}\n"
            text += f"   От: User #{ticket.user_id}\n"
            text += f"   Создан: {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    builder = InlineKeyboardBuilder()
    
    if tickets:
        for ticket in tickets[:10]:
            builder.button(
                text=f"Открыть #{ticket.id}",
                callback_data=f"admin_ticket_{ticket.id}"
            )
    
    builder.button(text="🔙 Назад", callback_data="back_to_admin")
    builder.adjust(2)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin_ticket_"))
async def admin_view_ticket(callback: CallbackQuery, user: User, session: AsyncSession, state: FSMContext):
    """View ticket for admin."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    ticket_id = int(callback.data.split("_")[2])
    
    # Get messages
    messages = await ticket_service.get_ticket_messages(session, ticket_id)
    
    if not messages:
        await callback.answer("❌ Тикет не найден", show_alert=True)
        return
    
    # Get ticket
    from database.models import SupportTicket
    from sqlalchemy import select
    stmt = select(SupportTicket).where(SupportTicket.id == ticket_id)
    result = await session.execute(stmt)
    ticket = result.scalar_one_or_none()
    
    text = f"🎫 **Тикет #{ticket_id}**\n\n"
    text += f"От: User #{ticket.user_id}\n"
    text += f"Статус: {ticket.status}\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for msg in messages:
        sender = "👤 Пользователь" if not msg.is_admin else "👑 Админ"
        time = msg.created_at.strftime('%d.%m %H:%M')
        text += f"**{sender}** _{time}_:\n{msg.message}\n\n"
    
    builder = InlineKeyboardBuilder()
    
    if ticket.status != 'closed':
        builder.button(text="💬 Ответить", callback_data=f"admin_reply_ticket_{ticket_id}")
        builder.button(text="✅ Закрыть тикет", callback_data=f"admin_close_ticket_{ticket_id}")
    
    builder.button(text="🔙 К списку", callback_data="back_to_tickets")
    builder.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_reply_ticket_"))
async def admin_reply_init(callback: CallbackQuery, user: User, state: FSMContext):
    """Start admin reply."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    ticket_id = int(callback.data.split("_")[3])
    
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(AdminReplyStates.waiting_for_reply)
    
    await callback.message.edit_text("✍️ **Напишите ваш ответ пользователю:**")
    await callback.answer()


@router.message(AdminReplyStates.waiting_for_reply)
async def admin_reply_send(message: Message, user: User, session: AsyncSession, state: FSMContext):
    """Send admin reply."""
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    
    if not ticket_id:
        await message.answer("❌ Ошибка")
        await state.clear()
        return
    
    # Add message
    await ticket_service.add_message(session, ticket_id, user.id, message.text, is_admin=True)
    
    # TODO: Send notification to user
    
    await message.answer(
        f"✅ Ответ отправлен пользователю!\n\n"
        f"Тикет #{ticket_id}",
        reply_markup=admin_menu_keyboard()
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_close_ticket_"))
async def admin_close_ticket(callback: CallbackQuery, user: User, session: AsyncSession):
    """Close ticket."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    ticket_id = int(callback.data.split("_")[3])
    
    await ticket_service.close_ticket(session, ticket_id)
    await callback.answer("✅ Тикет закрыт", show_alert=True)
    
    # Return to tickets list
    await callback.message.delete()


@router.callback_query(F.data == "back_to_tickets")
async def back_to_tickets(callback: CallbackQuery, user: User, session: AsyncSession):
    """Return to tickets list."""
    if not is_admin(user.id, settings.admin_list):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    """Return to tickets list."""
    await admin_tickets_menu(callback.message, user, session)
    await callback.message.delete()

