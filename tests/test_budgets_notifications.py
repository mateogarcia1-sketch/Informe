import datetime as dt
from decimal import Decimal

HOY = dt.date.today().isoformat()


def gastar(client, headers, account_id, category_id, monto):
    response = client.post(
        "/transactions",
        json={
            "account_id": account_id,
            "category_id": category_id,
            "type": "expense",
            "amount": str(monto),
            "description": "prueba",
            "date": HOY,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text


def notificaciones(client, headers, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return client.get(f"/notifications?{query}", headers=headers).json()


def crear_presupuesto(client, headers, category_id, limite="100000", **extra):
    return client.post(
        "/budgets",
        json={"category_id": category_id, "monthly_limit": limite, **extra},
        headers=headers,
    )


def test_crear_y_listar_presupuesto(client, auth_headers, account_id, categories):
    response = crear_presupuesto(client, auth_headers, categories["Alimentación"])
    assert response.status_code == 201
    assert response.json()["category_name"] == "Alimentación"

    gastar(client, auth_headers, account_id, categories["Alimentación"], 25000)
    lista = client.get("/budgets", headers=auth_headers).json()
    assert len(lista) == 1
    assert Decimal(lista[0]["spent"]) == Decimal("25000")
    assert lista[0]["percentage_used"] == 25.0


def test_presupuesto_invalido(client, auth_headers, categories):
    # Duplicado
    crear_presupuesto(client, auth_headers, categories["Alimentación"])
    assert crear_presupuesto(client, auth_headers, categories["Alimentación"]).status_code == 409
    # Categoría de ingreso
    assert crear_presupuesto(client, auth_headers, categories["Salario"]).status_code == 400
    # Límite inválido
    assert crear_presupuesto(client, auth_headers, categories["Transporte"], limite="0").status_code == 422
    # Categoría inexistente
    assert crear_presupuesto(client, auth_headers, 999).status_code == 404


def test_eliminar_presupuesto(client, auth_headers, categories):
    budget = crear_presupuesto(client, auth_headers, categories["Alimentación"]).json()
    assert client.delete(f"/budgets/{budget['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/budgets/{budget['id']}", headers=auth_headers).status_code == 404
    assert client.get("/budgets", headers=auth_headers).json() == []


def test_alertas_al_acercarse_y_superar_el_limite(client, auth_headers, account_id, categories):
    alimentacion = categories["Alimentación"]
    crear_presupuesto(client, auth_headers, alimentacion, limite="100000")

    gastar(client, auth_headers, account_id, alimentacion, 50000)  # 50%
    assert notificaciones(client, auth_headers) == []

    gastar(client, auth_headers, account_id, alimentacion, 35000)  # 85% -> aviso
    lista = notificaciones(client, auth_headers)
    assert [n["kind"] for n in lista] == ["budget_warning"]
    assert "85%" in lista[0]["message"]

    gastar(client, auth_headers, account_id, alimentacion, 5000)  # 90% -> sin nuevo aviso
    assert len(notificaciones(client, auth_headers)) == 1

    gastar(client, auth_headers, account_id, alimentacion, 20000)  # 110% -> superado
    kinds = [n["kind"] for n in notificaciones(client, auth_headers)]
    assert kinds == ["budget_exceeded", "budget_warning"]

    gastar(client, auth_headers, account_id, alimentacion, 1000)  # sigue superado, sin repetir
    assert len(notificaciones(client, auth_headers)) == 2


def test_un_solo_gasto_que_supera_el_limite(client, auth_headers, account_id, categories):
    crear_presupuesto(client, auth_headers, categories["Transporte"], limite="50000")
    gastar(client, auth_headers, account_id, categories["Transporte"], 80000)
    kinds = [n["kind"] for n in notificaciones(client, auth_headers)]
    assert kinds == ["budget_exceeded"]


def test_sin_presupuesto_no_hay_alertas(client, auth_headers, account_id, categories):
    gastar(client, auth_headers, account_id, categories["Alimentación"], 500000)
    assert notificaciones(client, auth_headers) == []


def test_alerta_por_movimiento_grande(client, auth_headers, account_id, categories):
    gastar(client, auth_headers, account_id, categories["Vivienda"], 1500000)
    lista = notificaciones(client, auth_headers)
    assert [n["kind"] for n in lista] == ["large_transaction"]
    assert "$1.500.000" in lista[0]["message"]


def test_marcar_notificaciones_como_leidas(client, auth_headers, account_id, categories):
    gastar(client, auth_headers, account_id, categories["Vivienda"], 1200000)
    gastar(client, auth_headers, account_id, categories["Salud"], 1300000)

    assert len(notificaciones(client, auth_headers, unread_only="true")) == 2
    dashboard = client.get("/dashboard", headers=auth_headers).json()
    assert dashboard["unread_notifications"] == 2

    primera = notificaciones(client, auth_headers)[0]["id"]
    response = client.post(f"/notifications/{primera}/read", headers=auth_headers)
    assert response.json()["is_read"] is True
    assert len(notificaciones(client, auth_headers, unread_only="true")) == 1

    todas = client.post("/notifications/read-all", headers=auth_headers).json()
    assert todas == {"updated": 1}
    assert notificaciones(client, auth_headers, unread_only="true") == []


def test_notificaciones_son_privadas(client, auth_headers, make_headers, account_id, categories):
    gastar(client, auth_headers, account_id, categories["Vivienda"], 1500000)
    nid = notificaciones(client, auth_headers)[0]["id"]

    otro = make_headers("luis@example.com")
    assert notificaciones(client, otro) == []
    assert client.post(f"/notifications/{nid}/read", headers=otro).status_code == 404
