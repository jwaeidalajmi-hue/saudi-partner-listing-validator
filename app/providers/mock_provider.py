"""A model-free stand-in so anyone can try the prototype without an API key.

It is NOT computer vision and cannot see photos. Criteria come from a small
keyword list (or, failing that, the first phrase of the description), and a
photo's content is guessed from its FILE NAME (e.g. `pool.jpg`, `bathroom-2.png`,
`steak.jpg`). A photo whose name gives no hint is reported as "not checked"
rather than guessed. Reports made with it say engine = "mock". Use real model
mode to judge actual photos."""
from __future__ import annotations

import re

from ..criteria import is_arabic
from ..models import Claim, ImageAnalysis
from .base import VisionProvider

# keyword -> (label_en, label_ar, kind, core, scene)
LEXICON = {
    "activities": {
        "snorkel": ("snorkelling", "الغطس السطحي", "experience", True, "activity"),
        "diving": ("diving", "الغوص", "experience", True, "activity"),
        "dive": ("diving", "الغوص", "experience", True, "activity"),
        "reef": ("coral reef", "الشعاب المرجانية", "place", False, "place"),
        "الشعاب": ("coral reef", "الشعاب المرجانية", "place", False, "place"),
        "dune": ("dune bashing", "التطعيس", "experience", True, "activity"),
        "hike": ("hiking", "المشي الجبلي", "experience", True, "activity"),
        "tour": ("guided tour", "جولة مع مرشد", "experience", True, "activity"),
        "boat": ("boat", "قارب", "equipment", True, "equipment"),
        "camel": ("camel ride", "ركوب الجمال", "experience", True, "activity"),
        "pool": ("swimming pool", "مسبح", "amenity", False, "pool"),
        "lunch": ("lunch", "غداء", "inclusion", False, "food"),
        "dinner": ("dinner", "عشاء", "inclusion", False, "food"),
        "مسبح": ("swimming pool", "مسبح", "amenity", False, "pool"),
        "غطس سطحي": ("snorkelling", "الغطس السطحي", "experience", True, "activity"),
        "غطس": ("diving", "الغطس", "experience", True, "activity"),
        "غداء": ("lunch", "غداء", "inclusion", False, "food"),
        "غوص": ("diving", "الغوص", "experience", True, "activity"),
        "مرشد": ("guide", "المرشد", "experience", False, "host"),
        "guide": ("guide", "المرشد", "experience", False, "host"),
        "جولة": ("guided tour", "جولة مع مرشد", "experience", True, "activity"),
        "قارب": ("boat", "قارب", "equipment", True, "equipment"),
    },
    "accommodation": {
        "bedroom": ("bedroom", "غرفة نوم", "space", True, "bedroom"),
        "king bed": ("king bed", "سرير كبير", "bed", True, "bedroom"),
        "bathroom": ("bathroom", "دورة مياه", "space", True, "bathroom"),
        "bathtub": ("bathtub", "حوض استحمام", "feature", False, "bathroom"),
        "kitchen": ("kitchen", "مطبخ", "space", True, "kitchen"),
        "pool": ("swimming pool", "مسبح", "amenity", False, "pool"),
        "gym": ("gym", "نادٍ رياضي", "amenity", False, "gym"),
        "view": ("view", "إطلالة", "view", False, "view"),
        "غرفة نوم": ("bedroom", "غرفة نوم", "space", True, "bedroom"),
        "دورة مياه": ("bathroom", "دورة مياه", "space", True, "bathroom"),
        "حوض استحمام": ("bathtub", "حوض استحمام", "feature", False, "bathroom"),
        "النادي الرياضي": ("gym", "نادٍ رياضي", "amenity", False, "gym"),
        "إطلالة": ("view", "إطلالة", "view", False, "view"),
        "مسبح": ("swimming pool", "مسبح", "amenity", False, "pool"),
    },
    "fnb": {
        "salad": ("salads", "سلطات", "dish", True, "dish"),
        "steak": ("steak", "ستيك", "dish", True, "dish"),
        "kabsa": ("kabsa", "كبسة", "dish", True, "dish"),
        "coffee": ("coffee", "قهوة", "drink", True, "drink"),
        "juice": ("fresh juice", "عصير طازج", "drink", False, "drink"),
        "terrace": ("outdoor terrace", "جلسات خارجية", "feature", False, "dining"),
        "سلطة": ("salads", "سلطات", "dish", True, "dish"),
        "سلطات": ("salads", "سلطات", "dish", True, "dish"),
        "عصير": ("fresh juice", "عصير طازج", "drink", False, "drink"),
        "جلسات خارجية": ("outdoor terrace", "جلسات خارجية", "feature", False, "dining"),
        "كبسة": ("kabsa", "كبسة", "dish", True, "dish"),
        "قهوة": ("coffee", "قهوة", "drink", True, "drink"),
    },
    "shopping": {
        "t-shirt": ("t-shirts", "قمصان تي شيرت", "product", True, "product"),
        "tshirt": ("t-shirts", "قمصان تي شيرت", "product", True, "product"),
        "rug": ("rugs", "سجاد", "product", True, "product"),
        "perfume": ("perfume", "عطور", "product", True, "product"),
        "dates": ("dates", "تمور", "product", True, "product"),
        "cotton": ("cotton", "قطن", "attribute", False, None),
        "تيشيرت": ("t-shirts", "قمصان تي شيرت", "product", True, "product"),
        "تي شيرت": ("t-shirts", "قمصان تي شيرت", "product", True, "product"),
        "قطنية": ("cotton", "قطن", "attribute", False, None),
        "سجاد": ("rugs", "سجاد", "product", True, "product"),
        "عطور": ("perfume", "عطور", "product", True, "product"),
    },
}

