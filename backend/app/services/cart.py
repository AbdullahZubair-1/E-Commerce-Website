import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.cart import CartRepository
from app.repositories.product import ProductRepository
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse, CartItemResponse
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_cart_response(cart) -> CartResponse:
    items = []
    total = Decimal("0.00")
    for item in cart.items:
        subtotal = Decimal(str(item.product.price)) * item.quantity
        total += subtotal
        items.append(CartItemResponse(
            id=item.id,
            cart_id=item.cart_id,
            product_id=item.product_id,
            quantity=item.quantity,
            product=item.product,
            subtotal=subtotal,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ))
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=items,
        total=total,
        item_count=sum(i.quantity for i in cart.items),
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


class CartService:
    def __init__(self, db: AsyncSession):
        self.repo = CartRepository(db)
        self.product_repo = ProductRepository(db)

    async def get_cart(self, user_id: uuid.UUID) -> CartResponse:
        cart = await self.repo.get_or_create(user_id)
        return _build_cart_response(cart)

    async def add_item(self, user_id: uuid.UUID, data: CartItemAdd) -> CartResponse:
        product = await self.product_repo.get_by_id(data.product_id)
        if not product:
            raise NotFoundError("Product not found.")
        if not product.is_active:
            raise BadRequestError("Product is not available.")
        if product.stock_quantity < data.quantity:
            raise BadRequestError(
                f"Insufficient stock. Available: {product.stock_quantity}"
            )

        cart = await self.repo.get_or_create(user_id)
        existing_item = await self.repo.get_item(cart.id, data.product_id)

        if existing_item:
            new_quantity = existing_item.quantity + data.quantity
            if product.stock_quantity < new_quantity:
                raise BadRequestError(
                    f"Insufficient stock. Available: {product.stock_quantity}"
                )
            await self.repo.update_item_quantity(existing_item, new_quantity)
        else:
            await self.repo.add_item(cart.id, data.product_id, data.quantity)

        cart = await self.repo.get_by_user_id(user_id)
        return _build_cart_response(cart)  # type: ignore

    async def update_item(
        self, user_id: uuid.UUID, item_id: uuid.UUID, data: CartItemUpdate
    ) -> CartResponse:
        cart = await self.repo.get_or_create(user_id)
        item = await self.repo.get_item_by_id(item_id)

        if not item or item.cart_id != cart.id:
            raise NotFoundError("Cart item not found.")

        product = await self.product_repo.get_by_id(item.product_id)
        if product and product.stock_quantity < data.quantity:
            raise BadRequestError(
                f"Insufficient stock. Available: {product.stock_quantity}"
            )

        await self.repo.update_item_quantity(item, data.quantity)
        cart = await self.repo.get_by_user_id(user_id)
        return _build_cart_response(cart)  # type: ignore

    async def remove_item(self, user_id: uuid.UUID, item_id: uuid.UUID) -> CartResponse:
        cart = await self.repo.get_or_create(user_id)
        item = await self.repo.get_item_by_id(item_id)

        if not item or item.cart_id != cart.id:
            raise NotFoundError("Cart item not found.")

        await self.repo.remove_item(item)
        cart = await self.repo.get_by_user_id(user_id)
        return _build_cart_response(cart)  # type: ignore

    async def clear_cart(self, user_id: uuid.UUID) -> CartResponse:
        cart = await self.repo.get_or_create(user_id)
        await self.repo.clear_cart(cart)
        cart = await self.repo.get_by_user_id(user_id)
        return _build_cart_response(cart)  # type: ignore
