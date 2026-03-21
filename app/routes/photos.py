"""
Public photo endpoints.

Routes
------
GET  /photos               – paginated list of all photos
GET  /search?tag=<tag>     – photos that contain the given tag  (must be before /{photo_id})
GET  /photos/{id}          – single photo by UUID
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.photo_model import Photo
from app.schemas.photo_schema import PhotoRead, PhotoListResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /photos
# ---------------------------------------------------------------------------
@router.get("/", response_model=PhotoListResponse, summary="List all photos")
async def list_photos(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return a paginated list of photos, newest first.
    """
    offset = (page - 1) * page_size

    # Total count
    count_result = await db.execute(select(func.count()).select_from(Photo))
    total = count_result.scalar_one()

    # Paginated results
    result = await db.execute(
        select(Photo).order_by(Photo.created_at.desc()).offset(offset).limit(page_size)
    )
    photos = result.scalars().all()

    return PhotoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        results=[PhotoRead.model_validate(p) for p in photos],
    )


# ---------------------------------------------------------------------------
# GET /search?tag=<tag>
# ---------------------------------------------------------------------------
@router.get("/search", response_model=PhotoListResponse, summary="Search photos by tag or filters")
async def search_photos(
    tag: str = Query("", description="Tag or title to search for"),
    resolution: Optional[str] = Query(None, description="Resolution filter (e.g. '4k', '2k', '1080p')"),
    date: Optional[str] = Query(None, description="Date filter (e.g. 'today', 'week', 'month')"),
    category: Optional[str] = Query(None, description="Category filter"),
    collection: Optional[str] = Query(None, description="Collection filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Search photos with advanced filters.
    """
    query = select(Photo)
    
    if tag:
        tag_lower = tag.strip().lower()
        # Search in title, caption or tags
        query = query.where(
            (Photo.tags.any(tag_lower)) | 
            (Photo.title.ilike(f"%{tag_lower}%")) |
            (Photo.caption.ilike(f"%{tag_lower}%"))
        )
        
    if category:
        cat_lower = category.strip().lower()
        query = query.where(Photo.tags.any(cat_lower))
        
    if resolution:
        res = resolution.lower()
        if res == '4k':
            query = query.where(Photo.image_4k_url.is_not(None))
        elif res == '2k':
            query = query.where(Photo.image_2k_url.is_not(None))
        elif res == '1080p':
            query = query.where(Photo.image_1080_url.is_not(None))
        elif res == '720p':
            query = query.where(Photo.image_720_url.is_not(None))

    if date:
        # Simplistic date filter mock
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        if date == 'today':
            query = query.where(Photo.created_at >= now - timedelta(days=1))
        elif date == 'week':
            query = query.where(Photo.created_at >= now - timedelta(days=7))
        elif date == 'month':
            query = query.where(Photo.created_at >= now - timedelta(days=30))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(Photo.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    photos = result.scalars().all()

    return PhotoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        results=[PhotoRead.model_validate(p) for p in photos],
    )


# ---------------------------------------------------------------------------
# GET /photos/{id}
# ---------------------------------------------------------------------------
@router.get("/{photo_id}", response_model=PhotoRead, summary="Get photo by ID")
async def get_photo(
    photo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Return a single photo by its UUID.  Raises 404 if not found.
    """
    result = await db.execute(select(Photo).where(Photo.id == photo_id))
    photo = result.scalar_one_or_none()

    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo with id '{photo_id}' not found.",
        )

    return PhotoRead.model_validate(photo)
