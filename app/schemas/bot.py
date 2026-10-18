from typing import Any

from pydantic import BaseModel, Field


class BotMessage(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class BotReply(BaseModel):
    reply: str
    action: str
    data: dict[str, Any] | None = None
