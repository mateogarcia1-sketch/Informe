import datetime as dt
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionType, User
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.accounts import get_user_account
from app.services.categories import get_user_category


def _validate_refs(
    db: Session,
    user_id: int,
    account_id: int,
    category_id: int,
    tx_type: TransactionType,
    check_active: bool = True,
) -> None:
    account = get_user_account(db, user_id, account_id)
    if check_active and not account.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La cuenta está inactiva")
    category = get_user_category(db, user_id, category_id)
    if category.type != tx_type:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "La categoría no corresponde al tipo de movimiento",
        )


def get_user_transaction(db: Session, user_id: int, tx_id: int) -> Transaction:
    tx = db.scalar(
        select(Transaction).where(Transaction.id == tx_id, Transaction.user_id == user_id)
    )
    if tx is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movimiento no encontrado")
    return tx


def create_transaction(db: Session, user: User, data: TransactionCreate) -> Transaction:
    _validate_refs(db, user.id, data.account_id, data.category_id, data.type)
    tx = Transaction(user_id=user.id, **data.model_dump())
    db.add(tx)
    db.flush()
    db.commit()
    db.refresh(tx)
    return tx


def update_transaction(
    db: Session, user: User, tx_id: int, data: TransactionUpdate
) -> Transaction:
    tx = get_user_transaction(db, user.id, tx_id)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    merged = {
        "account_id": tx.account_id,
        "category_id": tx.category_id,
        "type": tx.type,
        **{k: v for k, v in changes.items() if k in ("account_id", "category_id", "type")},
    }
    _validate_refs(
        db,
        user.id,
        merged["account_id"],
        merged["category_id"],
        merged["type"],
        check_active="account_id" in changes,
    )
    for field, value in changes.items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, user: User, tx_id: int) -> None:
    tx = get_user_transaction(db, user.id, tx_id)
    db.delete(tx)
    db.commit()


def search_transactions(
    db: Session,
    user_id: int,
    *,
    account_id: int | None = None,
    category_id: int | None = None,
    tx_type: TransactionType | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Transaction], int]:
    """Historial de movimientos con filtros. Devuelve (movimientos, total)."""
    query = select(Transaction).where(Transaction.user_id == user_id)
    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)
    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)
    if tx_type is not None:
        query = query.where(Transaction.type == tx_type)
    if date_from is not None:
        query = query.where(Transaction.date >= date_from)
    if date_to is not None:
        query = query.where(Transaction.date <= date_to)
    if min_amount is not None:
        query = query.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.where(Transaction.amount <= max_amount)
    if search:
        query = query.where(Transaction.description.ilike(f"%{search}%"))

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total
