from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class APIKey:
    id: UUID
    owner_id: UUID
    prefix: str          # İlk 8 karakter, görünür (log-safe)
    hashed_key: str      # SHA-256 hash, DB'de saklanır
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime
    is_active: bool = True