# file-name word -> scene, plus the object it implies
FILE_HINTS = {
    "pool": ("pool", "pool"), "snorkel": ("activity", "snorkel"), "diving": ("activity", "diver"),
    "boat": ("equipment", "boat"), "dune": ("activity", "dune"), "camel": ("activity", "camel"),
    "guests": ("people", "people"), "guide": ("host", "guide"), "beach": ("place", "beach"),
    "landmark": ("place", "landmark"), "reef": ("place", "reef"), "dive": ("activity", "diver"), "view": ("view", "view"), "exterior": ("exterior", "building"),
    "bedroom": ("bedroom", "bed"), "bed": ("bedroom", "bed"), "bathroom": ("bathroom", "bathroom"),
    "kitchen": ("kitchen", "kitchen"), "gym": ("gym", "gym"), "lobby": ("lobby", "lobby"),
    "salad": ("dish", "salad"), "steak": ("dish", "steak"), "kabsa": ("dish", "kabsa"),
    "coffee": ("drink", "coffee cup"), "juice": ("drink", "juice"), "dining": ("dining", "tables"),
    "entrance": ("entrance", "entrance"), "chef": ("kitchen", "chef"),
    "tshirt-rack": ("range", "t-shirts"), "tshirt": ("product", "t-shirt"), "t-shirt": ("product", "t-shirt"), "rack": ("range", "t-shirts"),
    "display": ("range", "display"), "storefront": ("storefront", "store front"), "store": ("interior", "store"),
    "rug": ("product", "rug"), "perfume": ("product", "perfume"),
}
OVERLAY_HINTS = {"watermark": "watermark", "logo": "logo", "text": "text"}


PHRASE_SPLIT = re.compile(r"[.،,؛;!؟?\n]+|\s+(?:and|with|و|مع)\s+")


def _terms(c: Claim, provider_type: str) -> set[str]:
    """English words a file name could carry for this criterion, whatever language it is in."""
    terms = {c.label_en.lower(), c.label.lower()}
    for kw, (en, ar, *_rest) in LEXICON.get(provider_type, {}).items():
        if kw in c.label.lower() or ar == c.label or en == c.label_en.lower():
            terms |= {en, kw}
    return {t for t in terms if t}


class MockProvider(VisionProvider):
    name = "mock"

    async def extract_claims(self, description: str, provider_type: str, std: dict) -> list[Claim]:
        text = description.lower()
        ar_text = is_arabic(description)
        out, seen = [], set()
        for kw in sorted(LEXICON.get(provider_type, {}), key=len, reverse=True):
            en, ar, kind, core, scene = LEXICON[provider_type][kw]
            if kw in text and en not in seen and not any(kw in k and k in text and k != kw for k in seen):
                seen.add(en)
                seen.add(kw)
                out.append(Claim(id=f"c{len(out) + 1}", label=ar if ar_text else en, label_en=en,
                                 label_ar=ar, kind=kind, core=core,
                                 scene=scene if scene in std["scenes"] else None))
        if not out and description.strip():
            # nothing in the keyword list: the first phrase becomes the one criterion
            phrase = next((p.strip() for p in PHRASE_SPLIT.split(description) if p.strip()), "")
            words = phrase.split()[:6]
            if words:
                label = " ".join(words)
                out.append(Claim(id="c1", label=label, label_en=label, label_ar=label, kind="other", core=True))
        return out

    async def analyze_image(self, data: bytes, mime: str, filename: str, provider_type: str,
                            std: dict, claims: list[Claim]) -> ImageAnalysis | None:
        name = filename.lower()
        words = set(re.split(r"[^a-z]+", name))
        scenes, objects = [], []
        for key in sorted(FILE_HINTS, key=len, reverse=True):
            if key in name:
                s, obj = FILE_HINTS[key]
                if obj not in objects:
                    objects.append(obj)
                if s in std["scenes"] and s not in scenes:
                    scenes.append(s)
        overlays = [v for k, v in OVERLAY_HINTS.items() if k in words]
        if not objects and not overlays and not {"collage", "screenshot"} & words:
            return None            # the name says nothing: report "not checked", never guess
        scene = scenes[0] if scenes else "other"
        supports = [c.id for c in claims
                    if any(o in t or t.rstrip("s") in o or t in name for o in objects for t in _terms(c, provider_type))
                    or (c.scene and c.scene in scenes and c.kind not in ("dish", "product", "drink"))]
        dish_like = [c for c in claims if c.kind in ("dish", "product", "drink")]
        contradicts = []
        if scene in ("dish", "product", "drink") and objects and not supports and dish_like:
            contradicts = [dish_like[0].id]
        unrelated = scene == "other" or (bool(contradicts) and provider_type == "shopping")
        return ImageAnalysis(
            scene=scene, scenes=scenes, scene_confidence=0.9 if scenes else 0.2, objects=objects,
            supports=supports, contradicts=contradicts, unrelated=unrelated and not supports,
            overlays=overlays, collage="collage" in words, screenshot="screenshot" in words,
            stock_or_ai="stock" in words, people="guests" in words, quality=4 if scenes else 2,
            caption_en=", ".join(objects) or "something not recognised",
            caption_ar="، ".join(objects) or "محتوى غير معروف",
        )
