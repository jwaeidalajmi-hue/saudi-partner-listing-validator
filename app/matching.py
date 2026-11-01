"""Turns the claims, the per-photo analyses and the technical measurements into
issues, a score out of 100 and a verdict. No AI here: plain, testable rules."""
from __future__ import annotations

from .messages import OVERLAY_AR, render
from .models import (Breakdown, Claim, ClaimCoverage, ImageAnalysis, Issue, SceneCheck, Technical)
from .technical import hash_distance

TIER_SCORE = {"4k": 1.0, "full_hd": 1.0, "hd": 0.7, "below_hd": 0.0}
BLOCKS_ON_PHOTO = {"below_hd", "too_large", "blurry", "overlay", "collage", "screenshot",
                   "unrelated", "contradicts", "exact_duplicate"}


def issue(code: str, severity: str, photo: int | None = None, claim_id: str | None = None, **v) -> Issue:
    en, ar = render(code, photo=photo, **v)
    return Issue(code=code, severity=severity, photo=photo, claim=claim_id, message_en=en, message_ar=ar)


def photo_issues(n: int, t: Technical, a: ImageAnalysis | None, std: dict, th: dict,
                 claims: dict[str, Claim]) -> list[Issue]:
    out: list[Issue] = []
    # technical
    if t.tier == "below_hd":
        out.append(issue("below_hd", "block", n, w=t.width, h=t.height))
    elif t.tier == "hd":
        out.append(issue("hd_not_full_hd", "warn", n, w=t.width, h=t.height))
    if t.bytes > th["max_bytes"]:
        out.append(issue("too_large", "block", n, mb=f"{t.bytes / 1048576:.1f}"))
    portrait_ok = a is not None and a.scene in std.get("portrait_ok", [])
    if t.orientation == "portrait" and not portrait_ok:
        out.append(issue("portrait", "warn", n))
    elif t.orientation == "square":
        out.append(issue("square", "warn", n))
    if t.sharpness < th["sharpness_block"]:
        out.append(issue("blurry", "block", n))
    elif t.sharpness < th["sharpness_pass"]:
        out.append(issue("slightly_soft", "warn", n))
    lo, hi = th["brightness"]
    if t.brightness < lo:
        out.append(issue("too_dark", "warn", n))
    elif t.brightness > hi or t.clipped > th["clipped_max"]:
        out.append(issue("too_bright", "warn", n))
    if t.saturation < th["grayscale_saturation"]:
        out.append(issue("black_and_white", "warn", n))
    if a is None:
        out.append(issue("not_checked", "info", n))
        return out
    # vision
    if a.overlays:
        out.append(issue("overlay", "block", n, what=", ".join(a.overlays),
                         what_ar="، ".join(OVERLAY_AR.get(x, x) for x in a.overlays)))
    if a.collage:
        out.append(issue("collage", "block", n))
    if a.screenshot:
        out.append(issue("screenshot", "block", n))
    if a.contradicts:
        c = claims.get(a.contradicts[0])
        out.append(issue("contradicts", "block", n, claim_id=a.contradicts[0],
                         caption=a.caption_en or "something else", caption_ar=a.caption_ar or "شيئًا آخر",
                         claim_ar=c.label_ar if c else "", claim=c.label_en if c else ""))
    elif a.unrelated and not a.supports:
        out.append(issue("unrelated", "block", n, caption=a.caption_en or "something else",
                         caption_ar=a.caption_ar or "شيئًا آخر"))
    if a.stock_or_ai:
        out.append(issue("stock_or_ai", "warn", n))
    if a.children:
        out.append(issue("children", "warn", n))
    elif a.people:
        out.append(issue("people_consent", "warn", n))
    if a.licence_plate:
        out.append(issue("licence_plate", "warn", n))
    if a.quality <= 2 and not any(i.severity == "block" for i in out):
        out.append(issue("low_quality", "warn", n, q=a.quality))
    return out


def duplicate_issues(techs: list[Technical], th: dict) -> dict[int, list[Issue]]:
    found: dict[int, list[Issue]] = {}
    for j in range(len(techs)):
        for i in range(j):
            d = hash_distance(techs[i].phash, techs[j].phash)
            if d == 0:
                found.setdefault(j + 1, []).append(issue("exact_duplicate", "block", j + 1, other=i + 1))
                break
            if d <= th["near_duplicate_distance"]:
                found.setdefault(j + 1, []).append(issue("near_duplicate", "warn", j + 1, other=i + 1))
                break
    return found


