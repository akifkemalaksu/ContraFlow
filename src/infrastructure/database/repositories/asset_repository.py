from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.asset import Asset
from src.domain.repositories.asset_repository import IAssetRepository
from src.infrastructure.database.models.asset_model import AssetModel


def _to_domain(model: AssetModel) -> Asset:
    return Asset(
        asset_id=model.asset_id,
        symbol=model.symbol,
        sz_decimals=model.sz_decimals,
        is_perp=model.is_perp,
    )


class AssetRepository(IAssetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, asset_id: int) -> Asset | None:
        result = await self._session.execute(
            select(AssetModel).where(AssetModel.asset_id == asset_id)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def get_by_symbol(self, symbol: str) -> Asset | None:
        result = await self._session.execute(
            select(AssetModel).where(AssetModel.symbol == symbol)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def get_all(self) -> list[Asset]:
        result = await self._session.execute(select(AssetModel))
        return [_to_domain(m) for m in result.scalars().all()]

    async def save(self, asset: Asset) -> Asset:
        model = AssetModel(
            asset_id=asset.asset_id,
            symbol=asset.symbol,
            sz_decimals=asset.sz_decimals,
            is_perp=asset.is_perp,
        )
        self._session.add(model)
        await self._session.flush()
        return asset

    async def upsert(self, asset: Asset) -> Asset:
        stmt = (
            insert(AssetModel)
            .values(
                asset_id=asset.asset_id,
                symbol=asset.symbol,
                sz_decimals=asset.sz_decimals,
                is_perp=asset.is_perp,
            )
            .on_conflict_do_update(
                index_elements=["asset_id"],
                set_={"symbol": asset.symbol, "sz_decimals": asset.sz_decimals},
            )
        )
        await self._session.execute(stmt)
        return asset
