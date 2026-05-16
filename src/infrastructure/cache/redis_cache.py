from redis.asyncio import Redis

from src.domain.services.cache import ICacheService


class RedisCacheService(ICacheService):
    def __init__(self, redis: Redis):
        self._redis = redis

    @property
    def client(self) -> Redis:
        """Raw Redis client — only for infrastructure wiring (e.g. FastAPICache)."""
        return self._redis

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self._redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def close(self) -> None:
        await self._redis.aclose()
