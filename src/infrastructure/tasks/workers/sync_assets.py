import asyncio
import logging

from src.infrastructure.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="hl.sync_assets", bind=True, max_retries=3)
def sync_assets(self):
    """Fetch all perp and spot assets from Hyperliquid and upsert into DB."""
    from src.infrastructure.database.repositories.asset_repository import AssetRepository
    from src.infrastructure.database.session import AsyncSessionFactory
    from src.infrastructure.hyperliquid.client import HyperliquidInfoClient

    async def _run() -> int:
        client = HyperliquidInfoClient(skip_ws=True)
        assets = await client.get_all_assets()
        async with AsyncSessionFactory() as session:
            repo = AssetRepository(session)
            for asset in assets:
                await repo.upsert(asset)
            await session.commit()
        return len(assets)

    try:
        count = asyncio.run(_run())
        logger.info("Synced %d assets from Hyperliquid", count)
        return {"synced": count}
    except Exception as exc:
        logger.exception("sync_assets failed")
        raise self.retry(exc=exc, countdown=60)
