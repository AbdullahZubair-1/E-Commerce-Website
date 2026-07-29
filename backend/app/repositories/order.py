import uuid
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _order_query(self):
        return select(Order).options(selectinload(Order.items))

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[OrderStatus] = None,
        user_id: Optional[uuid.UUID] = None,
        site_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[Order], int]:
        query = self._order_query()
        count_query = select(func.count(Order.id))

        if site_id:
            # Orders don't carry site_id directly -- scope through the
            # order's own user, since every user belongs to exactly one site.
            query = query.join(User, Order.user_id == User.id).where(User.site_id == site_id)
            count_query = count_query.join(User, Order.user_id == User.id).where(User.site_id == site_id)

        if status:
            query = query.where(Order.status == status)
            count_query = count_query.where(Order.status == status)

        if user_id:
            query = query.where(Order.user_id == user_id)
            count_query = count_query.where(Order.user_id == user_id)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id(self, order_id: uuid.UUID, site_id: Optional[uuid.UUID] = None) -> Optional[Order]:
        query = self._order_query().where(Order.id == order_id)
        if site_id:
            query = query.join(User, Order.user_id == User.id).where(User.site_id == site_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_and_user(self, order_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Order]:
        result = await self.db.execute(
            self._order_query().where(Order.id == order_id, Order.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        total_amount,
        shipping_address: str,
        items: list[dict],
        notes: Optional[str] = None,
    ) -> Order:
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            notes=notes,
        )
        self.db.add(order)
        await self.db.flush()

        for item_data in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                product_name=item_data["product_name"],
                product_price=item_data["product_price"],
                quantity=item_data["quantity"],
                subtotal=item_data["subtotal"],
            )
            self.db.add(order_item)

        await self.db.flush()
        return await self.get_by_id(order.id)  # type: ignore

    async def update_status(self, order: Order, status: OrderStatus) -> Order:
        order.status = status
        await self.db.flush()
        # Re-fetch with items eagerly loaded — refresh() drops relationship caches
        return await self.get_by_id(order.id)  # type: ignore
