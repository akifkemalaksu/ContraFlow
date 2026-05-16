from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.login_user import LoginUseCase
from src.application.use_cases.manage_api_keys import CreateAPIKeyUseCase, RevokeAPIKeyUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.infrastructure.database.repositories.api_key_repository import APIKeyRepository
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.bcrypt_hasher import BcryptPasswordHasher
from src.infrastructure.security.jwt_service import JWTService

_hasher = BcryptPasswordHasher()
_token_svc = JWTService()


def get_token_service() -> JWTService:
    return _token_svc


def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


def get_api_key_repo(session: AsyncSession = Depends(get_db_session)) -> APIKeyRepository:
    return APIKeyRepository(session)


def get_register_use_case(session: AsyncSession = Depends(get_db_session)) -> RegisterUserUseCase:
    return RegisterUserUseCase(UserRepository(session), _hasher)


def get_login_use_case(session: AsyncSession = Depends(get_db_session)) -> LoginUseCase:
    return LoginUseCase(UserRepository(session), _hasher, _token_svc)


def get_create_api_key_use_case(session: AsyncSession = Depends(get_db_session)) -> CreateAPIKeyUseCase:
    return CreateAPIKeyUseCase(APIKeyRepository(session))


def get_revoke_api_key_use_case(session: AsyncSession = Depends(get_db_session)) -> RevokeAPIKeyUseCase:
    return RevokeAPIKeyUseCase(APIKeyRepository(session))
