import asyncio
import logging
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from src.domain.entities.copy_strategy import CopyStrategy
from src.domain.entities.cross_asset_trigger import CrossAssetTrigger
from src.domain.entities.fill import Fill
from src.domain.entities.order import Order
from src.domain.enums import Direction, Operator, OrderStatus
from src.domain.repositories.copy_strategy_repository import ICopyStrategyRepository
from src.domain.repositories.cross_asset_trigger_repository import ICrossAssetTriggerRepository
from src.domain.repositories.fill_repository import IFillRepository
from src.domain.repositories.order_repository import IOrderRepository
from src.domain.services.exchange_client import IExchangeClientFactory
from src.infrastructure.hyperliquid.client import HyperliquidInfoClient
from src.infrastructure.hyperliquid.ws_manager import HyperliquidWSManager

logger = logging.getLogger(__name__)


class CopyTradingEngine:
    """Watches target wallets via WebSocket and mirrors fills onto user wallets.

    Lifecycle: call start() once, then stop() to clean up.
    """

    def __init__(
        self,
        strategy_repo: ICopyStrategyRepository,
        order_repo: IOrderRepository,
        fill_repo: IFillRepository,
        trigger_repo: ICrossAssetTriggerRepository,
        info_client: HyperliquidInfoClient,
        ws_manager: HyperliquidWSManager,
        private_key_resolver: Callable[[str], str | None],
        exchange_factory: IExchangeClientFactory,
    ):
        self._strategy_repo = strategy_repo
        self._order_repo = order_repo
        self._fill_repo = fill_repo
        self._trigger_repo = trigger_repo
        self._info = info_client
        self._ws = ws_manager
        # resolver maps user_wallet address → private key (fetched from secrets manager)
        self._resolve_key = private_key_resolver
        self._exchange_factory = exchange_factory
        self._loop: asyncio.AbstractEventLoop | None = None
        self._mid_prices: dict[str, Decimal] = {}

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
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
                asyncio.run_coroutine_threadsafe(
                    self._process_fill(target_wallet, raw_fill),
                    self._loop,
                )
        return handler

    async def _process_fill(self, target_wallet: str, raw_fill: dict) -> None:
        coin: str = raw_fill["coin"]
        is_buy: bool = raw_fill["side"] == "B"
        px = Decimal(str(raw_fill["px"]))
        sz = Decimal(str(raw_fill["sz"]))
        oid: int = raw_fill["oid"]
        timestamp: int = raw_fill["time"]

        strategies = await self._strategy_repo.get_by_target_wallet(target_wallet)
        if not strategies:
            return

        for strategy in strategies:
            await self._execute_strategy(strategy, coin, is_buy, px, sz, oid, timestamp)

    async def _execute_strategy(
        self,
        strategy: CopyStrategy,
        coin: str,
        target_is_buy: bool,
        target_px: Decimal,
        target_sz: Decimal,
        target_oid: int,
        timestamp: int,
    ) -> None:
        private_key = self._resolve_key(strategy.user_wallet)
        if not private_key:
            logger.warning("No private key for wallet %s — skipping", strategy.user_wallet)
            return

        # Apply direction
        is_buy = target_is_buy if strategy.direction == Direction.FORWARD else not target_is_buy

        # Apply copy ratio
        sz = (target_sz * strategy.copy_ratio).quantize(Decimal("0.0001"))

        # Apply markup: increase ask price when buying, decrease when selling
        if strategy.markup_pct != 0:
            factor = 1 + strategy.markup_pct / 100 if is_buy else 1 - strategy.markup_pct / 100
            limit_px = (target_px * Decimal(str(factor))).quantize(Decimal("0.00001"))
        else:
            limit_px = target_px

        # Check cross-asset triggers before placing the order
        await self._check_triggers(strategy, private_key)

        exchange = self._exchange_factory.create(private_key, account_address=strategy.user_wallet)
        try:
            result = await exchange.place_limit_order(coin, is_buy, sz, limit_px)
        except Exception:
            logger.exception(
                "Failed to place copy order for strategy %s on %s", strategy.id, coin
            )
            return

        # Persist order
        statuses = result.get("response", {}).get("data", {}).get("statuses", [{}])
        oid_new = statuses[0].get("resting", {}).get("oid") if statuses else None
        if oid_new:
            order = Order(
                oid=oid_new,
                owner_address=strategy.user_wallet,
                asset_id=self._info._info.coin_to_asset.get(coin, -1),
                is_buy=is_buy,
                limit_px=limit_px,
                sz=sz,
                status=OrderStatus.OPEN,
                strategy_id=strategy.id,
            )
            await self._order_repo.save(order)

        logger.info(
            "Copied fill from %s → %s: %s %s @ %s (strategy=%s)",
            strategy.target_wallet, strategy.user_wallet, "BUY" if is_buy else "SELL", sz, limit_px, strategy.id,
        )

    async def _check_triggers(self, strategy: CopyStrategy, private_key: str) -> None:
        if not strategy.id:
            return
        triggers = await self._trigger_repo.get_by_strategy(strategy.id)
        for trigger in triggers:
            await self._evaluate_trigger(trigger, strategy, private_key)

    async def _evaluate_trigger(
        self,
        trigger: CrossAssetTrigger,
        strategy: CopyStrategy,
        private_key: str,
    ) -> None:
        ref_symbol = self._asset_id_to_symbol(trigger.ref_asset_id)
        if not ref_symbol:
            return
        current_px = self._mid_prices.get(ref_symbol)
        if current_px is None:
            return

        fired = (
            (trigger.operator == Operator.GT and current_px > trigger.threshold_px)
            or (trigger.operator == Operator.LT and current_px < trigger.threshold_px)
        )
        if not fired:
            return

        logger.info(
            "CrossAssetTrigger %s fired: %s %s %s (current=%s) — closing %s%% of position",
            trigger.id, ref_symbol, trigger.operator, trigger.threshold_px, current_px, trigger.close_pct,
        )
        exchange = self._exchange_factory.create(private_key, account_address=strategy.user_wallet)
        symbol = self._asset_id_to_symbol(
            self._info._info.coin_to_asset.get(strategy.target_wallet, trigger.ref_asset_id)
        )
        if symbol:
            try:
                await exchange.close_position(symbol, trigger.close_pct)
            except Exception:
                logger.exception("Failed to close position for trigger %s", trigger.id)

    def _asset_id_to_symbol(self, asset_id: int) -> str | None:
        for coin, aid in self._info._info.coin_to_asset.items():
            if aid == asset_id:
                return coin
        return None
