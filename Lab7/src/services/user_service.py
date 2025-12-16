import logging

from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserUpdate
from src.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class UserService:
    USER_CACHE_TTL = 3600  # Cache TTL: 1 hour

    def __init__(self, user_repository: UserRepository, cache_service: CacheService):
        self.user_repository = user_repository
        self.cache_service = cache_service

    def _get_user_cache_key(self, user_id: int) -> str:
        """Generate cache key for user"""
        return f"user:{user_id}"

    def _user_to_dict(self, user: User) -> dict:
        """Convert User model to dict for caching"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID"""
        cache_key = self._get_user_cache_key(user_id)

        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Cache HIT for user {user_id}")
            return cached_data

        logger.info(f"Cache MISS for user {user_id}")
        user = await self.user_repository.get_by_id(user_id)

        if user:
            user_dict = self._user_to_dict(user)
            await self.cache_service.set(cache_key, user_dict, self.USER_CACHE_TTL)
            return user

        return None

    async def get_by_filter(self, count: int, page: int, **kwargs) -> dict:
        """Get a list of users with filtering and the total number"""
        users = await self.user_repository.get_by_filter(count, page, **kwargs)
        total = await self.user_repository.count(**kwargs)
        return {"total": total, "items": users}

    async def create(self, user_data: UserCreate) -> User:
        """Create a new user"""
        return await self.user_repository.create(user_data)

    async def update(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user data"""
        patch = (
            user_data.model_dump(exclude_none=True)
            if hasattr(user_data, "model_dump")
            else dict(user_data)
        )

        updated_user = await self.user_repository.update(user_id, user_data)

        if updated_user:
            cache_key = self._get_user_cache_key(user_id)
            user_dict = self._user_to_dict(updated_user)
            await self.cache_service.set(cache_key, user_dict, self.USER_CACHE_TTL)
            logger.info(f"Cache UPDATED for user {user_id}")

        return updated_user

    async def delete(self, user_id: int) -> None:
        """Удалить пользователя"""
        await self.user_repository.delete(user_id)

        cache_key = self._get_user_cache_key(user_id)
        await self.cache_service.delete(cache_key)
        logger.info(f"Cache DELETED for user {user_id}")
