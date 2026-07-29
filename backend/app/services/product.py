import uuid
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.product import ProductRepository
from app.repositories.category import CategoryRepository
from app.repositories.brand import BrandRepository
from app.schemas.product import ProductCreate, ProductUpdate, StockUpdate, ProductResponse, ProductListResponse
from app.schemas.base import PaginatedData
from app.utils.pagination import paginate
from app.utils.file_upload import save_product_image, delete_file
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
import math

logger = get_logger(__name__)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.brand_repo = BrandRepository(db)

    async def get_all(
        self,
        site_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        brand_id: Optional[uuid.UUID] = None,
        active_only: bool = True,
    ) -> PaginatedData[ProductListResponse]:
        products, total = await self.repo.get_all(
            page=page,
            page_size=page_size,
            search=search,
            category_id=category_id,
            brand_id=brand_id,
            active_only=active_only,
            site_id=site_id,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return PaginatedData(
            items=[ProductListResponse.model_validate(p) for p in products],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_by_id(self, product_id: uuid.UUID, site_id: uuid.UUID) -> ProductResponse:
        product = await self.repo.get_by_id(product_id, site_id=site_id)
        if not product:
            raise NotFoundError("Product not found.")
        return ProductResponse.model_validate(product)

    async def get_by_slug(self, slug: str, site_id: uuid.UUID) -> ProductResponse:
        product = await self.repo.get_by_slug(slug, site_id=site_id)
        if not product:
            raise NotFoundError("Product not found.")
        return ProductResponse.model_validate(product)

    async def create(self, data: ProductCreate, site_id: uuid.UUID, image: Optional[UploadFile] = None) -> ProductResponse:
        image_url = None
        if image and image.filename:
            image_url = await save_product_image(image)

        product = await self.repo.create(
            name=data.name,
            description=data.description,
            price=data.price,
            stock_quantity=data.stock_quantity,
            category_id=data.category_id,
            brand_id=data.brand_id,
            image_url=image_url,
            site_id=site_id,
        )
        logger.info(f"Product created: {product.name} (site={site_id})")
        return ProductResponse.model_validate(product)

    async def update(
        self, product_id: uuid.UUID, data: ProductUpdate, site_id: uuid.UUID, image: Optional[UploadFile] = None
    ) -> ProductResponse:
        product = await self.repo.get_by_id(product_id, site_id=site_id)
        if not product:
            raise NotFoundError("Product not found.")

        updates = data.model_dump(exclude_none=True)

        if image and image.filename:
            old_image = product.image_url
            updates["image_url"] = await save_product_image(image)
            if old_image:
                delete_file(old_image)

        product = await self.repo.update(product, **updates)
        logger.info(f"Product updated: {product.name}")
        return ProductResponse.model_validate(product)

    async def update_stock(self, product_id: uuid.UUID, data: StockUpdate, site_id: uuid.UUID) -> ProductResponse:
        product = await self.repo.get_by_id(product_id, site_id=site_id)
        if not product:
            raise NotFoundError("Product not found.")

        product = await self.repo.update(product, stock_quantity=data.stock_quantity)
        logger.info(f"Stock updated for: {product.name} -> {data.stock_quantity}")
        return ProductResponse.model_validate(product)

    async def delete(self, product_id: uuid.UUID, site_id: uuid.UUID) -> None:
        product = await self.repo.get_by_id(product_id, site_id=site_id)
        if not product:
            raise NotFoundError("Product not found.")
        if product.image_url:
            delete_file(product.image_url)
        await self.repo.delete(product)
        logger.info(f"Product deleted: {product.name}")
