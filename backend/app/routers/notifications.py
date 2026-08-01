from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Notification, User
from ..schemas import NotificationOut
from ..auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/read-all", status_code=204)
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(
        Notification.recipient_id == current_user.id, Notification.is_read == False  # noqa: E712
    ).update({"is_read": True})
    db.commit()
