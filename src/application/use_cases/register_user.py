from src.application.dtos.auth_dtos import UserCreateDTO
from src.domain.entities.user import User
from src.domain.repositories.user_repository import IUserRepository
from src.interfaces.api.v1.dependencies.password import hash_password


class RegisterUserUseCase:
    def __init__(self, user_repo: IUserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, dto: UserCreateDTO) -> User:
        existing = await self._user_repo.get_by_email(dto.email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            email=dto.email,
            hashed_password=hash_password(dto.password),
        )
        return await self._user_repo.save(user)
