"""One listing in, one report out: technical checks, criteria, vision, matching."""
from __future__ import annotations

import asyncio
import time

from . import standards
from .config import settings
from .criteria import finalise
from .matching import evaluate
from .models import Claim, CriteriaResponse, ImageAnalysis, ListingReport, PhotoReport
from .providers.base import VisionProvider
from .technical import for_model, measure


async def read_criteria(provider: VisionProvider, provider_type: str, description: str) -> CriteriaResponse:
    """What the photos will be checked against, for the provider to review and edit before checking."""
    std = standards.provider(provider_type)
    claims = await provider.extract_claims(description, provider_type, std) if description.strip() else []
    final, from_standard = finalise(claims, std)
    return CriteriaResponse(provider_type=provider_type, claims=final, from_standard=from_standard,
                            engine=provider.name)


async def validate_listing(provider: VisionProvider, provider_type: str, description: str,
                           photos: list[tuple[str, bytes]], criteria: list[Claim] | None = None) -> ListingReport:
    """`criteria`: the provider's reviewed list. None = read them from the description now."""
    t0 = time.perf_counter()
    std = standards.provider(provider_type)
    th = standards.thresholds()

    techs = [measure(data) for _, data in photos]
    if criteria is None:
        criteria = await provider.extract_claims(description, provider_type, std) if description.strip() else []
    claims, from_standard = finalise(criteria, std)

    sem = asyncio.Semaphore(settings.concurrency)

    async def one(name: str, data: bytes) -> ImageAnalysis | None:
        async with sem:
            try:
                small, mime = for_model(data)
                return await provider.analyze_image(small, mime, name, provider_type, std, claims)
            except Exception:
                return None      # reported as "not checked"; technical checks still apply

    analyses = list(await asyncio.gather(*(one(n, d) for n, d in photos)))
    demo = provider.name == "mock"
    r = evaluate(provider_type, std, th, claims, techs, analyses, demo=demo, from_standard=from_standard)

    photo_reports = [PhotoReport(index=i + 1, filename=photos[i][0], checked=analyses[i] is not None,
                                 technical=techs[i],
                                 analysis=analyses[i] or ImageAnalysis(caption_en="not checked",
                                                                        caption_ar="لم تُحلَّل"),
                                 issues=r["per_photo"][i]) for i in range(len(photos))]
    all_issues = r["listing_issues"] + [i for p in r["per_photo"] for i in p]
    blocks = sum(i.severity == "block" for i in all_issues)
    shown = sum(c.status == "shown" for c in r["coverage"])
    checked = sum(a is not None for a in analyses)
    n = len(claims)
    en = f"{shown} of {n} criteria have a matching photo."
    ar = f"{shown} من {n} معايير لها صورة مطابقة."
    if checked < len(photos):
        why_en = " (demo mode, no AI)" if demo else ""
        why_ar = " (وضع تجريبي بلا ذكاء اصطناعي)" if demo else ""
        en += f" The content of {len(photos) - checked} of {len(photos)} photos wasn't analysed{why_en}."
        ar += f" لم يُحلَّل محتوى {len(photos) - checked} من {len(photos)} صور{why_ar}."
    if r["verdict"] == "ready":
        summary_en, summary_ar = f"Ready for review. {en}", f"جاهز للمراجعة. {ar}"
    elif r["verdict"] == "partly_checked":
        summary_en, summary_ar = f"Checked in part, nothing to fix so far. {en}", f"فُحص جزئيًا، ولا شيء يحتاج إلى إصلاح حتى الآن. {ar}"
    else:
        summary_en = f"Needs changes: {blocks} issue(s) to fix before review. {en}"
        summary_ar = f"يحتاج إلى تعديل: {blocks} ملاحظة يجب معالجتها قبل المراجعة. {ar}"
    return ListingReport(
        provider_type=provider_type, verdict=r["verdict"], score=r["score"], breakdown=r["breakdown"],
        claims=r["coverage"], rules=r["rules"], suggested=r["suggested"], min_photos=std["min_photos"],
        photo_count=len(photos), photos_checked=checked, cover_ok=r["cover_ok"], photos=photo_reports,
        issues=all_issues, summary_en=summary_en, summary_ar=summary_ar, engine=provider.name,
        standard_version=standards.load()["version"], duration_ms=round((time.perf_counter() - t0) * 1000),
    )
