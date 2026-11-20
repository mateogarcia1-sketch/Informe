"""Bot de lenguaje natural.

Interpreta mensajes en español con un clasificador de presupuestos y reglas locales, y
ejecuta las mismas operaciones que el usuario haría en la aplicación:
registrar gastos e ingresos, consultar saldo, movimientos y resúmenes.
"""
import datetime as dt
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.money import format_money, to_money
from app.models import Account, Category, TransactionType, User
from app.schemas.bot import BotReply
from app.schemas.budget import BudgetCreate
from app.schemas.transaction import TransactionCreate
from app.services import reports
from app.services.accounts import compute_balances, total_balance
from app.services.budget_intent import classify_budget
from app.services.budgets import list_user_budgets, save_budget
from app.services.transactions import create_transaction, search_transactions

HELP_TEXT = (
    "Puedo ayudarte con cosas como:\n"
    "- «gasté 20.000 en almuerzo» o «pagué 80k de arriendo con Nequi»\n"
    "- «recibí 1.500.000 de salario»\n"
    "- «cuánto tengo» (saldo)\n"
    "- «cuánto gasté en comida este mes»\n"
    "- «últimos movimientos»\n"
    "- «resumen»\n"
    "- «crea un presupuesto de 45.000 para transporte»"
)

AMOUNT_RE = re.compile(r"(?<![\w.,])(\d+(?:[.,]\d+)*)\s*(millones|millon|mil|k)?(?!\w)")
INCOME_RE = re.compile(
    r"\b(recibi|me pagaron|me pagan|me llego|me consignaron|me depositaron|gane|cobre|ingreso|ingrese)\b"
)
EXPENSE_RE = re.compile(r"\b(gaste|pague|compre|gasto|pago|me cobraron)\b")

MULTIPLIERS = {"k": 1_000, "mil": 1_000, "millon": 1_000_000, "millones": 1_000_000}

# Palabras que sugieren una categoría (clave = nombre normalizado de la categoría)
SYNONYMS = {
    "alimentacion": ["comida", "mercado", "restaurante", "almuerzo", "cena", "desayuno",
                     "supermercado", "domicilio", "cafe", "snack"],
    "transporte": ["bus", "taxi", "uber", "gasolina", "metro", "pasaje", "transporte", "parqueadero"],
    "vivienda": ["arriendo", "renta", "alquiler", "hipoteca", "administracion"],
    "servicios": ["luz", "agua", "internet", "gas", "celular", "telefono", "servicios"],
    "salud": ["medico", "doctor", "medicina", "medicinas", "farmacia", "drogueria", "salud"],
    "educacion": ["matricula", "curso", "universidad", "libros", "educacion"],
    "entretenimiento": ["cine", "netflix", "spotify", "juego", "fiesta", "concierto", "entretenimiento"],
    "ropa": ["ropa", "zapatos", "camisa", "pantalon"],
    "salario": ["salario", "sueldo", "nomina", "quincena"],
    "ventas": ["venta", "ventas", "vendi"],
}


