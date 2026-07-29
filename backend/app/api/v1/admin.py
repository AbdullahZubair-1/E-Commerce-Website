import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.base import success_response
from app.dependencies.auth import get_current_owner
from app.dependencies.site import get_current_site
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.category import Category
from app.models.brand import Brand
from app.models.site import Site
from app.schemas.product import ProductCreate
from app.services.product import ProductService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Get dashboard statistics for the owner's own site only (owner only)."""
    site_id = owner.site_id

    # Total products (this site only)
    total_products = (
        await db.execute(select(func.count(Product.id)).where(Product.site_id == site_id))
    ).scalar_one()
    active_products = (
        await db.execute(
            select(func.count(Product.id)).where(Product.site_id == site_id, Product.is_active == True)
        )
    ).scalar_one()
    low_stock_products = (
        await db.execute(
            select(func.count(Product.id)).where(
                Product.site_id == site_id, Product.stock_quantity <= 5, Product.is_active == True
            )
        )
    ).scalar_one()

    # Total orders (this site's users only, via the order's user)
    total_orders = (
        await db.execute(
            select(func.count(Order.id)).join(User, Order.user_id == User.id).where(User.site_id == site_id)
        )
    ).scalar_one()
    pending_orders = (
        await db.execute(
            select(func.count(Order.id))
            .join(User, Order.user_id == User.id)
            .where(User.site_id == site_id, Order.status == OrderStatus.PENDING)
        )
    ).scalar_one()

    # Total users (this site only)
    total_users = (
        await db.execute(
            select(func.count(User.id)).where(User.site_id == site_id, User.is_owner == False)
        )
    ).scalar_one()

    # Revenue (this site's users only)
    revenue_result = await db.execute(
        select(func.sum(Order.total_amount))
        .join(User, Order.user_id == User.id)
        .where(User.site_id == site_id, Order.status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED]))
    )
    total_revenue = float(revenue_result.scalar_one() or 0)

    # Categories and brands (this site only, now that they're per-site too)
    total_categories = (
        await db.execute(select(func.count(Category.id)).where(Category.site_id == site_id))
    ).scalar_one()
    total_brands = (
        await db.execute(select(func.count(Brand.id)).where(Brand.site_id == site_id))
    ).scalar_one()

    return success_response(
        data={
            "products": {
                "total": total_products,
                "active": active_products,
                "low_stock": low_stock_products,
            },
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
            },
            "customers": {
                "total": total_users,
            },
            "revenue": {
                "total": total_revenue,
            },
            "catalog": {
                "categories": total_categories,
                "brands": total_brands,
            },
        },
        message="Dashboard statistics retrieved.",
    )


@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_admin_product(
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
