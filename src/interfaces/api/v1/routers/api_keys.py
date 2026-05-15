from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.auth_dtos import APIKeyCreateDTO
from src.application.use_cases.manage_api_keys import CreateAPIKeyUseCase, RevokeAPIKeyUseCase
from src.domain.entities.user import User
from src.infrastructure.database.repositories.api_key_repository import APIKeyRepository
from src.infrastructure.database.session import get_db_session
from src.interfaces.api.v1.dependencies.auth import get_current_user
from src.interfaces.schemas.auth_schemas import (
    APIKeyCreateRequest,
    APIKeyCreatedResponse,
    APIKeyResponse,
)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("/", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    use_case = CreateAPIKeyUseCase(APIKeyRepository(session))
    api_key, raw_key = await use_case.execute(
        owner_id=current_user.id,
        dto=APIKeyCreateDTO(scopes=body.scopes, expires_in_days=body.expires_in_days),
    )
    await session.commit()
    return APIKeyCreatedResponse(
        id=api_key.id,
        prefix=api_key.prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        raw_key=raw_key,
    )


@router.get("/", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    repo = APIKeyRepository(session)
    keys = await repo.list_by_owner(current_user.id)
    return [
        APIKeyResponse(
            id=k.id,
            prefix=k.prefix,
            scopes=k.scopes,
            expires_at=k.expires_at,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    use_case = RevokeAPIKeyUseCase(APIKeyRepository(session))
    revoked = await use_case.execute(key_id=key_id, owner_id=current_user.id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    await session.commit()
