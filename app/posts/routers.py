import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, Request, status

from app.core.config import settings
from app.core.exceptions import DetailedException, ValidationException
from app.middleware.request import RequestWrapper, get_request_wrapper
from .constants import CATEGORIES
from .schemas import CategoryResponse, UploadResponse

router = APIRouter(prefix="/posts", tags=["posts"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@router.get("/categories", response_model=List[CategoryResponse])
def list_categories():
    """List the categories a post can belong to."""
    return CATEGORIES


@router.post(
    "/images",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                mime: {"schema": {"type": "string", "format": "binary"}}
                for mime in ALLOWED_IMAGE_TYPES
            },
        }
    },
)
async def upload_image(
    request: Request,
    wrapper: RequestWrapper = Depends(get_request_wrapper),
):
    """Upload a single image as the raw request body (Content-Type: image/*)."""
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    extension = ALLOWED_IMAGE_TYPES.get(content_type)
    if not extension:
        raise ValidationException(
            f"Unsupported image type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > settings.MAX_UPLOAD_BYTES:
        raise DetailedException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image is too large")

    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > settings.MAX_UPLOAD_BYTES:
            raise DetailedException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image is too large")
        chunks.append(chunk)
    if size == 0:
        raise ValidationException("Image body is empty")

    user_dir = Path(settings.MEDIA_DIR) / "uploads" / str(wrapper.get_user_id())
    user_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    (user_dir / filename).write_bytes(b"".join(chunks))

    base = str(request.base_url).rstrip("/")
    relative = f"{settings.MEDIA_URL}/uploads/{wrapper.get_user_id()}/{filename}"
    return {"url": f"{base}{relative}"}