def normalize(text: str) -> str:
    """Minúsculas, sin tildes y con espacios simples."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def parse_amount(text: str) -> Decimal | None:
    """Extrae el primer monto del texto: 20.000, 20k, 2 mil, 1,5 millones..."""
    match = AMOUNT_RE.search(normalize(text))
    if not match:
        return None
    raw, suffix = match.groups()
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", raw):
        number = Decimal(re.sub(r"[.,]", "", raw))  # separadores de miles
    else:
        try:
            number = Decimal(raw.replace(",", "."))
        except InvalidOperation:
            return None
    if suffix:
        number *= MULTIPLIERS[suffix]
    return to_money(number) if number > 0 else None


def _has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def detect_intent(t: str) -> str:
    budget_intent = classify_budget(t)
    if budget_intent:
        return budget_intent
    if "cuanto" in t and re.search(r"\bgast\w*", t):
        return "spending"
    if any(p in t for p in ("saldo", "cuanto tengo", "cuanta plata tengo", "cuanto dinero tengo", "balance")):
        return "balance"
    if any(p in t for p in ("ultimos movimientos", "ultimas transacciones", "ultimos gastos",
                            "movimientos recientes", "historial")):
        return "recent"
    if any(p in t for p in ("resumen", "como voy", "como van mis finanzas")):
        return "summary"
    if INCOME_RE.search(t):
        return "income"
    if EXPENSE_RE.search(t):
        return "expense"
    return "help"


def _user_categories(db: Session, user_id: int, tx_type: TransactionType) -> list[Category]:
    return list(
        db.scalars(
            select(Category)
            .where(Category.user_id == user_id, Category.type == tx_type)
            .order_by(Category.id)
        )
    )


def find_category(
    db: Session, user_id: int, t: str, tx_type: TransactionType
) -> Category | None:
    categories = _user_categories(db, user_id, tx_type)
    by_name = {normalize(c.name): c for c in categories}
    for name, category in by_name.items():
        if _has_word(t, name):
            return category
    for name, words in SYNONYMS.items():
        if name in by_name and any(_has_word(t, w) for w in words):
            return by_name[name]
    return None


def fallback_category(db: Session, user_id: int, tx_type: TransactionType) -> Category | None:
    categories = _user_categories(db, user_id, tx_type)
    for category in categories:
        if normalize(category.name).startswith("otros"):
            return category
    return categories[0] if categories else None


def find_account(db: Session, user_id: int, t: str) -> tuple[Account | None, list[Account]]:
    accounts = list(
        db.scalars(
            select(Account)
            .where(Account.user_id == user_id, Account.is_active.is_(True))
            .order_by(Account.id)
        )
    )
    for account in accounts:
        for candidate in (account.name, account.institution):
            name = normalize(candidate or "")
            if name and _has_word(t, name):
                return account, accounts
    if len(accounts) == 1:
        return accounts[0], accounts
    return None, accounts


def _period(t: str, today: dt.date) -> tuple[dt.date, dt.date, str]:
    if _has_word(t, "hoy"):
        return today, today, "hoy"
    if _has_word(t, "ayer"):
        yesterday = today - dt.timedelta(days=1)
        return yesterday, yesterday, "ayer"
    if _has_word(t, "semana"):
        return today - dt.timedelta(days=today.weekday()), today, "esta semana"
    if "mes pasado" in t:
        start, end = reports.month_range(reports.previous_month(today), today)
        return start, end, "el mes pasado"
    start, end = reports.month_range(None, today)
    return start, end, "este mes"


def _register(db: Session, user: User, text: str, t: str, tx_type: TransactionType, *, commit: bool) -> BotReply:
    amount = parse_amount(text)
    if amount is None:
        return BotReply(
            action="needs_info",
            reply="No encontré el monto. Prueba por ejemplo: «gasté 20.000 en comida».",
        )

    account, accounts = find_account(db, user.id, t)
    if not accounts:
        return BotReply(
            action="needs_info",
            reply="Primero debes vincular una cuenta para poder registrar movimientos.",
        )
    if account is None:
        nombres = ", ".join(a.name for a in accounts)
        return BotReply(
            action="needs_info",
            reply=f"¿En cuál cuenta? Tus cuentas son: {nombres}. "
            "Repite el mensaje mencionándola, por ejemplo: «... con " + accounts[0].name + "».",
        )

    category = find_category(db, user.id, t, tx_type) or fallback_category(db, user.id, tx_type)
    if category is None:
        return BotReply(action="needs_info", reply="No tienes categorías de ese tipo creadas.")

    when = dt.date.today() - dt.timedelta(days=1) if _has_word(t, "ayer") else dt.date.today()
    try:
        data = TransactionCreate(
            account_id=account.id,
            category_id=category.id,
            type=tx_type,
            amount=amount,
            description=text.strip()[:255],
            date=when,
        )
    except ValidationError:
        return BotReply(action="needs_info", reply="El monto indicado no es válido.")

    tx = create_transaction(db, user, data, commit=commit)
    kind = "gasto" if tx_type == TransactionType.expense else "ingreso"
    return BotReply(
        action="transaction_created",
        reply=f"Listo, registré un {kind} de {format_money(amount)} en {category.name} "
        f"(cuenta {account.name}).",
        data={
            "transaction_id": tx.id,
            "type": tx_type.value,
            "amount": str(amount),
            "category": category.name,
            "account": account.name,
            "date": when.isoformat(),
        },
    )


def _balance(db: Session, user: User) -> BotReply:
    accounts = list(
        db.scalars(
            select(Account)
            .where(Account.user_id == user.id, Account.is_active.is_(True))
            .order_by(Account.id)
        )
    )
    if not accounts:
        return BotReply(action="balance", reply="Aún no tienes cuentas vinculadas.")
    balances = compute_balances(db, user.id)
    lines = [f"Tu saldo total es {format_money(total_balance(db, user.id))}."]
    lines += [f"- {a.name}: {format_money(balances[a.id])}" for a in accounts]
    return BotReply(action="balance", reply="\n".join(lines))


def _spending(db: Session, user: User, t: str) -> BotReply:
    today = dt.date.today()
    start, end, label = _period(t, today)
    category = find_category(db, user.id, t, TransactionType.expense)
    rows = reports.by_category(db, user.id, start, end, TransactionType.expense)
    if category is not None:
        total = next((r[2] for r in rows if r[0] == category.id), to_money(0))
        reply = f"Gastaste {format_money(total)} en {category.name} {label}."
    else:
        total = sum((r[2] for r in rows), start=to_money(0))
        reply = f"Gastaste {format_money(total)} en total {label}."
    return BotReply(action="spending", reply=reply, data={"total": str(total)})


def _recent(db: Session, user: User) -> BotReply:
    items, _ = search_transactions(db, user.id, limit=5)
    if not items:
        return BotReply(action="recent", reply="Aún no tienes movimientos registrados.")
    lines = ["Tus últimos movimientos:"]
    for tx in items:
        kind = "gasto" if tx.type == TransactionType.expense else "ingreso"
        detail = f" · {tx.description}" if tx.description else ""
        lines.append(f"- {tx.date.isoformat()} · {kind} · {format_money(tx.amount)}{detail}")
    return BotReply(action="recent", reply="\n".join(lines))


def _summary(db: Session, user: User) -> BotReply:
    start, end = reports.month_range()
    income, expenses = reports.period_totals(db, user.id, start, end)
    lines = [
        f"Resumen de este mes: ingresos {format_money(income)}, "
        f"gastos {format_money(expenses)}, balance {format_money(income - expenses)}."
    ]
    top = reports.by_category(db, user.id, start, end)
    if top:
        lines.append(f"Tu mayor gasto es {top[0][1]} ({format_money(top[0][2])}).")
    return BotReply(action="summary", reply="\n".join(lines))


def _register_budget(db: Session, user: User, text: str, *, commit: bool) -> BotReply:
    if re.search(r"\b(semanal|quincenal|anual|diario|por semana|por dia|por ano)\b", text):
        return BotReply(action="needs_info", reply="Los presupuestos son mensuales. ¿Qué límite quieres fijar por mes?")
    category = find_category(db, user.id, text, TransactionType.expense)
    if category is None:
        categories = _user_categories(db, user.id, TransactionType.expense)
        names = ", ".join(item.name for item in categories[:8])
        return BotReply(
            action="needs_info",
            reply=f"Indica una categoría de gasto en el mensaje. Puedes usar {names}."
            if names else "Crea una categoría de gasto en la web y vuelve a escribir el presupuesto.",
        )

    amounts = list(AMOUNT_RE.finditer(text))
    if len(amounts) != 1 or text[:amounts[0].start()].rstrip().rstrip("$").rstrip().endswith(("-", "−")):
        return BotReply(
            action="needs_info",
            reply=f"Indica un solo monto mensual positivo. Por ejemplo, «crea un presupuesto de 100.000 para {category.name}».",
        )
    try:
        data = BudgetCreate(category_id=category.id, monthly_limit=parse_amount(text))
    except (ValidationError, InvalidOperation):
        return BotReply(action="needs_info", reply="Indica un límite mensual positivo con hasta dos decimales.")
    try:
        budget = save_budget(db, user.id, data, commit=commit)
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
        return BotReply(
            action="budget_exists",
            reply=f"Ya tienes un presupuesto para {category.name}. Puedes revisarlo en Presupuestos.",
        )

    remaining = budget.monthly_limit - budget.spent
    progress = (
        f"Has gastado {format_money(budget.spent)} este mes y te quedan {format_money(remaining)}."
        if remaining >= 0
        else f"Ya superaste el límite de este mes por {format_money(-remaining)}."
    )
    return BotReply(
        action="budget_created",
        reply=f"Registré el presupuesto mensual de {category.name} por {format_money(budget.monthly_limit)}. {progress}",
        data=budget.model_dump(mode="json"),
    )


def _list_budgets(db: Session, user: User) -> BotReply:
    budgets = list_user_budgets(db, user.id)
    if not budgets:
        return BotReply(action="budget_list", reply="Todavía no tienes presupuestos. Prueba «crea un presupuesto de 45.000 para transporte».")
    lines = ["Tus presupuestos mensuales:"]
    for item in budgets:
        lines.append(f"- {item.category_name}: {format_money(item.spent)} gastados de {format_money(item.monthly_limit)}.")
    return BotReply(action="budget_list", reply="\n".join(lines))


def handle_message(db: Session, user: User, text: str, *, commit: bool = True) -> BotReply:
    """Interpreta el mensaje del usuario y ejecuta la acción correspondiente."""
    t = normalize(text)
    intent = detect_intent(t)
    if intent == "budget_create":
        return _register_budget(db, user, t, commit=commit)
    if intent == "budget_list":
        return _list_budgets(db, user)
    if intent == "budget_help":
        return BotReply(action="needs_info", reply="Para crear un presupuesto, indica categoría y monto mensual. También puedes escribir «ver mis presupuestos».")
    if intent == "spending":
        return _spending(db, user, t)
    if intent == "balance":
        return _balance(db, user)
    if intent == "recent":
        return _recent(db, user)
    if intent == "summary":
        return _summary(db, user)
    if intent == "income":
        return _register(db, user, text, t, TransactionType.income, commit=commit)
    if intent == "expense":
        return _register(db, user, text, t, TransactionType.expense, commit=commit)
    return BotReply(action="help", reply=HELP_TEXT)
