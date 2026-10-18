import datetime as dt

from sqlalchemy import func, select

from app.models import Category

VALID_USER = {
    "email": "ana@example.com",
    "full_name": "Ana Pérez",
    "password": "Contrasena123",
    "birth_date": "1995-05-10",
}


def test_registro_exitoso(client, db_session):
    response = client.post("/auth/register", json=VALID_USER)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert "password" not in body and "password_hash" not in body

    # Se crean las categorías por defecto
    total = db_session.scalar(select(func.count()).select_from(Category))
    assert total == 12


def test_correo_se_guarda_en_minusculas(client):
    response = client.post("/auth/register", json={**VALID_USER, "email": "ANA@Example.com"})
    assert response.json()["email"] == "ana@example.com"


def test_correo_duplicado(client):
    client.post("/auth/register", json=VALID_USER)
    response = client.post("/auth/register", json=VALID_USER)
    assert response.status_code == 409


def test_menor_de_edad_no_puede_registrarse(client):
    hace_diez_anos = (dt.date.today() - dt.timedelta(days=365 * 10)).isoformat()
    response = client.post("/auth/register", json={**VALID_USER, "birth_date": hace_diez_anos})
    assert response.status_code == 422


def test_contrasena_corta(client):
    response = client.post("/auth/register", json={**VALID_USER, "password": "123"})
    assert response.status_code == 422


def test_login_correcto_e_incorrecto(client):
    client.post("/auth/register", json=VALID_USER)

    ok = client.post("/auth/login", json={"email": "ana@example.com", "password": "Contrasena123"})
    assert ok.status_code == 200
    assert ok.json()["token_type"] == "bearer"

    mal = client.post("/auth/login", json={"email": "ana@example.com", "password": "otra-clave"})
    assert mal.status_code == 401


def test_me_requiere_token(client, auth_headers):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer falso"}).status_code == 401

    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"
