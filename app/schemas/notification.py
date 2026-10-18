import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationKind


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: NotificationKind
    message: str
    is_read: bool
    created_at: dt.datetime
