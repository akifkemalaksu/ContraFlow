from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.auth_dtos import UserCreateDTO
from src.application.use_cases.login_user import LoginUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.domain.entities.user import User
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.jwt_service import JWTService
from src.interfaces.api.v1.dependencies.auth import require_auth_either
from src.interfaces.api.v1.dependencies.composition import (
    get_login_use_case,
    get_register_use_case,
    get_token_service,
    get_user_repo,
)
from src.interfaces.schemas.auth_schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_use_case),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        user = await use_case.execute(UserCreateDTO(email=body.email, password=body.password))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    await session.commit()
    return _user_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    try:
        tokens = await use_case.execute(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(access_token=tokens.access_token, refresh_token=tokens.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    token_svc: JWTService = Depends(get_token_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    try:
        payload = token_svc.decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await user_repo.get_by_id(UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=token_svc.create_access_token(str(user.id), [r.name for r in user.roles]),
        refresh_token=token_svc.create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(require_auth_either)):
    return _user_response(current_user)
