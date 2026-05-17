from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.permission import Permission
from src.domain.entities.role import Role
from src.domain.entities.user import User
from src.domain.repositories.user_repository import IUserRepository
from src.infrastructure.database.models.role_model import RoleModel
from src.infrastructure.database.models.user_model import UserModel


def _role_to_domain(model: RoleModel) -> Role:
    return Role(
        id=model.id,
        name=model.name,
        description=model.description,
        permissions=[Permission(id=p.id, name=p.name, description=p.description, created_at=p.created_at) for p in model.permissions],
        created_at=model.created_at,
    )


def _to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        hashed_password=model.hashed_password,
        roles=[_role_to_domain(r) for r in model.roles],
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        email=user.email,
        hashed_password=user.hashed_password,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def save(self, user: User) -> User:
        model = _to_model(user)
        self._session.add(model)
        await self._session.flush()
        return user

    async def update(self, user: User) -> User:
        result = await self._session.execute(select(UserModel).where(UserModel.id == user.id))
        model = result.scalar_one()
        model.email = user.email
        model.hashed_password = user.hashed_password
        model.is_active = user.is_active
        model.updated_at = datetime.now(UTC)
        await self._session.flush()
        return user
