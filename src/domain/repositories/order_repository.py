from abc import ABC, abstractmethod

from src.domain.entities.order import Order
from src.domain.enums import OrderStatus


class IOrderRepository(ABC):
    @abstractmethod
    async def get_by_oid(self, oid: int) -> Order | None: ...

    @abstractmethod
    async def get_by_owner(self, owner_address: str) -> list[Order]: ...

    @abstractmethod
    async def get_by_strategy(self, strategy_id: int) -> list[Order]: ...

    @abstractmethod
    async def get_by_status(self, owner_address: str, status: OrderStatus) -> list[Order]: ...

    @abstractmethod
    async def save(self, order: Order) -> Order: ...

    @abstractmethod
    async def update_status(self, oid: int, status: OrderStatus) -> Order: ...
