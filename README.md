# Finanzas App

Aplicación de finanzas personales para centralizar cuentas bancarias, registrar
gastos e ingresos, y obtener reportes sobre los hábitos de gasto.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 + SQLite
- Pytest

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

Documentación interactiva: http://127.0.0.1:8000/docs

## Pruebas

```bash
pytest
```

## Estructura

```
app/
  core/       configuración y base de datos
  models/     modelos SQLAlchemy
  schemas/    esquemas Pydantic
  routers/    endpoints
  services/   lógica de negocio
tests/
```
