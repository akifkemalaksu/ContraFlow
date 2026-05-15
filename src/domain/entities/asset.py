from dataclasses import dataclass


@dataclass
class Asset:
    asset_id: int  # PK, Hyperliquid internal ID (perp: 0,1.. spot: 10000+)
    symbol: str
    sz_decimals: int  # rounding precision for order size
    is_perp: bool
