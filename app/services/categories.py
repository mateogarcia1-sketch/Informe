from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Category, TransactionType

DEFAULT_CATEGORIES = [
    ("Alimentación", TransactionType.expense),
    ("Transporte", TransactionType.expense),
    ("Vivienda", TransactionType.expense),
    ("Servicios", TransactionType.expense),
    ("Salud", TransactionType.expense),
    ("Educación", TransactionType.expense),
    ("Entretenimiento", TransactionType.expense),
    ("Ropa", TransactionType.expense),
    ("Otros gastos", TransactionType.expense),
    ("Salario", TransactionType.income),
    ("Ventas", TransactionType.income),
    ("Otros ingresos", TransactionType.income),
]


def create_default_categories(db: Session, user_id: int) -> None:
    """Crea las categorías iniciales para un usuario nuevo."""
    db.add_all(
        Category(user_id=user_id, name=name, type=tx_type)
        for name, tx_type in DEFAULT_CATEGORIES
    )


def get_user_category(db: Session, user_id: int, category_id: int) -> Category:
    category = db.scalar(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoría no encontrada")
    return category
