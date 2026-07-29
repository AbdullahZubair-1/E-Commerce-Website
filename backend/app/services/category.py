import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import get_logger

logger = get_logger(__name__)


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def get_all(self, site_id: uuid.UUID) -> list[CategoryResponse]:
        categories = await self.repo.get_all(site_id=site_id)
        return [CategoryResponse.model_validate(c) for c in categories]

    async def get_by_id(self, category_id: uuid.UUID, site_id: uuid.UUID) -> CategoryResponse:
        category = await self.repo.get_by_id(category_id, site_id=site_id)
        if not category:
            raise NotFoundError("Category not found.")
        return CategoryResponse.model_validate(category)

    async def create(self, data: CategoryCreate, site_id: uuid.UUID) -> CategoryResponse:
        existing = await self.repo.get_by_name(data.name, site_id=site_id)
        if existing:
            raise ConflictError(f"Category '{data.name}' already exists.")

        category = await self.repo.create(name=data.name, site_id=site_id, description=data.description)
        logger.info(f"Category created: {category.name} (site={site_id})")
        return CategoryResponse.model_validate(category)

    async def update(self, category_id: uuid.UUID, data: CategoryUpdate, site_id: uuid.UUID) -> CategoryResponse:
        category = await self.repo.get_by_id(category_id, site_id=site_id)
        if not category:
            raise NotFoundError("Category not found.")

        if data.name and data.name != category.name:
            existing = await self.repo.get_by_name(data.name, site_id=site_id)
            if existing:
                raise ConflictError(f"Category '{data.name}' already exists.")

        updates = data.model_dump(exclude_none=True)
        category = await self.repo.update(category, **updates)
        logger.info(f"Category updated: {category.name}")
        return CategoryResponse.model_validate(category)

    async def delete(self, category_id: uuid.UUID, site_id: uuid.UUID) -> None:
        category = await self.repo.get_by_id(category_id, site_id=site_id)
        if not category:
            raise NotFoundError("Category not found.")
        await self.repo.delete(category)
        logger.info(f"Category deleted: {category.name}")
