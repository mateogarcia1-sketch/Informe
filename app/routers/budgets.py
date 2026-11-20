from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.models import Budget
from app.schemas.budget import BudgetCreate, BudgetOut
from app.services.budgets import list_user_budgets, save_budget

router = APIRouter(prefix="/budgets", tags=["presupuestos"])


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(data: BudgetCreate, user: CurrentUser, db: DbSession):
    """Define un límite mensual de gasto para una categoría."""
    return save_budget(db, user.id, data)


@router.get("", response_model=list[BudgetOut])
def list_budgets(user: CurrentUser, db: DbSession):
    return list_user_budgets(db, user.id)


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
