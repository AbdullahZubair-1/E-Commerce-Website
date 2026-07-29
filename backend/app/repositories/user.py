import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, site_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email.lower(), User.site_id == site_id)
        )
        return result.scalar_one_or_none()

    async def get_superadmin_by_email(self, email: str) -> Optional[User]:
        """Superadmin accounts have no site_id -- looked up independent of
        any site header."""
        result = await self.db.execute(
            select(User).where(
                User.email == email.lower(),
                User.site_id.is_(None),
                User.is_superadmin == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        first_name: str,
        last_name: str,
        hashed_password: str,
        site_id: Optional[uuid.UUID] = None,
        is_owner: bool = False,
        is_superadmin: bool = False,
    ) -> User:
        user = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed_password,
            is_owner=is_owner,
            is_superadmin=is_superadmin,
            site_id=site_id,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def exists_by_email(self, email: str, site_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower(), User.site_id == site_id)
        )
        return result.scalar_one_or_none() is not None