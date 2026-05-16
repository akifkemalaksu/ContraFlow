from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import UUID, uuid4


@dataclass
class Permission:
    name: str
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
