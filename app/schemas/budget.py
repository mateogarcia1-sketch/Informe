from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetCreate(BaseModel):
    category_id: int
    monthly_limit: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    alert_threshold: Decimal = Field(
        default=Decimal("0.80"),
        ge=Decimal("0.10"),
        le=Decimal("1.00"),
        max_digits=3,
        decimal_places=2,
        description="Fracción del límite a partir de la cual se envía una alerta",
    )


class BudgetOut(BaseModel):
    id: int
    category_id: int
    category_name: str
    monthly_limit: Decimal
    alert_threshold: Decimal
    spent: Decimal
    percentage_used: float
