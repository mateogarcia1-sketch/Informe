from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Budget(Base):
    """Límite mensual de gasto para una categoría."""

    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "category_id", name="uq_budget_user_category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    monthly_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    # Fracción del límite a partir de la cual se envía una alerta (0.80 = 80%)
    alert_threshold: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal("0.80")
    )
