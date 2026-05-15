from dataclasses import dataclass

from decimal import Decimal

from src.domain.enums import OrderStatus


@dataclass
class Order:
    oid: int  # PK BIGINT, assigned by Hyperliquid
    owner_address: str  # FK -> accounts.address
    asset_id: int  # FK -> assets.asset_id
    is_buy: bool
    limit_px: Decimal
    sz: Decimal
    status: OrderStatus = OrderStatus.OPEN
    strategy_id: int | None = None  # FK -> copy_strategies.id, NULL if manual
