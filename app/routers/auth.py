from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.user import Token, UserCreate, UserLogin, UserOut
from app.services.categories import create_default_categories

router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession):
    """Registra un usuario adulto (18+) y le crea categorías por defecto."""
    if db.scalar(select(User).where(User.email == data.email)):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ya existe un usuario con ese correo"
        )
    user = User(
        email=data.email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        birth_date=data.birth_date,
    )
    db.add(user)
    db.flush()
    create_default_categories(db, user.id)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: DbSession):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos"
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
