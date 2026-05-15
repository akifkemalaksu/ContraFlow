from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.value_objects.api_key import APIKey
from src.domain.repositories.api_key_repository import IAPIKeyRepository
from src.infrastructure.database.models.api_key_model import APIKeyModel


def _to_domain(model: APIKeyModel) -> APIKey:
    return APIKey(
        id=model.id,
        owner_id=model.owner_id,
        prefix=model.prefix,
        hashed_key=model.hashed_key,
        scopes=model.scopes or [],
        expires_at=model.expires_at,
        is_active=model.is_active,
        created_at=model.created_at,
    )


class APIKeyRepository(IAPIKeyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, key_id: UUID) -> APIKey | None:
        result = await self._session.execute(select(APIKeyModel).where(APIKeyModel.id == key_id))
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def get_by_hashed_key(self, hashed_key: str) -> APIKey | None:
        result = await self._session.execute(
            select(APIKeyModel).where(
                APIKeyModel.hashed_key == hashed_key, APIKeyModel.is_active.is_(True)
            )
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def list_by_owner(self, owner_id: UUID) -> list[APIKey]:
        result = await self._session.execute(
            select(APIKeyModel).where(APIKeyModel.owner_id == owner_id)
        )
        return [_to_domain(m) for m in result.scalars().all()]

    async def save(self, api_key: APIKey) -> APIKey:
        model = APIKeyModel(
            id=api_key.id,
            owner_id=api_key.owner_id,
            prefix=api_key.prefix,
            hashed_key=api_key.hashed_key,
            scopes=list(api_key.scopes),
            expires_at=api_key.expires_at,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return api_key

    async def revoke(self, key_id: UUID, owner_id: UUID) -> bool:
        result = await self._session.execute(
            update(APIKeyModel)
            .where(APIKeyModel.id == key_id, APIKeyModel.owner_id == owner_id)
            .values(is_active=False)
        )
        return result.rowcount > 0
