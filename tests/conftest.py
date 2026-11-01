import io
import os
import sys

import numpy as np
import pytest
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("VISION_PROVIDER", "mock")


def make_photo(w=1920, h=1080, blur=0, colour=(90, 140, 190), brightness=None, seed=1) -> bytes:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w]
    base = np.array(colour, dtype=np.float32)
    img = base + (np.sin(x / 7.0) * np.cos(y / 11.0) * 45)[..., None] + rng.normal(0, 18, (h, w, 1))
    if brightness is not None:
        img = img * 0 + brightness + rng.normal(0, 3, (h, w, 1))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@pytest.fixture
def photo():
    return make_photo
