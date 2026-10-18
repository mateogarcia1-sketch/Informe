from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.money import to_money
from app.models import Account, Transaction, TransactionType


def get_user_account(db: Session, user_id: int, account_id: int) -> Account:
    account = db.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    )
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cuenta no encontrada")
    return account


def compute_balances(db: Session, user_id: int) -> dict[int, Decimal]:
    """Saldo de cada cuenta del usuario: saldo inicial + ingresos - gastos."""
    accounts = db.scalars(select(Account).where(Account.user_id == user_id)).all()
    balances = {a.id: to_money(a.initial_balance) for a in accounts}

    rows = db.execute(
        select(Transaction.account_id, Transaction.type, func.sum(Transaction.amount))
        .where(Transaction.user_id == user_id)
        .group_by(Transaction.account_id, Transaction.type)
    ).all()
    for account_id, tx_type, total in rows:
        sign = 1 if tx_type == TransactionType.income else -1
        balances[account_id] = balances.get(account_id, Decimal("0.00")) + sign * to_money(total)
    return balances


def total_balance(db: Session, user_id: int) -> Decimal:
    """Saldo total sumando solo las cuentas activas."""
    balances = compute_balances(db, user_id)
    active_ids = db.scalars(
        select(Account.id).where(Account.user_id == user_id, Account.is_active.is_(True))
    ).all()
    return sum((balances[i] for i in active_ids), Decimal("0.00"))
