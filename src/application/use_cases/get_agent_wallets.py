from dataclasses import dataclass, field
from uuid import UUID

from src.domain.enums import AccountType
from src.domain.repositories.wallet_repository import IWalletRepository
from src.infrastructure.hyperliquid.client import HyperliquidInfoClient


@dataclass
class GetAgentWalletsDTO:
    master_wallet_address: str
    user_id: UUID


@dataclass
class AgentWalletInfo:
    address: str
    name: str
    is_active: bool | None
    is_approved_on_hl: bool
    valid_until: int | None
    last_nonce: int | None


@dataclass
class GetAgentWalletsResult:
    master_address: str
    agents: list[AgentWalletInfo] = field(default_factory=list)


class GetAgentWalletsUseCase:
    def __init__(self, wallet_repo: IWalletRepository, hl_client: HyperliquidInfoClient) -> None:
        self._wallet_repo = wallet_repo
        self._hl_client = hl_client

    async def execute(self, dto: GetAgentWalletsDTO) -> GetAgentWalletsResult:
        master = await self._wallet_repo.get_by_address(dto.master_wallet_address)
        if not master or master.user_id != dto.user_id:
            raise PermissionError("Master wallet not found or does not belong to you")
        if master.account_type != AccountType.MASTER:
            raise PermissionError("Target wallet is not a master wallet")

        agent_wallets = await self._wallet_repo.get_by_master_wallet_address(dto.master_wallet_address)

        hl_agents = await self._hl_client.get_extra_agents(dto.master_wallet_address)
        hl_approved: dict[str, dict] = {a["address"].lower(): a for a in hl_agents}

        agents = [
            AgentWalletInfo(
                address=w.address,
                name=w.name,
                is_active=w.is_active,
                is_approved_on_hl=w.address.lower() in hl_approved,
                valid_until=hl_approved.get(w.address.lower(), {}).get("validUntil"),
                last_nonce=w.last_nonce,
            )
            for w in agent_wallets
        ]

        return GetAgentWalletsResult(master_address=dto.master_wallet_address, agents=agents)
