import asyncio
from decimal import Decimal

import eth_account
from eth_account.signers.local import LocalAccount
from hyperliquid.exchange import Exchange

from src.config import settings
from src.domain.services.exchange_client import IExchangeClient


class HyperliquidExchangeClient(IExchangeClient):
    """Per-wallet exchange client. Private key must be provided by the caller.

    The key is kept only for the lifetime of this object and never persisted here.
    """

    def __init__(self, private_key: str, account_address: str | None = None):
        wallet: LocalAccount = eth_account.Account.from_key(private_key)
        self._exchange = Exchange(
            wallet=wallet,
            base_url=settings.hyperliquid_base_url,
            account_address=account_address,
        )

    async def place_limit_order(
        self,
        symbol: str,
        is_buy: bool,
        sz: Decimal,
        limit_px: Decimal,
        reduce_only: bool = False,
    ) -> dict:
        result = await asyncio.to_thread(
            self._exchange.order,
            symbol,
            is_buy,
            float(sz),
            float(limit_px),
            {"limit": {"tif": "Gtc"}},
            reduce_only,
        )
        return result

    async def place_market_order(
        self,
        symbol: str,
        is_buy: bool,
        sz: Decimal,
        slippage: float = 0.05,
    ) -> dict:
        result = await asyncio.to_thread(
            self._exchange.market_open,
            symbol,
            is_buy,
            float(sz),
            None,
            slippage,
        )
        return result

    async def cancel_order(self, symbol: str, oid: int) -> dict:
        return await asyncio.to_thread(self._exchange.cancel, symbol, oid)

    async def cancel_all_orders(self, symbol: str) -> dict:
        open_orders = await asyncio.to_thread(
            self._exchange.info.open_orders,
            self._exchange.wallet.address,
        )
        cancels = [
            {"coin": o["coin"], "oid": o["oid"]}
            for o in open_orders
            if o["coin"] == self._exchange.info.name_to_coin.get(symbol, symbol)
        ]
        if not cancels:
            return {"status": "ok", "message": "no open orders"}
        return await asyncio.to_thread(self._exchange.bulk_cancel, cancels)

    async def close_position(
        self,
        symbol: str,
        close_pct: Decimal,
        slippage: float = 0.05,
    ) -> dict | None:
        state = await asyncio.to_thread(
            self._exchange.info.user_state,
            self._exchange.wallet.address,
        )
        for pos in state["assetPositions"]:
            item = pos["position"]
            if item["coin"] != symbol:
                continue
            szi = Decimal(item["szi"])
            if szi == 0:
                return None
            sz = abs(szi) * close_pct / 100
            is_buy = szi < 0
            px = await asyncio.to_thread(
                self._exchange._slippage_price, symbol, is_buy, slippage
            )
            return await asyncio.to_thread(
                self._exchange.order,
                symbol,
                is_buy,
                float(sz),
                float(px),
                {"limit": {"tif": "Ioc"}},
                True,
            )
        return None

    async def approve_agent(self, name: str | None = None) -> tuple[dict, str]:
        return await asyncio.to_thread(self._exchange.approve_agent, name)
