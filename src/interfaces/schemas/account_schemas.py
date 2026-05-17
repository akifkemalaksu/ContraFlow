from pydantic import BaseModel

from src.domain.enums import AccountType


class AddMasterWalletRequest(BaseModel):
    address: str


class AccountResponse(BaseModel):
    address: str
    account_type: AccountType
    is_active: bool
