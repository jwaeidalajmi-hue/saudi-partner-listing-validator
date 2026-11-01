"""End to end through the HTTP API, in mock mode (no API key needed)."""
import json
import os

from fastapi.testclient import TestClient

from app.main import app

SAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "mock-photos")
client = TestClient(app)


def post(ptype, description, names, criteria=None, rename=None):
    files = [("photos", ((rename or {}).get(n, n), open(os.path.join(SAMPLES, n), "rb").read(), "image/jpeg"))
             for n in names]
    data = {"provider_type": ptype, "description": description}
    if criteria is not None:
        data["criteria"] = json.dumps(criteria, ensure_ascii=False)
    return client.post("/api/validate", data=data, files=files)


def test_health_and_standards():
    assert client.get("/api/health").json()["ok"]
    s = client.get("/api/standards").json()
    assert set(s["provider_types"]) == {"activities", "accommodation", "fnb", "shopping"}


def test_tshirt_store_flags_coffee_cup():
    r = post("shopping", "A store selling printed cotton t-shirts.",
             ["tshirt-rack.jpg", "tshirt-closeup.jpg", "storefront.jpg", "coffee-cup.jpg"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["engine"] == "mock"
    photo4 = body["photos"][3]
    assert any(i["code"] == "unrelated" for i in photo4["issues"])
    assert body["verdict"] == "needs_changes"


def test_salad_cafe_flags_steak():
    r = post("fnb", "Fresh salads, fresh juice and coffee.",
             ["salad-bowl.jpg", "steak-plate.jpg", "dining-area.jpg", "entrance.jpg"])
    body = r.json()
    assert any(i["code"] == "contradicts" for i in body["photos"][1]["issues"])


def test_lodge_without_bathroom_photo():
    r = post("accommodation", "Suites with a bedroom with a king bed and a private bathroom. Outdoor pool.",
             ["exterior.jpg", "bedroom-king-bed.jpg", "pool.jpg", "view.jpg", "lobby.jpg"])
    body = r.json()
    missing = [c for c in body["claims"] if not c["shown"]]
    assert any(c["claim"]["label_en"] == "bathroom" for c in missing)
    assert any(i["code"] == "below_hd" for i in body["photos"][3]["issues"])     # view.jpg is 960x640


def test_rejects_bad_input():
    assert client.post("/api/validate", data={"provider_type": "spa"},
                       files=[("photos", ("a.jpg", b"x", "image/jpeg"))]).status_code == 422
    assert client.post("/api/validate", data={"provider_type": "fnb"},
                       files=[("photos", ("a.gif", b"x", "image/gif"))]).status_code == 415


def test_criteria_are_read_from_any_description():
    r = client.post("/api/criteria", data={"provider_type": "activities", "description": "رحلة غطس"}).json()
    assert [c["label_ar"] for c in r["claims"]] == ["الغطس"] and not r["from_standard"]
    r = client.post("/api/criteria", data={"provider_type": "activities", "description": "Kayaking in Umluj"}).json()
    assert r["claims"][0]["label"] == "Kayaking in Umluj"          # not in the demo word list: kept as written
    r = client.post("/api/criteria", data={"provider_type": "fnb", "description": ""}).json()
    assert r["from_standard"] and {c["source"] for c in r["claims"]} == {"standard"}


def test_short_arabic_description_matches_a_diving_photo():
    body = post("activities", "رحلة غطس", ["snorkel-reef.jpg"]).json()
    assert [(c["claim"]["label_ar"], c["status"]) for c in body["claims"]] == [("الغطس", "shown")]
    assert {r["code"]: r["status"] for r in body["rules"]} == {"min_photos": "fail", "cover": "pass"}
    assert not any(i["code"] == "required_scene_missing" for i in body["issues"])


def test_photo_the_demo_cannot_see_is_not_checked():
    body = post("activities", "رحلة غطس", ["snorkel-reef.jpg"], rename={"snorkel-reef.jpg": "images (2).jpg"}).json()
    assert body["claims"][0]["status"] == "unchecked" and body["photos_checked"] == 0
    assert body["photos"][0]["checked"] is False
    assert any(i["code"] == "not_checked_demo" for i in body["photos"][0]["issues"])
    assert not any(i["code"] == "core_claim_missing" for i in body["issues"])


def test_provider_edited_criteria_replace_the_description():
    body = post("activities", "رحلة غطس", ["snorkel-reef.jpg", "boat-deck.jpg"],
                criteria=[{"label": "قارب", "core": True}, {"label": "عشاء", "core": False}]).json()
    status = {c["claim"]["label"]: (c["status"], c["claim"]["source"]) for c in body["claims"]}
    assert status == {"قارب": ("shown", "provider"), "عشاء": ("missing", "provider")}
    bad = client.post("/api/validate", data={"provider_type": "activities", "criteria": "{not json"},
                      files=[("photos", ("a.jpg", b"x", "image/jpeg"))])
    assert bad.status_code == 422
