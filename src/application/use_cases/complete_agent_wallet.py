from dataclasses import dataclass
from uuid import UUID

from src.config import settings
from src.domain.enums import AccountType
from src.domain.repositories.wallet_repository import IWalletRepository
from src.infrastructure.hyperliquid.exchange_api import HyperliquidExchangeAPI

#_SIGNATURE_CHAIN_ID = "0x66eee" # 421614 — Arbitrum Sepolia, Hyperliquid user-signed actions
_SIGNATURE_CHAIN_ID = "0x7e4" # 2020 — Ronin


def _split_signature(sig_hex: str) -> dict:
    """Split a 65-byte EIP-712 hex signature into {r, s, v}."""
    s = sig_hex.removeprefix("0x")
    if len(s) != 130:
        raise ValueError("Signature must be 65 bytes (130 hex chars)")
    return {
        "r": "0x" + s[:64],
        "s": "0x" + s[64:128],
        "v": int(s[128:130], 16),
    }


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
        action = {
            "type": "approveAgent",
            "agentAddress": dto.agent_address.lower(),
            "agentName": agent.name,
            "signatureChainId": _SIGNATURE_CHAIN_ID,
            "hyperliquidChain": "Mainnet" if is_mainnet else "Testnet",
        }

        signature = _split_signature(dto.signature)
        response = await self._exchange_api.post_action(action, signature, dto.nonce)

        return CompleteAgentWalletResult(status="ok", response=response)
