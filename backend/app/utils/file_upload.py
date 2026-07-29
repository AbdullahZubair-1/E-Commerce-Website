import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


async def save_product_image(file: UploadFile) -> str:
    """Save uploaded product image and return the relative URL."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' is not allowed. Use JPEG, PNG, WebP, or GIF.",
        )

    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the maximum limit of {settings.MAX_FILE_SIZE // 1024 // 1024}MB.",
        )

    # Create upload directory
    upload_path = Path(settings.UPLOAD_DIR) / "products"
    upload_path.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    ext = Path(file.filename or "image.jpg").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = upload_path / filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    return f"/uploads/products/{filename}"


def delete_file(file_url: str) -> None:
    """Delete a file given its URL path."""
    if not file_url:
        return

    if file_url.startswith("/uploads/"):
        file_path = Path(settings.UPLOAD_DIR) / file_url.removeprefix("/uploads/")
    elif file_url.startswith("uploads/"):
        file_path = Path(settings.UPLOAD_DIR) / file_url.removeprefix("uploads/")
    else:
        file_path = Path(file_url)

    if file_path.exists():
        file_path.unlink()
