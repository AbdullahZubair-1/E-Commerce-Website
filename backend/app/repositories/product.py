import uuid
from typing import Optional
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product
from app.utils.slug import generate_slug


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self):
        return select(Product).options(
            selectinload(Product.category),
            selectinload(Product.brand),
        )

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        brand_id: Optional[uuid.UUID] = None,
        active_only: bool = True,
        site_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[Product], int]:
        query = self._base_query()
        count_query = select(func.count(Product.id))

        if site_id:
            query = query.where(Product.site_id == site_id)
            count_query = count_query.where(Product.site_id == site_id)

        if active_only:
            query = query.where(Product.is_active == True)
            count_query = count_query.where(Product.is_active == True)

        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if category_id:
            query = query.where(Product.category_id == category_id)
            count_query = count_query.where(Product.category_id == category_id)

        if brand_id:
            query = query.where(Product.brand_id == brand_id)
            count_query = count_query.where(Product.brand_id == brand_id)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(Product.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id(self, product_id: uuid.UUID, site_id: Optional[uuid.UUID] = None) -> Optional[Product]:
        query = self._base_query().where(Product.id == product_id)
        if site_id:
            query = query.where(Product.site_id == site_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str, site_id: Optional[uuid.UUID] = None) -> Optional[Product]:
        query = self._base_query().where(Product.slug == slug)
        if site_id:
            query = query.where(Product.site_id == site_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        name: str,
        price,
        stock_quantity: int,
        site_id: uuid.UUID,
        description: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        brand_id: Optional[uuid.UUID] = None,
        image_url: Optional[str] = None,
    ) -> Product:
        slug = await self._unique_slug(name)
        product = Product(
            name=name,
            slug=slug,
            description=description,
            price=price,
            stock_quantity=stock_quantity,
            category_id=category_id,
            brand_id=brand_id,
            image_url=image_url,
            site_id=site_id,
        )
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return await self.get_by_id(product.id)  # type: ignore

    async def update(self, product: Product, **kwargs) -> Product:
        if "name" in kwargs and kwargs["name"]:
            kwargs["slug"] = await self._unique_slug(kwargs["name"], exclude_id=product.id)
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        await self.db.flush()
        return await self.get_by_id(product.id)  # type: ignore

    async def delete(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.flush()

    async def decrement_stock(self, product_id: uuid.UUID, quantity: int) -> None:
        product = await self.get_by_id(product_id)
        if product:
            product.stock_quantity = max(0, product.stock_quantity - quantity)
            await self.db.flush()

    async def _unique_slug(self, name: str, exclude_id: Optional[uuid.UUID] = None) -> str:
        base_slug = generate_slug(name)
        slug = base_slug
        counter = 1
        while True:
            q = select(Product.id).where(Product.slug == slug)
            if exclude_id:
                q = q.where(Product.id != exclude_id)
            result = await self.db.execute(q)
            if result.scalar_one_or_none() is None:
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1
