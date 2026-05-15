from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.account import Account


class IAccountRepository(ABC):
    @abstractmethod
    async def get_by_address(self, address: str) -> Account | None: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[Account]: ...

    @abstractmethod
    async def save(self, account: Account) -> Account: ...

    @abstractmethod
    async def update(self, account: Account) -> Account: ...

    @abstractmethod
    async def delete(self, address: str) -> None: ...
