import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    institution: str = Field(default="", max_length=80)
    account_type: AccountType = AccountType.checking
    last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    currency: str = Field(default="COP", min_length=3, max_length=3)
    initial_balance: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    institution: str | None = Field(default=None, max_length=80)
    last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    is_active: bool | None = None


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    institution: str
    account_type: AccountType
    last4: str | None
    currency: str
    initial_balance: Decimal
    is_active: bool
    created_at: dt.datetime
    balance: Decimal = Decimal("0")
