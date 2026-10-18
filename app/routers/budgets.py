import datetime as dt

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.money import to_money
from app.models import Budget, Category, TransactionType
from app.schemas.budget import BudgetCreate, BudgetOut
from app.services.categories import get_user_category
from app.services.reports import spent_in_month

router = APIRouter(prefix="/budgets", tags=["presupuestos"])


def _to_out(db, user_id: int, budget: Budget, category: Category) -> BudgetOut:
    spent = spent_in_month(db, user_id, budget.category_id, dt.date.today())
    limit = to_money(budget.monthly_limit)
    return BudgetOut(
        id=budget.id,
        category_id=budget.category_id,
        category_name=category.name,
        monthly_limit=limit,
        alert_threshold=budget.alert_threshold,
        spent=spent,
        percentage_used=round(float(spent / limit * 100), 2),
    )


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(data: BudgetCreate, user: CurrentUser, db: DbSession):
    """Define un límite mensual de gasto para una categoría."""
    category = get_user_category(db, user.id, data.category_id)
    if category.type != TransactionType.expense:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Solo se pueden crear presupuestos para categorías de gasto",
        )
    exists = db.scalar(
        select(Budget).where(Budget.user_id == user.id, Budget.category_id == category.id)
    )
    if exists:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un presupuesto para esa categoría"
        )
    budget = Budget(user_id=user.id, **data.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return _to_out(db, user.id, budget, category)


@router.get("", response_model=list[BudgetOut])
def list_budgets(user: CurrentUser, db: DbSession):
    rows = db.execute(
        select(Budget, Category)
        .join(Category, Category.id == Budget.category_id)
        .where(Budget.user_id == user.id)
        .order_by(Budget.id)
    ).all()
    return [_to_out(db, user.id, budget, category) for budget, category in rows]


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, user: CurrentUser, db: DbSession):
    budget = db.scalar(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user.id)
    )
    if budget is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Presupuesto no encontrado")
    db.delete(budget)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
