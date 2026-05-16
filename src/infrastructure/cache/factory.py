from redis.asyncio import from_url

from src.domain.services.cache import ICacheServiceFactory
from src.infrastructure.cache.redis_cache import RedisCacheService


class RedisCacheServiceFactory(ICacheServiceFactory):
    def __init__(self, redis_url: str):
        self._redis_url = redis_url

    def create(self) -> RedisCacheService:
        redis = from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        return RedisCacheService(redis)
