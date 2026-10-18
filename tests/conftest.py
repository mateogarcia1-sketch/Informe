import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    """Base de datos SQLite en memoria, nueva para cada prueba."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def make_headers(client):
    """Entrega una función que registra un usuario y devuelve su encabezado de autenticación."""

    def _make(email: str = "ana@example.com") -> dict[str, str]:
        client.post(
            "/auth/register",
            json={
                "email": email,
                "full_name": "Ana Pérez",
                "password": "Contrasena123",
                "birth_date": "1995-05-10",
            },
        )
        response = client.post(
            "/auth/login", json={"email": email, "password": "Contrasena123"}
        )
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _make


@pytest.fixture()
def auth_headers(make_headers):
    return make_headers()


@pytest.fixture()
def account_id(client, auth_headers):
    """Crea una cuenta con saldo inicial de 1.000.000 y devuelve su id."""
    response = client.post(
        "/accounts",
        json={
            "name": "Bancolombia",
            "institution": "Bancolombia",
            "account_type": "checking",
            "last4": "1234",
            "initial_balance": "1000000",
        },
        headers=auth_headers,
    )
    return response.json()["id"]


@pytest.fixture()
def categories(client, auth_headers):
    """Diccionario nombre -> id con las categorías por defecto del usuario."""
    items = client.get("/categories", headers=auth_headers).json()
    return {item["name"]: item["id"] for item in items}
