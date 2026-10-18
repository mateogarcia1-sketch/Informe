from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, update

from app.core.deps import CurrentUser, DbSession
from app.models import Notification
from app.schemas.notification import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notificaciones"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: CurrentUser, db: DbSession, unread_only: bool = False):
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    return db.scalars(query.order_by(Notification.id.desc())).all()


@router.post("/read-all")
def mark_all_read(user: CurrentUser, db: DbSession):
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return {"updated": result.rowcount}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, user: CurrentUser, db: DbSession):
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    if notification is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notificación no encontrada")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
