import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.brand import BrandRepository
from app.schemas.brand import BrandCreate, BrandUpdate, BrandResponse
from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import get_logger

logger = get_logger(__name__)


class BrandService:
    def __init__(self, db: AsyncSession):
        self.repo = BrandRepository(db)

    async def get_all(self, site_id: uuid.UUID) -> list[BrandResponse]:
        brands = await self.repo.get_all(site_id=site_id)
        return [BrandResponse.model_validate(b) for b in brands]

    async def get_by_id(self, brand_id: uuid.UUID, site_id: uuid.UUID) -> BrandResponse:
        brand = await self.repo.get_by_id(brand_id, site_id=site_id)
        if not brand:
            raise NotFoundError("Brand not found.")
        return BrandResponse.model_validate(brand)

    async def create(self, data: BrandCreate, site_id: uuid.UUID) -> BrandResponse:
        existing = await self.repo.get_by_name(data.name, site_id=site_id)
        if existing:
            raise ConflictError(f"Brand '{data.name}' already exists.")

        brand = await self.repo.create(name=data.name, site_id=site_id, description=data.description)
        logger.info(f"Brand created: {brand.name} (site={site_id})")
        return BrandResponse.model_validate(brand)

    async def update(self, brand_id: uuid.UUID, data: BrandUpdate, site_id: uuid.UUID) -> BrandResponse:
        brand = await self.repo.get_by_id(brand_id, site_id=site_id)
        if not brand:
            raise NotFoundError("Brand not found.")

        if data.name and data.name != brand.name:
            existing = await self.repo.get_by_name(data.name, site_id=site_id)
            if existing:
                raise ConflictError(f"Brand '{data.name}' already exists.")

        updates = data.model_dump(exclude_none=True)
        brand = await self.repo.update(brand, **updates)
        logger.info(f"Brand updated: {brand.name}")
        return BrandResponse.model_validate(brand)

    async def delete(self, brand_id: uuid.UUID, site_id: uuid.UUID) -> None:
        brand = await self.repo.get_by_id(brand_id, site_id=site_id)
        if not brand:
            raise NotFoundError("Brand not found.")
        await self.repo.delete(brand)
        logger.info(f"Brand deleted: {brand.name}")
