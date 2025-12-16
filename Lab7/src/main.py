import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar
from litestar.di import Provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.controllers.order_controller import OrderController
from src.controllers.product_controller import ProductController
from src.controllers.user_controller import UserController
from src.messaging.broker import broker
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.services.cache_service import CacheService
from src.services.order_service import OrderService
from src.services.product_service import ProductService
from src.services.user_service import UserService

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Конфигурация базы данных."""

    def __init__(self):
        self.url = os.getenv(
            "DATABASE_URL", "postgresql+asyncpg://user:superpass@db:5432/db"
        )
        self.echo = True

    def create_engine(self) -> AsyncEngine:
        """Создает engine для подключения к БД."""
        return create_async_engine(
            self.url,
            echo=self.echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )


class RedisConfig:
    """Конфигурация Redis."""

    def __init__(self):
        self.host = "redis"
        self.port = 6379
        self.db = 0

    def create_client(self) -> Redis:
        """Создает клиент Redis."""
        return Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=False,
        )


db_config = DatabaseConfig()
engine = db_config.create_engine()
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

redis_config = RedisConfig()
redis_client: Redis = None


async def provide_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Провайдер сессии базы данных.

    Yields:
        AsyncSession: Активная сессия БД
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def provide_cache_service() -> CacheService:
    """Провайдер сервиса кеширования."""
    return CacheService(redis_client)


async def provide_user_repository(db_session: AsyncSession) -> UserRepository:
    """Провайдер репозитория пользователей."""
    return UserRepository(db_session)


async def provide_product_repository(db_session: AsyncSession) -> ProductRepository:
    """Провайдер репозитория продуктов."""
    return ProductRepository(db_session)


async def provide_order_repository(db_session: AsyncSession) -> OrderRepository:
    """Провайдер репозитория заказов."""
    return OrderRepository(db_session)


async def provide_user_service(
    user_repository: UserRepository, cache_service: CacheService
) -> UserService:
    """Провайдер сервиса пользователей."""
    return UserService(user_repository, cache_service)


async def provide_product_service(
    product_repository: ProductRepository, cache_service: CacheService
) -> ProductService:
    """Провайдер сервиса продуктов."""
    return ProductService(product_repository, cache_service)


async def provide_order_service(
    order_repository: OrderRepository,
    product_repository: ProductRepository,
    user_repository: UserRepository,
) -> OrderService:
    """Провайдер сервиса заказов."""
    return OrderService(order_repository, product_repository, user_repository)


async def _broker_connect_loop(shutdown_event: asyncio.Event) -> None:
    """
    Фоновая задача для запуска брокера и
    поддержания его работы до завершения работы системы.
    Брокер самостоятельно управляет переподключением
    благодаря своему устойчивому соединению.
    """
    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            logger.info(
                f"Attempting to start Rabbit broker (attempt {attempt + 1}/{max_retries})..."
            )
            await broker.start()
            logger.info("Rabbit broker connected successfully")

            await shutdown_event.wait()

            logger.info("Shutdown requested, closing broker...")
            await broker.close()
            logger.info("Broker closed successfully")
            return

        except Exception as e:
            logger.error(
                f"Broker connection error (attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Max retries reached, giving up on broker connection")
                raise


@asynccontextmanager
async def lifespan(app: Litestar):
    """
    Управление жизненным циклом приложения.

    Выполняется при старте и остановке приложения.
    """
    global redis_client

    redis_client = redis_config.create_client()
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

    shutdown_event = asyncio.Event()
    broker_task = asyncio.create_task(_broker_connect_loop(shutdown_event))

    from src.messaging import order, product  # noqa: F401

    try:
        yield
    finally:
        shutdown_event.set()

        try:
            await broker.close()
        except Exception:
            logger.exception("Error while closing broker")

        broker_task.cancel()
        try:
            await broker_task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Broker task raised while shutting down")

        try:
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception:
            logger.exception("Error closing Redis connection")

        try:
            await engine.dispose()
        except Exception:
            logger.exception("Error disposing engine")


def create_app() -> Litestar:
    """
    Фабрика для создания приложения Litestar.

    Returns:
        Litestar: Сконфигурированное приложение
    """
    return Litestar(
        route_handlers=[
            UserController,
            ProductController,
            OrderController,
        ],
        dependencies={
            # Database
            "db_session": Provide(provide_db_session),
            # Cache
            "cache_service": Provide(provide_cache_service),
            # Repositories
            "user_repository": Provide(provide_user_repository),
            "product_repository": Provide(provide_product_repository),
            "order_repository": Provide(provide_order_repository),
            # Services
            "user_service": Provide(provide_user_service),
            "product_service": Provide(provide_product_service),
            "order_service": Provide(provide_order_service),
        },
        lifespan=[lifespan],
        debug=True,
    )


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
