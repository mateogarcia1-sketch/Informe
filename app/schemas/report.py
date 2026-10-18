import datetime as dt
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import TransactionType
from app.schemas.transaction import TransactionOut


class AccountSummary(BaseModel):
    id: int
    name: str
    currency: str
    balance: Decimal


class DashboardOut(BaseModel):
    period_start: dt.date
    period_end: dt.date
    total_balance: Decimal
    income: Decimal
    expenses: Decimal
    net: Decimal
    accounts: list[AccountSummary]
    recent_transactions: list[TransactionOut]
    unread_notifications: int


class CategoryReportItem(BaseModel):
    category_id: int
    category: str
    total: Decimal
    percentage: float
    count: int


class CategoryReport(BaseModel):
    date_from: dt.date
    date_to: dt.date
    type: TransactionType
    total: Decimal
    items: list[CategoryReportItem]


class MonthlyItem(BaseModel):
    month: int
    income: Decimal
    expenses: Decimal
    net: Decimal


class MonthlyReport(BaseModel):
    year: int
    months: list[MonthlyItem]


class InsightsOut(BaseModel):
    period_start: dt.date
    period_end: dt.date
    insights: list[str]
