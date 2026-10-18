import datetime as dt
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import AccountType


class Account(Base):
    """Cuenta financiera vinculada por el usuario.

    Por seguridad solo se guardan los últimos 4 dígitos (last4); nunca el
    número completo ni credenciales bancarias.
    """

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    institution: Mapped[str] = mapped_column(String(80), default="")
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, native_enum=False, length=20), default=AccountType.checking
    )
    last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="COP")
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
