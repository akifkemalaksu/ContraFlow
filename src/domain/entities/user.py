from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import UUID, uuid4

from src.domain.entities.account import Account
from src.domain.entities.role import Role


@dataclass
class User:
    email: str
    hashed_password: str
    id: UUID = field(default_factory=uuid4)
    roles: list[Role] = field(default_factory=list)
    accounts: list[Account] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
