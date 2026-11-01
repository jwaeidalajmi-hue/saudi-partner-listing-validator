"""Data shapes shared by the pipeline and the API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["block", "warn", "info"]
Verdict = Literal["ready", "needs_changes"]


class Claim(BaseModel):
    """Something the description says that a photo can show."""
    id: str
    label: str                      # in the description's language
    label_en: str
    label_ar: str
    kind: str                       # one of the provider type's claim_kinds
    core: bool                      # what the listing is about: needs a photo
    scene: str | None = None        # the scene key a matching photo would have


class ImageAnalysis(BaseModel):
    """What the vision model sees in one photo."""
    scene: str = "other"            # a scene key of the provider type, or "other"
    scene_confidence: float = 0.0
    objects: list[str] = Field(default_factory=list)
    supports: list[str] = Field(default_factory=list)      # claim ids this photo shows
    contradicts: list[str] = Field(default_factory=list)   # claim ids this photo goes against
    unrelated: bool = False         # shows nothing the listing is about
    overlays: list[str] = Field(default_factory=list)      # watermark, logo, text, border
    collage: bool = False
    screenshot: bool = False
    stock_or_ai: bool = False
    people: bool = False
    children: bool = False
    licence_plate: bool = False
    quality: int = 3                # 1 poor to 5 excellent, as a booking-page photo
    caption_en: str = ""
    caption_ar: str = ""


class Technical(BaseModel):
    width: int
    height: int
    megapixels: float
    tier: Literal["below_hd", "hd", "full_hd", "4k"]
    orientation: Literal["landscape", "portrait", "square"]
    bytes: int
    sharpness: float
    brightness: float
    clipped: float
    saturation: float
    phash: str


class Issue(BaseModel):
    code: str
    severity: Severity
    photo: int | None = None        # 1-based photo number
    claim: str | None = None
    message_en: str
    message_ar: str


class PhotoReport(BaseModel):
    index: int                      # 1-based
    filename: str
    technical: Technical
    analysis: ImageAnalysis
    issues: list[Issue]


class ClaimCoverage(BaseModel):
    claim: Claim
    shown: bool
    photos: list[int]


class SceneCheck(BaseModel):
    scene: str
    label_en: str
    label_ar: str
    present: bool
    photos: list[int]


class Breakdown(BaseModel):
    technical: float
    coverage: float
    relevance: float
    completeness: float


class ListingReport(BaseModel):
    provider_type: str
    verdict: Verdict
    score: int
    breakdown: Breakdown
    claims: list[ClaimCoverage]
    required: list[SceneCheck]
    min_photos: int
    photo_count: int
    cover_ok: bool
    photos: list[PhotoReport]
    issues: list[Issue]
    summary_en: str
    summary_ar: str
    engine: str                     # "anthropic:<model>" or "mock"
    standard_version: str
    duration_ms: int
