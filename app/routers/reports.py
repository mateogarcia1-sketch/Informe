import datetime as dt

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession
from app.models import TransactionType
from app.schemas.report import (
    CategoryReport,
    CategoryReportItem,
    InsightsOut,
    MonthlyItem,
    MonthlyReport,
)
from app.services import reports

router = APIRouter(prefix="/reports", tags=["reportes"])


@router.get("/by-category", response_model=CategoryReport)
def report_by_category(
    user: CurrentUser,
    db: DbSession,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    type: TransactionType = TransactionType.expense,
):
    """Gasto (o ingreso) por categoría en un periodo; por defecto, el mes actual."""
    default_from, default_to = reports.month_range()
    date_from = date_from or default_from
    date_to = date_to or default_to
    if date_from > date_to:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "date_from no puede ser posterior a date_to"
        )

    rows = reports.by_category(db, user.id, date_from, date_to, type)
    grand_total = sum((total for _, _, total, _ in rows), start=0)
    items = [
        CategoryReportItem(
            category_id=cid,
            category=name,
            total=total,
            percentage=round(float(total / grand_total * 100), 2) if grand_total else 0.0,
            count=count,
        )
        for cid, name, total, count in rows
    ]
    return CategoryReport(
        date_from=date_from,
        date_to=date_to,
        type=type,
        total=grand_total,
        items=items,
    )


@router.get("/monthly", response_model=MonthlyReport)
def report_monthly(
    user: CurrentUser,
    db: DbSession,
    year: int = Query(default_factory=lambda: dt.date.today().year, ge=2000, le=2100),
):
    """Ingresos, gastos y balance mes a mes de un año."""
    months = reports.monthly_breakdown(db, user.id, year)
    return MonthlyReport(year=year, months=[MonthlyItem(**m) for m in months])


@router.get("/insights", response_model=InsightsOut)
def insights(user: CurrentUser, db: DbSession):
    """Observaciones sobre tus patrones de gasto del mes actual."""
    start, end = reports.month_range()
    return InsightsOut(
        period_start=start,
        period_end=end,
        insights=reports.build_insights(db, user.id),
    )
