from abc import ABC, abstractmethod

from src.domain.entities.asset import Asset


class IAssetRepository(ABC):
    @abstractmethod
    async def get_by_id(self, asset_id: int) -> Asset | None: ...

    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Asset | None: ...

    @abstractmethod
    async def get_all(self) -> list[Asset]: ...

    @abstractmethod
    async def save(self, asset: Asset) -> Asset: ...

    @abstractmethod
    async def upsert(self, asset: Asset) -> Asset: ...
