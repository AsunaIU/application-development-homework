import logging
from typing import Dict

from faststream.rabbit import RabbitQueue

from src.main import async_session_maker, redis_client
from src.messaging.broker import broker
from src.repositories.product_repository import ProductRepository
from src.schemas.product import ProductCreate, ProductUpdate
from src.services.cache_service import CacheService
from src.services.product_service import ProductService

logger = logging.getLogger(__name__)


@broker.subscriber(queue=RabbitQueue("product", durable=True))
async def subscribe_product(message: Dict):
    """
    Обработчик очереди 'product'.

    Поддерживаемые операции:
    - create: создание нового продукта
    - update: обновление существующего продукта
    - mark_out_of_stock: пометить продукт как закончившийся
    """
    async with async_session_maker() as session:
        try:
            action = message.get("action")
            data = message.get("data", {})

            product_repo = ProductRepository(session)
            cache_service = CacheService(redis_client)
            product_service = ProductService(product_repo, cache_service)

            if action == "create":
                await handle_product_create(product_service, data)
            elif action == "update":
                await handle_product_update(product_service, data)
            elif action == "mark_out_of_stock":
                await handle_product_mark_out_of_stock(product_service, data)
            else:
                logger.error(f"Unknown action for product queue: {action}")

        except Exception as e:
            logger.exception(f"Error processing product message: {e}")
            raise


async def handle_product_create(service: ProductService, data: Dict):
    """Создание нового продукта"""
    try:
        product_create = ProductCreate(**data)
        product = await service.create(product_create)
        logger.info(f"Product created: ID={product.id}, name={product.name}")
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise


async def handle_product_update(service: ProductService, data: Dict):
    """Обновление существующего продукта"""
    try:
        product_id = data.pop("id", None)
        if not product_id:
            raise ValueError("Product ID is required for update")

        product_update = ProductUpdate(**data)
        product = await service.update(product_id, product_update)

        if product:
            logger.info(f"Product updated: ID={product.id}")
        else:
            logger.warning(f"Product not found: ID={product_id}")
    except Exception as e:
        logger.error(f"Failed to update product: {e}")
        raise


async def handle_product_mark_out_of_stock(service: ProductService, data: Dict):
    """Пометить продукт как закончившийся на складе"""
    try:
        product_id = data.get("id")
        if not product_id:
            raise ValueError("Product ID is required")

        product_update = ProductUpdate(stock_quantity=0)
        product = await service.update(product_id, product_update)

        if product:
            logger.info(f"Product marked as out of stock: ID={product.id}")
        else:
            logger.warning(f"Product not found: ID={product_id}")
    except Exception as e:
        logger.error(f"Failed to mark product as out of stock: {e}")
        raise
