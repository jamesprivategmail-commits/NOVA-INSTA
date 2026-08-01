from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9._]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    display_name: Optional[str] = None
    bio: str
    avatar_url: str
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=160)


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    text: str
    created_at: datetime


class PostCreate(BaseModel):
    caption: str = Field(default="", max_length=2200)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    author_id: str
    media_url: str
    media_type: str
    caption: str
    created_at: datetime
    like_count: int = 0
    comment_count: int = 0
    liked_by_me: bool = False


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    actor_id: str
    type: str
    post_id: Optional[str]
    is_read: bool
    created_at: datetime


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    email: str
    display_name: Optional[str] = None
    is_admin: bool
    is_verified: bool
    is_banned: bool
    created_at: datetime


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    sender_id: str
    recipient_id: str
    text: str
    is_read: bool
    created_at: datetime


class ThreadPreview(BaseModel):
    username: str
    display_name: Optional[str] = None
    avatar_url: str
    last_message: str
    last_message_at: datetime
    unread: bool


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    author_id: str
    media_url: str
    media_type: str
    created_at: datetime
    expires_at: datetime
    view_count: int = 0
    viewed_by_me: bool = False


class DeviceTokenRegister(BaseModel):
    token: str
    platform: str = Field(default="web", pattern="^(ios|android|web)$")
