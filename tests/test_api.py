"""End to end through the HTTP API, in mock mode (no API key needed)."""
import os

from fastapi.testclient import TestClient

from app.main import app

SAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "mock-photos")
client = TestClient(app)


def post(ptype, description, names):
    files = [("photos", (n, open(os.path.join(SAMPLES, n), "rb").read(), "image/jpeg")) for n in names]
    return client.post("/api/validate", data={"provider_type": ptype, "description": description}, files=files)


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
