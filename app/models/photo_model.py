"""
SQLAlchemy ORM model for the `photos` table.

Columns
-------
id              : UUID primary key
title           : photo title
caption         : longer description / caption
tags            : PostgreSQL TEXT[] array – supports tag-based search
thumbnail_url   : URL for the thumbnail (~300px)
image_720_url   : URL for the 720-p version
image_1080_url  : URL for the 1080-p version
image_2k_url    : URL for the 2K version
image_4k_url    : URL for the 4K version
created_at      : auto-set UTC timestamp
downloads       : download counter (default 0)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Integer, TIMESTAMP, ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        index=True,
        comment="Searchable array of tag strings",
    )

    # Resolution variants (URLs returned from S3 / Cloudinary)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_720_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_1080_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_2k_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_4k_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_8k_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
