import logging
from typing import Any, Dict

from src.repositories.product_repository import ProductRepository
from src.schemas.product import ProductCreate, ProductUpdate
from src.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class ProductService:
    PRODUCT_CACHE_TTL = 600 # Cache TTL: 10 min

    def __init__(self, product_repository: ProductRepository, cache_service: CacheService):
        self.product_repository = product_repository
        self.cache_service = cache_service

    def _get_product_cache_key(self, product_id: int) -> str:
        """Generate cache key for product"""
        return f"product:{product_id}"

    def _product_to_dict(self, product) -> dict:
        """Convert Product model to dict for caching"""
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "stock_quantity": product.stock_quantity,
        }

    async def create(self, data: ProductCreate | dict) ->  Dict[str, Any]:
        payload = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        return await self.product_repository.create(**payload)

    async def get_by_id(self, product_id: int):
        """Get product by id (with caching)"""
        cache_key = self._get_product_cache_key(product_id)
        
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Cache HIT for product {product_id}")
            return cached_data
        
        logger.info(f"Cache MISS for product {product_id}")
        product = await self.product_repository.get_by_id(product_id)
        
        if product:
            product_dict = self._product_to_dict(product)
            await self.cache_service.set(cache_key, product_dict, self.PRODUCT_CACHE_TTL)
            return product
        
        return None

    async def get_by_filter(self, count: int = 10, page: int = 1) -> Dict[str, Any]:
        """Get product with page filter"""
        return await self.product_repository.get_by_filter(count, page)

    async def update(self, product_id: int, data: ProductUpdate | dict) ->  Dict[str, Any]:
        """Update product with caching"""
        patch = (
            data.model_dump(exclude_none=True)
            if hasattr(data, "model_dump")
            else dict(data)
        )
        
        updated_product = await self.product_repository.update(product_id, **patch)
        
        if updated_product:
            cache_key = self._get_product_cache_key(product_id)
            product_dict = self._product_to_dict(updated_product)
            await self.cache_service.set(cache_key, product_dict, self.PRODUCT_CACHE_TTL)
            logger.info(f"Cache UPDATED for product {product_id}")
        
        return updated_product

    async def delete(self, product_id: int) -> None:
        """Delete product from db and cache"""
        await self.product_repository.delete(product_id)
        
        cache_key = self._get_product_cache_key(product_id)
        await self.cache_service.delete(cache_key)
        logger.info(f"Cache DELETED for product {product_id}")
