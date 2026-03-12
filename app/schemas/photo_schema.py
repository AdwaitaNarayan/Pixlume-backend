"""
Pydantic schemas for Photo – used for request validation and response serialisation.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------
class PhotoBase(BaseModel):
    title: str
    caption: Optional[str] = None
    tags: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Read schema (returned by public & admin endpoints)
# ---------------------------------------------------------------------------
class PhotoRead(PhotoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    thumbnail_url: Optional[str] = None
    image_720_url: Optional[str] = None
    image_1080_url: Optional[str] = None
    image_2k_url: Optional[str] = None
    image_4k_url: Optional[str] = None
    created_at: datetime
    downloads: int


# ---------------------------------------------------------------------------
# Upload request body (multipart fields sent alongside the image file)
# ---------------------------------------------------------------------------
class PhotoUploadRequest(BaseModel):
    title: str
    caption: Optional[str] = None
    tags: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Internal schema that storage_service returns after uploading variants
# ---------------------------------------------------------------------------
class PhotoURLs(BaseModel):
    thumbnail_url: str
    image_720_url: str
    image_1080_url: str
    image_2k_url: str
    image_4k_url: str


# ---------------------------------------------------------------------------
# Pagination wrapper
# ---------------------------------------------------------------------------
class PhotoListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[PhotoRead]
