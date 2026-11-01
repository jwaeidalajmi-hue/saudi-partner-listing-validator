"""Loads the photo standard (standards.yaml) and checks it is usable."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

PATH = Path(__file__).with_name("standards.yaml")
PROVIDER_TYPES = ("activities", "accommodation", "fnb", "shopping")


class StandardError(ValueError):
    pass


def validate(data: dict) -> dict:
    t = data.get("thresholds", {})
    if t.get("hd", [0, 0])[0] < 1024:
        raise StandardError("thresholds.hd must keep a long edge of at least 1024 pixels")
    for key in PROVIDER_TYPES:
        pt = data.get("provider_types", {}).get(key)
        if not pt:
            raise StandardError(f"provider type '{key}' is missing")
        scenes = pt.get("scenes", {})
        for field in ("fallback_required", "always_required", "suggested", "cover", "portrait_ok"):
            for s in pt.get(field, []):
                if s not in scenes:
                    raise StandardError(f"{key}.{field} names '{s}', which is not one of its scenes")
        if not pt.get("fallback_required"):
            raise StandardError(f"{key}.fallback_required needs at least one scene")
        if int(pt.get("min_photos", 0)) < 1:
            raise StandardError(f"{key}.min_photos must be 1 or more")
    return data


@lru_cache(maxsize=1)
def load() -> dict:
    with PATH.open(encoding="utf-8") as f:
        return validate(yaml.safe_load(f))


def provider(key: str) -> dict:
    data = load()
    if key not in data["provider_types"]:
        raise StandardError(f"unknown provider type '{key}'")
    return data["provider_types"][key]


def thresholds() -> dict:
    return load()["thresholds"]
