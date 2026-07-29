import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from app.database.session import get_db
from app.schemas.product import ProductCreate, ProductUpdate, StockUpdate
from app.schemas.base import success_response
from app.services.product import ProductService
from app.dependencies.auth import get_current_owner
from app.dependencies.site import get_current_site
from app.models.user import User
from app.models.site import Site

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/")
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    brand_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """List all active products with pagination and filters (public, scoped to the current site via X-Site-Slug)."""
    service = ProductService(db)
    result = await service.get_all(
        site_id=site.id,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        brand_id=brand_id,
        active_only=True,
    )
    return success_response(
        data={
            "items": [p.model_dump() for p in result.items],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        },
        message="Products retrieved.",
    )


@router.get("/slug/{slug}")
async def get_product_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """Get a product by its slug (public, scoped to the current site)."""
    service = ProductService(db)
    result = await service.get_by_slug(slug, site_id=site.id)
    return success_response(data=result.model_dump(), message="Product retrieved.")


@router.get("/{product_id}")
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    site: Site = Depends(get_current_site),
):
    """Get a product by ID (public, scoped to the current site)."""
    service = ProductService(db)
    result = await service.get_by_id(product_id, site_id=site.id)
    return success_response(data=result.model_dump(), message="Product retrieved.")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    price: Decimal = Form(...),
    stock_quantity: int = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[uuid.UUID] = Form(None),
    brand_id: Optional[uuid.UUID] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Create a new product (owner only). Automatically tagged to the
    owner's own site -- an owner account can only ever add products to the
    storefront it belongs to, regardless of what any client sends."""
    service = ProductService(db)
    data = ProductCreate(
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category_id=category_id,
        brand_id=brand_id,
    )
    result = await service.create(data, site_id=owner.site_id, image=image)
    return success_response(data=result.model_dump(), message="Product created.")


@router.put("/{product_id}")
async def update_product(
    product_id: uuid.UUID,
    name: Optional[str] = Form(None),
    price: Optional[Decimal] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[uuid.UUID] = Form(None),
    brand_id: Optional[uuid.UUID] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Update a product (owner only, must belong to the owner's own site)."""
    service = ProductService(db)
    data = ProductUpdate(
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity,
        category_id=category_id,
        brand_id=brand_id,
        is_active=is_active,
    )
    result = await service.update(product_id, data, site_id=owner.site_id, image=image)
    return success_response(data=result.model_dump(), message="Product updated.")


@router.patch("/{product_id}/stock")
async def update_stock(
    product_id: uuid.UUID,
    data: StockUpdate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Update product stock quantity (owner only, must belong to the owner's own site)."""
    service = ProductService(db)
    result = await service.update_stock(product_id, data, site_id=owner.site_id)
    return success_response(data=result.model_dump(), message="Stock updated.")


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Delete a product (owner only, must belong to the owner's own site)."""
    service = ProductService(db)
    await service.delete(product_id, site_id=owner.site_id)
    return success_response(message="Product deleted.")
