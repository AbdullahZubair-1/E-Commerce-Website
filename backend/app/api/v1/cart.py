import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.cart import CartItemAdd, CartItemUpdate
from app.schemas.base import success_response
from app.services.cart import CartService
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/")
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's cart."""
    service = CartService(db)
    result = await service.get_cart(current_user.id)
    return success_response(data=result.model_dump(), message="Cart retrieved.")


@router.post("/items")
async def add_to_cart(
    data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a product to the cart."""
    service = CartService(db)
    result = await service.add_item(current_user.id, data)
    return success_response(data=result.model_dump(), message="Item added to cart.")


@router.put("/items/{item_id}")
async def update_cart_item(
    item_id: uuid.UUID,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update quantity of a cart item."""
    service = CartService(db)
    result = await service.update_item(current_user.id, item_id, data)
    return success_response(data=result.model_dump(), message="Cart item updated.")


@router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an item from the cart."""
    service = CartService(db)
    result = await service.remove_item(current_user.id, item_id)
    return success_response(data=result.model_dump(), message="Item removed from cart.")


@router.delete("/")
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear all items from the cart."""
    service = CartService(db)
    result = await service.clear_cart(current_user.id)
    return success_response(data=result.model_dump(), message="Cart cleared.")
