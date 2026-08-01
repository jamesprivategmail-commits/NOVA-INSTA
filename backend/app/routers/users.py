from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import User, Follow, Notification, NotificationType
from ..schemas import UserOut, UserUpdate
from ..auth import get_current_user
from ..push import notify_event

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.bio is not None:
        current_user.bio = payload.bio
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{username}", response_model=UserOut)
def get_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/{username}/follow", status_code=204)
async def follow_user(username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    exists = db.query(Follow).filter_by(follower_id=current_user.id, followee_id=target.id).first()
    if exists:
        return

    db.add(Follow(follower_id=current_user.id, followee_id=target.id))
    db.add(Notification(recipient_id=target.id, actor_id=current_user.id, type=NotificationType.follow))
    db.commit()
    await notify_event(db, target.id, "New follower", f"{current_user.username} started following you")


@router.delete("/{username}/follow", status_code=204)
def unfollow_user(username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(Follow).filter_by(follower_id=current_user.id, followee_id=target.id).delete()
    db.commit()


@router.get("/{username}/followers")
def followers(username: str, db: Session = Depends(get_db)):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    count = db.query(func.count(Follow.id)).filter(Follow.followee_id == target.id).scalar()
    return {"count": count}


@router.get("/{username}/following")
def following(username: str, db: Session = Depends(get_db)):
    target = db.query(User).filter(User.username == username).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    count = db.query(func.count(Follow.id)).filter(Follow.follower_id == target.id).scalar()
    return {"count": count}
