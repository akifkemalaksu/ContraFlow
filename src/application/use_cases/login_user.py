from src.application.dtos.auth_dtos import TokenPairDTO
from src.domain.repositories.user_repository import IUserRepository
from src.interfaces.api.v1.dependencies.password import verify_password
from src.interfaces.api.v1.dependencies.jwt import create_access_token, create_refresh_token


class LoginUseCase:
    def __init__(self, user_repo: IUserRepository) -> None:
        self._user_repo = user_repo

    async def execute(self, email: str, password: str) -> TokenPairDTO:
        user = await self._user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is deactivated")

        access_token = create_access_token(
            subject=str(user.id),
            roles=[r.name for r in user.roles],
        )
        refresh_token = create_refresh_token(subject=str(user.id))
        return TokenPairDTO(access_token=access_token, refresh_token=refresh_token)
