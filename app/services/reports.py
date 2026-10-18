import calendar
import datetime as dt
import re
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.money import format_money, to_money
from app.models import Category, Transaction, TransactionType


def month_range(
    month: str | None = None, today: dt.date | None = None
) -> tuple[dt.date, dt.date]:
    """Primer y último día de un mes dado como 'AAAA-MM' (por defecto, el actual)."""
    today = today or dt.date.today()
    if month is None:
        year, mon = today.year, today.month
    else:
        match = re.fullmatch(r"(\d{4})-(\d{2})", month)
        if not match or not 1 <= int(match.group(2)) <= 12:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Formato de mes inválido, usa AAAA-MM"
            )
        year, mon = int(match.group(1)), int(match.group(2))
    last_day = calendar.monthrange(year, mon)[1]
    return dt.date(year, mon, 1), dt.date(year, mon, last_day)


def previous_month(today: dt.date) -> str:
    year, mon = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    return f"{year}-{mon:02d}"


def period_totals(
    db: Session, user_id: int, date_from: dt.date, date_to: dt.date
) -> tuple[Decimal, Decimal]:
    """Devuelve (ingresos, gastos) del periodo."""
    rows = db.execute(
        select(Transaction.type, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by(Transaction.type)
    ).all()
    totals = {tx_type: to_money(total) for tx_type, total in rows}
    return (
        totals.get(TransactionType.income, Decimal("0.00")),
        totals.get(TransactionType.expense, Decimal("0.00")),
    )


def by_category(
    db: Session,
    user_id: int,
    date_from: dt.date,
    date_to: dt.date,
    tx_type: TransactionType = TransactionType.expense,
) -> list[tuple[int, str, Decimal, int]]:
    """Totales por categoría, de mayor a menor: (id, nombre, total, cantidad)."""
    total_col = func.sum(Transaction.amount)
    rows = db.execute(
        select(Category.id, Category.name, total_col, func.count(Transaction.id))
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == tx_type,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by(Category.id, Category.name)
        .order_by(total_col.desc())
    ).all()
    return [(cid, name, to_money(total), count) for cid, name, total, count in rows]


def spent_in_month(
    db: Session, user_id: int, category_id: int, ref_date: dt.date
) -> Decimal:
    """Total gastado en una categoría durante el mes de ref_date."""
    start, end = month_range(f"{ref_date.year}-{ref_date.month:02d}")
    total = db.scalar(
        select(func.sum(Transaction.amount)).where(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.type == TransactionType.expense,
            Transaction.date >= start,
            Transaction.date <= end,
        )
    )
    return to_money(total)


def monthly_breakdown(db: Session, user_id: int, year: int) -> list[dict]:
    """Ingresos, gastos y balance de cada mes del año."""
    rows = db.execute(
        select(Transaction.date, Transaction.type, Transaction.amount).where(
            Transaction.user_id == user_id,
            Transaction.date >= dt.date(year, 1, 1),
            Transaction.date <= dt.date(year, 12, 31),
        )
    ).all()
    months = {m: {"income": Decimal("0.00"), "expenses": Decimal("0.00")} for m in range(1, 13)}
    for date, tx_type, amount in rows:
        key = "income" if tx_type == TransactionType.income else "expenses"
        months[date.month][key] += to_money(amount)
    return [
        {"month": m, **values, "net": values["income"] - values["expenses"]}
        for m, values in months.items()
    ]


def build_insights(db: Session, user_id: int, today: dt.date | None = None) -> list[str]:
    """Observaciones simples sobre los hábitos de gasto del mes actual."""
    today = today or dt.date.today()
    start, end = month_range(None, today)
    income, expenses = period_totals(db, user_id, start, end)

    if income == 0 and expenses == 0:
        return ["Aún no tienes movimientos este mes. Registra tus gastos e ingresos para ver tus insights."]

    insights: list[str] = []

    top = by_category(db, user_id, start, end)
    if top and expenses > 0:
        _, name, total, _ = top[0]
        pct = round(total / expenses * 100)
        insights.append(
            f"Tu mayor gasto del mes es {name}: {format_money(total)} ({pct}% de tus gastos)."
        )

    # Comparación con el mismo tramo del mes anterior
    prev_start, prev_end = month_range(previous_month(today))
    same_day = dt.date(prev_end.year, prev_end.month, min(today.day, prev_end.day))
    _, prev_expenses = period_totals(db, user_id, prev_start, same_day)
    if prev_expenses > 0:
        change = (expenses - prev_expenses) / prev_expenses * 100
        direction = "más" if change >= 0 else "menos"
        insights.append(
            f"Hasta el día {today.day} llevas un {abs(round(change))}% {direction} de gasto "
            f"que en el mismo periodo del mes pasado."
        )

    if expenses > 0:
        insights.append(
            f"Tu gasto diario promedio este mes es {format_money(expenses / today.day)}."
        )

    if income > 0:
        saved = income - expenses
        if saved >= 0:
            insights.append(f"Has ahorrado el {round(saved / income * 100)}% de tus ingresos este mes.")
        else:
            insights.append(
                f"Tus gastos superan tus ingresos este mes en {format_money(-saved)}."
            )
    return insights
