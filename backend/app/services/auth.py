import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.logging import get_logger
from app.core.email_webhook_client import send_welcome_email

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, data: UserRegister, site_id: uuid.UUID, site_name: str = "") -> TokenResponse:
        if await self.repo.exists_by_email(data.email, site_id=site_id):
            raise ConflictError("A user with this email already exists.")

        hashed_password = get_password_hash(data.password)
        user = await self.repo.create(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            hashed_password=hashed_password,
            site_id=site_id,
        )
        logger.info(f"New user registered: {user.email} (site={site_id})")

        # Best-effort -- never let an email hiccup block a real registration.
        await send_welcome_email(
            site_name=site_name,
            customer_name=f"{user.first_name} {user.last_name}",
            customer_email=user.email,
        )

        access_token = create_access_token(subject=str(user.id))
        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )

    async def login(self, data: UserLogin, site_id: uuid.UUID) -> TokenResponse:
        user = await self.repo.get_by_email(data.email, site_id=site_id)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedError("Your account has been deactivated.")

        logger.info(f"User logged in: {user.email} (site={site_id})")
        access_token = create_access_token(
            subject=str(user.id),
            extra_data={"is_owner": user.is_owner},
        )
        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )

    async def superadmin_login(self, data: UserLogin) -> TokenResponse:
        """Superadmin accounts have no site -- looked up independent of any
        X-Site-Slug header."""
        user = await self.repo.get_superadmin_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedError("Your account has been deactivated.")

        logger.info(f"Superadmin logged in: {user.email}")
        access_token = create_access_token(
            subject=str(user.id),
            extra_data={"is_superadmin": True},
        )
        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )