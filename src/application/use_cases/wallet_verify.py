import secrets

import eth_account
from eth_account.messages import encode_defunct

from src.application.dtos.auth_dtos import TokenPairDTO
from src.application.ports.password_hasher import IPasswordHasher
from src.application.ports.token_service import ITokenService
from src.application.use_cases.wallet_challenge import _CHALLENGE_KEY_PREFIX
from src.domain.entities.user import User
from src.domain.entities.wallet import Wallet
from src.domain.enums import AccountType
from src.domain.repositories.user_repository import IUserRepository
from src.domain.repositories.wallet_repository import IWalletRepository
from src.domain.services.cache import ICacheService


class WalletVerifyUseCase:
    def __init__(
        self,
        cache: ICacheService,
        user_repo: IUserRepository,
        wallet_repo: IWalletRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
    ) -> None:
        self._cache = cache
        self._user_repo = user_repo
        self._wallet_repo = wallet_repo
        self._hasher = password_hasher
        self._tokens = token_service

    async def execute(self, address: str, message: str, signature: str) -> TokenPairDTO:
        key = _CHALLENGE_KEY_PREFIX + address
        expected = await self._cache.get(key)
        if not expected:
            raise ValueError("Wallet challenge expired")
        if message != expected:
            raise ValueError("Invalid wallet challenge")

        recovered = eth_account.Account.recover_message(
            encode_defunct(text=message),
            signature=signature,
        )
        if recovered.lower() != address.lower():
            raise ValueError("Invalid wallet signature")

        await self._cache.delete(key)

        wallet = await self._wallet_repo.get_by_address(address)
        if wallet and not wallet.is_active:
            raise ValueError("Wallet is disabled")

        if wallet:
            user = await self._user_repo.get_by_id(wallet.user_id)
            if not user or not user.is_active:
                raise ValueError("User not found")
        else:
            user = User(
                email=f"wallet_{address.lower()}@contraflow.invalid",
                hashed_password=self._hasher.hash(secrets.token_urlsafe(32)),
            )
            await self._user_repo.save(user)
            await self._wallet_repo.save(
                Wallet(
                    user_id=user.id,
                    address=address,
                    name="MetaMask",
                    account_type=AccountType.MASTER,
                )
            )

        return TokenPairDTO(
            access_token=self._tokens.create_access_token(str(user.id), [r.name for r in user.roles]),
            refresh_token=self._tokens.create_refresh_token(str(user.id)),
        )
