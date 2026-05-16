from abc import ABC, abstractmethod
from decimal import Decimal


class IExchangeClient(ABC):
    @abstractmethod
    async def place_limit_order(
        self,
        symbol: str,
        is_buy: bool,
        sz: Decimal,
        limit_px: Decimal,
        reduce_only: bool = False,
    ) -> dict: ...

    @abstractmethod
    async def place_market_order(
        self,
        symbol: str,
        is_buy: bool,
        sz: Decimal,
        slippage: float = 0.05,
    ) -> dict: ...

    @abstractmethod
    async def cancel_order(self, symbol: str, oid: int) -> dict: ...

    @abstractmethod
    async def cancel_all_orders(self, symbol: str) -> dict: ...

    @abstractmethod
    async def close_position(
        self,
        symbol: str,
        close_pct: Decimal,
        slippage: float = 0.05,
    ) -> dict | None: ...

    @abstractmethod
    async def approve_agent(self, name: str | None = None) -> tuple[dict, str]: ...


class IExchangeClientFactory(ABC):
    @abstractmethod
    def create(self, private_key: str, account_address: str | None = None) -> IExchangeClient: ...
