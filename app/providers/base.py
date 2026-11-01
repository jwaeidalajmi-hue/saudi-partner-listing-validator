"""The one interface the pipeline uses to reach a model. Swap the model by
writing another provider; nothing else changes."""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

from ..models import Claim, ImageAnalysis


class VisionProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def extract_claims(self, description: str, provider_type: str, std: dict) -> list[Claim]:
        ...

    @abstractmethod
    async def analyze_image(self, data: bytes, mime: str, filename: str, provider_type: str,
                            std: dict, claims: list[Claim]) -> ImageAnalysis:
        ...


def parse_json(text: str) -> dict:
    """Read the model's JSON even if it wrapped it in a code fence or a sentence."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1)
    start = min([i for i in (text.find("{"), text.find("[")) if i >= 0], default=-1)
    end = max(text.rfind("}"), text.rfind("]"))
    if start < 0 or end < start:
        raise ValueError("no JSON in the model reply")
    return json.loads(text[start:end + 1])


def clean_claims(raw: dict, std: dict) -> list[Claim]:
    out, seen = [], set()
    for i, c in enumerate(raw.get("claims", [])[:12], 1):
        label_en = str(c.get("label_en") or c.get("label") or "").strip()
        if not label_en or label_en.lower() in seen:
            continue
        seen.add(label_en.lower())
        scene = c.get("scene")
        out.append(Claim(
            id=str(c.get("id") or f"c{i}"),
            label=str(c.get("label") or label_en),
            label_en=label_en,
            label_ar=str(c.get("label_ar") or c.get("label") or label_en),
            kind=str(c.get("kind") or "other"),
            core=bool(c.get("core", False)),
            scene=scene if scene in std["scenes"] else None,
        ))
    return out


def clean_analysis(raw: dict, std: dict, claim_ids: set[str]) -> ImageAnalysis:
    scene = raw.get("scene")
    return ImageAnalysis(
        scene=scene if scene in std["scenes"] else "other",
        scene_confidence=float(raw.get("scene_confidence") or 0),
        objects=[str(x) for x in raw.get("objects", [])][:8],
        supports=[str(x) for x in raw.get("supports", []) if str(x) in claim_ids],
        contradicts=[str(x) for x in raw.get("contradicts", []) if str(x) in claim_ids],
        unrelated=bool(raw.get("unrelated", False)),
        overlays=[str(x) for x in raw.get("overlays", []) if x in ("watermark", "logo", "text", "border")],
        collage=bool(raw.get("collage", False)),
        screenshot=bool(raw.get("screenshot", False)),
        stock_or_ai=bool(raw.get("stock_or_ai", False)),
        people=bool(raw.get("people", False)),
        children=bool(raw.get("children", False)),
        licence_plate=bool(raw.get("licence_plate", False)),
        quality=max(1, min(5, int(raw.get("quality") or 3))),
        caption_en=str(raw.get("caption_en") or ""),
        caption_ar=str(raw.get("caption_ar") or ""),
    )
