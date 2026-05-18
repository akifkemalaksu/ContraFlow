from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain.entities.user import User
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.infrastructure.security.jwt_service import JWTService
from src.interfaces.api.v1.dependencies.composition import (
    get_token_service,
    get_user_repo,
)

_bearer = HTTPBearer(auto_error=False)


async def require_jwt_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    user_repo: UserRepository = Depends(get_user_repo),
    token_svc: JWTService = Depends(get_token_service),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = token_svc.decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise ValueError
        user = await user_repo.get_by_id(UUID(payload["sub"]))
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT token")
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_permission(permission: str):
    async def _dependency(user: User = Depends(require_jwt_user)) -> User:
        for role in user.roles:
            if any(p.name == permission for p in role.permissions):
                return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {permission}",
        )

    return Depends(_dependency)
