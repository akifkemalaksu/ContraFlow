from dataclasses import dataclass, field
from uuid import UUID

from src.domain.enums import AccountType


@dataclass
class Account:
    user_id: UUID
    address: str  # PK, VARCHAR(42)
    account_type: AccountType
    agent_address: str | None = None
    is_active: bool = True
