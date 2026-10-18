from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbSession
from app.models import Account, Transaction
from app.schemas.account import AccountCreate, AccountOut, AccountUpdate
from app.services.accounts import compute_balances, get_user_account

router = APIRouter(prefix="/accounts", tags=["cuentas"])


def _with_balance(db, user_id: int, account: Account) -> AccountOut:
    balance = compute_balances(db, user_id)[account.id]
    return AccountOut.model_validate(account).model_copy(update={"balance": balance})


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def link_account(data: AccountCreate, user: CurrentUser, db: DbSession):
    """Vincula una cuenta. Solo se guardan los últimos 4 dígitos, nunca claves."""
    account = Account(user_id=user.id, **data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return _with_balance(db, user.id, account)


@router.get("", response_model=list[AccountOut])
def list_accounts(user: CurrentUser, db: DbSession, include_inactive: bool = False):
    query = select(Account).where(Account.user_id == user.id).order_by(Account.id)
    if not include_inactive:
        query = query.where(Account.is_active.is_(True))
    balances = compute_balances(db, user.id)
    return [
        AccountOut.model_validate(a).model_copy(update={"balance": balances[a.id]})
        for a in db.scalars(query)
    ]


@router.get("/{account_id}", response_model=AccountOut)
def get_account(account_id: int, user: CurrentUser, db: DbSession):
    return _with_balance(db, user.id, get_user_account(db, user.id, account_id))


@router.patch("/{account_id}", response_model=AccountOut)
def update_account(account_id: int, data: AccountUpdate, user: CurrentUser, db: DbSession):
    account = get_user_account(db, user.id, account_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    db.commit()
    db.refresh(account)
    return _with_balance(db, user.id, account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, user: CurrentUser, db: DbSession):
    account = get_user_account(db, user.id, account_id)
    movements = db.scalar(
        select(func.count()).select_from(Transaction).where(Transaction.account_id == account.id)
    )
    if movements:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La cuenta tiene movimientos; desactívala en lugar de eliminarla",
        )
    db.delete(account)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
