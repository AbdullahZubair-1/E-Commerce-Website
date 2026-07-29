import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.brand import BrandCreate, BrandUpdate
from app.schemas.base import success_response
from app.services.brand import BrandService
from app.dependencies.auth import get_current_owner
from app.dependencies.site import get_current_site
from app.models.user import User
from app.models.site import Site

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("/")
async def list_brands(
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """List all brands for the current site (public, scoped via X-Site-Slug)."""
    service = BrandService(db)
    result = await service.get_all(site_id=site.id)
    return success_response(data=[r.model_dump() for r in result], message="Brands retrieved.")


@router.get("/{brand_id}")
async def get_brand(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """Get a single brand by ID (public, scoped to the current site)."""
    service = BrandService(db)
    result = await service.get_by_id(brand_id, site_id=site.id)
    return success_response(data=result.model_dump(), message="Brand retrieved.")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_brand(
    data: BrandCreate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Create a new brand, automatically tagged to the owner's own site (owner only)."""
    service = BrandService(db)
    result = await service.create(data, site_id=owner.site_id)
    return success_response(data=result.model_dump(), message="Brand created.")


@router.put("/{brand_id}")
async def update_brand(
    brand_id: uuid.UUID,
    data: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Update a brand, must belong to the owner's own site (owner only)."""
    service = BrandService(db)
    result = await service.update(brand_id, data, site_id=owner.site_id)
    return success_response(data=result.model_dump(), message="Brand updated.")


@router.delete("/{brand_id}", status_code=status.HTTP_200_OK)
async def delete_brand(
    brand_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Delete a brand, must belong to the owner's own site (owner only)."""
    service = BrandService(db)
    await service.delete(brand_id, site_id=owner.site_id)
    return success_response(message="Brand deleted.")
