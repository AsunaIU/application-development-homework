import logging
from typing import Dict

from faststream.rabbit import RabbitQueue

from src.main import async_session_maker
from src.messaging.broker import broker
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.schemas.order import OrderCreate, OrderUpdate
from src.services.order_service import OrderService

logger = logging.getLogger(__name__)


@broker.subscriber(RabbitQueue("order", durable=True))
async def subscribe_order(message: Dict):
    """
    Обработчик очереди 'order'.

    Поддерживаемые операции:
    - create: создание нового заказа с несколькими позициями
    - update_status: обновление статуса заказа
    - update: полное обновление заказа (статус + позиции)
    """
    async with async_session_maker() as session:
        try:
            action = message.get("action")
            data = message.get("data", {})

            order_repo = OrderRepository(session)
            product_repo = ProductRepository(session)
            user_repo = UserRepository(session)
            order_service = OrderService(order_repo, product_repo, user_repo)

            if action == "create":
                await handle_order_create(order_service, data)
            elif action == "update_status":
                await handle_order_update_status(order_service, data)
            elif action == "update":
                await handle_order_update(order_service, data)
            else:
                logger.error(f"Unknown action for order queue: {action}")

        except Exception as e:
            logger.exception(f"Error processing order message: {e}")
            raise


async def handle_order_create(service: OrderService, data: Dict):
    """
    Создание нового заказа с несколькими позициями.

    Проверяет наличие товаров на складе перед созданием заказа.
    """
    try:
        order_create = OrderCreate(**data)

        order = await service.create_order(order_create.model_dump())

        logger.info(
            f"Order created: ID={order.id}, user_id={order.user_id}, "
            f"total={order.total_amount}, items_count={len(order.items)}"
        )
    except ValueError as e:
        logger.error(f"Business logic error while creating order: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        raise


async def handle_order_update_status(service: OrderService, data: Dict):
    """
    Обновление статуса заказа.

    При отмене заказа (cancelled) автоматически возвращает товары на склад.
    """
    try:
        order_id = data.get("order_id")
        new_status = data.get("status")

        if not order_id:
            raise ValueError("order_id is required")
        if not new_status:
            raise ValueError("status is required")

        update_data = {"status": new_status}
        order = await service.update(order_id, update_data)

        logger.info(f"Order status updated: ID={order.id}, new_status={order.status}")
    except ValueError as e:
        logger.error(f"Business logic error while updating order status: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise


async def handle_order_update(service: OrderService, data: Dict):
    """
    Полное обновление заказа (статус и/или позиции).
    """
    try:
        order_id = data.pop("order_id", None)
        if not order_id:
            raise ValueError("order_id is required for update")

        order_update = OrderUpdate(**data)

        order = await service.update(
            order_id, order_update.model_dump(exclude_unset=True)
        )

        logger.info(
            f"Order updated: ID={order.id}, status={order.status}, "
            f"items_count={len(order.items)}"
        )
    except ValueError as e:
        logger.error(f"Business logic error while updating order: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to update order: {e}")
        raise
