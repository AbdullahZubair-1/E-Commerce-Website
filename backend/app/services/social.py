import uuid
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.friendship import FriendRequestRepository
from app.repositories.message import MessageRepository
from app.repositories.user import UserRepository
from app.models.friendship import FriendRequestStatus
from app.models.user import User
from app.schemas.social import (
    UserSearchResult,
    FriendRequestResponse,
    FriendResponse,
    MessageResponse,
)
from app.core.exceptions import BadRequestError, NotFoundError, ForbiddenError, ConflictError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SocialService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.friend_repo = FriendRequestRepository(db)
        self.message_repo = MessageRepository(db)
        self.user_repo = UserRepository(db)

    # --- Search ---
    async def search_users(self, query: str, site_id: uuid.UUID, exclude_user_id: uuid.UUID) -> list[UserSearchResult]:
        if not query or len(query.strip()) < 2:
            return []
        like = f"%{query.strip()}%"
        result = await self.db.execute(
            select(User).where(
                User.site_id == site_id,
                User.id != exclude_user_id,
                User.is_owner == False,  # noqa: E712
                User.is_superadmin == False,  # noqa: E712
                or_(
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                    User.email.ilike(like),
                ),
            ).limit(20)
        )
        users = list(result.scalars().all())
        return [UserSearchResult.model_validate(u) for u in users]

    # --- Friend requests ---
    async def send_friend_request(self, requester: User, addressee_id: uuid.UUID) -> FriendRequestResponse:
        if requester.id == addressee_id:
            raise BadRequestError("You can't send a friend request to yourself.")

        addressee = await self.user_repo.get_by_id(addressee_id)
        if not addressee or addressee.site_id != requester.site_id:
            # Same error either way -- don't reveal whether the ID exists on
            # another site.
            raise NotFoundError("User not found.")

        existing = await self.friend_repo.get_between(requester.id, addressee_id)
        if existing:
            if existing.status == FriendRequestStatus.ACCEPTED:
                raise ConflictError("You're already friends.")
            if existing.status == FriendRequestStatus.PENDING:
                raise ConflictError("A friend request already exists between you two.")
            # Previously declined -- allow a fresh request by resetting it.
            existing = await self.friend_repo.update_status(existing, FriendRequestStatus.PENDING)
            return await self._to_response(existing, requester.id)

        req = await self.friend_repo.create(requester.id, addressee_id)
        logger.info(f"Friend request: {requester.id} -> {addressee_id}")
        return await self._to_response(req, requester.id)

    async def respond_to_request(self, current_user: User, request_id: uuid.UUID, accept: bool) -> FriendRequestResponse:
        req = await self.friend_repo.get_by_id(request_id)
        if not req or req.addressee_id != current_user.id:
            raise NotFoundError("Friend request not found.")
        if req.status != FriendRequestStatus.PENDING:
            raise BadRequestError("This request has already been responded to.")

        new_status = FriendRequestStatus.ACCEPTED if accept else FriendRequestStatus.DECLINED
        req = await self.friend_repo.update_status(req, new_status)
        return await self._to_response(req, current_user.id)

    async def list_friends(self, user_id: uuid.UUID) -> list[FriendResponse]:
        friends = await self.friend_repo.list_friends(user_id)
        return [FriendResponse.model_validate(f) for f in friends]

    async def list_incoming_requests(self, user_id: uuid.UUID) -> list[FriendRequestResponse]:
        requests = await self.friend_repo.list_incoming_pending(user_id)
        return [await self._to_response(r, user_id) for r in requests]

    async def list_outgoing_requests(self, user_id: uuid.UUID) -> list[FriendRequestResponse]:
        requests = await self.friend_repo.list_outgoing_pending(user_id)
        return [await self._to_response(r, user_id) for r in requests]

    async def _to_response(self, req, viewer_id: uuid.UUID) -> FriendRequestResponse:
        other_id = req.addressee_id if req.requester_id == viewer_id else req.requester_id
        other = await self.user_repo.get_by_id(other_id)
        return FriendRequestResponse(
            id=req.id,
            requester_id=req.requester_id,
            addressee_id=req.addressee_id,
            status=req.status.value,
            created_at=req.created_at,
            other_user_id=other_id,
            other_user_name=f"{other.first_name} {other.last_name}" if other else "Unknown",
            other_user_email=other.email if other else "",
        )

    # --- Messaging ---
    async def send_message(self, sender: User, recipient_id: uuid.UUID, content: str) -> MessageResponse:
        content = content.strip()
        if not content:
            raise BadRequestError("Message can't be empty.")
        if len(content) > 4000:
            raise BadRequestError("Message is too long.")

        if not await self.friend_repo.are_friends(sender.id, recipient_id):
            raise ForbiddenError("You can only message people you're friends with.")

        message = await self.message_repo.create(sender.id, recipient_id, content)
        return MessageResponse.model_validate(message)

    async def get_conversation(
        self, current_user: User, friend_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> list[MessageResponse]:
        if not await self.friend_repo.are_friends(current_user.id, friend_id):
            raise ForbiddenError("You can only view conversations with friends.")

        messages = await self.message_repo.get_conversation(current_user.id, friend_id, page, page_size)
        await self.message_repo.mark_read(sender_id=friend_id, recipient_id=current_user.id)
        return [MessageResponse.model_validate(m) for m in messages]