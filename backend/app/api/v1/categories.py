import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.base import success_response
from app.services.category import CategoryService
from app.dependencies.auth import get_current_owner
from app.dependencies.site import get_current_site
from app.models.user import User
from app.models.site import Site

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """List all categories for the current site (public, scoped via X-Site-Slug)."""
    service = CategoryService(db)
    result = await service.get_all(site_id=site.id)
    return success_response(data=[r.model_dump() for r in result], message="Categories retrieved.")


@router.get("/{category_id}")
async def get_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """Get a single category by ID (public, scoped to the current site)."""
    service = CategoryService(db)
    result = await service.get_by_id(category_id, site_id=site.id)
    return success_response(data=result.model_dump(), message="Category retrieved.")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Create a new category, automatically tagged to the owner's own site (owner only)."""
    service = CategoryService(db)
    result = await service.create(data, site_id=owner.site_id)
    return success_response(data=result.model_dump(), message="Category created.")


@router.put("/{category_id}")
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Update a category, must belong to the owner's own site (owner only)."""
    service = CategoryService(db)
    result = await service.update(category_id, data, site_id=owner.site_id)
    return success_response(data=result.model_dump(), message="Category updated.")


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Delete a category, must belong to the owner's own site (owner only)."""
    service = CategoryService(db)
    await service.delete(category_id, site_id=owner.site_id)
    return success_response(message="Category deleted.")
