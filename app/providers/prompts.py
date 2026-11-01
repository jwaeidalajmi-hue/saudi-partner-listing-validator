"""Prompts for the language and vision model. Both ask for JSON only."""
import json


def claims_prompt(description: str, provider_type: str, std: dict) -> str:
    scenes = {k: v["en"] for k, v in std["scenes"].items()}
    return f"""You read a tourism listing a provider is writing on Saudi Partner and turn its description into the criteria its photos will be checked against: the things the description says that a photo could show.

Provider type: {std['name']['en']} ({provider_type})
Allowed kinds: {', '.join(std['claim_kinds'])}
Scene keys for this provider type: {json.dumps(scenes, ensure_ascii=False)}

Rules:
- Work from whatever the provider wrote, however short ("diving trip", "رحلة غطس") or long, in Arabic or English. Never add things the description does not say.
- Only things a photo can show: the activity itself, places, landmarks, spaces, rooms, beds, amenities, dishes, drinks, products, equipment, vehicles. Not prices, times, policies, licences or feelings.
- core = true for what the listing is about (the activity itself, the rooms offered, the signature dishes, the product range). Extras such as a balcony, a sea view or an included lunch are core = false.
- Name each thing as the provider would: "diving" for غطس / غوص, not a narrower activity they did not name.
- label in the description's own language; label_en and label_ar always filled.
- evidence_en and evidence_ar: what a photo that shows it would contain, in a few words ("a person diving underwater", "شخص يغوص تحت الماء").
- scene = the scene key a matching photo would have, or null if none fits.
- At most 10 criteria. Merge duplicates. If nothing in the description can be photographed, return an empty list.

Description:
\"\"\"{description}\"\"\"

Reply with only JSON:
{{"claims":[{{"id":"c1","label":"...","label_en":"...","label_ar":"...","kind":"...","core":true,"scene":"activity","evidence_en":"...","evidence_ar":"..."}}]}}"""


def image_prompt(provider_type: str, std: dict, claims: list[dict], filename: str) -> str:
    scenes = {k: v["en"] for k, v in std["scenes"].items()}
    criteria = [{"id": c["id"], "label": c["label"], "label_en": c["label_en"], "must_show": c["core"],
                 "a matching photo shows": c.get("evidence_en") or c["label_en"]} for c in claims]
    return f"""You check one photo a provider uploaded to a {std['name']['en']} listing on Saudi Partner, against the criteria taken from that listing's description (some written or edited by the provider).

Scene keys: {json.dumps(scenes, ensure_ascii=False)} (use "other" if none fits)
Criteria: {json.dumps(criteria, ensure_ascii=False)}
File name (a hint only, often meaningless): {filename}

Decide:
- scenes: every scene key the photo clearly shows (a diver over a coral reef is both "activity" and "place"); scene: the main one; scene_confidence 0 to 1.
- objects: up to 8 short nouns for what is clearly visible.
- supports: ids of criteria this photo clearly shows. Judge by meaning, in any language: a person underwater with a mask supports "diving" and "رحلة غطس"; a bed supports "bedroom"; a salad supports "salads"; t-shirts support "t-shirts".
- contradicts: ids of criteria this photo goes against (a steak where the criterion is "vegan salads").
- unrelated: true if the photo shows nothing this listing is about (a coffee cup in a t-shirt store, a random street in a spa).
- overlays: any of "watermark", "logo", "text", "border" printed over the photo.
- collage, screenshot, stock_or_ai (looks like stock or AI-generated), people (identifiable faces), children, licence_plate (readable): true or false.
- quality: 1 to 5 as a photo for a booking page (sharpness, light, framing, appeal).
- caption_en and caption_ar: what the photo shows, in a few words.

Reply with only JSON:
{{"scenes":["activity","place"],"scene":"activity","scene_confidence":0.9,"objects":["diver","coral reef"],"supports":["c1"],"contradicts":[],"unrelated":false,"overlays":[],"collage":false,"screenshot":false,"stock_or_ai":false,"people":false,"children":false,"licence_plate":false,"quality":4,"caption_en":"a diver over a coral reef","caption_ar":"غوّاص فوق شعاب مرجانية"}}"""
