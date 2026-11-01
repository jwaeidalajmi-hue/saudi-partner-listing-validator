"""Prompts for the language and vision model. Both ask for JSON only."""
import json


def claims_prompt(description: str, provider_type: str, std: dict) -> str:
    scenes = {k: v["en"] for k, v in std["scenes"].items()}
    return f"""You read a tourism listing on Saudi Partner and list the things its description says that a photo could show.

Provider type: {std['name']['en']} ({provider_type})
Allowed claim kinds: {', '.join(std['claim_kinds'])}
Scene keys for this provider type: {json.dumps(scenes, ensure_ascii=False)}

Rules:
- Only things a photo can show: spaces, rooms, beds, amenities, dishes, drinks, products, equipment, vehicles, places, landmarks, the activity itself. Not prices, times, policies or feelings.
- core = true for what the listing is about (the activity itself, the rooms offered, the signature dishes, the product categories). Extras such as a balcony or a sea view are core = false.
- scene = the scene key a matching photo would have, or null if none fits.
- label in the description's own language; label_en and label_ar always filled.
- At most 12 claims. Merge duplicates.

Description:
\"\"\"{description}\"\"\"

Reply with only JSON:
{{"claims":[{{"id":"c1","label":"...","label_en":"...","label_ar":"...","kind":"...","core":true,"scene":"pool"}}]}}"""


def image_prompt(provider_type: str, std: dict, claims: list[dict], filename: str) -> str:
    scenes = {k: v["en"] for k, v in std["scenes"].items()}
    claim_list = [{"id": c["id"], "label": c["label_en"], "core": c["core"]} for c in claims]
    return f"""You check one photo a provider uploaded to a {std['name']['en']} listing on Saudi Partner, against what the listing's description claims.

Scene keys: {json.dumps(scenes, ensure_ascii=False)} (use "other" if none fits)
Claims from the description: {json.dumps(claim_list, ensure_ascii=False)}
File name (a hint only, may be meaningless): {filename}

Decide:
- scene: the best scene key; scene_confidence 0 to 1.
- objects: up to 8 short nouns for what is clearly visible.
- supports: ids of claims this photo clearly shows (a pool for "swimming pool", a bed for "bedroom", a salad for "salads", t-shirts for "t-shirts").
- contradicts: ids of claims this photo goes against (a steak where the claim is "vegan salads").
- unrelated: true if the photo shows nothing this listing is about (a coffee cup in a t-shirt store, a random street in a spa).
- overlays: any of "watermark", "logo", "text", "border" printed over the photo.
- collage, screenshot, stock_or_ai (looks like stock or AI-generated), people (identifiable faces), children, licence_plate (readable): true or false.
- quality: 1 to 5 as a photo for a booking page (sharpness, light, framing, appeal).
- caption_en and caption_ar: what the photo shows, in a few words.

Reply with only JSON:
{{"scene":"pool","scene_confidence":0.9,"objects":["pool","sun loungers"],"supports":["c1"],"contradicts":[],"unrelated":false,"overlays":[],"collage":false,"screenshot":false,"stock_or_ai":false,"people":false,"children":false,"licence_plate":false,"quality":4,"caption_en":"outdoor swimming pool","caption_ar":"مسبح خارجي"}}"""
