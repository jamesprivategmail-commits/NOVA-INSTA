from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, users, posts, notifications, admin, messages, stories, push

# Schema is now managed by Alembic (see /migrations) — run `alembic upgrade head` on deploy.
# Base/engine are still imported here since routers depend on the shared metadata at import time.

app = FastAPI(title="Nova World API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your actual web/mobile origins before launch
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(messages.router)
app.include_router(stories.router)
app.include_router(push.router)


@app.get("/health")
def health():
    return {"status": "ok"}
