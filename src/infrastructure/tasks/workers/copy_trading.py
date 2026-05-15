import asyncio
import logging

from src.infrastructure.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="hl.start_copy_watch")
def start_copy_watch(target_wallet: str):
    """Subscribe to a target wallet's fills via WebSocket and mirror them.

    Runs in an asyncio event loop until the process is killed or the task
    is revoked. Intended to be a long-lived task (use Celery Canvas or a
    dedicated worker queue for long-running tasks).
    """
    from src.infrastructure.database.repositories.copy_strategy_repository import CopyStrategyRepository
    from src.infrastructure.database.repositories.cross_asset_trigger_repository import CrossAssetTriggerRepository
    from src.infrastructure.database.repositories.fill_repository import FillRepository
    from src.infrastructure.database.repositories.order_repository import OrderRepository
    from src.infrastructure.database.session import AsyncSessionFactory
    from src.infrastructure.hyperliquid.client import HyperliquidInfoClient
    from src.infrastructure.hyperliquid.copy_trading.engine import CopyTradingEngine
    from src.infrastructure.hyperliquid.ws_manager import HyperliquidWSManager

    async def _run():
        info_client = HyperliquidInfoClient()
        ws_manager = HyperliquidWSManager(info_client)

        async with AsyncSessionFactory() as session:
            engine = CopyTradingEngine(
                strategy_repo=CopyStrategyRepository(session),
                order_repo=OrderRepository(session),
                fill_repo=FillRepository(session),
                trigger_repo=CrossAssetTriggerRepository(session),
                info_client=info_client,
                ws_manager=ws_manager,
                private_key_resolver=_resolve_private_key,
            )
            loop = asyncio.get_running_loop()
            engine.start(loop)
            await engine.watch_target(target_wallet)
            logger.info("Copy watch started for %s — keeping alive", target_wallet)
            # Keep alive until task is revoked
            while True:
                await asyncio.sleep(30)

    asyncio.run(_run())


def _resolve_private_key(user_wallet: str) -> str | None:
    """Fetch the private key for a wallet from the secrets store.

    Replace this with your actual secrets backend (Vault, AWS Secrets Manager, etc.).
    """
    import os
    env_key = f"HL_PRIVATE_KEY_{user_wallet.upper().replace('0X', '')}"
    return os.environ.get(env_key)


@celery_app.task(name="hl.stop_copy_watch")
def stop_copy_watch(target_wallet: str):
    """Revoke all active copy_watch tasks for a given target wallet."""
    from celery.result import AsyncResult
    inspect = celery_app.control.inspect()
    active = inspect.active() or {}
    for worker, tasks in active.items():
        for task in tasks:
            if task["name"] == "hl.start_copy_watch":
                args = task.get("args", [])
                if args and args[0] == target_wallet:
                    celery_app.control.revoke(task["id"], terminate=True)
                    logger.info("Revoked copy_watch task %s for %s", task["id"], target_wallet)
