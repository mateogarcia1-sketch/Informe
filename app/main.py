from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401
from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth
from app.routers import accounts
from app.routers import categories, transactions
from app.routers import dashboard, reports
from app.routers import budgets, notifications
from app.routers import bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas de la base de datos al iniciar la aplicación."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

# Interfaz web estática servida desde la misma aplicación FastAPI.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(budgets.router)
app.include_router(notifications.router)
app.include_router(bot.router)


@app.get("/health", tags=["sistema"])
def health():
    """Verifica que la API está en funcionamiento."""
    return {"status": "ok", "app": settings.app_name}
