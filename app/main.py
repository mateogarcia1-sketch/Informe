from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401
from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth
from app.routers import accounts
from app.routers import categories, transactions
from app.routers import dashboard, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas de la base de datos al iniciar la aplicación."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


@app.get("/health", tags=["sistema"])
def health():
    """Verifica que la API está en funcionamiento."""
    return {"status": "ok", "app": settings.app_name}
