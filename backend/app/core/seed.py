from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from app.core.logging import get_logger
from app.models.site import Site
from app.models.user import User

logger = get_logger(__name__)

# One entry per site: (site slug, site display name, owner email, password, first name, last name).
# Add a new tuple here any time a new storefront is added, and its owner
# account will be created automatically the next time the backend starts.
SITE_SEEDS = [
    (
        "chemisto",
        "Chemisto",
        settings.OWNER_EMAIL,
        settings.OWNER_PASSWORD,
        settings.OWNER_FIRST_NAME,
        settings.OWNER_LAST_NAME,
    ),
    (
        "chemisto-food",
        "Chemisto Food",
        settings.CHEMISTO_FOOD_OWNER_EMAIL,
        settings.CHEMISTO_FOOD_OWNER_PASSWORD,
        settings.CHEMISTO_FOOD_OWNER_FIRST_NAME,
        settings.CHEMISTO_FOOD_OWNER_LAST_NAME,
    ),
]


async def seed_sites_and_owners() -> None:
    """Ensures every site in SITE_SEEDS exists, that each one has its owner
    account, and that the org-level superadmin account exists. Safe to run
    on every startup -- does nothing if any of these already exist."""
    async with AsyncSessionLocal() as db:
        for slug, name, owner_email, owner_password, first_name, last_name in SITE_SEEDS:
            result = await db.execute(select(Site).where(Site.slug == slug))
            site = result.scalar_one_or_none()
            if not site:
                site = Site(slug=slug, name=name)
                db.add(site)
                await db.flush()
                logger.info(f"Created site: {slug}")

            result = await db.execute(
                select(User).where(User.site_id == site.id, User.is_owner == True)  # noqa: E712
            )
            existing_owner = result.scalar_one_or_none()
            if existing_owner:
                continue

            # No owner yet for this site -- check if the configured owner
            # email is already registered as a regular user first, so we
            # don't fail on a duplicate-email constraint.
            result = await db.execute(
                select(User).where(User.site_id == site.id, User.email == owner_email.lower())
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                existing_user.is_owner = True
                logger.info(f"Promoted existing user to owner: {owner_email} ({slug})")
            else:
                owner = User(
                    site_id=site.id,
                    email=owner_email.lower(),
                    first_name=first_name,
                    last_name=last_name,
                    hashed_password=get_password_hash(owner_password),
                    is_owner=True,
                )
                db.add(owner)
                logger.info(f"Created owner account: {owner_email} ({slug})")

        # Org-level superadmin -- belongs to no single site (site_id is NULL).
        result = await db.execute(select(User).where(User.is_superadmin == True))  # noqa: E712
        existing_superadmin = result.scalar_one_or_none()
        if not existing_superadmin:
            superadmin = User(
                site_id=None,
                email=settings.SUPERADMIN_EMAIL.lower(),
                first_name=settings.SUPERADMIN_FIRST_NAME,
                last_name=settings.SUPERADMIN_LAST_NAME,
                hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
                is_owner=False,
                is_superadmin=True,
            )
            db.add(superadmin)
            logger.info(f"Created superadmin account: {settings.SUPERADMIN_EMAIL}")

        await db.commit()