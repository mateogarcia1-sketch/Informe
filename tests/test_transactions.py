from decimal import Decimal


def crear(client, headers, account_id, category_id, **cambios):
    payload = {
        "account_id": account_id,
        "category_id": category_id,
        "type": "expense",
        "amount": "50000",
        "description": "Almuerzo",
        "date": "2026-10-05",
    }
    payload.update(cambios)
    return client.post("/transactions", json=payload, headers=headers)


def saldo(client, headers, account_id):
    response = client.get(f"/accounts/{account_id}", headers=headers)
    return Decimal(response.json()["balance"])


def test_categorias_por_defecto(client, auth_headers, categories):
    assert "Alimentación" in categories
    assert "Salario" in categories
    gastos = client.get("/categories?type=expense", headers=auth_headers).json()
    assert all(c["type"] == "expense" for c in gastos)


def test_crear_categoria_propia_y_duplicada(client, auth_headers):
    body = {"name": "Mascotas", "type": "expense"}
    assert client.post("/categories", json=body, headers=auth_headers).status_code == 201
    assert client.post("/categories", json=body, headers=auth_headers).status_code == 409


def test_gasto_e_ingreso_actualizan_el_saldo(client, auth_headers, account_id, categories):
    crear(client, auth_headers, account_id, categories["Alimentación"], amount="50000")
    assert saldo(client, auth_headers, account_id) == Decimal("950000")

    crear(
        client, auth_headers, account_id, categories["Salario"],
        type="income", amount="300000", description="Quincena",
    )
    assert saldo(client, auth_headers, account_id) == Decimal("1250000")


def test_monto_invalido(client, auth_headers, account_id, categories):
    for monto in ("0", "-5"):
        response = crear(client, auth_headers, account_id, categories["Alimentación"], amount=monto)
        assert response.status_code == 422


def test_categoria_debe_coincidir_con_el_tipo(client, auth_headers, account_id, categories):
    response = crear(client, auth_headers, account_id, categories["Salario"], type="expense")
    assert response.status_code == 400


def test_cuenta_o_categoria_inexistente(client, auth_headers, account_id, categories):
    assert crear(client, auth_headers, 999, categories["Alimentación"]).status_code == 404
    assert crear(client, auth_headers, account_id, 999).status_code == 404


def test_no_se_puede_registrar_en_cuenta_inactiva(client, auth_headers, account_id, categories):
    client.patch(f"/accounts/{account_id}", json={"is_active": False}, headers=auth_headers)
    response = crear(client, auth_headers, account_id, categories["Alimentación"])
    assert response.status_code == 400


def test_historial_con_filtros(client, auth_headers, account_id, categories):
    crear(client, auth_headers, account_id, categories["Alimentación"],
          amount="50000", date="2026-10-05", description="Almuerzo")
    crear(client, auth_headers, account_id, categories["Transporte"],
          amount="120000", date="2026-10-10", description="Gasolina")
    crear(client, auth_headers, account_id, categories["Salario"],
          type="income", amount="3000000", date="2026-10-01", description="Nómina")

    def consultar(query):
        return client.get(f"/transactions?{query}", headers=auth_headers).json()

    todos = consultar("")
    assert todos["total"] == 3
    # Orden: del más reciente al más antiguo
    assert [t["date"] for t in todos["items"]] == ["2026-10-10", "2026-10-05", "2026-10-01"]

    assert consultar("type=expense")["total"] == 2
    assert consultar("date_from=2026-10-06")["total"] == 1
    assert consultar("date_to=2026-10-05")["total"] == 2
    assert consultar("type=expense&min_amount=100000")["total"] == 1
    assert consultar(f"category_id={categories['Alimentación']}")["total"] == 1
    assert consultar("search=gasolina")["total"] == 1


def test_paginacion(client, auth_headers, account_id, categories):
    for i in range(5):
        crear(client, auth_headers, account_id, categories["Alimentación"],
              date=f"2026-10-0{i + 1}")
    pagina = client.get("/transactions?limit=2&offset=2", headers=auth_headers).json()
    assert pagina["total"] == 5
    assert len(pagina["items"]) == 2


def test_editar_y_eliminar_movimiento(client, auth_headers, account_id, categories):
    tx = crear(client, auth_headers, account_id, categories["Alimentación"]).json()

    editado = client.patch(
        f"/transactions/{tx['id']}",
        json={"amount": "20000", "description": "Café"},
        headers=auth_headers,
    )
    assert editado.status_code == 200
    assert Decimal(editado.json()["amount"]) == Decimal("20000")
    assert saldo(client, auth_headers, account_id) == Decimal("980000")

    assert client.delete(f"/transactions/{tx['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/transactions/{tx['id']}", headers=auth_headers).status_code == 404
    assert saldo(client, auth_headers, account_id) == Decimal("1000000")


def test_no_se_elimina_cuenta_ni_categoria_con_movimientos(
    client, auth_headers, account_id, categories
):
    crear(client, auth_headers, account_id, categories["Alimentación"])
    assert client.delete(f"/accounts/{account_id}", headers=auth_headers).status_code == 409
    assert (
        client.delete(f"/categories/{categories['Alimentación']}", headers=auth_headers).status_code
        == 409
    )


def test_un_usuario_no_ve_movimientos_de_otro(
    client, auth_headers, make_headers, account_id, categories
):
    tx = crear(client, auth_headers, account_id, categories["Alimentación"]).json()
    otro = make_headers("luis@example.com")
    assert client.get(f"/transactions/{tx['id']}", headers=otro).status_code == 404
    assert client.get("/transactions", headers=otro).json()["total"] == 0
