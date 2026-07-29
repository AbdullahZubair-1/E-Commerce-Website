import uuid
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.brand import Brand
from app.utils.slug import generate_slug


class BrandRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, site_id: Optional[uuid.UUID] = None) -> list[Brand]:
        query = select(Brand).order_by(Brand.name)
        if site_id:
            query = query.where(Brand.site_id == site_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, brand_id: uuid.UUID, site_id: Optional[uuid.UUID] = None) -> Optional[Brand]:
        query = select(Brand).where(Brand.id == brand_id)
        if site_id:
            query = query.where(Brand.site_id == site_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str, site_id: Optional[uuid.UUID] = None) -> Optional[Brand]:
        query = select(Brand).where(Brand.slug == slug)
        if site_id:
            query = query.where(Brand.site_id == site_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, site_id: uuid.UUID) -> Optional[Brand]:
        result = await self.db.execute(
            select(Brand).where(func.lower(Brand.name) == name.lower(), Brand.site_id == site_id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, site_id: uuid.UUID, description: Optional[str] = None) -> Brand:
        slug = await self._unique_slug(name, site_id)
        brand = Brand(name=name, slug=slug, description=description, site_id=site_id)
        self.db.add(brand)
        await self.db.flush()
        await self.db.refresh(brand)
        return brand

    async def update(self, brand: Brand, **kwargs) -> Brand:
        if "name" in kwargs and kwargs["name"]:
            kwargs["slug"] = await self._unique_slug(kwargs["name"], brand.site_id, exclude_id=brand.id)
        for key, value in kwargs.items():
            if hasattr(brand, key):
                setattr(brand, key, value)
        await self.db.flush()
        await self.db.refresh(brand)
        return brand

    async def delete(self, brand: Brand) -> None:
        await self.db.delete(brand)
        await self.db.flush()

    async def _unique_slug(self, name: str, site_id: uuid.UUID, exclude_id: Optional[uuid.UUID] = None) -> str:
        base_slug = generate_slug(name)
        slug = base_slug
        counter = 1
        while True:
            q = select(Brand.id).where(Brand.slug == slug, Brand.site_id == site_id)
            if exclude_id:
                q = q.where(Brand.id != exclude_id)
            result = await self.db.execute(q)
            if result.scalar_one_or_none() is None:
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1
