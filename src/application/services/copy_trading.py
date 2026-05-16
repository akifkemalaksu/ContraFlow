import logging
from collections.abc import Callable
from decimal import Decimal

from src.domain.entities.copy_strategy import CopyStrategy
from src.domain.entities.order import Order
from src.domain.enums import OrderStatus
from src.domain.repositories.copy_strategy_repository import ICopyStrategyRepository
from src.domain.repositories.cross_asset_trigger_repository import ICrossAssetTriggerRepository
from src.domain.repositories.order_repository import IOrderRepository
from src.domain.services.exchange_client import IExchangeClientFactory

logger = logging.getLogger(__name__)


class CopyTradingService:
    def __init__(
        self,
        strategy_repo: ICopyStrategyRepository,
        order_repo: IOrderRepository,
        trigger_repo: ICrossAssetTriggerRepository,
        exchange_factory: IExchangeClientFactory,
        key_resolver: Callable[[str], str | None],
    ) -> None:
        self._strategy_repo = strategy_repo
        self._order_repo = order_repo
        self._trigger_repo = trigger_repo
        self._exchange_factory = exchange_factory
        self._resolve_key = key_resolver

    async def process_fill(
        self,
        target_wallet: str,
        coin: str,
        target_is_buy: bool,
        target_px: Decimal,
        target_sz: Decimal,
        target_oid: int,
        asset_id: int,
        mid_prices: dict[str, Decimal],
        symbol_map: dict[int, str],
    ) -> None:
        strategies = await self._strategy_repo.get_by_target_wallet(target_wallet)
        for strategy in strategies:
            await self._execute_strategy(
                strategy, coin, target_is_buy, target_px, target_sz, asset_id,
                mid_prices, symbol_map,
            )

    async def _execute_strategy(
        self,
        strategy: CopyStrategy,
        coin: str,
        target_is_buy: bool,
        target_px: Decimal,
        target_sz: Decimal,
        asset_id: int,
        mid_prices: dict[str, Decimal],
        symbol_map: dict[int, str],
    ) -> None:
        private_key = self._resolve_key(strategy.user_wallet)
        if not private_key:
            logger.warning("No private key for wallet %s — skipping", strategy.user_wallet)
            return

        is_buy, sz, limit_px = strategy.compute_order(target_is_buy, target_sz, target_px)

        await self._check_triggers(strategy, private_key, mid_prices, symbol_map)

        exchange = self._exchange_factory.create(private_key, account_address=strategy.user_wallet)
        try:
            result = await exchange.place_limit_order(coin, is_buy, sz, limit_px)
        except Exception:
            logger.exception("Failed to place copy order for strategy %s on %s", strategy.id, coin)
            return

        statuses = result.get("response", {}).get("data", {}).get("statuses", [{}])
        oid_new = statuses[0].get("resting", {}).get("oid") if statuses else None
        if oid_new:
            order = Order(
                oid=oid_new,
                owner_address=strategy.user_wallet,
                asset_id=asset_id,
                is_buy=is_buy,
                limit_px=limit_px,
                sz=sz,
                status=OrderStatus.OPEN,
                strategy_id=strategy.id,
            )
            await self._order_repo.save(order)

        logger.info(
            "Copied fill from %s → %s: %s %s @ %s (strategy=%s)",
            strategy.target_wallet, strategy.user_wallet,
            "BUY" if is_buy else "SELL", sz, limit_px, strategy.id,
        )

    async def _check_triggers(
        self,
        strategy: CopyStrategy,
        private_key: str,
        mid_prices: dict[str, Decimal],
        symbol_map: dict[int, str],
    ) -> None:
        if not strategy.id:
            return
        triggers = await self._trigger_repo.get_by_strategy(strategy.id)
        for trigger in triggers:
            ref_symbol = symbol_map.get(trigger.ref_asset_id)
            if not ref_symbol:
                continue
            current_px = mid_prices.get(ref_symbol)
            if current_px is None or not trigger.is_fired(current_px):
                continue

            logger.info(
                "CrossAssetTrigger %s fired: %s %s %s (current=%s) — closing %s%% of position",
                trigger.id, ref_symbol, trigger.operator, trigger.threshold_px,
                current_px, trigger.close_pct,
            )
            close_symbol = symbol_map.get(trigger.ref_asset_id)
            if not close_symbol:
                continue
            exchange = self._exchange_factory.create(private_key, account_address=strategy.user_wallet)
            try:
                await exchange.close_position(close_symbol, trigger.close_pct)
            except Exception:
                logger.exception("Failed to close position for trigger %s", trigger.id)
