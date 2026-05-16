import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.config import settings
from src.infrastructure.cache.factory import RedisCacheServiceFactory
from src.infrastructure.database.seed import run_seed
from src.infrastructure.database.session import AsyncSessionFactory
from src.interfaces.api.middleware.logging import LoggingMiddleware
from src.interfaces.api.v1.routers import auth, api_keys, health

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

_cache_factory = RedisCacheServiceFactory(settings.REDIS_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache = _cache_factory.create()
    FastAPICache.init(RedisBackend(cache.client), prefix="contraflow:")
    async with AsyncSessionFactory() as session:
        await run_seed(session)
    yield
    await cache.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(api_keys.router, prefix="/api/v1")

    return app


app = create_app()
