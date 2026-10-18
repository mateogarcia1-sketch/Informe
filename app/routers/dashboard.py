from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbSession
from app.models import Account, Notification
from app.schemas.report import AccountSummary, DashboardOut
from app.services import reports
from app.services.accounts import compute_balances, total_balance
from app.services.transactions import search_transactions

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(
    user: CurrentUser,
    db: DbSession,
    month: str | None = Query(default=None, description="Mes en formato AAAA-MM; por defecto, el actual"),
):
    """Resumen: saldo total, ingresos y gastos del periodo, cuentas y últimos movimientos."""
    start, end = reports.month_range(month)
    income, expenses = reports.period_totals(db, user.id, start, end)
    balances = compute_balances(db, user.id)
    accounts = db.scalars(
        select(Account)
        .where(Account.user_id == user.id, Account.is_active.is_(True))
        .order_by(Account.id)
    ).all()
    recent, _ = search_transactions(db, user.id, limit=5)
    unread = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user.id, Notification.is_read.is_(False))
    )
    return DashboardOut(
        period_start=start,
        period_end=end,
        total_balance=total_balance(db, user.id),
        income=income,
        expenses=expenses,
        net=income - expenses,
        accounts=[
            AccountSummary(id=a.id, name=a.name, currency=a.currency, balance=balances[a.id])
            for a in accounts
        ],
        recent_transactions=recent,
        unread_notifications=unread,
    )
