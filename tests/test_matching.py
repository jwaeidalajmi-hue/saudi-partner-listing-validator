"""The rules that turn claims + photo analyses into a verdict, with the four
examples from the brief: a pool, a bedroom and bathroom, a salad, t-shirts."""
from app import standards
from app.matching import evaluate
from app.models import Claim, ImageAnalysis, Technical


def tech(w=1920, h=1080, sharp=200, bright=130, size=400_000, phash=None, n=0):
    return Technical(width=w, height=h, megapixels=round(w * h / 1e6, 2),
                     tier="full_hd" if w >= 1920 else ("hd" if w >= 1280 else "below_hd"),
                     orientation="landscape" if w > h else "portrait", bytes=size, sharpness=sharp,
                     brightness=bright, clipped=0.0, saturation=60,
                     phash=phash or f"{(0x8f3c << (n % 48)) & 0xffffffffffffffff:016x}")


def claim(i, en, ar, kind, core, scene):
    return Claim(id=i, label=en, label_en=en, label_ar=ar, kind=kind, core=core, scene=scene)


def run(ptype, claims, analyses, techs=None, from_standard=False):
    std, th = standards.provider(ptype), standards.thresholds()
    techs = techs or [tech(n=i * 7) for i in range(len(analyses))]
    return evaluate(ptype, std, th, claims, techs, analyses, from_standard=from_standard)


def codes(r):
    return {i.code for i in r["listing_issues"]} | {i.code for p in r["per_photo"] for i in p}


def test_activity_pool_claim_without_pool_photo():
    claims = [claim("c1", "snorkelling", "الغطس", "experience", True, "activity"),
              claim("c2", "swimming pool", "مسبح", "amenity", True, "pool")]
    photos = [ImageAnalysis(scene="activity", supports=["c1"]), ImageAnalysis(scene="place"),
              ImageAnalysis(scene="people"), ImageAnalysis(scene="equipment")]
    r = run("activities", claims, photos)
    assert "core_claim_missing" in codes(r)
    missing = [i for i in r["listing_issues"] if i.code == "core_claim_missing"]
    assert missing[0].claim == "c2" and "swimming pool" in missing[0].message_en
    assert r["verdict"] == "needs_changes"


def test_accommodation_needs_bedroom_and_bathroom():
    claims = [claim("c1", "bedroom", "غرفة نوم", "space", True, "bedroom"),
              claim("c2", "bathroom", "دورة مياه", "space", True, "bathroom")]
    photos = [ImageAnalysis(scene="exterior"), ImageAnalysis(scene="bedroom", supports=["c1"]),
              ImageAnalysis(scene="pool"), ImageAnalysis(scene="view"), ImageAnalysis(scene="lobby")]
    r = run("accommodation", claims, photos)
    missing = [i for i in r["listing_issues"] if i.code == "core_claim_missing"]
    assert [i.claim for i in missing] == ["c2"]
    assert {cc.claim.id: cc.status for cc in r["coverage"]} == {"c1": "shown", "c2": "missing"}
    assert r["verdict"] == "needs_changes"


def test_fnb_steak_contradicts_salad():
    claims = [claim("c1", "salads", "سلطات", "dish", True, "dish")]
    photos = [ImageAnalysis(scene="dish", supports=["c1"]),
              ImageAnalysis(scene="dish", contradicts=["c1"], caption_en="a steak", caption_ar="ستيك"),
              ImageAnalysis(scene="dining"), ImageAnalysis(scene="entrance")]
    r = run("fnb", claims, photos)
    contra = [i for i in r["per_photo"][1] if i.code == "contradicts"]
    assert contra and contra[0].severity == "block" and "steak" in contra[0].message_en


def test_shopping_coffee_cup_is_unrelated():
    claims = [claim("c1", "t-shirts", "قمصان", "product", True, "product")]
    photos = [ImageAnalysis(scene="range", supports=["c1"]), ImageAnalysis(scene="product", supports=["c1"]),
              ImageAnalysis(scene="other", unrelated=True, caption_en="a coffee cup", caption_ar="كوب قهوة")]
    r = run("shopping", claims, photos)
    assert [i.code for i in r["per_photo"][2]] == ["unrelated"]
    assert r["breakdown"].relevance < 20


def test_clean_listing_is_ready():
    claims = [claim("c1", "t-shirts", "قمصان", "product", True, "product")]
    photos = [ImageAnalysis(scene="range", supports=["c1"], quality=4),
              ImageAnalysis(scene="product", supports=["c1"], quality=4),
              ImageAnalysis(scene="storefront", quality=4)]
    r = run("shopping", claims, photos)
    assert r["verdict"] == "ready" and r["score"] >= 80, (r["score"], codes(r))


