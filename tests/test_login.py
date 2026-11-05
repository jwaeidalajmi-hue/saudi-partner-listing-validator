"""The optional sign-in (app/auth.py), on a small app so it doesn't depend on the rest."""
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth

USERS = "tester:secret-1, Sara:كلمة:سر ,broken, :nopass, noname:"


@pytest.fixture
def client():
    auth.FAIL_DELAY = 0
    auth._fails.clear()
    app = FastAPI()
    assert auth.install(app, "عنوان", "Title", USERS)

    @app.get("/")
    def home():
        return {"home": True}

    @app.get("/api/data")
    def data():
        return {"x": 1}

    @app.post("/api/data")
    def post_data():
        return {"x": 2}

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return TestClient(app)


def sign_in(c, name="tester", password="secret-1", nxt="/"):
    return c.post("/login", data={"username": name, "password": password, "next": nxt, "lang": "ar"},
                  follow_redirects=False)


def test_off_without_users():
    assert auth.install(FastAPI(), "a", "b", "") is False
    assert auth.install(FastAPI(), "a", "b", " , :x, y:") is False


def test_parse_users():
    assert auth.parse_users(USERS) == {"tester": "secret-1", "sara": "كلمة:سر"}


def test_pages_redirect_and_api_refuses(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login?next=%2F"
    assert client.get("/api/data").status_code == 401
    assert client.post("/api/data").status_code == 401
    assert client.get("/docs", follow_redirects=False).status_code == 303
    assert client.get("/api/health").status_code == 200


def test_login_page_both_languages(client):
    ar = client.get("/login").text
    assert 'name="password"' in ar and 'dir="rtl"' in ar and "تسجيل الدخول" in ar
    en = client.get("/login?lang=en").text
    assert 'dir="ltr"' in en and "Sign in" in en and "Title" in en


def test_wrong_then_right(client):
    r = sign_in(client, password="nope")
    assert r.status_code == 401 and "غير صحيحة" in r.text and "set-cookie" not in r.headers
    assert client.get("/api/data").status_code == 401
    r = sign_in(client, nxt="/api/data")
    assert r.status_code == 303 and r.headers["location"] == "/api/data"
    assert "httponly" in r.headers["set-cookie"].lower()
    assert client.get("/api/data").json() == {"x": 1}
    assert client.get("/").json() == {"home": True}


def test_name_ignores_case_and_password_may_have_colon(client):
    assert sign_in(client, "TESTER").status_code == 303
    client.cookies.clear()
    assert sign_in(client, "sara", "كلمة:سر").status_code == 303
    assert client.get("/api/data").status_code == 200
    client.cookies.clear()
    assert sign_in(client, "tester", "SECRET-1").status_code == 401     # passwords are exact


def test_no_open_redirect(client):
    for bad in ("//evil.example", "https://evil.example", "/\\evil.example", "/logout"):
        client.cookies.clear()
        assert sign_in(client, nxt=bad).headers["location"] == "/"


def test_logout(client):
    sign_in(client)
    r = client.get("/logout", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/login?bye=1")
    assert client.get("/api/data").status_code == 401
    assert "تم تسجيل خروجك" in client.get("/login?bye=1").text


def test_altered_or_expired_cookie(client):
    key = __import__("hashlib").sha256(("saudi-partner-login|" + USERS).encode()).digest()
    good = auth.make_token(key, "tester", int(time.time()) + 60)
    client.cookies.set(auth.COOKIE, good)
    assert client.get("/api/data").status_code == 200
    client.cookies.set(auth.COOKIE, good[:-1] + ("0" if good[-1] != "0" else "1"))
    assert client.get("/api/data").status_code == 401
    client.cookies.set(auth.COOKIE, auth.make_token(key, "tester", int(time.time()) - 1))
    assert client.get("/api/data").status_code == 401
    client.cookies.set(auth.COOKIE, auth.make_token(key, "someone-else", int(time.time()) + 60))
    assert client.get("/api/data").status_code == 401
    client.cookies.set(auth.COOKIE, "junk")
    assert client.get("/api/data").status_code == 401


def test_too_many_attempts(client):
    for _ in range(auth.MAX_FAILS):
        assert sign_in(client, password="nope").status_code == 401
    r = sign_in(client)                                   # right password, but locked for now
    assert r.status_code == 429 and "10" in r.text


def test_main_app_reports_login_off():
    from app.main import app
    assert TestClient(app).get("/api/health").json()["login"] is False
