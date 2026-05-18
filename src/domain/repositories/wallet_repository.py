from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.wallet import Wallet


class IWalletRepository(ABC):
    @abstractmethod
    async def get_by_address(self, address: str) -> Wallet | None: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[Wallet]: ...

    @abstractmethod
    async def save(self, wallet: Wallet) -> Wallet: ...

    @abstractmethod
    async def update(self, wallet: Wallet) -> Wallet: ...

    @abstractmethod
    async def delete(self, address: str) -> None: ...
