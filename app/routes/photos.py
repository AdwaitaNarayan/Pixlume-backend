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
# GET /categories
# ---------------------------------------------------------------------------
@router.get("/categories", summary="Get all unique categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """
    Return a list of all distinct categories currently used by photos.
    """
    result = await db.execute(select(func.unnest(Photo.categories)).distinct())
    return [row[0] for row in result.all()]


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
    device_type: Optional[str] = Query(None, description="Device filter ('desktop', 'mobile')"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Search photos with advanced filters.
    """
    query = select(Photo)
    suggestion = None
    if tag:
        tag_lower = tag.strip().lower()
        # 1. Primary search (Exact/Partial)
        # We also include similarity on caption to catch typos there immediately
        query = query.where(
            (Photo.tags.any(tag_lower)) | 
            (Photo.categories.any(tag_lower)) |
            (Photo.caption.ilike(f"%{tag_lower}%")) |
            (func.similarity(Photo.caption, tag_lower) > 0.4)
        )
        
        # 2. Check for suggestions if we might have a typo
        # We unnest tags and categories into a subquery of 'terms'
        tags_sub = select(func.unnest(Photo.tags).label("term")).where(Photo.tags.is_not(None))
        cats_sub = select(func.unnest(Photo.categories).label("term")).where(Photo.categories.is_not(None))
        all_terms = tags_sub.union(cats_sub).subquery()
        
        sim_query = select(all_terms.c.term).order_by(
            func.similarity(all_terms.c.term, tag_lower).desc()
        ).limit(1)
        
        sim_result = await db.execute(sim_query)
        best_match = sim_result.scalar_one_or_none()
        
        # Only suggest if the match is different from the original tag and quite similar (> 0.3)
        if best_match and best_match != tag_lower:
            match_score_result = await db.execute(select(func.similarity(best_match, tag_lower)))
            if match_score_result.scalar_one() > 0.3:
                suggestion = best_match

    if category:
        cat_lower = category.strip().lower()
        query = query.where(Photo.categories.any(cat_lower))
        
    if device_type:
        dev_lower = device_type.strip().lower()
        # If user searches for 'mobile', we show 'mobile' AND 'both'
        if dev_lower in ['mobile', 'desktop']:
            query = query.where(
                (Photo.device_type == dev_lower) | 
                (Photo.device_type == 'both')
            )
        else:
            query = query.where(Photo.device_type == dev_lower)
        
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

    discovery_categories = None
    # IF NO RESULTS AND NO SUGGESTION -> Fetch Top 5 Popular Categories
    if total == 0 and not suggestion:
        # SELECT unnest(categories) as cat, count(*) FROM photos GROUP BY cat ORDER BY count DESC LIMIT 5
        cat_unnest = func.unnest(Photo.categories).label("cat")
        disco_query = select(cat_unnest).group_by(cat_unnest).order_by(func.count().desc()).limit(5)
        disco_result = await db.execute(disco_query)
        discovery_categories = [row[0] for row in disco_result.all()]

    return PhotoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        results=[PhotoRead.model_validate(p) for p in photos],
        suggestion=suggestion,
        discovery_categories=discovery_categories
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
