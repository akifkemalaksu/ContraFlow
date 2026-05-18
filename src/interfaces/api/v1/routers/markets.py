from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.infrastructure.database.repositories.asset_repository import AssetRepository
from src.infrastructure.database.session import get_db_session
from src.interfaces.api.v1.dependencies.auth import require_permission
from src.interfaces.schemas.market_schemas import AssetResponse

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("", response_model=list[AssetResponse])
async def list_markets(
    is_perp: bool | None = None,
    _: User = require_permission("trading:read"),
    session: AsyncSession = Depends(get_db_session),
):
    repo = AssetRepository(session)
    assets = await repo.get_all()
    if is_perp is not None:
        assets = [a for a in assets if a.is_perp == is_perp]
    return [AssetResponse(asset_id=a.asset_id, symbol=a.symbol, sz_decimals=a.sz_decimals, is_perp=a.is_perp) for a in assets]


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_market(
    asset_id: int,
    _: User = require_permission("trading:read"),
    session: AsyncSession = Depends(get_db_session),
):
    repo = AssetRepository(session)
    asset = await repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return AssetResponse(asset_id=asset.asset_id, symbol=asset.symbol, sz_decimals=asset.sz_decimals, is_perp=asset.is_perp)


