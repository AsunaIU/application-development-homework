import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar
from litestar.di import Provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.controllers.order_controller import OrderController
from src.controllers.product_controller import ProductController
from src.controllers.user_controller import UserController
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.services.order_service import OrderService
from src.services.product_service import ProductService
from src.services.user_service import UserService


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


db_config = DatabaseConfig()
engine = db_config.create_engine()
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


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


async def provide_user_repository(db_session: AsyncSession) -> UserRepository:
    """Провайдер репозитория пользователей."""
    return UserRepository(db_session)


async def provide_product_repository(db_session: AsyncSession) -> ProductRepository:
    """Провайдер репозитория продуктов."""
    return ProductRepository(db_session)


async def provide_order_repository(db_session: AsyncSession) -> OrderRepository:
    """Провайдер репозитория заказов."""
    return OrderRepository(db_session)


async def provide_user_service(user_repository: UserRepository) -> UserService:
    """Провайдер сервиса пользователей."""
    return UserService(user_repository)


async def provide_product_service(
    product_repository: ProductRepository,
) -> ProductService:
    """Провайдер сервиса продуктов."""
    return ProductService(product_repository)


async def provide_order_service(
    order_repository: OrderRepository,
    product_repository: ProductRepository,
    user_repository: UserRepository,
) -> OrderService:
    """Провайдер сервиса заказов."""
    return OrderService(order_repository, product_repository, user_repository)


@asynccontextmanager
async def lifespan(app: Litestar):
    """
    Управление жизненным циклом приложения.

    Выполняется при старте и остановке приложения.
    """
    yield
    await engine.dispose()


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
