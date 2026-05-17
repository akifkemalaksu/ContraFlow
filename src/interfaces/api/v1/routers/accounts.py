from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.add_master_wallet import AddMasterWalletDTO, AddMasterWalletUseCase
from src.domain.entities.user import User
from src.infrastructure.database.session import get_db_session
from src.interfaces.api.v1.dependencies.auth import require_permission
from src.interfaces.api.v1.dependencies.composition import get_add_master_wallet_use_case
from src.interfaces.schemas.account_schemas import AccountResponse, AddMasterWalletRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/wallets", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def add_master_wallet(
    body: AddMasterWalletRequest,
    current_user: User = require_permission("accounts:write"),
    use_case: AddMasterWalletUseCase = Depends(get_add_master_wallet_use_case),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        account = await use_case.execute(AddMasterWalletDTO(address=body.address, user_id=current_user.id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    await session.commit()
    return AccountResponse(address=account.address, account_type=account.account_type, is_active=account.is_active)
