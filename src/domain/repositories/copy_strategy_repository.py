from abc import ABC, abstractmethod

from src.domain.entities.copy_strategy import CopyStrategy


class ICopyStrategyRepository(ABC):
    @abstractmethod
    async def get_by_id(self, strategy_id: int) -> CopyStrategy | None: ...

    @abstractmethod
    async def get_by_user_wallet(self, user_wallet: str) -> list[CopyStrategy]: ...

    @abstractmethod
    async def get_by_target_wallet(self, target_wallet: str) -> list[CopyStrategy]: ...

    @abstractmethod
    async def save(self, strategy: CopyStrategy) -> CopyStrategy: ...

    @abstractmethod
    async def update(self, strategy: CopyStrategy) -> CopyStrategy: ...

    @abstractmethod
    async def delete(self, strategy_id: int) -> None: ...
