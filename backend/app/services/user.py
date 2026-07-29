import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate, PasswordChange, UserResponse
from app.core.security import verify_password, get_password_hash
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def get_profile(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return UserResponse.model_validate(user)

    async def update_profile(self, user_id: uuid.UUID, data: UserUpdate) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")

        updates = data.model_dump(exclude_none=True)
        if updates:
            user = await self.repo.update(user, **updates)

        logger.info(f"Profile updated for user: {user.email}")
        return UserResponse.model_validate(user)

    async def change_password(self, user_id: uuid.UUID, data: PasswordChange) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")

        if not verify_password(data.current_password, user.hashed_password):
            raise BadRequestError("Current password is incorrect.")

        new_hash = get_password_hash(data.new_password)
        await self.repo.update(user, hashed_password=new_hash)
        logger.info(f"Password changed for user: {user.email}")
