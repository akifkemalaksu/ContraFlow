from abc import ABC, abstractmethod


class ICacheService(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int | None = None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...

    @abstractmethod
    async def close(self) -> None: ...


class ICacheServiceFactory(ABC):
    @abstractmethod
    def create(self) -> ICacheService: ...
