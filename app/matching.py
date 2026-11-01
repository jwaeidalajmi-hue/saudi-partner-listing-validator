"""Turns the criteria, the per-photo analyses and the technical measurements into
issues, a score out of 100 and a verdict. No AI here: plain, testable rules.

What a listing must show comes from its criteria (its own description, as the
provider edited it). The provider type adds two rules (enough photos; a first
photo that shows what the listing is about) and suggestions that never block."""
from __future__ import annotations

from .messages import OVERLAY_AR, render
from .models import (Breakdown, Claim, ClaimCoverage, ImageAnalysis, Issue, RuleCheck, SceneCheck,
                     Technical)
from .technical import hash_distance

TIER_SCORE = {"4k": 1.0, "full_hd": 1.0, "hd": 0.7, "below_hd": 0.0}
MAX_SUGGESTIONS = 2


def issue(code: str, severity: str, photo: int | None = None, claim_id: str | None = None, **v) -> Issue:
    en, ar = render(code, photo=photo, **v)
    return Issue(code=code, severity=severity, photo=photo, claim=claim_id, message_en=en, message_ar=ar)


def scenes_of(a: ImageAnalysis | None) -> list[str]:
    return a.all_scenes() if a else []


def shows(a: ImageAnalysis | None, c: Claim) -> bool:
    """A photo shows a criterion when the model says so; a standard criterion
    (a scene of the provider type) is also met by a photo of that scene."""
    if a is None:
        return False
    return c.id in a.supports or (c.source == "standard" and c.scene in scenes_of(a))


def photo_issues(n: int, t: Technical, a: ImageAnalysis | None, std: dict, th: dict,
                 claims: dict[str, Claim], demo: bool = False) -> list[Issue]:
    out: list[Issue] = []
    # technical
    if t.tier == "below_hd":
        out.append(issue("below_hd", "block", n, w=t.width, h=t.height))
    elif t.tier == "hd":
        out.append(issue("hd_not_full_hd", "warn", n, w=t.width, h=t.height))
    if t.bytes > th["max_bytes"]:
        out.append(issue("too_large", "block", n, mb=f"{t.bytes / 1048576:.1f}"))
    portrait_ok = a is not None and any(s in std.get("portrait_ok", []) for s in scenes_of(a))
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
        out.append(issue("not_checked_demo" if demo else "not_checked", "info", n))
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


def _join(labels: list[str], word: str) -> str:
    return labels[0] if len(labels) == 1 else f" {word} ".join([", ".join(labels[:-1]), labels[-1]])


