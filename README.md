# Finanzas App

Registra gastos e ingresos desde la web o desde un chat privado de Telegram. El historial, el saldo y los reportes se calculan con los mismos movimientos de la base SQL. La web incluye registro de usuarios, inicio de sesión, cuentas, presupuestos y alertas.

## Instalación en un equipo nuevo

Necesitas Git y Python 3.12. En Windows usa PowerShell.

```powershell
git clone https://github.com/mateogarcia1-sketch/Informe.git
cd Informe
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

En Linux o macOS, después de clonar y entrar a `Informe`:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --reload
```

Abre [Finanzas App en tu equipo](http://127.0.0.1:8000/). FastAPI crea las tablas al iniciar y, por defecto, guarda los datos en `finanzas.db`. Configura una clave propia en `SECRET_KEY` en `.env` antes de compartir una instancia. La [documentación de la API](http://127.0.0.1:8000/docs) permite probar rutas autenticadas con el JWT que devuelve `POST /auth/login`.

## Presupuestos desde el asistente

Escribe «registra un presupuesto para transporte de 45.000» o «fija un límite mensual de 100.000 para alimentación» desde la web o Telegram. El asistente guarda el límite en **Presupuestos** y te informa cuánto has gastado este mes. Usa «ver mis presupuestos» para consultarlos.

Un clasificador ligero, entrenado con ejemplos en español, reconoce frases de creación y consulta. La aplicación valida categoría y monto antes de guardar el registro.

## Telegram

En la instancia con Telegram configurado, inicia sesión, agrega una cuenta financiera de prueba y abre **Asistente → Generar enlace de Telegram**. Abre el chat, pulsa **Iniciar** y envía `gasté 20.000 en almuerzo`. Puedes consultar `resumen`, `cuánto tengo` o `últimos movimientos` y ver el gasto en **Historial**.

## Entrega

- [Bot de Telegram](https://t.me/FinanzasInformeBot)
- [Finanzas App en Render](https://informe-finanzas-app.onrender.com/)
- [Wiki final publicada](https://github.com/mateogarcia1-sketch/Informe/wiki)

- [Repositorio de GitHub](https://github.com/mateogarcia1-sketch/Informe)
- [Documentación de la wiki en el repositorio](docs/wiki/Home.md)
- [Diagrama de arquitectura y secuencia](docs/wiki/Arquitectura.md)
- [Despliegue HTTPS en Render con PostgreSQL y activación de Telegram](docs/wiki/Despliegue.md)
- [Pruebas y guion de demo](docs/wiki/Pruebas.md)
- [Cierre y aprendizajes](docs/CIERRE.md)
- [Diapositivas de presentación](docs/presentacion.pptx)

## Pruebas

Ejecuta `python -m pytest` con el Python del entorno virtual. En Windows puedes usar `.\.venv\Scripts\python.exe -m pytest`. Las pruebas usan SQLite en memoria.

## Estructura

| Ruta | Contenido |
|---|---|
| `app/` | API FastAPI, autenticación JWT, modelos SQLAlchemy y servicios |
| `frontend/` | Web servida por FastAPI |
| `scripts/` | Registro del webhook HTTPS en Telegram |
| `tests/` | Pruebas funcionales de la API |
| `render.yaml` | Servicio web y base PostgreSQL para el despliegue |
