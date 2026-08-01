import os
import httpx
from sqlalchemy.orm import Session

from .models import DeviceToken

FCM_SERVER_KEY = os.environ.get("FCM_SERVER_KEY")  # unset in dev = push calls are silently skipped
FCM_URL = "https://fcm.googleapis.com/fcm/send"


async def _send_fcm(tokens: list[str], title: str, body: str, data: dict | None = None):
    if not FCM_SERVER_KEY or not tokens:
        return  # no-op until FCM_SERVER_KEY is configured — safe for local/dev use

    headers = {"Authorization": f"key={FCM_SERVER_KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=10) as client:
        for token in tokens:
            payload = {
                "to": token,
                "notification": {"title": title, "body": body},
                "data": data or {},
            }
            try:
                await client.post(FCM_URL, json=payload, headers=headers)
            except httpx.HTTPError:
                pass  # a failed push shouldn't break the request that triggered it


async def notify_new_message(db: Session, recipient_id: str, sender_username: str, text: str):
    tokens = [t.token for t in db.query(DeviceToken).filter(DeviceToken.user_id == recipient_id).all()]
    preview = text if len(text) <= 80 else text[:77] + "..."
    await _send_fcm(tokens, title=f"{sender_username} sent you a message", body=preview)


async def notify_event(db: Session, recipient_id: str, title: str, body: str):
    tokens = [t.token for t in db.query(DeviceToken).filter(DeviceToken.user_id == recipient_id).all()]
    await _send_fcm(tokens, title=title, body=body)
