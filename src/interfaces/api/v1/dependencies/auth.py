import hashlib
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.domain.entities.user import User
from src.domain.value_objects.api_key import APIKey
from src.infrastructure.database.repositories.api_key_repository import APIKeyRepository
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.jwt_service import JWTService
from src.interfaces.api.v1.dependencies.composition import get_token_service

_bearer = HTTPBearer(auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def _fetch_user(user_id: UUID, session: AsyncSession) -> User | None:
    user = await UserRepository(session).get_by_id(user_id)
    return user if user and user.is_active else None


async def _user_from_jwt(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
    token_svc: JWTService,
) -> User | None:
    if not credentials:
        return None
    try:
        payload = token_svc.decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        return await _fetch_user(UUID(payload["sub"]), session)
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT token")


async def _resolve_api_key(raw_key: str, session: AsyncSession) -> tuple[APIKey, User] | None:
    hashed = hashlib.sha256((raw_key + settings.API_KEY_SECRET).encode()).hexdigest()
    api_key = await APIKeyRepository(session).get_by_hashed_key(hashed)
    if not api_key:
        return None
    if api_key.expires_at is not None:
        exp = api_key.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return None
    user = await _fetch_user(api_key.owner_id, session)
    if not user:
        return None
    return api_key, user


async def require_jwt_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    session: AsyncSession = Depends(get_db_session),
    token_svc: JWTService = Depends(get_token_service),
) -> User:
    user = await _user_from_jwt(credentials, session, token_svc)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


async def require_api_key_user(
    raw_key: str | None = Security(_api_key_header),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if not raw_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    result = await _resolve_api_key(raw_key, session)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API key"
        )
    _, user = result
    return user


async def require_auth_either(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    raw_key: str | None = Security(_api_key_header),
    session: AsyncSession = Depends(get_db_session),
    token_svc: JWTService = Depends(get_token_service),
) -> User:
    user = await _user_from_jwt(credentials, session, token_svc)
    if user:
        return user
    if raw_key:
        result = await _resolve_api_key(raw_key, session)
        if result is not None:
            return result[1]
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def require_api_key_scopes(required_scopes: list[str]):
    async def _dependency(
        raw_key: str | None = Security(_api_key_header),
        session: AsyncSession = Depends(get_db_session),
    ) -> User:
        if not raw_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        result = await _resolve_api_key(raw_key, session)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API key"
            )
        api_key, user = result
        missing = [s for s in required_scopes if s not in api_key.scopes]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {missing}",
            )
        return user

    return Depends(_dependency)
