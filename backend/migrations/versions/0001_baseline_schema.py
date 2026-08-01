"""baseline schema

Revision ID: 0001
Revises:
Create Date: 2026-08-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("username", sa.String(30), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(60)),
        sa.Column("bio", sa.String(160), server_default=""),
        sa.Column("avatar_url", sa.String(500), server_default=""),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_banned", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("media_url", sa.String(500), nullable=False),
        sa.Column("media_type", sa.String(10), server_default="image"),
        sa.Column("caption", sa.String(2200), server_default=""),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_posts_author_id", "posts", ["author_id"])
    op.create_index("ix_posts_created_at", "posts", ["created_at"])

    op.create_table(
        "likes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "post_id", name="uq_like_user_post"),
    )
    op.create_index("ix_likes_user_id", "likes", ["user_id"])
    op.create_index("ix_likes_post_id", "likes", ["post_id"])

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("posts.id"), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_comments_user_id", "comments", ["user_id"])
    op.create_index("ix_comments_post_id", "comments", ["post_id"])

    op.create_table(
        "follows",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("follower_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("followee_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("follower_id", "followee_id", name="uq_follow_pair"),
    )
    op.create_index("ix_follows_follower_id", "follows", ["follower_id"])
    op.create_index("ix_follows_followee_id", "follows", ["followee_id"])

    notification_type = postgresql.ENUM("like", "comment", "follow", name="notificationtype")
    notification_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("posts.id"), nullable=True),
        sa.Column("is_read", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_recipient_id", "notifications", ["recipient_id"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("sender_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("text", sa.String(2000), nullable=False),
        sa.Column("is_read", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])
    op.create_index("ix_messages_recipient_id", "messages", ["recipient_id"])
    op.create_index("ix_messages_thread", "messages", ["sender_id", "recipient_id", "created_at"])

    op.create_table(
        "stories",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("media_url", sa.String(500), nullable=False),
        sa.Column("media_type", sa.String(10), server_default="image"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_stories_author_id", "stories", ["author_id"])
    op.create_index("ix_stories_created_at", "stories", ["created_at"])
    op.create_index("ix_stories_expires_at", "stories", ["expires_at"])

    op.create_table(
        "story_views",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("story_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("viewer_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("viewed_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("story_id", "viewer_id", name="uq_story_viewer"),
    )
    op.create_index("ix_story_views_story_id", "story_views", ["story_id"])

    op.create_table(
        "device_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(10), server_default="web"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("token", name="uq_device_token"),
    )
    op.create_index("ix_device_tokens_user_id", "device_tokens", ["user_id"])


def downgrade():
    op.drop_table("device_tokens")
    op.drop_table("story_views")
    op.drop_table("stories")
    op.drop_table("messages")
    op.drop_table("notifications")
    postgresql.ENUM(name="notificationtype").drop(op.get_bind(), checkfirst=True)
    op.drop_table("follows")
    op.drop_table("comments")
    op.drop_table("likes")
    op.drop_table("posts")
    op.drop_table("users")
