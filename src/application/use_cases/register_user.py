from src.application.dtos.auth_dtos import UserCreateDTO
from src.application.ports.password_hasher import IPasswordHasher
from src.domain.entities.user import User
from src.domain.repositories.user_repository import IUserRepository


class RegisterUserUseCase:
    def __init__(self, user_repo: IUserRepository, password_hasher: IPasswordHasher) -> None:
        self._user_repo = user_repo
        self._hasher = password_hasher

    async def execute(self, dto: UserCreateDTO) -> User:
        existing = await self._user_repo.get_by_email(dto.email)
        if existing:
            raise ValueError("Email already registered")

        user = User(
            email=dto.email,
            hashed_password=self._hasher.hash(dto.password),
        )
        return await self._user_repo.save(user)
