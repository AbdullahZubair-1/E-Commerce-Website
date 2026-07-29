from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.user import UserUpdate, PasswordChange
from app.schemas.base import success_response
from app.services.user import UserService
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the authenticated user's profile."""
    service = UserService(db)
    result = await service.get_profile(current_user.id)
    return success_response(data=result.model_dump(), message="Profile retrieved.")


@router.put("/me")
async def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update first/last name."""
    service = UserService(db)
    result = await service.update_profile(current_user.id, data)
    return success_response(data=result.model_dump(), message="Profile updated.")


@router.put("/me/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the authenticated user's password."""
    service = UserService(db)
    await service.change_password(current_user.id, data)
    return success_response(message="Password changed successfully.")
