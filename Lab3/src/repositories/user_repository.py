from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """Получить пользователя по ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_filter(self, count: int, page: int, **kwargs) -> list[User]:
        """Получить список пользователей с пагинацией и фильтрацией"""
        query = select(User)
        
        # Применяем фильтры
        for key, value in kwargs.items():
            if hasattr(User, key) and value is not None:
                query = query.where(getattr(User, key) == value)
        
        # Пагинация
        offset = (page - 1) * count
        query = query.offset(offset).limit(count)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, user_data: UserCreate) -> User:
        """Создать нового пользователя"""
        user = User(**user_data.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: int, user_data: UserUpdate) -> User:
        """Обновить данные пользователя"""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Обновляем только переданные поля
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: int) -> None:
        """Удалить пользователя"""
        await self.session.execute(
            delete(User).where(User.id == user_id)
        )
        await self.session.commit()

    async def count(self, **filters) -> int:
        """Подсчитать количество пользователей с фильтрами"""
        query = select(func.count()).select_from(User)
        for key, value in filters.items():
            if value is not None:
                query = query.where(getattr(User, key) == value)
        result = await self.session.execute(query)
        return result.scalar_one()
