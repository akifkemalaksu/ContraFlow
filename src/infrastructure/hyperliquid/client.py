import asyncio
from decimal import Decimal
from functools import lru_cache

from hyperliquid.info import Info

from src.config import settings
from src.domain.entities.asset import Asset
from src.domain.entities.fill import Fill
from src.domain.entities.order import Order
from src.domain.enums import OrderStatus


@lru_cache(maxsize=1)
def get_info_client(skip_ws: bool = False) -> Info:
    return Info(base_url=settings.hyperliquid_base_url, skip_ws=skip_ws)


class HyperliquidInfoClient:
    def __init__(self, skip_ws: bool = False):
        self._info = get_info_client(skip_ws)

    async def get_all_assets(self) -> list[Asset]:
        meta, ctxs = await asyncio.to_thread(self._info.meta_and_asset_ctxs)
        assets: list[Asset] = []
        for i, item in enumerate(meta["universe"]):
            assets.append(Asset(
                asset_id=i,
                symbol=item["name"],
                sz_decimals=item["szDecimals"],
                is_perp=True,
            ))
        spot_meta, spot_ctxs = await asyncio.to_thread(self._info.spot_meta_and_asset_ctxs)
        token_by_index = {t["index"]: t for t in spot_meta["tokens"]}
        for spot_info in spot_meta["universe"]:
            base = token_by_index[spot_info["tokens"][0]]
            assets.append(Asset(
                asset_id=spot_info["index"] + 10000,
                symbol=f"{base['name']}/USDC",
                sz_decimals=base["szDecimals"],
                is_perp=False,
            ))
        return assets

    async def get_all_mids(self) -> dict[str, Decimal]:
        raw: dict = await asyncio.to_thread(self._info.all_mids)
        return {coin: Decimal(px) for coin, px in raw.items()}

    async def get_order_book(self, symbol: str) -> dict:
        return await asyncio.to_thread(self._info.l2_snapshot, symbol)

    async def get_user_fills(self, address: str) -> list[Fill]:
        raw = await asyncio.to_thread(self._info.user_fills, address)
        fills: list[Fill] = []
        for r in raw:
            fills.append(Fill(
                oid=r["oid"],
                owner_address=address,
                px=Decimal(r["px"]),
                sz=Decimal(r["sz"]),
                timestamp=r["time"],
            ))
        return fills

    async def get_open_orders(self, address: str) -> list[Order]:
        raw = await asyncio.to_thread(self._info.open_orders, address)
        orders: list[Order] = []
        for r in raw:
            asset_id = self._info.coin_to_asset.get(r["coin"], -1)
            orders.append(Order(
                oid=r["oid"],
                owner_address=address,
                asset_id=asset_id,
                is_buy=r["side"] == "B",
                limit_px=Decimal(r["limitPx"]),
                sz=Decimal(r["sz"]),
                status=OrderStatus.OPEN,
            ))
        return orders

    async def get_user_state(self, address: str) -> dict:
        return await asyncio.to_thread(self._info.user_state, address)

    def subscribe(self, subscription: dict, callback) -> int:
        return self._info.subscribe(subscription, callback)

    def unsubscribe(self, subscription: dict, subscription_id: int) -> bool:
        return self._info.unsubscribe(subscription, subscription_id)

    def disconnect(self) -> None:
        self._info.disconnect_websocket()
