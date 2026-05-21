from dataclasses import dataclass
from uuid import UUID

from src.config import settings
from src.domain.enums import AccountType
from src.domain.repositories.wallet_repository import IWalletRepository
from src.infrastructure.hyperliquid.exchange_api import HyperliquidExchangeAPI
from src.infrastructure.hyperliquid.signing_helpers import (
    build_approve_agent_post_action,
    split_eip712_signature,
)


@dataclass
class CompleteAgentWalletDTO:
    master_wallet_address: str
    agent_address: str
    nonce: int
    signature: str  # 0x-prefixed 65-byte hex from eth_signTypedData_v4
    user_id: UUID


@dataclass
class CompleteAgentWalletResult:
    status: str
    response: dict


class CompleteAgentWalletUseCase:
    def __init__(self, wallet_repo: IWalletRepository, exchange_api: HyperliquidExchangeAPI) -> None:
        self._wallet_repo = wallet_repo
        self._exchange_api = exchange_api

    async def execute(self, dto: CompleteAgentWalletDTO) -> CompleteAgentWalletResult:
        master = await self._wallet_repo.get_by_address(dto.master_wallet_address)
        if not master or master.user_id != dto.user_id:
            raise PermissionError("Master wallet not found")
        if master.account_type != AccountType.MASTER:
            raise ValueError("Target wallet is not a master wallet")

        agent = await self._wallet_repo.get_by_address(dto.agent_address)
        if not agent or agent.user_id != dto.user_id:
            raise PermissionError("Agent wallet not found")
        if agent.account_type != AccountType.AGENT:
            raise ValueError("Wallet is not an agent wallet")
        if agent.master_wallet_address != dto.master_wallet_address:
            raise ValueError("Agent wallet does not belong to this master wallet")
        if agent.last_nonce != dto.nonce:
            raise ValueError("Nonce mismatch — use the nonce returned from the initiate step")

        is_mainnet = not settings.HYPERLIQUID_USE_TESTNET
        action = build_approve_agent_post_action(
            dto.agent_address,
            agent.name,
            dto.nonce,
            is_mainnet=is_mainnet,
        )

        signature = split_eip712_signature(dto.signature)
        response = await self._exchange_api.post_action(action, signature, dto.nonce)

        return CompleteAgentWalletResult(status="ok", response=response)
