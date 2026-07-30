import uuid
from datetime import datetime, timezone
from sqlalchemy import select, or_, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, sender_id: uuid.UUID, recipient_id: uuid.UUID, content: str) -> Message:
        message = Message(sender_id=sender_id, recipient_id=recipient_id, content=content)
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_conversation(
        self, user_a: uuid.UUID, user_b: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> list[Message]:
        query = (
            select(Message)
            .where(
                or_(
                    and_(Message.sender_id == user_a, Message.recipient_id == user_b),
                    and_(Message.sender_id == user_b, Message.recipient_id == user_a),
                )
            )
            .order_by(Message.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        # Reverse so the returned list is oldest-first (chat reading order).
        return list(reversed(result.scalars().all()))

    async def mark_read(self, sender_id: uuid.UUID, recipient_id: uuid.UUID) -> None:
        """Mark every unread message FROM sender_id TO recipient_id as read
        (i.e. recipient_id just opened the conversation)."""
        await self.db.execute(
            update(Message)
            .where(Message.sender_id == sender_id, Message.recipient_id == recipient_id, Message.read_at.is_(None))
            .values(read_at=datetime.now(timezone.utc))
        )
        await self.db.flush()

    async def unread_counts_by_sender(self, recipient_id: uuid.UUID) -> dict[uuid.UUID, int]:
        """One grouped query: {sender_id: unread_count} for every friend who
        has sent recipient_id at least one unread message. Used to badge
        each friend in the friends list without an N+1 query per friend."""
        result = await self.db.execute(
            select(Message.sender_id, func.count(Message.id))
            .where(Message.recipient_id == recipient_id, Message.read_at.is_(None))
            .group_by(Message.sender_id)
        )
        return {row[0]: row[1] for row in result.all()}

    async def total_unread_count(self, recipient_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(Message.id))
            .where(Message.recipient_id == recipient_id, Message.read_at.is_(None))
        )
        return result.scalar_one()