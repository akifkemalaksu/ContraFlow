import asyncio
import logging

from src.infrastructure.hyperliquid.client import HyperliquidInfoClient
from src.infrastructure.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="hl.sync_assets", bind=True, max_retries=3)
def sync_assets(self):
    """Fetch all perp and spot assets from Hyperliquid and upsert into DB."""
    from src.infrastructure.database.repositories.asset_repository import AssetRepository
    from src.infrastructure.database.session import AsyncSessionFactory

    async def _run():
        client = HyperliquidInfoClient(skip_ws=True)
        assets = await client.get_all_assets()
        async with AsyncSessionFactory() as session:
            repo = AssetRepository(session)
            for asset in assets:
                await repo.upsert(asset)
            await session.commit()
        logger.info("Synced %d assets from Hyperliquid", len(assets))

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.exception("sync_assets failed")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="hl.sync_fills", bind=True, max_retries=3)
def sync_fills(self, address: str):
    """Fetch all historical fills for an account and persist missing ones."""
    from src.infrastructure.database.repositories.fill_repository import FillRepository
    from src.infrastructure.database.repositories.order_repository import OrderRepository
    from src.infrastructure.database.session import AsyncSessionFactory

    async def _run():
        client = HyperliquidInfoClient(skip_ws=True)
        fills = await client.get_user_fills(address)
        async with AsyncSessionFactory() as session:
            order_repo = OrderRepository(session)
            fill_repo = FillRepository(session)
            for fill in fills:
                existing = await fill_repo.get_by_id(fill.fill_id)
                if existing:
                    continue
                # ensure parent order exists (best-effort)
                order = await order_repo.get_by_oid(fill.oid)
                if not order:
                    logger.debug("Parent order %d not found for fill %s", fill.oid, fill.fill_id)
                    continue
                await fill_repo.save(fill)
            await session.commit()
        logger.info("Synced fills for %s", address)

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.exception("sync_fills failed for %s", address)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="hl.sync_open_orders")
def sync_open_orders(address: str):
    """Snapshot open orders from Hyperliquid and update DB statuses."""
    from src.infrastructure.database.repositories.order_repository import OrderRepository
    from src.infrastructure.database.session import AsyncSessionFactory
    from src.domain.enums import OrderStatus

    async def _run():
        client = HyperliquidInfoClient(skip_ws=True)
        open_orders = await client.get_open_orders(address)
        open_oids = {o.oid for o in open_orders}

        async with AsyncSessionFactory() as session:
            repo = OrderRepository(session)
            db_open = await repo.get_by_status(address, OrderStatus.OPEN)
            for order in db_open:
                if order.oid not in open_oids:
                    await repo.update_status(order.oid, OrderStatus.CANCELED)
            await session.commit()
        logger.info("Synced open orders for %s", address)

    asyncio.run(_run())
