import uuid
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, site_id: uuid.UUID, title: str, message: str, order_id: uuid.UUID | None = None, type: str = "order") -> Notification:
        notification = Notification(site_id=site_id, title=title, message=message, order_id=order_id, type=type)
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def list_for_site(self, site_id: uuid.UUID, page: int = 1, page_size: int = 20) -> list[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.site_id == site_id)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all())

    async def unread_count(self, site_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count(Notification.id)).where(Notification.site_id == site_id, Notification.is_read == False)  # noqa: E712
        )
        return result.scalar_one()

    async def mark_read(self, notification_id: uuid.UUID, site_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.site_id == site_id)
            .values(is_read=True)
        )
        await self.db.flush()

    async def mark_all_read(self, site_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification).where(Notification.site_id == site_id, Notification.is_read == False).values(is_read=True)  # noqa: E712
        )
        await self.db.flush()