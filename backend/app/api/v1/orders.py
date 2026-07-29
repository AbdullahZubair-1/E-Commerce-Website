import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.schemas.base import success_response
from app.services.order import OrderService
from app.dependencies.auth import get_current_user, get_current_owner
from app.models.user import User
from app.models.order import OrderStatus
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


# --- Customer endpoints ---

@router.post("/")
async def place_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a new order from the cart."""
    service = OrderService(db)
    result = await service.place_order(current_user.id, data)
    return success_response(data=result.model_dump(), message="Order placed successfully.")


@router.get("/my")
async def get_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's orders."""
    service = OrderService(db)
    result = await service.get_my_orders(current_user.id, page=page, page_size=page_size)
    return success_response(
        data={
            "items": [o.model_dump() for o in result.items],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        },
        message="Orders retrieved.",
    )


@router.get("/my/{order_id}")
async def get_my_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific order belonging to the current user."""
    service = OrderService(db)
    result = await service.get_my_order(current_user.id, order_id)
    return success_response(data=result.model_dump(), message="Order retrieved.")


# --- Admin endpoints ---

@router.get("/admin/all")
async def get_all_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Get all orders for the owner's own site (owner only)."""
    service = OrderService(db)
    result = await service.get_all_orders(site_id=owner.site_id, page=page, page_size=page_size, status=status)
    try:
        logger.info(f"Admin orders requested by owner={owner.id} ({owner.email}), total_found={result.total}")
    except Exception:
        # non-fatal logging
        pass
    return success_response(
        data={
            "items": [o.model_dump() for o in result.items],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "total_pages": result.total_pages,
        },
        message="Orders retrieved.",
    )


@router.get("/admin/{order_id}")
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Get an order by ID, must belong to the owner's own site (owner only)."""
    service = OrderService(db)
    result = await service.get_order_by_id(order_id, site_id=owner.site_id)
    return success_response(data=result.model_dump(), message="Order retrieved.")


@router.patch("/admin/{order_id}/status")
async def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_current_owner),
):
    """Update an order's status, must belong to the owner's own site (owner only)."""
    service = OrderService(db)
    result = await service.update_order_status(order_id, data, site_id=owner.site_id)
    return success_response(data=result.model_dump(), message="Order status updated.")
