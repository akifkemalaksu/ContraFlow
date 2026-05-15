from abc import ABC, abstractmethod

from src.domain.entities.fill import Fill


class IFillRepository(ABC):
    @abstractmethod
    async def get_by_id(self, fill_id: str) -> Fill | None: ...

    @abstractmethod
    async def get_by_oid(self, oid: int) -> list[Fill]: ...

    @abstractmethod
    async def get_by_owner(self, owner_address: str) -> list[Fill]: ...

    @abstractmethod
    async def save(self, fill: Fill) -> Fill: ...
