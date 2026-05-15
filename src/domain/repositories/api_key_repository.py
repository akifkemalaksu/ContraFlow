from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.value_objects.api_key import APIKey


class IAPIKeyRepository(ABC):
    @abstractmethod
    async def get_by_id(self, key_id: UUID) -> APIKey | None: ...

    @abstractmethod
    async def get_by_hashed_key(self, hashed_key: str) -> APIKey | None: ...

    @abstractmethod
    async def list_by_owner(self, owner_id: UUID) -> list[APIKey]: ...

    @abstractmethod
    async def save(self, api_key: APIKey) -> APIKey: ...

    @abstractmethod
    async def revoke(self, key_id: UUID, owner_id: UUID) -> bool: ...
