from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DeviceToken, User
from ..schemas import DeviceTokenRegister
from ..auth import get_current_user

router = APIRouter(prefix="/push", tags=["push"])


@router.post("/register", status_code=204)
def register_device(payload: DeviceTokenRegister, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    existing = db.query(DeviceToken).filter(DeviceToken.token == payload.token).first()
    if existing:
        existing.user_id = current_user.id
        existing.platform = payload.platform
    else:
        db.add(DeviceToken(user_id=current_user.id, token=payload.token, platform=payload.platform))
    db.commit()


@router.delete("/unregister", status_code=204)
def unregister_device(payload: DeviceTokenRegister, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    db.query(DeviceToken).filter(DeviceToken.token == payload.token).delete()
    db.commit()
