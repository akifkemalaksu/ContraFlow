from dataclasses import dataclass
from uuid import UUID

from src.domain.repositories.wallet_repository import IWalletRepository
from src.infrastructure.hyperliquid.client import HyperliquidInfoClient


@dataclass
class GetWalletInfoDTO:
    address: str
    user_id: UUID


class GetWalletInfoUseCase:
    def __init__(self, wallet_repo: IWalletRepository, hl_client: HyperliquidInfoClient) -> None:
        self._wallet_repo = wallet_repo
        self._hl_client = hl_client

    async def execute(self, dto: GetWalletInfoDTO) -> dict:
        account = await self._wallet_repo.get_by_address(dto.address)
        if not account or account.user_id != dto.user_id:
            raise PermissionError("Wallet not found or does not belong to you")

        return await self._hl_client.get_user_state(dto.address)
