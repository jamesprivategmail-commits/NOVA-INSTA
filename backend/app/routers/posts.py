from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, exists

from ..database import get_db
from ..models import Post, Like, Comment, Follow, User, Notification, NotificationType
from ..schemas import PostOut, CommentCreate, CommentOut
from ..auth import get_current_user, get_optional_user
from ..storage import upload_media
from ..push import notify_event

router = APIRouter(prefix="/posts", tags=["posts"])


def _serialize(post: Post, db: Session, viewer: Optional[User]) -> PostOut:
    like_count = db.query(func.count(Like.id)).filter(Like.post_id == post.id).scalar()
    comment_count = db.query(func.count(Comment.id)).filter(Comment.post_id == post.id).scalar()
    liked_by_me = False
    if viewer:
        liked_by_me = db.query(Like).filter_by(post_id=post.id, user_id=viewer.id).first() is not None
    return PostOut(
        id=post.id, author_id=post.author_id, media_url=post.media_url, media_type=post.media_type,
        caption=post.caption, created_at=post.created_at,
        like_count=like_count, comment_count=comment_count, liked_by_me=liked_by_me,
    )


@router.post("", response_model=PostOut, status_code=201)
async def create_post(
    file: UploadFile = File(...),
    caption: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    media_url, media_type = await upload_media(file)
    post = Post(author_id=current_user.id, media_url=media_url, media_type=media_type, caption=caption)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _serialize(post, db, current_user)


@router.get("/feed", response_model=List[PostOut])
def get_feed(
    cursor: Optional[str] = Query(None, description="ISO timestamp of last seen post"),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    followee_ids = [f.followee_id for f in db.query(Follow).filter(Follow.follower_id == current_user.id).all()]
    followee_ids.append(current_user.id)

    q = db.query(Post).filter(Post.author_id.in_(followee_ids)).order_by(Post.created_at.desc())
    if cursor:
        q = q.filter(Post.created_at < cursor)
    posts = q.limit(limit).all()
    return [_serialize(p, db, current_user) for p in posts]


@router.get("/explore", response_model=List[PostOut])
def explore(
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_optional_user),
):
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(limit).all()
    return [_serialize(p, db, viewer) for p in posts]


@router.get("/user/{username}", response_model=List[PostOut])
def user_posts(
    username: str, limit: int = Query(30, le=60),
    db: Session = Depends(get_db), viewer: Optional[User] = Depends(get_optional_user),
):
    author = db.query(User).filter(User.username == username).first()
    if not author:
        raise HTTPException(status_code=404, detail="User not found")
    posts = db.query(Post).filter(Post.author_id == author.id).order_by(Post.created_at.desc()).limit(limit).all()
    return [_serialize(p, db, viewer) for p in posts]


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")
    db.delete(post)
    db.commit()


@router.post("/{post_id}/like", status_code=204)
async def like_post(post_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if db.query(Like).filter_by(post_id=post_id, user_id=current_user.id).first():
        return

    db.add(Like(post_id=post_id, user_id=current_user.id))
    if post.author_id != current_user.id:
        db.add(Notification(recipient_id=post.author_id, actor_id=current_user.id,
                             type=NotificationType.like, post_id=post_id))
    db.commit()
    if post.author_id != current_user.id:
        await notify_event(db, post.author_id, "New like", f"{current_user.username} liked your post")


@router.delete("/{post_id}/like", status_code=204)
def unlike_post(post_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Like).filter_by(post_id=post_id, user_id=current_user.id).delete()
    db.commit()


@router.post("/{post_id}/comments", response_model=CommentOut, status_code=201)
async def add_comment(post_id: str, payload: CommentCreate, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(post_id=post_id, user_id=current_user.id, text=payload.text)
    db.add(comment)
    if post.author_id != current_user.id:
        db.add(Notification(recipient_id=post.author_id, actor_id=current_user.id,
                             type=NotificationType.comment, post_id=post_id))
    db.commit()
    db.refresh(comment)
    if post.author_id != current_user.id:
        await notify_event(db, post.author_id, "New comment", f"{current_user.username} commented: {payload.text[:60]}")
    return comment


@router.get("/{post_id}/comments", response_model=List[CommentOut])
def list_comments(post_id: str, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.post_id == post_id).order_by(Comment.created_at.asc()).all()
