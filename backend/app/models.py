import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, UniqueConstraint, Boolean, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    username = Column(String(30), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(60))
    bio = Column(String(160), default="")
    avatar_url = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    is_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    author_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    media_url = Column(String(500), nullable=False)
    media_type = Column(String(10), default="image")  # image | video
    caption = Column(String(2200), default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    author = relationship("User", back_populates="posts")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_like_user_post"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(UUID(as_uuid=False), ForeignKey("posts.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="likes")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(UUID(as_uuid=False), ForeignKey("posts.id"), nullable=False, index=True)
    text = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    follower_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    followee_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationType(str, enum.Enum):
    like = "like"
    comment = "comment"
    follow = "follow"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    recipient_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    post_id = Column(UUID(as_uuid=False), ForeignKey("posts.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_thread", "sender_id", "recipient_id", "created_at"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    sender_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    text = Column(String(2000), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Story(Base):
    __tablename__ = "stories"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    author_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    media_url = Column(String(500), nullable=False)
    media_type = Column(String(10), default="image")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # created_at + 24h, enforced at query time


class StoryView(Base):
    __tablename__ = "story_views"
    __table_args__ = (UniqueConstraint("story_id", "viewer_id", name="uq_story_viewer"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    story_id = Column(UUID(as_uuid=False), ForeignKey("stories.id"), nullable=False, index=True)
    viewer_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)


class DeviceToken(Base):
    __tablename__ = "device_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_device_token"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), nullable=False)
    platform = Column(String(10), default="web")  # ios | android | web
    created_at = Column(DateTime, default=datetime.utcnow)
