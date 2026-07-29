import uuid
from typing import Optional
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.friendship import FriendRequest, FriendRequestStatus
from app.models.user import User


class FriendRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_between(self, user_a: uuid.UUID, user_b: uuid.UUID) -> Optional[FriendRequest]:
        """Any request between these two users, in either direction."""
        result = await self.db.execute(
            select(FriendRequest).where(
                or_(
                    and_(FriendRequest.requester_id == user_a, FriendRequest.addressee_id == user_b),
                    and_(FriendRequest.requester_id == user_b, FriendRequest.addressee_id == user_a),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, request_id: uuid.UUID) -> Optional[FriendRequest]:
        result = await self.db.execute(select(FriendRequest).where(FriendRequest.id == request_id))
        return result.scalar_one_or_none()

    async def create(self, requester_id: uuid.UUID, addressee_id: uuid.UUID) -> FriendRequest:
        req = FriendRequest(requester_id=requester_id, addressee_id=addressee_id)
        self.db.add(req)
        await self.db.flush()
        await self.db.refresh(req)
        return req

    async def update_status(self, req: FriendRequest, status: FriendRequestStatus) -> FriendRequest:
        req.status = status
        await self.db.flush()
        await self.db.refresh(req)
        return req

    async def list_friends(self, user_id: uuid.UUID) -> list[User]:
        """Every user this user has an ACCEPTED request with, in either direction."""
        result = await self.db.execute(
            select(FriendRequest).where(
                FriendRequest.status == FriendRequestStatus.ACCEPTED,
                or_(FriendRequest.requester_id == user_id, FriendRequest.addressee_id == user_id),
            )
        )
        requests = list(result.scalars().all())
        friend_ids = [
            (r.addressee_id if r.requester_id == user_id else r.requester_id) for r in requests
        ]
        if not friend_ids:
            return []
        friends_result = await self.db.execute(select(User).where(User.id.in_(friend_ids)))
        return list(friends_result.scalars().all())

    async def list_incoming_pending(self, user_id: uuid.UUID) -> list[FriendRequest]:
        result = await self.db.execute(
            select(FriendRequest).where(
                FriendRequest.addressee_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
        )
        return list(result.scalars().all())

    async def list_outgoing_pending(self, user_id: uuid.UUID) -> list[FriendRequest]:
        result = await self.db.execute(
            select(FriendRequest).where(
                FriendRequest.requester_id == user_id,
                FriendRequest.status == FriendRequestStatus.PENDING,
            )
        )
        return list(result.scalars().all())

    async def are_friends(self, user_a: uuid.UUID, user_b: uuid.UUID) -> bool:
        req = await self.get_between(user_a, user_b)
        return bool(req and req.status == FriendRequestStatus.ACCEPTED)