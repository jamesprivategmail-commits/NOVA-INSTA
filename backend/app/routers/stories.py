from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Story, StoryView, Follow, User
from ..schemas import StoryOut
from ..auth import get_current_user
from ..storage import upload_media

router = APIRouter(prefix="/stories", tags=["stories"])

STORY_LIFETIME = timedelta(hours=24)


def _serialize(story: Story, db: Session, viewer: User) -> StoryOut:
    view_count = db.query(func.count(StoryView.id)).filter(StoryView.story_id == story.id).scalar()
    viewed_by_me = db.query(StoryView).filter_by(story_id=story.id, viewer_id=viewer.id).first() is not None
    return StoryOut(
        id=story.id, author_id=story.author_id, media_url=story.media_url, media_type=story.media_type,
        created_at=story.created_at, expires_at=story.expires_at,
        view_count=view_count, viewed_by_me=viewed_by_me,
    )


@router.post("", response_model=StoryOut, status_code=201)
async def create_story(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    media_url, media_type = await upload_media(file)
    now = datetime.utcnow()
    story = Story(author_id=current_user.id, media_url=media_url, media_type=media_type,
                  created_at=now, expires_at=now + STORY_LIFETIME)
    db.add(story)
    db.commit()
    db.refresh(story)
    return _serialize(story, db, current_user)


@router.get("/feed", response_model=List[StoryOut])
def stories_feed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Active (non-expired) stories from people you follow, plus your own."""
    followee_ids = [f.followee_id for f in db.query(Follow).filter(Follow.follower_id == current_user.id).all()]
    followee_ids.append(current_user.id)

    stories = (
        db.query(Story)
        .filter(Story.author_id.in_(followee_ids), Story.expires_at > datetime.utcnow())
        .order_by(Story.created_at.desc())
        .all()
    )
    return [_serialize(s, db, current_user) for s in stories]


@router.get("/user/{username}", response_model=List[StoryOut])
def user_stories(username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    author = db.query(User).filter(User.username == username).first()
    if not author:
        raise HTTPException(status_code=404, detail="User not found")
    stories = (
        db.query(Story)
        .filter(Story.author_id == author.id, Story.expires_at > datetime.utcnow())
        .order_by(Story.created_at.asc())
        .all()
    )
    return [_serialize(s, db, current_user) for s in stories]


@router.post("/{story_id}/view", status_code=204)
def view_story(story_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if db.query(StoryView).filter_by(story_id=story_id, viewer_id=current_user.id).first():
        return
    db.add(StoryView(story_id=story_id, viewer_id=current_user.id))
    db.commit()


@router.delete("/{story_id}", status_code=204)
def delete_story(story_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if story.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your story")
    db.delete(story)
    db.commit()
