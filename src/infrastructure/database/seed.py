import logging
from datetime import datetime, UTC
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import src.infrastructure.database.models  # noqa: F401 — ensures all mappers are registered
from src.infrastructure.database.models.permission_model import PermissionModel
from src.infrastructure.database.models.role_model import RoleModel
from src.infrastructure.database.models.user_model import UserModel
from src.infrastructure.security.bcrypt_hasher import BcryptPasswordHasher

logger = logging.getLogger(__name__)

_DEFAULT_PERMISSIONS: list[tuple[str, str]] = [
    ("users:read", "View user profiles"),
    ("users:write", "Create and update users"),
    ("users:delete", "Delete users"),
    ("wallets:write", "Add and manage own trading wallets"),
    ("wallets:read", "View trading wallets"),
    ("trading:read", "View trading positions"),
    ("trading:write", "Place and cancel orders"),
]

_DEFAULT_ROLES: list[tuple[str, str, list[str]]] = [
    (
        "admin",
        "Full system access",
        [p[0] for p in _DEFAULT_PERMISSIONS],
    ),
    (
        "user",
        "Standard authenticated user",
        ["users:read", "wallets:write", "wallets:read", "trading:read", "trading:write"],
    ),
]

_DEFAULT_USERS: list[tuple[str, str, str]] = [
    ("developer@mail.com", "dev123123", "admin"),
]


async def run_seed(session: AsyncSession) -> None:
    async with session.begin():
        existing_roles = (await session.execute(select(RoleModel))).scalars().all()
        existing_permissions = (await session.execute(select(PermissionModel))).scalars().all()
        now = datetime.now(UTC)

        permission_map: dict[str, PermissionModel] = {p.name: p for p in existing_permissions}
        for name, description in _DEFAULT_PERMISSIONS:
            if name not in permission_map:
                perm = PermissionModel(id=uuid.uuid4(), name=name, description=description, created_at=now)
                session.add(perm)
                permission_map[name] = perm

        await session.flush()

        role_map: dict[str, RoleModel] = {r.name: r for r in existing_roles}
        for role_name, description, perm_names in _DEFAULT_ROLES:
            if role_name not in role_map:
                role = RoleModel(id=uuid.uuid4(), name=role_name, description=description, created_at=now)
                role.permissions = [permission_map[p] for p in perm_names if p in permission_map]
                session.add(role)
                role_map[role_name] = role

        await session.flush()

        hasher = BcryptPasswordHasher()
        existing_emails = {
            email
            for (email,) in (
                await session.execute(select(UserModel.email).where(UserModel.email.in_([u[0] for u in _DEFAULT_USERS])))
            ).all()
        }
        for email, password, role_name in _DEFAULT_USERS:
            if email not in existing_emails:
                user = UserModel(
                    id=uuid.uuid4(),
                    email=email,
                    hashed_password=hasher.hash(password),
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                if role_name in role_map:
                    user.roles = [role_map[role_name]]
                session.add(user)
                logger.info("Seed: created user %s", email)

        logger.info("Seed completed: default roles, permissions, and users inserted")
