import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cart import Cart, CartItem
from app.models.product import Product


def _product_loads():
    """Eagerly load product → category and product → brand."""
    return selectinload(CartItem.product).options(
        selectinload(Product.category),
        selectinload(Product.brand),
    )


def _full_cart_options():
    """Eagerly load cart → items → product → category & brand."""
    return selectinload(Cart.items).options(
        selectinload(CartItem.product).options(
            selectinload(Product.category),
            selectinload(Product.brand),
        )
    )


class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Cart]:
        result = await self.db.execute(
            select(Cart)
            .options(_full_cart_options())
            .where(Cart.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: uuid.UUID) -> Cart:
        cart = await self.get_by_user_id(user_id)
        if cart is None:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            await self.db.flush()
            await self.db.refresh(cart)
            cart = await self.get_by_user_id(user_id)
        return cart  # type: ignore

    async def get_item(self, cart_id: uuid.UUID, product_id: uuid.UUID) -> Optional[CartItem]:
        result = await self.db.execute(
            select(CartItem)
            .options(_product_loads())
            .where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_item_by_id(self, item_id: uuid.UUID) -> Optional[CartItem]:
        result = await self.db.execute(
            select(CartItem)
            .options(_product_loads())
            .where(CartItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def add_item(
        self, cart_id: uuid.UUID, product_id: uuid.UUID, quantity: int
    ) -> CartItem:
        item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
        self.db.add(item)
        await self.db.flush()
        # Re-fetch so the product + relations are loaded
        return await self.get_item(cart_id, product_id)  # type: ignore

    async def update_item_quantity(self, item: CartItem, quantity: int) -> CartItem:
        item.quantity = quantity
        await self.db.flush()
        return await self.get_item_by_id(item.id)  # type: ignore

    async def remove_item(self, item: CartItem) -> None:
        await self.db.delete(item)
        await self.db.flush()

    async def clear_cart(self, cart: Cart) -> None:
        for item in list(cart.items):
            await self.db.delete(item)
        await self.db.flush()
