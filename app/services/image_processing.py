"""
Image processing service.

Responsibilities
----------------
• Receive an uploaded image as bytes
• Resize it to five standardised sizes using Pillow
• Return a dict of {variant_name: BytesIO} ready for upload
"""

import io
from typing import BinaryIO

from PIL import Image


# ---------------------------------------------------------------------------
# Target dimensions (width × height).  Height is calculated proportionally
# so we only define a target **long-edge** size to preserve the aspect ratio.
# ---------------------------------------------------------------------------
VARIANTS: dict[str, int] = {
    "thumbnail": 300,
    "720p": 1280,     # 720 p → 1280 px wide (16:9 reference)
    "1080p": 1920,    # 1080p → 1920 px wide
    "2k": 2560,       # 2K / QHD
    "4k": 3840,       # 4K / UHD
    "8k": 7680,       # 8K UHD
}


def _resize_image(img: Image.Image, max_long_edge: int) -> Image.Image:
    """
    Resize *img* so that its longest edge equals *max_long_edge*.
    The image is never upscaled (if it's already smaller it's returned as-is).
    """
    width, height = img.size
    long_edge = max(width, height)

    if long_edge <= max_long_edge:
        return img.copy()

    scale = max_long_edge / long_edge
    new_size = (int(width * scale), int(height * scale))
    return img.resize(new_size, Image.LANCZOS)


def process_image(file: BinaryIO) -> dict[str, io.BytesIO]:
    """
    Read *file* (a file-like object), generate all size variants, and return
    a mapping of variant name → BytesIO buffer.

    Parameters
    ----------
    file : BinaryIO
        The raw image bytes received from the upload endpoint.

    Returns
    -------
    dict[str, io.BytesIO]
        Keys are the variant names defined in VARIANTS plus "thumbnail".
    """
    original = Image.open(file)
    width, height = original.size
    long_edge = max(width, height)

    # Ensure correct colour mode – some PNGs arrive as RGBA / P etc.
    if original.mode not in ("RGB", "L"):
        original = original.convert("RGB")

    outputs: dict[str, io.BytesIO] = {}

    for variant_name, max_edge in VARIANTS.items():
        # STRICT DOWNSCALING LOGIC:
        # We only generate a variant if the original image is actually large enough
        # to support it. This prevents "Upscaling" artifacts.
        # Exception: We always keep the 'thumbnail' variant.
        if variant_name != "thumbnail" and long_edge < max_edge:
            continue

        resized = _resize_image(original, max_edge)
        buffer = io.BytesIO()

        # Use JPEG for all variants (good compression / browser support).
        # Thumbnail gets slightly higher compression; large variants stay sharp.
        quality = 80 if variant_name == "thumbnail" else 90
        resized.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        outputs[variant_name] = buffer

    return outputs
