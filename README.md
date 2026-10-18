# Finanzas App

API para centralizar las finanzas personales: vincular cuentas bancarias,
registrar gastos e ingresos, ver un resumen general, consultar el historial,
obtener reportes y recibir alertas de gasto. Incluye un bot que entiende
mensajes en español como «gasté 20.000 en almuerzo».

Dirigida a usuarios adultos (18+) con varias cuentas bancarias.

## Funcionalidades

| Funcionalidad | Endpoints |
|---|---|
| Registro y sesión (JWT) | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Vinculación de cuentas | `POST/GET /accounts`, `GET/PATCH/DELETE /accounts/{id}` |
| Categorías | `POST/GET /categories`, `DELETE /categories/{id}` |
| Registro de movimientos | `POST /transactions`, `PATCH/DELETE /transactions/{id}` |
| Historial con filtros | `GET /transactions` (cuenta, categoría, tipo, fechas, monto, texto, paginación) |
| Dashboard de resumen | `GET /dashboard?month=AAAA-MM` |
| Reportes y análisis | `GET /reports/by-category`, `GET /reports/monthly`, `GET /reports/insights` |
| Presupuestos | `POST/GET /budgets`, `DELETE /budgets/{id}` |
| Notificaciones | `GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all` |
| Bot de automatización | `POST /bot/message` |

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 + SQLite
- JWT (PyJWT) y contraseñas con PBKDF2-SHA256
- Pytest

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # En Windows: copy .env.example .env
```

Cambia `SECRET_KEY` en `.env` por un valor propio antes de usar la app de verdad.

## Ejecución

```bash
uvicorn app.main:app --reload
```

Documentación interactiva: http://127.0.0.1:8000/docs

Para probar los endpoints protegidos: registra un usuario, haz login, copia el
`access_token` y pégalo en el botón **Authorize** de la documentación.

## Bot

Envía mensajes a `POST /bot/message`:

```json
{ "text": "gasté 20.000 en almuerzo" }
```

Ejemplos que entiende:

- `gasté 20.000 en almuerzo`, `pagué 80k de arriendo con Nequi`, `ayer gasté 3000 en bus`
- `recibí 1.500.000 de salario`
- `cuánto tengo`
- `cuánto gasté en comida este mes`
- `últimos movimientos`
- `resumen`

Si tienes varias cuentas y no mencionas cuál, el bot te la pregunta.

## Alertas

- Cuando un gasto lleva una categoría al 80% de su presupuesto (configurable) se
  crea una notificación de aviso; al superar el límite, otra de alerta.
- Los movimientos iguales o mayores a `LARGE_TRANSACTION_AMOUNT` también generan
  una notificación.

## Seguridad

- De cada cuenta solo se guardan los últimos 4 dígitos; nunca números completos
  ni credenciales bancarias.
- Las contraseñas se guardan con hash y sal; nunca en texto plano.
- Cada usuario solo puede ver y modificar sus propios datos.
- Solo pueden registrarse mayores de 18 años.

## Pruebas

```bash
pytest
```

## Estructura

```
app/
  core/       configuración, base de datos, seguridad y dependencias
  models/     modelos SQLAlchemy
  schemas/    esquemas Pydantic
  routers/    endpoints
  services/   lógica de negocio (saldos, reportes, alertas, bot)
tests/
```
