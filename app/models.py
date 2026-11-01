"""Data shapes shared by the pipeline and the API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["block", "warn", "info"]
Verdict = Literal["ready", "needs_changes", "partly_checked"]
Source = Literal["description", "provider", "standard"]


class Claim(BaseModel):
    """A criterion: something a photo of this listing should show.

    Most come from the listing's own description. The provider can edit them,
    remove them or add their own (source = "provider"). When the description
    names nothing a photo can show, the provider type's fallback scenes are
    used instead (source = "standard")."""
    id: str
    label: str                      # as written, in the description's language
    label_en: str
    label_ar: str
    kind: str = "other"             # one of the provider type's claim_kinds
    core: bool = True               # must be shown; False = nice to have
    scene: str | None = None        # the scene key a matching photo would have
    source: Source = "description"
    evidence_en: str = ""           # what a matching photo shows, e.g. "someone diving underwater"
    evidence_ar: str = ""


class ImageAnalysis(BaseModel):
    """What the vision model sees in one photo."""
    scene: str = "other"            # the main scene key of the provider type, or "other"
    scenes: list[str] = Field(default_factory=list)          # every scene it shows (a diver over a reef: activity + place)
    scene_confidence: float = 0.0
    objects: list[str] = Field(default_factory=list)
    supports: list[str] = Field(default_factory=list)      # criterion ids this photo shows
    contradicts: list[str] = Field(default_factory=list)   # criterion ids this photo goes against
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

    def all_scenes(self) -> list[str]:
        return self.scenes or [self.scene]


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
    checked: bool                   # False: the vision step did not run on this photo
    technical: Technical
    analysis: ImageAnalysis
    issues: list[Issue]


class ClaimCoverage(BaseModel):
    claim: Claim
    status: Literal["shown", "missing", "unchecked"]
    shown: bool
    photos: list[int]


class RuleCheck(BaseModel):
    """A rule of the provider type: enough photos, a first photo that shows what the listing is about."""
    code: Literal["min_photos", "cover"]
    label_en: str
    label_ar: str
    status: Literal["pass", "fail", "unchecked"]
    photos: list[int] = Field(default_factory=list)


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


class CriteriaResponse(BaseModel):
    provider_type: str
    claims: list[Claim]
    from_standard: bool             # True: the description named nothing a photo can show
    engine: str


class ListingReport(BaseModel):
    provider_type: str
    verdict: Verdict
    score: int
    breakdown: Breakdown
    claims: list[ClaimCoverage]     # the criteria and whether a photo shows each
    rules: list[RuleCheck]
    suggested: list[SceneCheck]     # tips for the provider type; never block
    min_photos: int
    photo_count: int
    photos_checked: int
    cover_ok: bool
    photos: list[PhotoReport]
    issues: list[Issue]
    summary_en: str
    summary_ar: str
    engine: str                     # "anthropic:<model>" or "mock"
    standard_version: str
    duration_ms: int
