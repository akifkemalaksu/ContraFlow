from abc import ABC, abstractmethod

from src.domain.entities.cross_asset_trigger import CrossAssetTrigger


class ICrossAssetTriggerRepository(ABC):
    @abstractmethod
    async def get_by_id(self, trigger_id: int) -> CrossAssetTrigger | None: ...

    @abstractmethod
    async def get_by_strategy(self, strategy_id: int) -> list[CrossAssetTrigger]: ...

    @abstractmethod
    async def save(self, trigger: CrossAssetTrigger) -> CrossAssetTrigger: ...

    @abstractmethod
    async def delete(self, trigger_id: int) -> None: ...
