from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import UUID, uuid4

from src.domain.entities.permission import Permission


@dataclass
class Role:
    name: str
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    permissions: list[Permission] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
