import base64
import io
import httpx
from PIL import Image


def load_image_from_url(url: str) -> Image.Image:
    """Load an image from a URL and convert to RGB PIL Image."""
    r = httpx.get(url, timeout=60)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")


def load_image_from_base64(b64: str) -> Image.Image:
    """Load an image from a base64 string and convert to RGB PIL Image."""
    raw = base64.b64decode(b64)
    return Image.open(io.BytesIO(raw)).convert("RGB")
