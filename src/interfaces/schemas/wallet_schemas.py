from decimal import Decimal

from pydantic import BaseModel

from src.domain.enums import AccountType


class InitiateAgentWalletRequest(BaseModel):
    agent_name: str


class EIP712Package(BaseModel):
    domain: dict
    types: dict
    primary_type: str
    message: dict


class InitiateAgentWalletResponse(BaseModel):
    agent_address: str
    eip712: EIP712Package


class AddMasterWalletRequest(BaseModel):
    address: str
    name: str


class WalletResponse(BaseModel):
    address: str
    name: str
    account_type: AccountType
    is_active: bool


class MarginSummary(BaseModel):
    account_value: Decimal
    total_margin_used: Decimal
    total_ntl_pos: Decimal
    total_raw_usd: Decimal


class Position(BaseModel):
    coin: str
    entry_px: Decimal | None
    leverage: dict
    liquidation_px: Decimal | None
    margin_used: Decimal
    position_value: Decimal
    return_on_equity: Decimal
    szi: Decimal
    unrealized_pnl: Decimal


class WalletInfoResponse(BaseModel):
    margin_summary: MarginSummary
    cross_margin_summary: MarginSummary
    cross_maintenance_margin_used: Decimal
    withdrawable: Decimal
    asset_positions: list[Position]
