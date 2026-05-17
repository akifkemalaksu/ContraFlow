from dataclasses import dataclass
from uuid import UUID

from src.domain.entities.account import Account
from src.domain.enums import AccountType
from src.domain.repositories.account_repository import IAccountRepository


@dataclass
class AddMasterWalletDTO:
    address: str
    user_id: UUID


class AddMasterWalletUseCase:
    def __init__(self, account_repo: IAccountRepository) -> None:
        self._account_repo = account_repo

    async def execute(self, dto: AddMasterWalletDTO) -> Account:
        existing = await self._account_repo.get_by_address(dto.address)
        if existing:
            raise ValueError("Wallet address already registered")

        account = Account(
            address=dto.address,
            user_id=dto.user_id,
            account_type=AccountType.MASTER,
        )
        return await self._account_repo.save(account)
