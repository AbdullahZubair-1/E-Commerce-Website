import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.order import OrderRepository
from app.repositories.cart import CartRepository
from app.repositories.product import ProductRepository
from app.repositories.user import UserRepository
from app.repositories.notification import NotificationRepository
from app.schemas.order import OrderCreate, OrderStatusUpdate, OrderResponse, OrderSummaryResponse
from app.schemas.base import PaginatedData
from app.models.order import OrderStatus
from app.models.site import Site
from app.core.exceptions import NotFoundError, BadRequestError, ForbiddenError
from app.core.logging import get_logger
from app.core.admin_notifications import admin_notification_manager
from app.core.email_webhook_client import send_order_confirmation_email
import math

logger = get_logger(__name__)


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)
        self.user_repo = UserRepository(db)
        self.notification_repo = NotificationRepository(db)

    async def place_order(self, user_id: uuid.UUID, data: OrderCreate) -> OrderResponse:
        cart = await self.cart_repo.get_by_user_id(user_id)
        if not cart or not cart.items:
            raise BadRequestError("Your cart is empty.")

        # Validate stock and build order items
        order_items = []
        total_amount = Decimal("0.00")

        for cart_item in cart.items:
            product = await self.product_repo.get_by_id(cart_item.product_id)
            if not product:
                raise BadRequestError(f"Product '{cart_item.product_id}' no longer exists.")
            if not product.is_active:
                raise BadRequestError(f"Product '{product.name}' is no longer available.")
            if product.stock_quantity < cart_item.quantity:
                raise BadRequestError(
                    f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}"
                )

            subtotal = Decimal(str(product.price)) * cart_item.quantity
            total_amount += subtotal

            order_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "product_price": product.price,
                "quantity": cart_item.quantity,
                "subtotal": subtotal,
            })

        # Create order
        order = await self.repo.create(
            user_id=user_id,
            total_amount=total_amount,
            shipping_address=data.shipping_address,
            items=order_items,
            notes=data.notes,
        )

        # Decrement stock
        for item in order_items:
            await self.product_repo.decrement_stock(item["product_id"], item["quantity"])

        # Clear cart
        await self.cart_repo.clear_cart(cart)

        # Notify the site's admin(s), both persisted and real-time.
        buyer = await self.user_repo.get_by_id(user_id)
        buyer_name = f"{buyer.first_name} {buyer.last_name}" if buyer else "A customer"
        item_count = sum(i["quantity"] for i in order_items)
        notification = await self.notification_repo.create(
            site_id=buyer.site_id,
            title="New order placed",
            message=f"{buyer_name} placed an order for {item_count} item(s) totaling ${total_amount:.2f}.",
            order_id=order.id,
        )
        await admin_notification_manager.notify_site(
            buyer.site_id,
            {
                "type": "notification",
                "notification": {
                    "id": str(notification.id),
                    "type": notification.type,
                    "title": notification.title,
                    "message": notification.message,
                    "order_id": str(notification.order_id),
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat(),
                },
            },
        )

        # Best-effort -- never let an email hiccup undo a real order.
        site_result = await self.db.execute(select(Site).where(Site.id == buyer.site_id))
        site = site_result.scalar_one_or_none()
        item_summary = ", ".join(f"{i['quantity']}x {i['product_name']}" for i in order_items)
        await send_order_confirmation_email(
            site_name=site.name if site else "",
            customer_name=buyer_name,
            customer_email=buyer.email if buyer else "",
            order_id=str(order.id),
            total_amount=f"{total_amount:.2f}",
            item_summary=item_summary,
        )

        logger.info(f"Order placed: {order.id} by user {user_id}")
        return OrderResponse.model_validate(order)

    async def get_my_orders(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> PaginatedData[OrderSummaryResponse]:
        orders, total = await self.repo.get_all(page=page, page_size=page_size, user_id=user_id)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        summaries = []
        for order in orders:
            summaries.append(OrderSummaryResponse(
                id=order.id,
                status=order.status,
                total_amount=order.total_amount,
                shipping_address=order.shipping_address,
                item_count=sum(i.quantity for i in order.items),
                created_at=order.created_at,
                updated_at=order.updated_at,
            ))
        return PaginatedData(
            items=summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_my_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> OrderResponse:
        order = await self.repo.get_by_id_and_user(order_id, user_id)
        if not order:
            raise NotFoundError("Order not found.")
        return OrderResponse.model_validate(order)

    # --- Admin ---
    async def get_all_orders(
        self,
        site_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[OrderStatus] = None,
    ) -> PaginatedData[OrderSummaryResponse]:
        orders, total = await self.repo.get_all(page=page, page_size=page_size, status=status, site_id=site_id)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        summaries = []
        for order in orders:
            summaries.append(OrderSummaryResponse(
                id=order.id,
                status=order.status,
                total_amount=order.total_amount,
                shipping_address=order.shipping_address,
                item_count=sum(i.quantity for i in order.items),
                created_at=order.created_at,
                updated_at=order.updated_at,
            ))
        return PaginatedData(
            items=summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_order_by_id(self, order_id: uuid.UUID, site_id: uuid.UUID) -> OrderResponse:
        order = await self.repo.get_by_id(order_id, site_id=site_id)
        if not order:
            raise NotFoundError("Order not found.")
        return OrderResponse.model_validate(order)

    async def update_order_status(
        self, order_id: uuid.UUID, data: OrderStatusUpdate, site_id: uuid.UUID
    ) -> OrderResponse:
        order = await self.repo.get_by_id(order_id, site_id=site_id)
        if not order:
            raise NotFoundError("Order not found.")
        order = await self.repo.update_status(order, data.status)
        logger.info(f"Order {order_id} status updated to {data.status}")
        return OrderResponse.model_validate(order)