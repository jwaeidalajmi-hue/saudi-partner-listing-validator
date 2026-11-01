"""HTTP API and the demo web page."""
from __future__ import annotations

from pathlib import Path

import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import standards
from .config import settings
from .criteria import from_provider
from .models import CriteriaResponse, ListingReport
from .pipeline import read_criteria, validate_listing
from .providers import get_provider

WEB = Path(__file__).resolve().parent.parent / "web"
ALLOWED = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="Saudi Partner Listing Validator", version="0.2.0",
              description="Checks a listing's photos against criteria read from its own description "
                          "(which the provider can edit), plus a photo standard per provider type.")


@app.get("/api/health")
def health():
    return {"ok": True, "engine": settings.vision_provider, "demo": settings.vision_provider == "mock",
            "model": settings.anthropic_model if settings.vision_provider == "anthropic" else None}


@app.get("/api/standards")
def get_standards():
    return standards.load()


def _provider():
    try:
        return get_provider()
    except RuntimeError as e:
        raise HTTPException(503, str(e))


def _check_type(provider_type: str):
    if provider_type not in standards.PROVIDER_TYPES:
        raise HTTPException(422, f"provider_type must be one of {', '.join(standards.PROVIDER_TYPES)}")


@app.post("/api/criteria", response_model=CriteriaResponse)
async def criteria(provider_type: str = Form(..., description="activities | accommodation | fnb | shopping"),
                   description: str = Form("", description="The listing description, Arabic or English")):
    """Read the description into the criteria the photos will be checked against,
    so the provider can review, edit, remove or add before checking."""
    _check_type(provider_type)
    try:
        return await read_criteria(_provider(), provider_type, description)
    except HTTPException:
        raise
    except Exception as e:                     # the model was unreachable or replied badly
        raise HTTPException(502, f"Couldn't read the description: {e}")


@app.post("/api/validate", response_model=ListingReport)
async def validate(provider_type: str = Form(..., description="activities | accommodation | fnb | shopping"),
                   description: str = Form("", description="The listing description, Arabic or English"),
                   criteria: str | None = Form(None, description="Optional JSON list of criteria from /api/criteria, "
                                                                 "as the provider edited them. Each item is text or "
                                                                 "{label, core?}. Omit to read them from the description."),
                   photos: list[UploadFile] = File(..., description="Photos in display order; the first is the cover")):
    _check_type(provider_type)
    chosen = None
    if criteria:
        try:
            chosen = from_provider(json.loads(criteria), standards.provider(provider_type))
        except (ValueError, TypeError) as e:
            raise HTTPException(422, f"criteria: {e}")
    if not photos:
        raise HTTPException(422, "Add at least one photo.")
    if len(photos) > settings.max_photos:
        raise HTTPException(422, f"At most {settings.max_photos} photos per listing.")
    items = []
    for f in photos:
        if f.content_type not in ALLOWED:
            raise HTTPException(415, f"{f.filename}: use JPEG, PNG or WebP.")
        data = await f.read()
        if len(data) > settings.max_upload_mb * 1048576:
            raise HTTPException(413, f"{f.filename} is larger than {settings.max_upload_mb:g} MB.")
        items.append((f.filename or f"photo-{len(items) + 1}", data))
    return await validate_listing(_provider(), provider_type, description, items, chosen)


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/web", StaticFiles(directory=WEB), name="web")
