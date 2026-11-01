"""The criteria a listing's photos are checked against.

They come from the description, may be edited by the provider, and fall back
to the provider type's scenes only when the description names nothing a photo
can show. No AI here."""
from __future__ import annotations

import re

from .models import Claim

MAX_CRITERIA = 15
MAX_LABEL = 80
ARABIC = re.compile(r"[؀-ۿ]")


def standard_criteria(std: dict, scenes: list[str], prefix: str = "s") -> list[Claim]:
    out = []
    for s in scenes:
        lab = std["scenes"][s]
        out.append(Claim(id=f"{prefix}_{s}", label=lab["en"], label_en=lab["en"], label_ar=lab["ar"],
                         kind="scene", core=True, scene=s, source="standard",
                         evidence_en=lab["en"], evidence_ar=lab["ar"]))
    return out


def finalise(claims: list[Claim], std: dict) -> tuple[list[Claim], bool]:
    """Add STA's always-required scenes; use the fallback scenes if nothing else.
    Returns the criteria and whether they came from the standard."""
    out = list(claims)
    from_standard = False
    if not any(c.source != "standard" for c in out):
        have = {c.scene for c in out if c.source == "standard"}
        out += [c for c in standard_criteria(std, std["fallback_required"]) if c.scene not in have]
        from_standard = True
    have = {c.scene for c in out if c.source == "standard"}
    out += [c for c in standard_criteria(std, std.get("always_required", []), "a") if c.scene not in have]
    return out[:MAX_CRITERIA + len(std.get("always_required", []))], from_standard


def from_provider(raw: list, std: dict) -> list[Claim]:
    """Criteria the provider sent back from the editor: theirs, edited or new."""
    if not isinstance(raw, list):
        raise ValueError("criteria must be a list")
    out, seen = [], set()
    for i, c in enumerate(raw[:MAX_CRITERIA], 1):
        if isinstance(c, str):
            c = {"label": c}
        if not isinstance(c, dict):
            raise ValueError("each criterion must be text or an object with a label")
        label = str(c.get("label") or "").strip()[:MAX_LABEL]
        if not label or label.lower() in seen:
            continue
        seen.add(label.lower())
        source = c.get("source") if c.get("source") in ("description", "provider", "standard") else "provider"
        scene = c.get("scene") if c.get("scene") in std["scenes"] else None
        if source == "standard" and not scene:
            source = "provider"
        out.append(Claim(
            id=str(c.get("id") or f"u{i}")[:24],
            label=label,
            label_en=str(c.get("label_en") or label).strip()[:MAX_LABEL],
            label_ar=str(c.get("label_ar") or label).strip()[:MAX_LABEL],
            kind=str(c.get("kind") or "other")[:24],
            core=bool(c.get("core", True)),
            scene=scene,
            source=source,
            evidence_en=str(c.get("evidence_en") or "")[:160],
            evidence_ar=str(c.get("evidence_ar") or "")[:160],
        ))
    ids = [c.id for c in out]
    if len(ids) != len(set(ids)):          # make ids unique if the client repeated one
        for n, c in enumerate(out, 1):
            c.id = f"u{n}"
    return out


def is_arabic(text: str) -> bool:
    return bool(ARABIC.search(text))
