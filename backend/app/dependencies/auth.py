import uuid
from typing import Optional
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.repositories.user import UserRepository
from app.models.user import User
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise UnauthorizedError("Authentication required.")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError("Invalid token.")
    except JWTError:
        raise UnauthorizedError("Token is invalid or expired.")

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise UnauthorizedError("User not found.")
    if not user.is_active:
        raise UnauthorizedError("Your account has been deactivated.")

    return user


async def get_current_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_owner:
        raise ForbiddenError("Owner access required.")
    return current_user


async def get_current_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superadmin:
        raise ForbiddenError("Superadmin access required.")
    return current_user