from src.repositories.user_repository import UserRepository
from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_by_id(self, user_id: int) -> User | None:
        """Получить пользователя по ID"""
        return await self.user_repository.get_by_id(user_id)

    async def get_by_filter(self, count: int, page: int, **kwargs) -> dict:
        """Получить список пользователей с фильтрацией и общее количество"""
        users = await self.user_repository.get_by_filter(count, page, **kwargs)
        total = await self.user_repository.count(**kwargs)
        return {"total": total, "items": users}

    async def create(self, user_data: UserCreate) -> User:
        """Создать нового пользователя"""
        return await self.user_repository.create(user_data)

    async def update(self, user_id: int, user_data: UserUpdate) -> User:
        """Обновить данные пользователя"""
        return await self.user_repository.update(user_id, user_data)

    async def delete(self, user_id: int) -> None:
        """Удалить пользователя"""
        await self.user_repository.delete(user_id)
