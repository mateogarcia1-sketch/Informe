from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.bot import BotMessage, BotReply
from app.services.bot import handle_message

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/message", response_model=BotReply)
def send_message(message: BotMessage, user: CurrentUser, db: DbSession):
    """Ejecuta operaciones con lenguaje natural, por ejemplo «gasté 20.000 en comida»."""
    return handle_message(db, user, message.text)
