import hashlib
import secrets
import uuid
from datetime import datetime, UTC, timedelta

from src.application.dtos.auth_dtos import APIKeyCreateDTO
from src.domain.value_objects.api_key import APIKey
from src.domain.repositories.api_key_repository import IAPIKeyRepository
from src.config import settings


def _generate_raw_key() -> str:
    return secrets.token_urlsafe(32)


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(
        (raw_key + settings.API_KEY_SECRET).encode()
    ).hexdigest()


class CreateAPIKeyUseCase:
    def __init__(self, api_key_repo: IAPIKeyRepository) -> None:
        self._repo = api_key_repo

    async def execute(self, owner_id: uuid.UUID, dto: APIKeyCreateDTO) -> tuple[APIKey, str]:
        raw_key = _generate_raw_key()
        prefix = raw_key[: settings.API_KEY_PREFIX_LENGTH]
        hashed = _hash_key(raw_key)

        expires_at = None
        if dto.expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=dto.expires_in_days)

        api_key = APIKey(
            id=uuid.uuid4(),
            owner_id=owner_id,
            prefix=prefix,
            hashed_key=hashed,
            scopes=dto.scopes,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        saved = await self._repo.save(api_key)
        return saved, raw_key  # raw_key yalnızca bir kez döner


class RevokeAPIKeyUseCase:
    def __init__(self, api_key_repo: IAPIKeyRepository) -> None:
        self._repo = api_key_repo

    async def execute(self, key_id: uuid.UUID, owner_id: uuid.UUID) -> bool:
        return await self._repo.revoke(key_id, owner_id)
