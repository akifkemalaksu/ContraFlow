from dataclasses import dataclass, field
from uuid import UUID

from src.domain.enums import AccountType


@dataclass
class Wallet:
    user_id: UUID
    address: str  # PK, VARCHAR(42)
    name: str
    account_type: AccountType
    master_wallet_address: str | None = None
    encrypted_agent_private_key: str | None = None
    encryption_iv: str | None = None
    last_nonce: int = 0
    is_active: bool = True
