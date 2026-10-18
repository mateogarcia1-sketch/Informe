import datetime as dt
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TransactionType


class Transaction(Base):
    """Movimiento de dinero (ingreso o gasto) asociado a una cuenta y categoría."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False, length=20)
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    description: Mapped[str] = mapped_column(String(255), default="")
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
