from typing import Optional, Dict, Any
from src.repositories.product_repository import ProductRepository
from src.schemas.product import ProductCreate, ProductUpdate

class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def create(self, data: ProductCreate | dict):
        payload = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        return await self.product_repository.create(**payload)

    async def get_by_id(self, product_id: int):
        return await self.product_repository.get_by_id(product_id)

    async def get_by_filter(self, count: int = 10, page: int = 1) -> Dict[str, Any]:
        return await self.product_repository.get_by_filter(count, page)

    async def update(self, product_id: int, data: ProductUpdate | dict):
        patch = data.model_dump(exclude_none=True) if hasattr(data, "model_dump") else dict(data)
        return await self.product_repository.update(product_id, **patch)

    async def delete(self, product_id: int) -> None:
        await self.product_repository.delete(product_id)
