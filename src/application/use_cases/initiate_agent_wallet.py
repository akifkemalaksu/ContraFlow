import secrets
import time
from dataclasses import dataclass
from uuid import UUID

import eth_account

from src.config import settings
from src.domain.entities.wallet import Wallet
from src.infrastructure.hyperliquid.signing_helpers import build_approve_agent_eip712
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
        typed_data = build_approve_agent_eip712(
            agent_eth_account.address,
            dto.agent_name,
            nonce,
            is_mainnet=is_mainnet,
        )
        eip712 = EIP712Package(
            domain=typed_data["domain"],
            types=typed_data["types"],
            primary_type=typed_data["primaryType"],
            message=typed_data["message"],
        )

        return InitiateAgentWalletResult(
            agent_address=agent_eth_account.address,
            signer_address=dto.master_wallet_address,
            eip712=eip712,
        )
