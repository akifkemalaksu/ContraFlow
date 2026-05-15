from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.role import Role
from src.domain.repositories.role_repository import IRoleRepository
from src.infrastructure.database.models.role_model import RoleModel, user_roles_table


def _to_domain(model: RoleModel) -> Role:
    return Role(
        id=model.id,
        name=model.name,
        description=model.description,
        created_at=model.created_at,
    )


class RoleRepository(IRoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, role_id: UUID) -> Role | None:
        result = await self._session.execute(select(RoleModel).where(RoleModel.id == role_id))
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def get_by_name(self, name: str) -> Role | None:
        result = await self._session.execute(select(RoleModel).where(RoleModel.name == name))
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def list_all(self) -> list[Role]:
        result = await self._session.execute(select(RoleModel))
        return [_to_domain(m) for m in result.scalars().all()]

    async def save(self, role: Role) -> Role:
        model = RoleModel(
            id=role.id,
            name=role.name,
            description=role.description,
            created_at=role.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return role

    async def assign_to_user(self, user_id: UUID, role_id: UUID) -> None:
        await self._session.execute(
            insert(user_roles_table).values(user_id=user_id, role_id=role_id)
        )

    async def remove_from_user(self, user_id: UUID, role_id: UUID) -> None:
        await self._session.execute(
            delete(user_roles_table).where(
                user_roles_table.c.user_id == user_id,
                user_roles_table.c.role_id == role_id,
            )
        )
