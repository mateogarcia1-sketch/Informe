import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.money import to_money
from app.models import Budget, Category, TransactionType
from app.schemas.budget import BudgetCreate, BudgetOut
from app.services.categories import get_user_category
from app.services.reports import spent_in_month


def budget_out(db: Session, user_id: int, budget: Budget, category: Category) -> BudgetOut:
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


def list_user_budgets(db: Session, user_id: int) -> list[BudgetOut]:
    rows = db.execute(
        select(Budget, Category)
        .join(Category, Category.id == Budget.category_id)
        .where(Budget.user_id == user_id)
        .order_by(Budget.id)
    ).all()
    return [budget_out(db, user_id, budget, category) for budget, category in rows]


def save_budget(db: Session, user_id: int, data: BudgetCreate, *, commit: bool = True) -> BudgetOut:
    category = get_user_category(db, user_id, data.category_id)
    if category.type != TransactionType.expense:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se pueden crear presupuestos para categorías de gasto")

    budget = Budget(user_id=user_id, **data.model_dump())
    try:
        with db.begin_nested():
            db.add(budget)
            db.flush()
    except IntegrityError:
        exists = db.scalar(
            select(Budget.id).where(Budget.user_id == user_id, Budget.category_id == category.id)
        )
        if exists is None:
            raise
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un presupuesto para esa categoría") from None

    result = budget_out(db, user_id, budget, category)
    if commit:
        db.commit()
    return result
