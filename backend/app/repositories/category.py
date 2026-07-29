import uuid
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.utils.slug import generate_slug


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, site_id: Optional[uuid.UUID] = None) -> list[Category]:
        query = select(Category).order_by(Category.name)
        if site_id:
            query = query.where(Category.site_id == site_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: uuid.UUID, site_id: Optional[uuid.UUID] = None) -> Optional[Category]:
        query = select(Category).where(Category.id == category_id)
        if site_id:
            query = query.where(Category.site_id == site_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str, site_id: Optional[uuid.UUID] = None) -> Optional[Category]:
        query = select(Category).where(Category.slug == slug)
        if site_id:
            query = query.where(Category.site_id == site_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, site_id: uuid.UUID) -> Optional[Category]:
        result = await self.db.execute(
            select(Category).where(func.lower(Category.name) == name.lower(), Category.site_id == site_id)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, site_id: uuid.UUID, description: Optional[str] = None) -> Category:
        slug = await self._unique_slug(name, site_id)
        category = Category(name=name, slug=slug, description=description, site_id=site_id)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category: Category, **kwargs) -> Category:
        if "name" in kwargs and kwargs["name"]:
            kwargs["slug"] = await self._unique_slug(kwargs["name"], category.site_id, exclude_id=category.id)
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self.db.delete(category)
        await self.db.flush()

    async def _unique_slug(self, name: str, site_id: uuid.UUID, exclude_id: Optional[uuid.UUID] = None) -> str:
        base_slug = generate_slug(name)
        slug = base_slug
        counter = 1
        while True:
            q = select(Category.id).where(Category.slug == slug, Category.site_id == site_id)
            if exclude_id:
                q = q.where(Category.id != exclude_id)
            result = await self.db.execute(q)
            if result.scalar_one_or_none() is None:
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1
