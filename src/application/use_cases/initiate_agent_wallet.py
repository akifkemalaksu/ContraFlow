import secrets
import time
from dataclasses import dataclass
from uuid import UUID

import eth_account

from src.config import settings
from src.domain.entities.wallet import Wallet
from src.domain.enums import AccountType
from src.domain.repositories.wallet_repository import IWalletRepository
from src.domain.services.key_encryptor import IKeyEncryptor


@dataclass
class InitiateAgentWalletDTO:
    master_wallet_address: str
    agent_name: str
    user_id: UUID


@dataclass
class EIP712Package:
    domain: dict
    types: dict
    primary_type: str
    message: dict


@dataclass
class InitiateAgentWalletResult:
    agent_address: str
    signer_address: str  # master wallet — UI enforces signing with this account
    eip712: EIP712Package


_APPROVE_AGENT_TYPES = [
    {"name": "hyperliquidChain", "type": "string"},
    {"name": "agentAddress", "type": "address"},
    {"name": "agentName", "type": "string"},
    {"name": "nonce", "type": "uint256"},
]

_EIP712_DOMAIN_TYPES = [
    {"name": "name", "type": "string"},
    {"name": "version", "type": "string"},
    {"name": "chainId", "type": "uint256"},
    {"name": "verifyingContract", "type": "address"},
]

_chainId = 2020 # 421614

class InitiateAgentWalletUseCase:
    def __init__(self, wallet_repo: IWalletRepository, key_encryptor: IKeyEncryptor) -> None:
        self._wallet_repo = wallet_repo
        self._key_encryptor = key_encryptor

    async def execute(self, dto: InitiateAgentWalletDTO) -> InitiateAgentWalletResult:
        master = await self._wallet_repo.get_by_address(dto.master_wallet_address)
        if not master or master.user_id != dto.user_id:
            raise PermissionError("Master wallet not found")
        if master.account_type != AccountType.MASTER:
            raise ValueError("Target wallet is not a master wallet")

        private_key = "0x" + secrets.token_hex(32)
        agent_eth_account = eth_account.Account.from_key(private_key)

        encrypted_key, iv = self._key_encryptor.encrypt(private_key)
        nonce = int(time.time() * 1000)

        agent = Wallet(
            address=agent_eth_account.address,
            user_id=dto.user_id,
            name=dto.agent_name,
            account_type=AccountType.AGENT,
            master_wallet_address=dto.master_wallet_address,
            encrypted_agent_private_key=encrypted_key,
            encryption_iv=iv,
            last_nonce=nonce,
        )
        await self._wallet_repo.save(agent)

        is_mainnet = not settings.HYPERLIQUID_USE_TESTNET
        eip712 = EIP712Package(
            domain={
                "name": "HyperliquidSignTransaction",
                "version": "1",
                "chainId": _chainId,
                "verifyingContract": "0x0000000000000000000000000000000000000000",
            },
            types={
                "HyperliquidTransaction:ApproveAgent": _APPROVE_AGENT_TYPES,
                "EIP712Domain": _EIP712_DOMAIN_TYPES,
            },
            primary_type="HyperliquidTransaction:ApproveAgent",
            message={
                "hyperliquidChain": "Mainnet" if is_mainnet else "Testnet",
                "agentAddress": agent_eth_account.address.lower(),
                "agentName": dto.agent_name,
                "nonce": nonce,
            },
        )

        return InitiateAgentWalletResult(
            agent_address=agent_eth_account.address,
            signer_address=dto.master_wallet_address,
            eip712=eip712,
        )
