import logging
from datetime import datetime, UTC
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import src.infrastructure.database.models  # noqa: F401 — ensures all mappers are registered
from src.infrastructure.database.models.permission_model import PermissionModel
from src.infrastructure.database.models.role_model import RoleModel

logger = logging.getLogger(__name__)

_DEFAULT_PERMISSIONS: list[tuple[str, str]] = [
    ("users:read", "View user profiles"),
    ("users:write", "Create and update users"),
    ("users:delete", "Delete users"),
    ("roles:read", "View roles and permissions"),
    ("roles:write", "Create and update roles"),
    ("api_keys:manage", "Create, revoke and list API keys"),
    ("trading:read", "View trading accounts and positions"),
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
        ["users:read", "api_keys:manage", "trading:read", "trading:write"],
    ),
]


async def run_seed(session: AsyncSession) -> None:
    async with session.begin():
        existing_roles = (await session.execute(select(RoleModel))).scalars().all()
        existing_permissions = (await session.execute(select(PermissionModel))).scalars().all()

        if existing_roles and existing_permissions:
            logger.info("Seed skipped: roles and permissions already exist")
            return

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

        logger.info("Seed completed: default roles and permissions inserted")
