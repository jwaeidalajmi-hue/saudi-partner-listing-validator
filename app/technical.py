"""Checks that need no AI: size, resolution tier, orientation, sharpness,
exposure, colour and perceptual hash. Runs locally on every photo."""
from __future__ import annotations

import io

import cv2
import imagehash
import numpy as np
from PIL import Image, ImageOps

from .models import Technical
from .standards import thresholds


def open_image(data: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(data))
    im = ImageOps.exif_transpose(im)     # respect camera orientation
    return im.convert("RGB")


def tier_of(w: int, h: int) -> str:
    t = thresholds()
    long_e, short_e = max(w, h), min(w, h)
    if long_e >= t["uhd"][0] and short_e >= t["uhd"][1]:
        return "4k"
    if long_e >= t["full_hd"][0] and short_e >= t["full_hd"][1]:
        return "full_hd"
    if long_e >= t["hd"][0] and short_e >= t["hd"][1]:
        return "hd"
    return "below_hd"


def orientation_of(w: int, h: int) -> str:
    r = w / h if h else 1
    if 0.95 <= r <= 1.05:
        return "square"
    return "landscape" if r > 1 else "portrait"


def measure(data: bytes) -> Technical:
    im = open_image(data)
    w, h = im.size
    # measure on a copy with a 1024 px long edge so thresholds mean the same at any size
    small = im.copy()
    small.thumbnail((1024, 1024))
    arr = np.asarray(small)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    bright = float(gray.mean())
    clipped = float(((gray <= 2) | (gray >= 253)).mean())
    sat = float(cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)[:, :, 1].mean())
    return Technical(
        width=w, height=h, megapixels=round(w * h / 1e6, 2),
        tier=tier_of(w, h), orientation=orientation_of(w, h), bytes=len(data),
        sharpness=round(sharp, 1), brightness=round(bright, 1), clipped=round(clipped, 4),
        saturation=round(sat, 1), phash=str(imagehash.phash(im)),
    )


def hash_distance(a: str, b: str) -> int:
    return imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b)


def for_model(data: bytes, long_edge: int = 1568) -> tuple[bytes, str]:
    """A JPEG copy sized for the vision model (fewer tokens, same content)."""
    im = open_image(data)
    im.thumbnail((long_edge, long_edge))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=88)
    return buf.getvalue(), "image/jpeg"
