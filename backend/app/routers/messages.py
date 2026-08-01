from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from ..database import get_db
from ..models import Message, User
from ..schemas import MessageCreate, MessageOut, ThreadPreview
from ..auth import get_current_user
from ..push import notify_new_message

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/threads", response_model=List[ThreadPreview])
def list_threads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    msgs = (
        db.query(Message)
        .filter(or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id))
        .order_by(Message.created_at.desc())
        .all()
    )

    seen = {}
    for m in msgs:
        other_id = m.recipient_id if m.sender_id == current_user.id else m.sender_id
        if other_id not in seen:
            seen[other_id] = m

    threads = []
    for other_id, last in seen.items():
        other = db.query(User).filter(User.id == other_id).first()
        if not other:
            continue
        unread = last.recipient_id == current_user.id and not last.is_read
        threads.append(ThreadPreview(
            username=other.username, display_name=other.display_name, avatar_url=other.avatar_url,
            last_message=last.text, last_message_at=last.created_at, unread=unread,
        ))
    return threads


@router.get("/{username}", response_model=List[MessageOut])
def get_conversation(username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    other = db.query(User).filter(User.username == username).first()
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    msgs = (
        db.query(Message)
        .filter(or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == other.id),
            and_(Message.sender_id == other.id, Message.recipient_id == current_user.id),
        ))
        .order_by(Message.created_at.asc())
        .all()
    )

    db.query(Message).filter(
        Message.sender_id == other.id, Message.recipient_id == current_user.id, Message.is_read == False  # noqa: E712
    ).update({"is_read": True})
    db.commit()

    return msgs


@router.post("/{username}", response_model=MessageOut, status_code=201)
async def send_message(username: str, payload: MessageCreate, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    other = db.query(User).filter(User.username == username).first()
    if not other:
        raise HTTPException(status_code=404, detail="User not found")
    if other.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    msg = Message(sender_id=current_user.id, recipient_id=other.id, text=payload.text)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    await notify_new_message(db, recipient_id=other.id, sender_username=current_user.username, text=payload.text)
    return msg
