"""HTTP API and the demo web page."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import standards
from .config import settings
from .models import ListingReport
from .pipeline import validate_listing
from .providers import get_provider

WEB = Path(__file__).resolve().parent.parent / "web"
ALLOWED = {"image/jpeg", "image/png", "image/webp"}

app = FastAPI(title="Saudi Partner Listing Photo Validator", version="0.1.0",
              description="Checks a listing's photos against its description and a photo standard per provider type.")


@app.get("/api/health")
def health():
    return {"ok": True, "engine": settings.vision_provider, "model": settings.anthropic_model
            if settings.vision_provider == "anthropic" else None}


@app.get("/api/standards")
def get_standards():
    return standards.load()


@app.post("/api/validate", response_model=ListingReport)
async def validate(provider_type: str = Form(..., description="activities | accommodation | fnb | shopping"),
                   description: str = Form("", description="The listing description, Arabic or English"),
                   photos: list[UploadFile] = File(..., description="Photos in display order; the first is the cover")):
    if provider_type not in standards.PROVIDER_TYPES:
        raise HTTPException(422, f"provider_type must be one of {', '.join(standards.PROVIDER_TYPES)}")
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
    try:
        provider = get_provider()
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return await validate_listing(provider, provider_type, description, items)


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


app.mount("/web", StaticFiles(directory=WEB), name="web")
