from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def to_money(value) -> Decimal:
    """Convierte cualquier valor numérico a Decimal con 2 decimales."""
    return Decimal(str(value or 0)).quantize(CENTS, rounding=ROUND_HALF_UP)


def format_money(value) -> str:
    """Formatea un valor en pesos, por ejemplo $1.500.000."""
    amount = to_money(value)
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.0f}".replace(",", ".")
