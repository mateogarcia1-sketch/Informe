from decimal import Decimal


def test_vincular_cuenta_con_saldo(client, auth_headers):
    response = client.post(
        "/accounts",
        json={"name": "Nequi", "account_type": "wallet", "initial_balance": "250000.50"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Nequi"
    assert Decimal(body["balance"]) == Decimal("250000.50")


def test_last4_debe_tener_cuatro_digitos(client, auth_headers):
    response = client.post(
        "/accounts",
        json={"name": "Tarjeta", "last4": "123456789"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_listar_y_obtener_cuentas(client, auth_headers, account_id):
    lista = client.get("/accounts", headers=auth_headers).json()
    assert [a["id"] for a in lista] == [account_id]

    una = client.get(f"/accounts/{account_id}", headers=auth_headers)
    assert una.status_code == 200
    assert Decimal(una.json()["balance"]) == Decimal("1000000")


def test_desactivar_cuenta_la_oculta_del_listado(client, auth_headers, account_id):
    response = client.patch(
        f"/accounts/{account_id}", json={"is_active": False}, headers=auth_headers
    )
    assert response.status_code == 200
    assert client.get("/accounts", headers=auth_headers).json() == []
    todas = client.get("/accounts?include_inactive=true", headers=auth_headers).json()
    assert len(todas) == 1


def test_eliminar_cuenta_sin_movimientos(client, auth_headers, account_id):
    assert client.delete(f"/accounts/{account_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/accounts/{account_id}", headers=auth_headers).status_code == 404


def test_un_usuario_no_ve_cuentas_de_otro(client, make_headers, account_id):
    otro = make_headers("luis@example.com")
    assert client.get(f"/accounts/{account_id}", headers=otro).status_code == 404
    assert client.get("/accounts", headers=otro).json() == []


def test_cuentas_requieren_autenticacion(client):
    assert client.get("/accounts").status_code == 401