def technical_score(t: Technical, issues: list[Issue], th: dict) -> float:
    s = TIER_SCORE[t.tier]
    if t.sharpness < th["sharpness_block"]:
        s *= 0.2
    elif t.sharpness < th["sharpness_pass"]:
        s *= 0.7
    if any(i.code in ("too_dark", "too_bright") for i in issues):
        s *= 0.8
    if any(i.code in ("overlay", "collage", "screenshot", "too_large") for i in issues):
        s = 0.0
    return s


def evaluate(provider_type: str, std: dict, th: dict, claims: list[Claim],
             techs: list[Technical], analyses: list[ImageAnalysis | None]) -> dict:
    by_id = {c.id: c for c in claims}
    n_photos = len(techs)
    per_photo = [photo_issues(i + 1, t, analyses[i], std, th, by_id) for i, t in enumerate(techs)]
    for n, extra in duplicate_issues(techs, th).items():
        per_photo[n - 1].extend(extra)

    # claims covered by photos
    coverage: list[ClaimCoverage] = []
    for c in claims:
        photos = [i + 1 for i, a in enumerate(analyses) if a and c.id in a.supports]
        coverage.append(ClaimCoverage(claim=c, shown=bool(photos), photos=photos))

    # required scenes and the cover
    scenes = [a.scene if a else "other" for a in analyses]
    required = [SceneCheck(scene=s, label_en=std["scenes"][s]["en"], label_ar=std["scenes"][s]["ar"],
                           present=s in scenes, photos=[i + 1 for i, x in enumerate(scenes) if x == s])
                for s in std["required"]]
    cover_ok = bool(scenes) and scenes[0] in std["cover"]

    listing: list[Issue] = []
    core = [cc for cc in coverage if cc.claim.core]
    secondary = [cc for cc in coverage if not cc.claim.core]
    if not claims:
        listing.append(issue("no_visual_claims", "warn"))
    for cc in core:
        if not cc.shown:
            listing.append(issue("core_claim_missing", "block", claim_id=cc.claim.id,
                                 claim=cc.claim.label_en, claim_ar=cc.claim.label_ar))
    for cc in secondary:
        if not cc.shown:
            listing.append(issue("secondary_claim_missing", "warn", claim_id=cc.claim.id,
                                 claim=cc.claim.label_en, claim_ar=cc.claim.label_ar))
    for r in required:
        if not r.present:
            listing.append(issue("required_scene_missing", "block", scene=r.label_en, scene_ar=r.label_ar,
                                 type=std["name"]["en"], type_ar=std["name"]["ar"]))
    if n_photos < std["min_photos"]:
        listing.append(issue("too_few_photos", "block", need=std["min_photos"] - n_photos,
                             min=std["min_photos"], type=std["name"]["en"], type_ar=std["name"]["ar"]))
    if n_photos and not cover_ok:
        first = std["scenes"][std["cover"][0]]
        listing.append(issue("cover_wrong", "warn", scene=first["en"], scene_ar=first["ar"]))

    # score
    tech = sum(technical_score(t, per_photo[i], th) for i, t in enumerate(techs)) / n_photos if n_photos else 0
    core_ratio = (sum(cc.shown for cc in core) / len(core)) if core else (1.0 if claims else 0.5)
    sec_ratio = (sum(cc.shown for cc in secondary) / len(secondary)) if secondary else 1.0
    cov = 0.8 * core_ratio + 0.2 * sec_ratio
    relevant = [not any(i.code in ("unrelated", "contradicts") for i in per_photo[k]) for k in range(n_photos)]
    rel = sum(relevant) / n_photos if n_photos else 0
    req_ratio = sum(r.present for r in required) / len(required) if required else 1.0
    comp = 0.6 * req_ratio + 0.2 * min(1.0, n_photos / std["min_photos"]) + 0.2 * (1.0 if cover_ok else 0.0)
    breakdown = Breakdown(technical=round(30 * tech, 1), coverage=round(35 * cov, 1),
                          relevance=round(20 * rel, 1), completeness=round(15 * comp, 1))
    score = round(breakdown.technical + breakdown.coverage + breakdown.relevance + breakdown.completeness)
    blocking = any(i.severity == "block" for i in listing) or any(
        i.severity == "block" for p in per_photo for i in p)
    verdict = "ready" if score >= th["ready_score"] and not blocking else "needs_changes"
    return dict(per_photo=per_photo, coverage=coverage, required=required, cover_ok=cover_ok,
                listing_issues=listing, breakdown=breakdown, score=score, verdict=verdict)
