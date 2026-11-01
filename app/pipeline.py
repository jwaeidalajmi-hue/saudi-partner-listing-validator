"""One listing in, one report out: technical checks, claims, vision, matching."""
from __future__ import annotations

import asyncio
import time

from . import standards
from .config import settings
from .matching import evaluate
from .models import ImageAnalysis, ListingReport, PhotoReport
from .providers.base import VisionProvider
from .technical import for_model, measure


async def validate_listing(provider: VisionProvider, provider_type: str, description: str,
                           photos: list[tuple[str, bytes]]) -> ListingReport:
    t0 = time.perf_counter()
    std = standards.provider(provider_type)
    th = standards.thresholds()

    techs = [measure(data) for _, data in photos]
    claims = await provider.extract_claims(description, provider_type, std)

    sem = asyncio.Semaphore(settings.concurrency)

    async def one(name: str, data: bytes) -> ImageAnalysis | None:
        async with sem:
            try:
                small, mime = for_model(data)
                return await provider.analyze_image(small, mime, name, provider_type, std, claims)
            except Exception:
                return None      # reported as "not checked"; technical checks still apply

    analyses = await asyncio.gather(*(one(n, d) for n, d in photos))
    r = evaluate(provider_type, std, th, claims, techs, list(analyses))

    photo_reports = [PhotoReport(index=i + 1, filename=photos[i][0], technical=techs[i],
                                 analysis=analyses[i] or ImageAnalysis(caption_en="not checked",
                                                                        caption_ar="لم تُفحص"),
                                 issues=r["per_photo"][i]) for i in range(len(photos))]
    all_issues = r["listing_issues"] + [i for p in r["per_photo"] for i in p]
    blocks = sum(i.severity == "block" for i in all_issues)
    shown = sum(c.shown for c in r["coverage"])
    if r["verdict"] == "ready":
        summary_en = f"Ready for review. {shown} of {len(claims)} claims in the description have a matching photo."
        summary_ar = f"جاهز للمراجعة. {shown} من {len(claims)} عناصر في الوصف لها صورة مطابقة."
    else:
        summary_en = (f"Needs changes: {blocks} issue(s) to fix before review. "
                      f"{shown} of {len(claims)} claims in the description have a matching photo.")
        summary_ar = (f"يحتاج إلى تعديل: {blocks} ملاحظة يجب معالجتها قبل المراجعة. "
                      f"{shown} من {len(claims)} عناصر في الوصف لها صورة مطابقة.")
    return ListingReport(
        provider_type=provider_type, verdict=r["verdict"], score=r["score"], breakdown=r["breakdown"],
        claims=r["coverage"], required=r["required"], min_photos=std["min_photos"],
        photo_count=len(photos), cover_ok=r["cover_ok"], photos=photo_reports, issues=all_issues,
        summary_en=summary_en, summary_ar=summary_ar, engine=provider.name,
        standard_version=standards.load()["version"], duration_ms=round((time.perf_counter() - t0) * 1000),
    )
