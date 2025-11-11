import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from src.models.base import Base
from src.models.user import User  # noqa

async def create_tables():
    engine = create_async_engine(
        "postgresql+asyncpg://user:superpass@db:5432/db",
        echo=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Tables created!")

if __name__ == "__main__":
    asyncio.run(create_tables())
