import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from src.config import settings
from src.domain.services.cache import ICacheService

_CHALLENGE_TTL_SECONDS = 5 * 60
_CHALLENGE_KEY_PREFIX = "wallet_auth:challenge:"


@dataclass
class WalletChallengeResultDTO:
    address: str
    message: str


class WalletChallengeUseCase:
    def __init__(self, cache: ICacheService) -> None:
        self._cache = cache

    async def execute(self, address: str) -> WalletChallengeResultDTO:
        nonce = secrets.token_urlsafe(16)
        issued_at = datetime.now(UTC).isoformat()
        message = (
            f"{settings.APP_NAME} wants you to sign in with your Ethereum account:\n"
            f"{address}\n\n"
            "Sign in to ContraFlow.\n\n"
            f"Nonce: {nonce}\n"
            f"Issued At: {issued_at}"
        )
        await self._cache.set(_CHALLENGE_KEY_PREFIX + address, message, ttl=_CHALLENGE_TTL_SECONDS)
        return WalletChallengeResultDTO(address=address, message=message)
