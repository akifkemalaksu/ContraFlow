from decimal import Decimal
from typing import Annotated

from eth_utils import is_address, to_checksum_address
from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import AfterValidator

from src.domain.enums import AccountType


def _to_checksum(v: str) -> str:
    if not is_address(v):
        raise ValueError(f"Invalid Ethereum address: {v!r}")
    return to_checksum_address(v)


ChecksumAddress = Annotated[str, AfterValidator(_to_checksum)]


class InitiateAgentWalletRequest(BaseModel):
    agent_name: str


class CompleteAgentWalletRequest(BaseModel):
    agent_address: ChecksumAddress
    nonce: int
    signature: str  # 0x-prefixed 65-byte hex from eth_signTypedData_v4


class CompleteAgentWalletResponse(BaseModel):
    status: str
    response: dict


class EIP712Package(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    domain: dict
    types: dict
    primary_type: str = Field(serialization_alias="primaryType")
    message: dict


class InitiateAgentWalletResponse(BaseModel):
    agent_address: str
    signer_address: str
    eip712: EIP712Package


class AddMasterWalletRequest(BaseModel):
    address: ChecksumAddress
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


class AgentWalletItem(BaseModel):
    address: str
    name: str
    is_active: bool | None
    is_approved_on_hl: bool
    valid_until: int | None
    last_nonce: int | None


class AgentWalletsResponse(BaseModel):
    master_address: str
    agents: list[AgentWalletItem]
