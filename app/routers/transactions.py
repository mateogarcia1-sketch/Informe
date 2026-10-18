import datetime as dt
from decimal import Decimal

from fastapi import APIRouter, Query, Response, status

from app.core.deps import CurrentUser, DbSession
from app.models import TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionOut,
    TransactionPage,
    TransactionUpdate,
)
from app.services import transactions as service

router = APIRouter(prefix="/transactions", tags=["movimientos"])


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionCreate, user: CurrentUser, db: DbSession):
    """Registra manualmente un gasto o ingreso."""
    return service.create_transaction(db, user, data)


@router.get("", response_model=TransactionPage)
def list_transactions(
    user: CurrentUser,
    db: DbSession,
    account_id: int | None = None,
    category_id: int | None = None,
    type: TransactionType | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    min_amount: Decimal | None = Query(default=None, ge=0),
    max_amount: Decimal | None = Query(default=None, ge=0),
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Historial de movimientos, del más reciente al más antiguo, con filtros."""
    items, total = service.search_transactions(
        db,
        user.id,
        account_id=account_id,
        category_id=category_id,
        tx_type=type,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
        limit=limit,
        offset=offset,
    )
    return TransactionPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{tx_id}", response_model=TransactionOut)
def get_transaction(tx_id: int, user: CurrentUser, db: DbSession):
    return service.get_user_transaction(db, user.id, tx_id)


@router.patch("/{tx_id}", response_model=TransactionOut)
def update_transaction(
    tx_id: int, data: TransactionUpdate, user: CurrentUser, db: DbSession
):
    return service.update_transaction(db, user, tx_id, data)


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(tx_id: int, user: CurrentUser, db: DbSession):
    service.delete_transaction(db, user, tx_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
