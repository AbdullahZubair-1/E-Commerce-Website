from sqlalchemy import select
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.site import Site
from app.core.exceptions import NotFoundError

# Defaults to the original storefront if a client doesn't send the header
# (keeps older/manual API calls, e.g. via /docs, working without breaking).
DEFAULT_SITE_SLUG = "chemisto"


async def get_current_site(
    x_site_slug: str | None = Header(default=None, alias="X-Site-Slug"),
    db: AsyncSession = Depends(get_db),
) -> Site:
    """Resolves which storefront (site) the current request belongs to, from
    the X-Site-Slug header each frontend sends. Used to scope public product
    browsing, registration, and the chatbot/voice agent to one storefront's
    data only."""
    slug = (x_site_slug or DEFAULT_SITE_SLUG).strip().lower()
    result = await db.execute(select(Site).where(Site.slug == slug))
    site = result.scalar_one_or_none()
    if not site:
        raise NotFoundError(f"Unknown site '{slug}'.")
    return site
