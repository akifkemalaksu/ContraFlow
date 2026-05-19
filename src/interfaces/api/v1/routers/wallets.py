from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.add_master_wallet import AddMasterWalletDTO, AddMasterWalletUseCase
from src.application.use_cases.complete_agent_wallet import CompleteAgentWalletDTO, CompleteAgentWalletUseCase
from src.application.use_cases.get_wallet_info import GetWalletInfoDTO, GetWalletInfoUseCase
from src.application.use_cases.initiate_agent_wallet import InitiateAgentWalletDTO, InitiateAgentWalletUseCase
from src.domain.entities.user import User
from src.infrastructure.database.session import get_db_session
from src.interfaces.api.v1.dependencies.auth import require_permission
from src.interfaces.api.v1.dependencies.composition import (
    get_add_master_wallet_use_case,
    get_complete_agent_wallet_use_case,
    get_initiate_agent_wallet_use_case,
    get_wallet_info_use_case,
)
from src.interfaces.schemas.wallet_schemas import (
    AddMasterWalletRequest,
    CompleteAgentWalletRequest,
    CompleteAgentWalletResponse,
    EIP712Package,
    InitiateAgentWalletRequest,
    InitiateAgentWalletResponse,
    MarginSummary,
    Position,
    WalletInfoResponse,
    WalletResponse,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def add_master_wallet(
    body: AddMasterWalletRequest,
    current_user: User = require_permission("wallets:write"),
    use_case: AddMasterWalletUseCase = Depends(get_add_master_wallet_use_case),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        wallet = await use_case.execute(AddMasterWalletDTO(address=body.address, name=body.name, user_id=current_user.id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    await session.commit()
    return WalletResponse(address=wallet.address, name=wallet.name, account_type=wallet.account_type, is_active=wallet.is_active)


@router.post("/{master_address}/agent", response_model=InitiateAgentWalletResponse, status_code=status.HTTP_201_CREATED)
async def initiate_agent_wallet(
    master_address: str,
    body: InitiateAgentWalletRequest,
    current_user: User = require_permission("wallets:write"),
    use_case: InitiateAgentWalletUseCase = Depends(get_initiate_agent_wallet_use_case),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        result = await use_case.execute(
            InitiateAgentWalletDTO(
                master_wallet_address=master_address,
                agent_name=body.agent_name,
                user_id=current_user.id,
            )
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await session.commit()
    return InitiateAgentWalletResponse(
        agent_address=result.agent_address,
        eip712=EIP712Package(
            domain=result.eip712.domain,
            types=result.eip712.types,
            primary_type=result.eip712.primary_type,
            message=result.eip712.message,
        ),
    )


@router.post("/{master_address}/agent/approve", response_model=CompleteAgentWalletResponse)
async def complete_agent_wallet(
    master_address: str,
    body: CompleteAgentWalletRequest,
    current_user: User = require_permission("wallets:write"),
    use_case: CompleteAgentWalletUseCase = Depends(get_complete_agent_wallet_use_case),
):
    try:
        result = await use_case.execute(
            CompleteAgentWalletDTO(
                master_wallet_address=master_address,
                agent_address=body.agent_address,
                nonce=body.nonce,
                signature=body.signature,
                user_id=current_user.id,
            )
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return CompleteAgentWalletResponse(status=result.status, response=result.response)


@router.get("/{address}/info", response_model=WalletInfoResponse)
async def get_wallet_info(
    address: str,
    current_user: User = require_permission("wallets:read"),
    use_case: GetWalletInfoUseCase = Depends(get_wallet_info_use_case),
):
    try:
        raw = await use_case.execute(GetWalletInfoDTO(address=address, user_id=current_user.id))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    def parse_margin(m: dict) -> MarginSummary:
        return MarginSummary(
            account_value=Decimal(m["accountValue"]),
            total_margin_used=Decimal(m["totalMarginUsed"]),
            total_ntl_pos=Decimal(m["totalNtlPos"]),
            total_raw_usd=Decimal(m["totalRawUsd"]),
        )

    positions = [
        Position(
            coin=p["position"]["coin"],
            entry_px=Decimal(p["position"]["entryPx"]) if p["position"].get("entryPx") else None,
            leverage=p["position"]["leverage"],
            liquidation_px=Decimal(p["position"]["liquidationPx"]) if p["position"].get("liquidationPx") else None,
            margin_used=Decimal(p["position"]["marginUsed"]),
            position_value=Decimal(p["position"]["positionValue"]),
            return_on_equity=Decimal(p["position"]["returnOnEquity"]),
            szi=Decimal(p["position"]["szi"]),
            unrealized_pnl=Decimal(p["position"]["unrealizedPnl"]),
        )
        for p in raw.get("assetPositions", [])
    ]

    return WalletInfoResponse(
        margin_summary=parse_margin(raw["marginSummary"]),
        cross_margin_summary=parse_margin(raw["crossMarginSummary"]),
        cross_maintenance_margin_used=Decimal(raw["crossMaintenanceMarginUsed"]),
        withdrawable=Decimal(raw["withdrawable"]),
        asset_positions=positions,
    )
