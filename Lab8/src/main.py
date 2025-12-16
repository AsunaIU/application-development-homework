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
from src.controllers.report_controller import ReportController
from src.messaging.broker import broker as faststream_broker
from src.messaging.taskiq_broker import taskiq_broker
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.repositories.report_repository import ReportRepository
from src.services.cache_service import CacheService
from src.services.order_service import OrderService
from src.services.product_service import ProductService
from src.services.user_service import UserService
from src.services.report_service import ReportService

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
    """Провайдер сессии базы данных."""
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


async def provide_report_repository(db_session: AsyncSession) -> ReportRepository:
    """Провайдер репозитория отчетов."""
    return ReportRepository(db_session)


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


async def provide_report_service(
    report_repository: ReportRepository,
) -> ReportService:
    """Провайдер сервиса отчетов."""
    return ReportService(report_repository)


async def _faststream_broker_connect(shutdown_event: asyncio.Event) -> None:
    """Запуск FastStream брокера для order/product."""
    max_retries = 10
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            logger.info(
                f"Starting FastStream broker (attempt {attempt + 1}/{max_retries})..."
            )
            await faststream_broker.start()
            logger.info("FastStream broker started successfully")

            await shutdown_event.wait()

            logger.info("Stopping FastStream broker...")
            await faststream_broker.close()
            logger.info("FastStream broker closed")
            return

        except Exception as e:
            logger.error(f"FastStream broker error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Max retries reached for FastStream broker")
                raise


async def _taskiq_worker_run(shutdown_event: asyncio.Event) -> None:
    """Запуск Taskiq worker для выполнения задач."""
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Starting Taskiq worker (attempt {attempt + 1}/{max_retries})...")
            
            from src.messaging.tasks import report  # noqa: F401
            
            await taskiq_broker.startup()
            logger.info("Taskiq broker started successfully")
            
            logger.info("Taskiq worker listening for tasks...")
            await taskiq_broker.listen()
            
            await shutdown_event.wait()
            
            logger.info("Stopping Taskiq worker...")
            await taskiq_broker.shutdown()
            logger.info("Taskiq worker closed")
            return
            
        except Exception as e:
            logger.error(f"Taskiq worker error (attempt {attempt + 1}): {e}", exc_info=True)
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Max retries reached for Taskiq worker")
                raise


@asynccontextmanager
async def lifespan(app: Litestar):
    """Управление жизненным циклом приложения."""
    global redis_client

    redis_client = redis_config.create_client()
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

    try:
        from src.messaging import order, product  # noqa: F401
        from src.messaging.tasks import report  # noqa: F401
        logger.info("Message handlers and tasks imported successfully")
    except Exception as e:
        logger.error(f"Failed to import handlers/tasks: {e}")
        raise

    shutdown_event = asyncio.Event()

    faststream_task = asyncio.create_task(_faststream_broker_connect(shutdown_event))

    start_taskiq_in_this_process = os.getenv("START_TASKIQ_WORKER", "0") == "1"
    
    taskiq_task = None
    if start_taskiq_in_this_process:
        logger.info("START_TASKIQ_WORKER=1 -> starting Taskiq worker in this process")
        taskiq_task = asyncio.create_task(_taskiq_worker_run(shutdown_event))
    else:
        logger.info(
            "START_TASKIQ_WORKER not set (or !=1). "
            "Taskiq worker will NOT be started in this process."
        )

    try:
        yield
    finally:
        logger.info("Starting shutdown sequence...")
        shutdown_event.set()

        for task, name in [(faststream_task, "FastStream"), (taskiq_task, "Taskiq")]:
            if task is None:
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"{name} task cancelled")
            except Exception:
                logger.exception(f"Error in {name} task")

        try:
            await redis_client.close()
            logger.info("Redis connection closed")
        except Exception:
            logger.exception("Error closing Redis")

        try:
            await engine.dispose()
            logger.info("Database engine disposed")
        except Exception:
            logger.exception("Error disposing engine")


def create_app() -> Litestar:
    """Фабрика для создания приложения Litestar."""
    return Litestar(
        route_handlers=[
            UserController,
            ProductController,
            OrderController,
            ReportController,
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
            "report_repository": Provide(provide_report_repository),
            # Services
            "user_service": Provide(provide_user_service),
            "product_service": Provide(provide_product_service),
            "order_service": Provide(provide_order_service),
            "report_service": Provide(provide_report_service),
        },
        lifespan=[lifespan],
        debug=True,
    )


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
    )
