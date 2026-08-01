import os
import uuid
import boto3
from fastapi import UploadFile, HTTPException

ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO = {"video/mp4", "video/quicktime"}
MAX_BYTES = 25 * 1024 * 1024  # 25MB

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT_URL"],       # e.g. Cloudflare R2 endpoint
    aws_access_key_id=os.environ["S3_ACCESS_KEY"],
    aws_secret_access_key=os.environ["S3_SECRET_KEY"],
)
BUCKET = os.environ["S3_BUCKET"]
PUBLIC_BASE_URL = os.environ["S3_PUBLIC_BASE_URL"]     # CDN / public bucket URL prefix


async def upload_media(file: UploadFile) -> tuple[str, str]:
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

    s3.put_object(Bucket=BUCKET, Key=key, Body=contents, ContentType=file.content_type)

    return f"{PUBLIC_BASE_URL}/{key}", media_type
