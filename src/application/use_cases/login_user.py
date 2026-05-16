from src.application.dtos.auth_dtos import TokenPairDTO
from src.application.ports.password_hasher import IPasswordHasher
from src.application.ports.token_service import ITokenService
from src.domain.repositories.user_repository import IUserRepository


class LoginUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = password_hasher
        self._tokens = token_service

    async def execute(self, email: str, password: str) -> TokenPairDTO:
        user = await self._user_repo.get_by_email(email)
        if not user or not self._hasher.verify(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is deactivated")

        access_token = self._tokens.create_access_token(
            subject=str(user.id),
            roles=[r.name for r in user.roles],
        )
        refresh_token = self._tokens.create_refresh_token(subject=str(user.id))
        return TokenPairDTO(access_token=access_token, refresh_token=refresh_token)
