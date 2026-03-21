"""
Admin endpoints – protected operations for photo management.

Routes
------
POST   /admin/upload        – upload + process + store a new photo
DELETE /admin/photo/{id}    – delete a photo record (DB only; storage cleanup TBD)

Security
--------
These endpoints are protected by a static API key passed in the
``X-Admin-Key`` request header.  Set ADMIN_API_KEY in your .env file.
For production you should replace this with proper auth (OAuth2, JWT, etc.).
"""

import os
import uuid

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.photo_model import Photo
from app.models.user_model import User
from app.schemas.photo_schema import PhotoRead
from app.services.image_processing import process_image
from app.services.storage_service import upload_variants
from app.services.auth_service import get_current_active_user

from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# JWT Auth dependency imported from auth_service


# ---------------------------------------------------------------------------
# POST /admin/upload
# ---------------------------------------------------------------------------
@router.post(
    "/upload",
    response_model=PhotoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new photo (admin only)",
)
async def upload_photo(
    title: str = Form(..., description="Photo title"),
    caption: str | None = Form(None, description="Optional caption / description"),
    tags: str | None = Form(
        None,
        description="Comma-separated list of tags, e.g. 'nature,sunset,landscape'",
    ),
    file: UploadFile = File(..., description="Image file (JPEG / PNG / WebP)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Full upload pipeline:

    1. Receive the image via multipart form.
    2. Resize it to 5 variants using Pillow.
    3. Upload each variant to S3 / Cloudinary.
    4. Persist the URLs + metadata in PostgreSQL.
    5. Return the newly created ``PhotoRead`` record.
    """
    # --- Validate content type ---------------------------------------------------
    accepted = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in accepted:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Accepted: {accepted}",
        )

    # --- Parse tags -------------------------------------------------------------
    tag_list: list[str] | None = None
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]

    # --- Image processing -------------------------------------------------------
    photo_id = uuid.uuid4()
    try:
        buffers = process_image(file.file)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image processing failed: {exc}",
        ) from exc

    # --- Upload to storage -------------------------------------------------------
    try:
        photo_urls = upload_variants(photo_id, buffers)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {exc}",
        ) from exc

    # --- Persist to DB -----------------------------------------------------------
    photo = Photo(
        id=photo_id,
        title=title,
        caption=caption,
        tags=tag_list,
        thumbnail_url=photo_urls.thumbnail_url,
        image_720_url=photo_urls.image_720_url,
        image_1080_url=photo_urls.image_1080_url,
        image_2k_url=photo_urls.image_2k_url,
        image_4k_url=photo_urls.image_4k_url,
    )
    db.add(photo)
    await db.flush()      # get the generated values without committing yet
    await db.refresh(photo)

    return PhotoRead.model_validate(photo)


# ---------------------------------------------------------------------------
# DELETE /admin/photo/{id}
# ---------------------------------------------------------------------------
@router.delete(
    "/photo/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a photo (admin only)",
)
async def delete_photo(
    photo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete the database record for *photo_id*.

    Note: This does **not** remove the images from S3 / Cloudinary.
    You can add CDN cleanup logic in ``storage_service`` if needed.
    """
    result = await db.execute(select(Photo).where(Photo.id == photo_id))
    photo = result.scalar_one_or_none()

    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with id '{photo_id}' not found.",
        )

    await db.execute(delete(Photo).where(Photo.id == photo_id))
    # Session commit is handled by the get_db dependency
