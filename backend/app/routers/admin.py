from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import User, Post
from ..schemas import AdminUserOut
from ..auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[AdminUserOut])
def list_users(
    q: Optional[str] = Query(None, description="search by username or email"),
    banned_only: bool = False,
    unverified_only: bool = False,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = db.query(User)
    if q:
        query = query.filter(or_(User.username.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    if banned_only:
        query = query.filter(User.is_banned == True)  # noqa: E712
    if unverified_only:
        query = query.filter(User.is_verified == False)  # noqa: E712
    return query.order_by(User.created_at.desc()).limit(limit).all()


@router.post("/users/{user_id}/verify", response_model=AdminUserOut)
def verify_user(user_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/unverify", response_model=AdminUserOut)
def unverify_user(user_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = False
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/ban", response_model=AdminUserOut)
def ban_user(user_id: str, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    user.is_banned = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/unban", response_model=AdminUserOut)
def unban_user(user_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = False
    db.commit()
    db.refresh(user)
    return user


@router.delete("/posts/{post_id}", status_code=204)
def admin_delete_post(post_id: str, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    """Moderation removal — deletes any user's post, unlike the owner-only DELETE /posts/{id}."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()


@router.get("/stats")
def stats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return {
        "total_users": db.query(User).count(),
        "banned_users": db.query(User).filter(User.is_banned == True).count(),  # noqa: E712
        "verified_users": db.query(User).filter(User.is_verified == True).count(),  # noqa: E712
        "total_posts": db.query(Post).count(),
    }