def test_below_hd_blocks_and_hd_warns():
    claims = [claim("c1", "t-shirts", "قمصان", "product", True, "product")]
    photos = [ImageAnalysis(scene="range", supports=["c1"]), ImageAnalysis(scene="product", supports=["c1"]),
              ImageAnalysis(scene="storefront")]
    techs = [tech(800, 600, n=1), tech(1280, 720, n=9), tech(n=17)]
    r = run("shopping", claims, photos, techs)
    assert r["per_photo"][0][0].code == "below_hd" and r["per_photo"][0][0].severity == "block"
    assert any(i.code == "hd_not_full_hd" and i.severity == "warn" for i in r["per_photo"][1])
    assert r["verdict"] == "needs_changes"


def test_exact_duplicate_blocks():
    claims = [claim("c1", "t-shirts", "قمصان", "product", True, "product")]
    photos = [ImageAnalysis(scene="range", supports=["c1"]), ImageAnalysis(scene="range", supports=["c1"]),
              ImageAnalysis(scene="product", supports=["c1"])]
    same = "ffd8c0a0b0e0f0f0"
    techs = [tech(phash=same), tech(phash=same), tech(n=30)]
    r = run("shopping", claims, photos, techs)
    assert any(i.code == "exact_duplicate" for i in r["per_photo"][1])


def test_messages_are_bilingual():
    claims = [claim("c1", "swimming pool", "مسبح", "amenity", True, "pool")]
    r = run("activities", claims, [ImageAnalysis(scene="activity")])
    for i in r["listing_issues"]:
        assert i.message_en and i.message_ar and i.message_en != i.message_ar


# --- criteria come from the description, not a fixed list per provider type ---

def test_requirements_follow_the_description_not_the_category():
    """A diving trip with diving photos needs no separate "place" or "people" photo:
    the category scenes are suggestions, never blocks."""
    claims = [claim("c1", "diving", "الغطس", "experience", True, "activity")]
    photos = [ImageAnalysis(scene="activity", scenes=["activity", "place"], supports=["c1"]) for _ in range(4)]
    techs = [tech(n=i * 7) for i in range(4)]
    r = run("activities", claims, photos, techs)
    assert not [i for i in r["listing_issues"] if i.severity == "block"], codes(r)
    assert {x.code: x.status for x in r["rules"]} == {"min_photos": "pass", "cover": "pass"}
    assert "الغطس" in r["rules"][1].label_ar
    assert r["verdict"] == "ready"


def test_one_photo_can_show_several_scenes():
    claims = [claim("c1", "diving", "الغطس", "experience", True, "activity")]
    photos = [ImageAnalysis(scene="activity", scenes=["activity", "place"], supports=["c1"])]
    r = run("activities", claims, photos)
    place = [s for s in r["suggested"] if s.scene == "place"][0]
    assert place.present and place.photos == [1]


def test_unanalysed_photos_are_not_counted_as_missing():
    claims = [claim("c1", "diving", "الغطس", "experience", True, "activity")]
    r = run("activities", claims, [None, None, None, None])
    assert r["coverage"][0].status == "unchecked"
    assert "core_claim_missing" not in codes(r) and "not_checked" in codes(r)
    assert r["rules"][1].status == "unchecked"
    assert r["verdict"] == "partly_checked"


def test_no_visual_criteria_falls_back_to_the_category_standard():
    from app.criteria import finalise
    std = standards.provider("activities")
    crit, from_standard = finalise([], std)
    assert from_standard and [c.scene for c in crit] == std["fallback_required"]
    photos = [ImageAnalysis(scene="activity"), ImageAnalysis(scene="people"),
              ImageAnalysis(scene="host"), ImageAnalysis(scene="equipment")]
    r = run("activities", crit, photos, from_standard=True)
    assert "no_visual_claims" in codes(r)
    assert [i.claim for i in r["listing_issues"] if i.code == "required_scene_missing"] == ["s_place"]


def test_provider_criteria_are_cleaned():
    from app.criteria import from_provider
    std = standards.provider("activities")
    out = from_provider(["قارب", {"label": "coral reef", "core": False}, {"label": ""}, "قارب",
                         {"label": "x" * 200, "scene": "nowhere", "source": "standard"}], std)
    assert [c.label for c in out][:2] == ["قارب", "coral reef"]
    assert all(c.source == "provider" for c in out) and out[1].core is False
    assert len(out) == 3 and len(out[2].label) == 80 and out[2].scene is None
