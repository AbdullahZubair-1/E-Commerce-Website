from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.user import UserRegister, UserLogin, TokenResponse
from app.schemas.base import success_response
from app.services.auth import AuthService
from app.dependencies.site import get_current_site
from app.models.site import Site

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """Register a new customer account, scoped to the current site (X-Site-Slug)."""
    service = AuthService(db)
    result = await service.register(data, site_id=site.id, site_name=site.name)
    return success_response(
        data=result.model_dump(),
        message="Registration successful.",
    )


@router.post("/login")
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """Login with email and password, scoped to the current site (X-Site-Slug)."""
    service = AuthService(db)
    result = await service.login(data, site_id=site.id)
    return success_response(
        data=result.model_dump(),
        message="Login successful.",
    )


@router.post("/superadmin-login")
async def superadmin_login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Login for the org-level superadmin account. Not scoped to any site --
    ignores X-Site-Slug entirely."""
    service = AuthService(db)
    result = await service.superadmin_login(data)
    return success_response(
        data=result.model_dump(),
        message="Login successful.",
    )