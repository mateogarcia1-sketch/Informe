from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import delete, func, select

from app.core.deps import CurrentUser, DbSession
from app.models import Budget, Category, Transaction, TransactionType
from app.schemas.category import CategoryCreate, CategoryOut
from app.services.categories import get_user_category

router = APIRouter(prefix="/categories", tags=["categorías"])


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, user: CurrentUser, db: DbSession):
    exists = db.scalar(
        select(Category).where(
            Category.user_id == user.id,
            Category.name == data.name,
            Category.type == data.type,
        )
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe esa categoría")
    category = Category(user_id=user.id, name=data.name, type=data.type)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=list[CategoryOut])
def list_categories(
    user: CurrentUser, db: DbSession, type: TransactionType | None = None
):
    query = select(Category).where(Category.user_id == user.id).order_by(Category.id)
    if type is not None:
        query = query.where(Category.type == type)
    return db.scalars(query).all()


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, user: CurrentUser, db: DbSession):
    category = get_user_category(db, user.id, category_id)
    used = db.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.category_id == category.id)
    )
    if used:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La categoría tiene movimientos y no puede eliminarse",
        )
    db.execute(delete(Budget).where(Budget.category_id == category.id))
    db.delete(category)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
