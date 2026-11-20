import hashlib
import secrets
import time
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.deps import CurrentUser, DbSession
from app.models import User
from app.models.telegram import TelegramCode, TelegramLink, TelegramReceipt
from app.services.bot import handle_message

router = APIRouter(prefix="/telegram", tags=["telegram"])


class Chat(BaseModel):
    id: int
    type: str


class Message(BaseModel):
    chat: Chat
    text: str | None = None


class Update(BaseModel):
    update_id: int
    message: Message | None = None


def digest(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


@router.get("/link")
def link_status(user: CurrentUser, db: DbSession):
    return {
        "configured": bool(settings.telegram_bot_username and settings.telegram_webhook_secret),
        "linked": db.get(TelegramLink, user.id) is not None,
    }


@router.post("/link")
def issue_link(user: CurrentUser, db: DbSession, response: Response):
    if not settings.telegram_bot_username or not settings.telegram_webhook_secret:
        raise HTTPException(503, "Telegram todavía no está configurado.")
    code = secrets.token_urlsafe(24)
    db.execute(delete(TelegramCode).where(TelegramCode.user_id == user.id))
    db.add(TelegramCode(user_id=user.id, digest=digest(code), expires_at=int(time.time()) + 600))
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"url": f"https://t.me/{settings.telegram_bot_username}?start={code}"}


@router.delete("/link", status_code=204)
def unlink(user: CurrentUser, db: DbSession):
    db.execute(delete(TelegramCode).where(TelegramCode.user_id == user.id))
    db.execute(delete(TelegramLink).where(TelegramLink.user_id == user.id))
    db.commit()


def process_message(db: DbSession, chat_id: int, text: str) -> str:
    user_id = db.scalar(select(TelegramLink.user_id).where(TelegramLink.chat_id == chat_id))
    command, _, code = text.partition(" ")
    if command == "/start" and code:
        if user_id is not None:
            return "Este chat ya está vinculado. Puedes desvincularlo desde la web."
        owner = db.scalar(
            delete(TelegramCode)
            .where(TelegramCode.digest == digest(code), TelegramCode.expires_at > int(time.time()))
            .returning(TelegramCode.user_id)
        )
        if owner is None:
            return "Enlace vencido o usado. Genera otro en Asistente, desde la web."
        try:
            with db.begin_nested():
                db.add(TelegramLink(user_id=owner, chat_id=chat_id))
                db.flush()
        except IntegrityError:
            return "La cuenta ya está vinculada. Desvincúlala desde la web para cambiar de chat."
        return "Cuenta vinculada. Prueba «gasté 20.000 en almuerzo»."
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        return "Inicia sesión en Finanzas App y genera un enlace en Asistente."
    if len(text) > 500:
        return "Envía un mensaje de hasta 500 caracteres."
    return handle_message(db, user, text, commit=False).reply


@router.post("/webhook", include_in_schema=False)
def webhook(
    update: Update,
    db: DbSession,
    secret: Annotated[str, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = "",
):
    expected = settings.telegram_webhook_secret
    username = settings.telegram_bot_username
    if not expected or not username or not secrets.compare_digest(secret.encode(), expected.encode()):
        raise HTTPException(403, "Webhook no autorizado.")
    message = update.message
    if not message or message.chat.type != "private" or not message.text:
        return {}
    receipt = TelegramReceipt(bot_username=username.lower(), update_id=update.update_id)
    db.add(receipt)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        # Telegram may retry after the SQL transaction has already committed.
        return {}
    reply = process_message(db, message.chat.id, message.text.strip())[:4096]
    db.commit()
    return {"method": "sendMessage", "chat_id": message.chat.id, "text": reply}
