import datetime as dt
from decimal import Decimal

from app.models import (
    Account,
    Category,
    Transaction,
    TransactionType,
    User,
)


def test_crear_y_leer_movimiento(db_session):
    user = User(
        email="ana@example.com",
        full_name="Ana Pérez",
        password_hash="x",
        birth_date=dt.date(1995, 5, 10),
    )
    db_session.add(user)
    db_session.flush()

    account = Account(user_id=user.id, name="Bancolombia", initial_balance=Decimal("1000"))
    category = Category(user_id=user.id, name="Alimentación", type=TransactionType.expense)
    db_session.add_all([account, category])
    db_session.flush()

    db_session.add(
        Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            type=TransactionType.expense,
            amount=Decimal("1500.50"),
            description="Mercado",
            date=dt.date(2026, 10, 5),
        )
    )
    db_session.commit()

    saved = db_session.query(Transaction).one()
    assert saved.amount == Decimal("1500.50")
    assert saved.type == TransactionType.expense
    assert saved.date == dt.date(2026, 10, 5)
