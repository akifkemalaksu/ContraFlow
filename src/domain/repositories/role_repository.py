from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.role import Role


class IRoleRepository(ABC):
    @abstractmethod
    async def get_by_id(self, role_id: UUID) -> Role | None: ...

    @abstractmethod
    async def get_by_name(self, name: str) -> Role | None: ...

    @abstractmethod
    async def list_all(self) -> list[Role]: ...

    @abstractmethod
    async def save(self, role: Role) -> Role: ...

    @abstractmethod
    async def assign_to_user(self, user_id: UUID, role_id: UUID) -> None: ...

    @abstractmethod
    async def remove_from_user(self, user_id: UUID, role_id: UUID) -> None: ...