def evaluate(provider_type: str, std: dict, th: dict, claims: list[Claim],
             techs: list[Technical], analyses: list[ImageAnalysis | None], demo: bool = False,
             from_standard: bool = False) -> dict:
    by_id = {c.id: c for c in claims}
    n_photos = len(techs)
    per_photo = [photo_issues(i + 1, t, analyses[i], std, th, by_id, demo) for i, t in enumerate(techs)]
    for n, extra in duplicate_issues(techs, th).items():
        per_photo[n - 1].extend(extra)
    any_unchecked = any(a is None for a in analyses)

    # every criterion: shown, missing, or not checked (some photos could not be analysed)
    coverage: list[ClaimCoverage] = []
    for c in claims:
        photos = [i + 1 for i, a in enumerate(analyses) if shows(a, c)]
        status = "shown" if photos else ("unchecked" if any_unchecked else "missing")
        coverage.append(ClaimCoverage(claim=c, status=status, shown=bool(photos), photos=photos))
    core = [cc for cc in coverage if cc.claim.core]
    secondary = [cc for cc in coverage if not cc.claim.core]

    # rule 1: enough photos
    rules = [RuleCheck(code="min_photos", status="pass" if n_photos >= std["min_photos"] else "fail",
                       label_en=f"At least {std['min_photos']} photos ({n_photos} now)",
                       label_ar=f"{std['min_photos']} صور على الأقل ({n_photos} حاليًا)")]
    # rule 2: the first photo shows what the listing is about
    main = (core or coverage)[:2]
    if main:
        main_en = _join([cc.claim.label_en for cc in main], "or")
        main_ar = _join([cc.claim.label_ar for cc in main], "أو")
    else:
        first = std["scenes"][std["cover"][0]]
        main_en, main_ar = first["en"], first["ar"]
    first_photo = analyses[0] if analyses else None
    if not n_photos:
        cover = "fail"
    elif first_photo is None:
        cover = "unchecked"
    elif core:
        cover = "pass" if any(shows(first_photo, cc.claim) for cc in core) else "fail"
    else:
        cover = "pass" if set(scenes_of(first_photo)) & set(std["cover"]) else "fail"
    rules.append(RuleCheck(code="cover", status=cover, photos=[1] if cover == "pass" else [],
                           label_en=f"The first photo shows {main_en}", label_ar=f"الصورة الأولى تُظهر {main_ar}"))
    cover_ok = cover == "pass"

    # suggestions for the provider type (never block)
    suggested = [SceneCheck(scene=s, label_en=std["scenes"][s]["en"], label_ar=std["scenes"][s]["ar"],
                            present=bool(ph := [i + 1 for i, a in enumerate(analyses) if s in scenes_of(a)]),
                            photos=ph) for s in std.get("suggested", [])]

    listing: list[Issue] = []
    if from_standard:
        listing.append(issue("no_visual_claims", "warn", type=std["name"]["en"], type_ar=std["name"]["ar"]))
    for cc in core:
        if cc.status == "missing":
            key = "required_scene_missing" if cc.claim.source == "standard" else "core_claim_missing"
            listing.append(issue(key, "block", claim_id=cc.claim.id, claim=cc.claim.label_en,
                                 claim_ar=cc.claim.label_ar, type=std["name"]["en"], type_ar=std["name"]["ar"]))
        elif cc.status == "unchecked":
            listing.append(issue("claim_unchecked", "info", claim_id=cc.claim.id, claim=cc.claim.label_en,
                                 claim_ar=cc.claim.label_ar))
    for cc in secondary:
        if cc.status == "missing":
            listing.append(issue("secondary_claim_missing", "warn", claim_id=cc.claim.id,
                                 claim=cc.claim.label_en, claim_ar=cc.claim.label_ar))
    if n_photos < std["min_photos"]:
        listing.append(issue("too_few_photos", "block", need=std["min_photos"] - n_photos,
                             min=std["min_photos"], type=std["name"]["en"], type_ar=std["name"]["ar"]))
    if n_photos and cover == "fail":
        listing.append(issue("cover_wrong", "warn", claim=main_en, claim_ar=main_ar))
    if not any_unchecked:
        covered = {c.scene for c in claims if c.scene}
        for s in [x for x in suggested if not x.present and x.scene not in covered][:MAX_SUGGESTIONS]:
            listing.append(issue("suggested_scene", "info", scene=s.label_en, scene_ar=s.label_ar))

    # score
    weight = {"shown": 1.0, "unchecked": 0.5, "missing": 0.0}
    tech = sum(technical_score(t, per_photo[i], th) for i, t in enumerate(techs)) / n_photos if n_photos else 0
    core_ratio = sum(weight[cc.status] for cc in core) / len(core) if core else 1.0
    sec_ratio = sum(weight[cc.status] for cc in secondary) / len(secondary) if secondary else 1.0
    cov = 0.8 * core_ratio + 0.2 * sec_ratio
    relevant = [not any(i.code in ("unrelated", "contradicts") for i in per_photo[k]) for k in range(n_photos)]
    rel = sum(relevant) / n_photos if n_photos else 0
    sugg_ratio = sum(s.present for s in suggested) / len(suggested) if suggested else 1.0
    comp = (0.5 * min(1.0, n_photos / std["min_photos"]) + 0.3 * {"pass": 1.0, "unchecked": 0.5, "fail": 0.0}[cover]
            + 0.2 * sugg_ratio)
    breakdown = Breakdown(technical=round(30 * tech, 1), coverage=round(35 * cov, 1),
                          relevance=round(20 * rel, 1), completeness=round(15 * comp, 1))
    score = round(breakdown.technical + breakdown.coverage + breakdown.relevance + breakdown.completeness)
    blocking = any(i.severity == "block" for i in listing) or any(
        i.severity == "block" for p in per_photo for i in p)
    unchecked = any(cc.status == "unchecked" for cc in coverage) or cover == "unchecked"
    if blocking:
        verdict = "needs_changes"
    elif unchecked:
        verdict = "partly_checked"
    else:
        verdict = "ready" if score >= th["ready_score"] else "needs_changes"
    return dict(per_photo=per_photo, coverage=coverage, rules=rules, suggested=suggested, cover_ok=cover_ok,
                listing_issues=listing, breakdown=breakdown, score=score, verdict=verdict)
