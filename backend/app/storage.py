import os
import uuid
import boto3
from fastapi import UploadFile, HTTPException

ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO = {"video/mp4", "video/quicktime"}
MAX_BYTES = 25 * 1024 * 1024  # 25MB

S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
BUCKET = os.environ.get("S3_BUCKET")
PUBLIC_BASE_URL = os.environ.get("S3_PUBLIC_BASE_URL")

STORAGE_CONFIGURED = all([S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY, BUCKET, PUBLIC_BASE_URL])

_s3 = None


def _get_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
    return _s3


async def upload_media(file: UploadFile) -> tuple[str, str]:
    if not STORAGE_CONFIGURED:
        raise HTTPException(
            status_code=503,
            detail="Media storage isn't configured yet — set S3_ENDPOINT_URL, S3_ACCESS_KEY, "
                   "S3_SECRET_KEY, S3_BUCKET, and S3_PUBLIC_BASE_URL to enable uploads.",
        )

    if file.content_type in ALLOWED_IMAGE:
        media_type = "image"
    elif file.content_type in ALLOWED_VIDEO:
        media_type = "video"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 25MB)")

    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "bin"
    key = f"posts/{uuid.uuid4()}.{ext}"

    _get_client().put_object(Bucket=BUCKET, Key=key, Body=contents, ContentType=file.content_type)

    return f"{PUBLIC_BASE_URL}/{key}", media_type
