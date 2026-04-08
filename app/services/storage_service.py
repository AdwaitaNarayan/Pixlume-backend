"""
Storage service – uploads image variants to AWS S3 *or* Cloudinary.

The active backend is chosen via the environment:
  • If CLOUDINARY_URL is set → Cloudinary is used.
  • Otherwise AWS_ACCESS_KEY + AWS_SECRET_KEY + S3_BUCKET are required.

Public API
----------
    upload_variants(photo_id, buffers) -> PhotoURLs
"""

import io
import os
import uuid
from typing import Literal

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import cloudinary
import cloudinary.uploader

from app.schemas.photo_schema import PhotoURLs

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Determine active backend
# ---------------------------------------------------------------------------
_CLOUDINARY_URL: str | None = os.environ.get("CLOUDINARY_URL")
_AWS_ACCESS_KEY: str | None = os.environ.get("AWS_ACCESS_KEY")
_AWS_SECRET_KEY: str | None = os.environ.get("AWS_SECRET_KEY")
_S3_BUCKET: str | None = os.environ.get("S3_BUCKET")
_AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")

StorageBackend = Literal["cloudinary", "s3"]

STORAGE_BACKEND: StorageBackend = "cloudinary" if _CLOUDINARY_URL else "s3"

# ---------------------------------------------------------------------------
# Cloudinary setup (lazy – only if backend is cloudinary)
# ---------------------------------------------------------------------------
if STORAGE_BACKEND == "cloudinary":
    cloudinary.config(cloudinary_url=_CLOUDINARY_URL)

# ---------------------------------------------------------------------------
# S3 client (lazy – only if backend is s3)
# ---------------------------------------------------------------------------
_s3_client = None


def _get_s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=_AWS_ACCESS_KEY,
            aws_secret_access_key=_AWS_SECRET_KEY,
            region_name=_AWS_REGION,
        )
    return _s3_client


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _upload_to_cloudinary(buffer: io.BytesIO, public_id: str) -> str:
    """Upload a BytesIO buffer to Cloudinary and return the secure URL."""
    result = cloudinary.uploader.upload(
        buffer,
        public_id=public_id,
        resource_type="image",
        format="jpg",
        overwrite=True,
    )
    return result["secure_url"]


def _upload_to_s3(buffer: io.BytesIO, key: str) -> str:
    """Upload a BytesIO buffer to S3 and return the public URL."""
    if not _S3_BUCKET:
        raise EnvironmentError("S3_BUCKET is not set in environment variables.")
    s3 = _get_s3()
    try:
        s3.upload_fileobj(
            buffer,
            _S3_BUCKET,
            key,
            ExtraArgs={"ContentType": "image/jpeg", "ACL": "public-read"},
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"S3 upload failed for key '{key}': {exc}") from exc

    return f"https://{_S3_BUCKET}.s3.{_AWS_REGION}.amazonaws.com/{key}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

VARIANT_KEY_MAP = {
    "thumbnail": "thumbnail",
    "720p": "720",
    "1080p": "1080",
    "2k": "2k",
    "4k": "4k",
    "8k": "8k",
}


def upload_variants(
    photo_id: uuid.UUID,
    buffers: dict[str, io.BytesIO],
) -> PhotoURLs:
    """
    Upload all image variants for a given photo and return their URLs.

    Parameters
    ----------
    photo_id : uuid.UUID
        Unique identifier – used to namespace the uploaded files.
    buffers : dict[str, io.BytesIO]
        Mapping returned by ``image_processing.process_image()``.

    Returns
    -------
    PhotoURLs
        Pydantic model containing five URL fields.
    """
    urls: dict[str, str] = {}

    for variant_name, buffer in buffers.items():
        slug = VARIANT_KEY_MAP.get(variant_name, variant_name)
        path = f"pixlume/{photo_id}/{slug}"

        if STORAGE_BACKEND == "cloudinary":
            url = _upload_to_cloudinary(buffer, public_id=path)
        else:
            key = f"{path}.jpg"
            url = _upload_to_s3(buffer, key=key)

        urls[variant_name] = url

    return PhotoURLs(
        thumbnail_url=urls["thumbnail"],
        image_720_url=urls["720p"],
        image_1080_url=urls["1080p"],
        image_2k_url=urls["2k"],
        image_4k_url=urls["4k"],
        image_8k_url=urls["8k"],
    )
