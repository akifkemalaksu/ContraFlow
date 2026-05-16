import asyncio
import logging
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from src.application.services.copy_trading import CopyTradingService
from src.infrastructure.hyperliquid.client import HyperliquidInfoClient
from src.infrastructure.hyperliquid.ws_manager import HyperliquidWSManager

logger = logging.getLogger(__name__)


class CopyTradingEngine:
    """WS adapter: subscribes to Hyperliquid fills and mid-price feeds,
    delegates all business logic to CopyTradingService.

    Lifecycle: call start() once, then stop() to clean up.
    """

    def __init__(
        self,
        service: CopyTradingService,
        info_client: HyperliquidInfoClient,
        ws_manager: HyperliquidWSManager,
    ) -> None:
        self._service = service
        self._info = info_client
        self._ws = ws_manager
        self._loop: asyncio.AbstractEventLoop | None = None
        self._mid_prices: dict[str, Decimal] = {}
        self._symbol_map: dict[int, str] = {}

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._symbol_map = {aid: coin for coin, aid in self._info._info.coin_to_asset.items()}
        self._ws.subscribe_all_mids(self._on_mids_update)
        logger.info("CopyTradingEngine started")

    def stop(self) -> None:
        self._ws.unsubscribe_all()
        logger.info("CopyTradingEngine stopped")

    async def watch_target(self, target_wallet: str) -> None:
        self._ws.subscribe_user_fills(target_wallet, self._make_fill_handler(target_wallet))
        logger.info("Watching target wallet %s", target_wallet)

    async def unwatch_target(self, target_wallet: str) -> None:
        self._ws.unsubscribe_user_fills(target_wallet)
        logger.info("Stopped watching target wallet %s", target_wallet)

    def _on_mids_update(self, data: Any) -> None:
        if isinstance(data, dict) and "data" in data:
            for coin, px in data["data"].items():
                self._mid_prices[coin] = Decimal(str(px))

    def _make_fill_handler(self, target_wallet: str) -> Callable[[Any], None]:
        def handler(data: Any) -> None:
            if self._loop is None:
                return
            fills = data.get("data", {}).get("fills", []) if isinstance(data, dict) else []
            for raw_fill in fills:
                coin: str = raw_fill["coin"]
                asyncio.run_coroutine_threadsafe(
                    self._service.process_fill(
                        target_wallet=target_wallet,
                        coin=coin,
                        target_is_buy=raw_fill["side"] == "B",
                        target_px=Decimal(str(raw_fill["px"])),
                        target_sz=Decimal(str(raw_fill["sz"])),
                        target_oid=raw_fill["oid"],
                        asset_id=self._info._info.coin_to_asset.get(coin, -1),
                        mid_prices=self._mid_prices,
                        symbol_map=self._symbol_map,
                    ),
                    self._loop,
                )

        return handler
