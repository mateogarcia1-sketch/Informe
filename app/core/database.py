from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# check_same_thread solo aplica a SQLite
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

url = make_url(settings.database_url)
if url.drivername in {"postgres", "postgresql"}:
    url = url.set(drivername="postgresql+psycopg")
engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Clase base para todos los modelos."""


def get_db():
    """Dependencia de FastAPI que entrega una sesión y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
