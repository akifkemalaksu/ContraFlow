import hashlib
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.domain.entities.user import User
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


async def _user_from_api_key(raw_key: str | None, session: AsyncSession) -> User | None:
    if not raw_key:
        return None
    hashed = hashlib.sha256((raw_key + settings.API_KEY_SECRET).encode()).hexdigest()
    api_key = await APIKeyRepository(session).get_by_hashed_key(hashed)
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return await _fetch_user(api_key.owner_id, session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    session: AsyncSession = Depends(get_db_session),
    token_svc: JWTService = Depends(get_token_service),
) -> User:
    user = await _user_from_jwt(credentials, session, token_svc)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
    raw_key: str | None = Security(_api_key_header),
    session: AsyncSession = Depends(get_db_session),
    token_svc: JWTService = Depends(get_token_service),
) -> User:
    """JWT veya API Key — birisi geçerliyse yeterli."""
    user = await _user_from_jwt(credentials, session, token_svc)
    if not user:
        user = await _user_from_api_key(raw_key, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
