"""Support ticket service."""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import SupportTicket, TicketMessage

logger = logging.getLogger(__name__)


class TicketService:
    """Service for managing support tickets."""
    
    @staticmethod
    async def create_ticket(
        session: AsyncSession,
        user_id: int,
        subject: str,
        first_message: str
    ) -> SupportTicket:
        """Create a new support ticket."""
        # Create ticket
        ticket = SupportTicket(
            user_id=user_id,
            subject=subject,
            status='open',
            priority='normal'
        )
        session.add(ticket)
        await session.flush()
        
        # Add first message
        message = TicketMessage(
            ticket_id=ticket.id,
            user_id=user_id,
            message=first_message,
            is_admin=False
        )
        session.add(message)
        
        await session.commit()
        await session.refresh(ticket)
        
        logger.info(f"Ticket #{ticket.id} created by user {user_id}: {subject}")
        return ticket
    
    @staticmethod
    async def add_message(
        session: AsyncSession,
        ticket_id: int,
        user_id: int,
        message: str,
        is_admin: bool = False
    ) -> TicketMessage:
        """Add a message to ticket."""
        ticket_msg = TicketMessage(
            ticket_id=ticket_id,
            user_id=user_id,
            message=message,
            is_admin=is_admin
        )
        session.add(ticket_msg)
        
        # Update ticket status if admin replied
        if is_admin:
            stmt = update(SupportTicket).where(
                SupportTicket.id == ticket_id
            ).values(
                status='in_progress',
                updated_at=datetime.now(timezone.utc)
            )
            await session.execute(stmt)
        
        await session.commit()
        await session.refresh(ticket_msg)
        
        logger.info(f"Message added to ticket #{ticket_id} by {'admin' if is_admin else 'user'} {user_id}")
        return ticket_msg
    
    @staticmethod
    async def get_user_tickets(session: AsyncSession, user_id: int) -> list[SupportTicket]:
        """Get all tickets for user."""
        stmt = select(SupportTicket).where(
            SupportTicket.user_id == user_id
        ).order_by(SupportTicket.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_ticket_messages(session: AsyncSession, ticket_id: int) -> list[TicketMessage]:
        """Get all messages for ticket."""
        stmt = select(TicketMessage).where(
            TicketMessage.ticket_id == ticket_id
        ).order_by(TicketMessage.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def close_ticket(session: AsyncSession, ticket_id: int) -> bool:
        """Close ticket."""
        stmt = update(SupportTicket).where(
            SupportTicket.id == ticket_id
        ).values(
            status='closed',
            updated_at=datetime.now(timezone.utc)
        )
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Ticket #{ticket_id} closed")
        return True
    
    @staticmethod
    async def assign_ticket(session: AsyncSession, ticket_id: int, admin_id: int) -> bool:
        """Assign ticket to admin."""
        stmt = update(SupportTicket).where(
            SupportTicket.id == ticket_id
        ).values(
            assigned_to=admin_id,
            status='in_progress',
            updated_at=datetime.now(timezone.utc)
        )
        await session.execute(stmt)
        await session.commit()
        logger.info(f"Ticket #{ticket_id} assigned to admin {admin_id}")
        return True
    
    @staticmethod
    async def get_open_tickets(session: AsyncSession) -> list[SupportTicket]:
        """Get all open/in-progress tickets for admins."""
        stmt = select(SupportTicket).where(
            SupportTicket.status.in_(['open', 'in_progress'])
        ).order_by(SupportTicket.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())


# Global instance
ticket_service = TicketService()

