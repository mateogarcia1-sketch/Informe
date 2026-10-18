from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.money import format_money
from app.models import (
    Budget,
    Category,
    Notification,
    NotificationKind,
    Transaction,
    TransactionType,
    User,
)
from app.services.reports import spent_in_month


def notify(db: Session, user_id: int, kind: NotificationKind, message: str) -> None:
    db.add(Notification(user_id=user_id, kind=kind, message=message))


def check_after_transaction(db: Session, user: User, tx: Transaction) -> None:
    """Genera alertas después de registrar un movimiento.

    Debe llamarse con el movimiento ya enviado a la base de datos (flush),
    para que los totales del mes lo incluyan.
    """
    if tx.amount >= settings.large_transaction_amount:
        tipo = "ingreso" if tx.type == TransactionType.income else "gasto"
        notify(
            db,
            user.id,
            NotificationKind.large_transaction,
            f"Movimiento importante: se registró un {tipo} de {format_money(tx.amount)}.",
        )

    if tx.type != TransactionType.expense:
        return

    budget = db.scalar(
        select(Budget).where(
            Budget.user_id == user.id, Budget.category_id == tx.category_id
        )
    )
    if budget is None:
        return

    category = db.get(Category, tx.category_id)
    limit = budget.monthly_limit
    warn_at = limit * budget.alert_threshold
    spent = spent_in_month(db, user.id, tx.category_id, tx.date)
    before = spent - tx.amount

    # Solo se alerta al cruzar cada umbral, para no repetir mensajes
    if spent > limit and before <= limit:
        notify(
            db,
            user.id,
            NotificationKind.budget_exceeded,
            f"Superaste tu presupuesto de {category.name}: llevas "
            f"{format_money(spent)} de {format_money(limit)} este mes.",
        )
    elif warn_at <= spent <= limit and before < warn_at:
        percent = int(spent / limit * 100)
        notify(
            db,
            user.id,
            NotificationKind.budget_warning,
            f"Alerta: ya usaste el {percent}% de tu presupuesto de {category.name} "
            f"({format_money(spent)} de {format_money(limit)}).",
        )
