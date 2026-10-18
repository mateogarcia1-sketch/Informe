import enum


class AccountType(str, enum.Enum):
    checking = "checking"  # cuenta corriente
    savings = "savings"  # cuenta de ahorros
    credit_card = "credit_card"  # tarjeta de crédito
    cash = "cash"  # efectivo
    wallet = "wallet"  # billetera digital (Nequi, Daviplata, etc.)


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class NotificationKind(str, enum.Enum):
    large_transaction = "large_transaction"
    budget_warning = "budget_warning"
    budget_exceeded = "budget_exceeded"
