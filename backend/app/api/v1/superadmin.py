from sqlalchemy import select, func
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.base import success_response
from app.dependencies.auth import get_current_superadmin
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.category import Category
from app.models.brand import Brand
from app.models.site import Site

router = APIRouter(prefix="/superadmin", tags=["Superadmin"])


async def _stats_for_site(db: AsyncSession, site_id) -> dict:
    total_products = (
        await db.execute(select(func.count(Product.id)).where(Product.site_id == site_id))
    ).scalar_one()
    total_orders = (
        await db.execute(
            select(func.count(Order.id)).join(User, Order.user_id == User.id).where(User.site_id == site_id)
        )
    ).scalar_one()
    total_customers = (
        await db.execute(
            select(func.count(User.id)).where(User.site_id == site_id, User.is_owner == False)  # noqa: E712
        )
    ).scalar_one()
    revenue_result = await db.execute(
        select(func.sum(Order.total_amount))
        .join(User, Order.user_id == User.id)
        .where(User.site_id == site_id, Order.status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED]))
    )
    total_revenue = float(revenue_result.scalar_one() or 0)
    total_categories = (
        await db.execute(select(func.count(Category.id)).where(Category.site_id == site_id))
    ).scalar_one()
    total_brands = (
        await db.execute(select(func.count(Brand.id)).where(Brand.site_id == site_id))
    ).scalar_one()

    return {
        "products": total_products,
        "orders": total_orders,
        "customers": total_customers,
        "revenue": total_revenue,
        "categories": total_categories,
        "brands": total_brands,
    }


@router.get("/dashboard")
async def get_superadmin_dashboard(
    db: AsyncSession = Depends(get_db),
    _superadmin: User = Depends(get_current_superadmin),
):
    """Combined dashboard across every site in the organization."""
    sites_result = await db.execute(select(Site).order_by(Site.name))
    sites = list(sites_result.scalars().all())

    per_site = []
    totals = {"products": 0, "orders": 0, "customers": 0, "revenue": 0.0, "categories": 0, "brands": 0}

    for site in sites:
        stats = await _stats_for_site(db, site.id)
        per_site.append({
            "id": str(site.id),
            "slug": site.slug,
            "name": site.name,
            "stats": stats,
        })
        for key in totals:
            totals[key] += stats[key]

    return success_response(
        data={
            "sites": per_site,
            "totals": totals,
        },
        message="Superadmin dashboard retrieved.",
    )


@router.get("/sites")
async def list_sites(
    db: AsyncSession = Depends(get_db),
    _superadmin: User = Depends(get_current_superadmin),
):
    """List every site in the organization."""
    result = await db.execute(select(Site).order_by(Site.name))
    sites = list(result.scalars().all())
    return success_response(
        data=[{"id": str(s.id), "slug": s.slug, "name": s.name} for s in sites],
        message="Sites retrieved.",
    )