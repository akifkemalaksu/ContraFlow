from dataclasses import dataclass
from uuid import UUID

from src.domain.entities.wallet import Wallet
from src.domain.enums import AccountType
from src.domain.repositories.wallet_repository import IWalletRepository


@dataclass
class AddMasterWalletDTO:
    address: str
    name: str
    user_id: UUID


class AddMasterWalletUseCase:
    def __init__(self, wallet_repo: IWalletRepository) -> None:
        self._wallet_repo = wallet_repo

    async def execute(self, dto: AddMasterWalletDTO) -> Wallet:
        existing = await self._wallet_repo.get_by_address(dto.address)
        if existing:
            raise ValueError("Wallet address already registered")

        wallet = Wallet(
            address=dto.address,
            name=dto.name,
            user_id=dto.user_id,
            account_type=AccountType.MASTER,
        )
        return await self._wallet_repo.save(wallet)
