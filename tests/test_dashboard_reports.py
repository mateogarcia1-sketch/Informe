import datetime as dt
from decimal import Decimal

HOY = dt.date.today().isoformat()


def crear(client, headers, account_id, category_id, tipo="expense", monto="10000", fecha=HOY):
    response = client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": tipo,
            "amount": monto,
            "description": "prueba",
            "date": fecha,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_dashboard_resume_el_mes(client, auth_headers, account_id, categories):
    crear(client, auth_headers, account_id, categories["Salario"], "income", "500000")
    crear(client, auth_headers, account_id, categories["Alimentación"], "expense", "200000")

    body = client.get("/dashboard", headers=auth_headers).json()
    assert Decimal(body["income"]) == Decimal("500000")
    assert Decimal(body["expenses"]) == Decimal("200000")
    assert Decimal(body["net"]) == Decimal("300000")
    assert Decimal(body["total_balance"]) == Decimal("1300000")
    assert len(body["accounts"]) == 1
    assert len(body["recent_transactions"]) == 2
    assert body["unread_notifications"] == 0


def test_dashboard_mes_especifico_y_formato_invalido(client, auth_headers, account_id, categories):
    crear(client, auth_headers, account_id, categories["Alimentación"], "expense", "40000", "2026-03-15")

    marzo = client.get("/dashboard?month=2026-03", headers=auth_headers).json()
    assert Decimal(marzo["expenses"]) == Decimal("40000")
    assert marzo["period_start"] == "2026-03-01"
    assert marzo["period_end"] == "2026-03-31"

    assert client.get("/dashboard?month=marzo", headers=auth_headers).status_code == 400
    assert client.get("/dashboard?month=2026-13", headers=auth_headers).status_code == 400


def test_dashboard_no_cuenta_cuentas_inactivas(client, auth_headers, account_id):
    client.patch(f"/accounts/{account_id}", json={"is_active": False}, headers=auth_headers)
    body = client.get("/dashboard", headers=auth_headers).json()
    assert Decimal(body["total_balance"]) == Decimal("0")
    assert body["accounts"] == []


def test_reporte_por_categoria(client, auth_headers, account_id, categories):
    crear(client, auth_headers, account_id, categories["Alimentación"], monto="30000")
    crear(client, auth_headers, account_id, categories["Alimentación"], monto="70000")
    crear(client, auth_headers, account_id, categories["Transporte"], monto="50000")

    body = client.get("/reports/by-category", headers=auth_headers).json()
    assert Decimal(body["total"]) == Decimal("150000")
    assert [i["category"] for i in body["items"]] == ["Alimentación", "Transporte"]
    primero = body["items"][0]
    assert Decimal(primero["total"]) == Decimal("100000")
    assert primero["count"] == 2
    assert primero["percentage"] == 66.67


def test_reporte_por_categoria_ingresos_y_rango(client, auth_headers, account_id, categories):
    crear(client, auth_headers, account_id, categories["Salario"], "income", "900000", "2026-01-10")
    crear(client, auth_headers, account_id, categories["Salario"], "income", "100000", "2026-02-10")

    body = client.get(
        "/reports/by-category?type=income&date_from=2026-01-01&date_to=2026-01-31",
        headers=auth_headers,
    ).json()
    assert Decimal(body["total"]) == Decimal("900000")

    invalido = client.get(
        "/reports/by-category?date_from=2026-02-01&date_to=2026-01-01", headers=auth_headers
    )
    assert invalido.status_code == 400


def test_reporte_mensual(client, auth_headers, account_id, categories):
    crear(client, auth_headers, account_id, categories["Salario"], "income", "2000000", "2026-01-05")
    crear(client, auth_headers, account_id, categories["Alimentación"], "expense", "300000", "2026-01-20")
    crear(client, auth_headers, account_id, categories["Alimentación"], "expense", "100000", "2026-03-02")

    body = client.get("/reports/monthly?year=2026", headers=auth_headers).json()
    assert len(body["months"]) == 12
    enero, febrero, marzo = body["months"][0], body["months"][1], body["months"][2]
    assert Decimal(enero["income"]) == Decimal("2000000")
    assert Decimal(enero["net"]) == Decimal("1700000")
    assert Decimal(febrero["expenses"]) == Decimal("0")
    assert Decimal(marzo["expenses"]) == Decimal("100000")


def test_insights_sin_movimientos(client, auth_headers):
    body = client.get("/reports/insights", headers=auth_headers).json()
    assert len(body["insights"]) == 1
    assert "Aún no tienes movimientos" in body["insights"][0]


def test_insights_con_movimientos(client, auth_headers, account_id, categories):
    crear(client, auth_headers, account_id, categories["Salario"], "income", "1000000")
    crear(client, auth_headers, account_id, categories["Alimentación"], "expense", "250000")

    textos = client.get("/reports/insights", headers=auth_headers).json()["insights"]
    unido = " ".join(textos)
    assert "Alimentación" in unido
    assert "promedio" in unido
    assert "ahorrado el 75%" in unido


def test_reportes_requieren_autenticacion(client):
    assert client.get("/dashboard").status_code == 401
    assert client.get("/reports/by-category").status_code == 401
    assert client.get("/reports/monthly").status_code == 401
    assert client.get("/reports/insights").status_code == 401
