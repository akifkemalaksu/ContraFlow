from pydantic import BaseModel


class AssetResponse(BaseModel):
    asset_id: int
    symbol: str
    sz_decimals: int
    is_perp: bool


class SyncResultResponse(BaseModel):
    synced: int
