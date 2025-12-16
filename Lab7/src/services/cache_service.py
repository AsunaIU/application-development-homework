import json
from typing import Any, Optional

from redis.asyncio import Redis


class CacheService:
    """Service for handling Redis caching operations"""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[dict]:
        """
        Get cached data by key
        """
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int) -> bool:
        """
        Set cache with TTL
        """
        try:
            serialized = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete cache key
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error for pattern {pattern}: {e}")
            return 0
