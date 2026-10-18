from decimal import Decimal

import pytest

from app.services.bot import detect_intent, normalize, parse_amount


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("gasté 20.000 en comida", Decimal("20000")),
        ("pagué 20000", Decimal("20000")),
        ("gasté 20k", Decimal("20000")),
        ("pagué 80 mil de arriendo", Decimal("80000")),
        ("me pagaron 1.500.000", Decimal("1500000")),
        ("recibí 1.5 millones", Decimal("1500000")),
        ("recibí 2,5 millones", Decimal("2500000")),
        ("gasté 12500,50", Decimal("12500.50")),
        ("hola, ¿qué tal?", None),
    ],
)
def test_parse_amount(texto, esperado):
    assert parse_amount(texto) == esperado


def test_normalize_quita_tildes():
    assert normalize("  Gasté   MÁS  ") == "gaste mas"


@pytest.mark.parametrize(
    "texto, intencion",
    [
        ("gasté 20000 en comida", "expense"),
        ("recibí mi salario", "income"),
        ("me pagaron 500000", "income"),
        ("cuánto tengo", "balance"),
        ("cuánto gasté este mes", "spending"),
        ("últimos movimientos", "recent"),
        ("dame un resumen", "summary"),
        ("buenos días", "help"),
    ],
)
def test_detect_intent(texto, intencion):
    assert detect_intent(normalize(texto)) == intencion


def mensaje(client, headers, texto):
    response = client.post("/bot/message", json={"text": texto}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_bot_requiere_autenticacion(client):
    assert client.post("/bot/message", json={"text": "hola"}).status_code == 401


def test_bot_registra_un_gasto(client, auth_headers, account_id, categories):
    respuesta = mensaje(client, auth_headers, "gasté 20.000 en almuerzo")
    assert respuesta["action"] == "transaction_created"
    assert "$20.000" in respuesta["reply"]

    historial = client.get("/transactions", headers=auth_headers).json()
    assert historial["total"] == 1
    tx = historial["items"][0]
    assert Decimal(tx["amount"]) == Decimal("20000")
    assert tx["type"] == "expense"
    assert tx["category_id"] == categories["Alimentación"]
    assert tx["account_id"] == account_id


def test_bot_registra_un_ingreso(client, auth_headers, account_id, categories):
    respuesta = mensaje(client, auth_headers, "recibí 1.500.000 de salario")
    assert respuesta["action"] == "transaction_created"
    assert respuesta["data"]["category"] == "Salario"

    cuenta = client.get(f"/accounts/{account_id}", headers=auth_headers).json()
    assert Decimal(cuenta["balance"]) == Decimal("2500000")


def test_bot_usa_otros_gastos_si_no_reconoce_la_categoria(client, auth_headers, account_id):
    respuesta = mensaje(client, auth_headers, "gasté 5000 en algo raro")
    assert respuesta["data"]["category"] == "Otros gastos"


def test_bot_gasto_de_ayer(client, auth_headers, account_id):
    respuesta = mensaje(client, auth_headers, "ayer gasté 3000 en bus")
    assert respuesta["data"]["category"] == "Transporte"
    tx = client.get("/transactions", headers=auth_headers).json()["items"][0]
    assert tx["date"] == respuesta["data"]["date"]


def test_bot_pide_monto_si_falta(client, auth_headers, account_id):
    respuesta = mensaje(client, auth_headers, "gasté en comida")
    assert respuesta["action"] == "needs_info"
    assert client.get("/transactions", headers=auth_headers).json()["total"] == 0


def test_bot_sin_cuentas(client, auth_headers):
    respuesta = mensaje(client, auth_headers, "gasté 5000 en bus")
    assert respuesta["action"] == "needs_info"
    assert "cuenta" in respuesta["reply"]


def test_bot_pregunta_la_cuenta_si_hay_varias(client, auth_headers, account_id):
    nequi = client.post(
        "/accounts",
        json={"name": "Nequi", "account_type": "wallet", "initial_balance": "0"},
        headers=auth_headers,
    ).json()

    ambiguo = mensaje(client, auth_headers, "gasté 5000 en bus")
    assert ambiguo["action"] == "needs_info"
    assert "Nequi" in ambiguo["reply"]
    assert client.get("/transactions", headers=auth_headers).json()["total"] == 0

    claro = mensaje(client, auth_headers, "gasté 5000 en bus con nequi")
    assert claro["action"] == "transaction_created"
    tx = client.get("/transactions", headers=auth_headers).json()["items"][0]
    assert tx["account_id"] == nequi["id"]


def test_bot_consulta_saldo(client, auth_headers, account_id):
    respuesta = mensaje(client, auth_headers, "cuánto tengo")
    assert respuesta["action"] == "balance"
    assert "$1.000.000" in respuesta["reply"]
    assert "Bancolombia" in respuesta["reply"]


def test_bot_consulta_gasto_por_categoria(client, auth_headers, account_id):
    mensaje(client, auth_headers, "gasté 20.000 en almuerzo")
    mensaje(client, auth_headers, "gasté 30.000 en mercado")
    mensaje(client, auth_headers, "pagué 10.000 de taxi")

    comida = mensaje(client, auth_headers, "cuánto gasté en comida este mes")
    assert comida["action"] == "spending"
    assert "$50.000" in comida["reply"]

    total = mensaje(client, auth_headers, "cuánto gasté este mes")
    assert "$60.000" in total["reply"]


def test_bot_ultimos_movimientos_y_resumen(client, auth_headers, account_id):
    vacio = mensaje(client, auth_headers, "últimos movimientos")
    assert "Aún no tienes movimientos" in vacio["reply"]

    mensaje(client, auth_headers, "recibí 500.000 de salario")
    mensaje(client, auth_headers, "gasté 100.000 en mercado")

    recientes = mensaje(client, auth_headers, "últimos movimientos")
    assert recientes["reply"].count("\n- ") == 2

    resumen = mensaje(client, auth_headers, "resumen")
    assert resumen["action"] == "summary"
    assert "$500.000" in resumen["reply"]
    assert "Alimentación" in resumen["reply"]


def test_bot_ayuda_con_mensaje_desconocido(client, auth_headers):
    respuesta = mensaje(client, auth_headers, "buenos días")
    assert respuesta["action"] == "help"
    assert "gasté" in respuesta["reply"]


def test_bot_dispara_alertas_de_presupuesto(client, auth_headers, account_id, categories):
    client.post(
        "/budgets",
        json={"category_id": categories["Alimentación"], "monthly_limit": "50000"},
        headers=auth_headers,
    )
    mensaje(client, auth_headers, "gasté 45.000 en comida")
    kinds = [n["kind"] for n in client.get("/notifications", headers=auth_headers).json()]
    assert kinds == ["budget_warning"]
