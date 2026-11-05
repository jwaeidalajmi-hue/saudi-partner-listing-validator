"""Sign-in for the prototype pages (optional).

Set LOGIN_USERS to name:password pairs separated by commas, for example

    LOGIN_USERS=tester1:first-password,tester2:second-password

and every page and API call needs a sign-in (except /api/health and the logo files).
Leave it unset and the app stays open, as for local runs, tests and CI.
Names ignore upper/lower case. A password may contain ":" but not ",".
Changing LOGIN_USERS signs everyone out. A sign-in lasts 12 hours.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import html
import os
import time
from urllib.parse import parse_qs, quote

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

COOKIE = "sp_session"
MAX_AGE = 12 * 3600
OPEN_PATHS = {"/login", "/logout", "/api/health", "/favicon.ico"}
OPEN_PREFIX = "/web/assets/"            # logo and banner, shown on the sign-in page
FAIL_DELAY = 1.0                        # seconds added to every wrong attempt
MAX_FAILS, WINDOW = 10, 600             # 10 wrong attempts from one address -> wait 10 minutes
_fails: dict[str, list[float]] = {}

TEXT = {
    "ar": {"sub": "نموذج أولي · للمختبرين المدعوين فقط", "user": "اسم المستخدم", "pass": "كلمة المرور",
           "go": "تسجيل الدخول", "bad": "اسم المستخدم أو كلمة المرور غير صحيحة.",
           "locked": "محاولات كثيرة. حاول مرة أخرى بعد 10 دقائق.", "bye": "تم تسجيل خروجك.",
           "help": "ليس لديك حساب؟ اطلبه من الشخص الذي أرسل لك الرابط.", "other": "English", "other_lang": "en"},
    "en": {"sub": "Prototype · invited testers only", "user": "Username", "pass": "Password",
           "go": "Sign in", "bad": "Wrong username or password.",
           "locked": "Too many attempts. Try again in 10 minutes.", "bye": "You're signed out.",
           "help": "No account? Ask the person who sent you the link.", "other": "العربية", "other_lang": "ar"},
}


def parse_users(raw: str) -> dict[str, str]:
    """'a:pw1, b:pw2' -> {'a': 'pw1', 'b': 'pw2'}; entries without a name or password are skipped."""
    users: dict[str, str] = {}
    for item in (raw or "").replace("\n", ",").split(","):
        name, sep, password = item.strip().partition(":")
        name = name.strip().lower()
        if sep and name and password:
            users[name] = password
    return users


def _b64(s: str) -> str:
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")


def _unb64(s: str) -> str:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)).decode()


def make_token(key: bytes, name: str, expires: int) -> str:
    body = f"{_b64(name)}.{expires}"
    return body + "." + hmac.new(key, body.encode(), hashlib.sha256).hexdigest()


def token_user(token: str | None, key: bytes, users: dict[str, str]) -> str | None:
    """The signed-in name, or None if the cookie is missing, altered, expired or for a removed user."""
    try:
        name_b64, expires, sig = (token or "").split(".")
        body = f"{name_b64}.{expires}"
        good = hmac.new(key, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(good, sig) or int(expires) < time.time():
            return None
        name = _unb64(name_b64)
        return name if name in users else None
    except (ValueError, UnicodeDecodeError):
        return None


def _client(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return fwd or (request.client.host if request.client else "?")


def _https(request: Request) -> bool:
    return request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip() == "https"


def _safe_next(n: str | None) -> str:
    n = n or "/"
    if not n.startswith("/") or n.startswith("//") or n.startswith("/\\") or n.startswith(("/login", "/logout")):
        return "/"
    return n


def _locked(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _fails.get(ip, []) if now - t < WINDOW]
    _fails[ip] = recent
    return len(recent) >= MAX_FAILS


def page(title: dict[str, str], lang: str = "ar", nxt: str = "/", msg: str = "", error: bool = False,
         name: str = "") -> str:
    lang = lang if lang in TEXT else "ar"
    t, esc = TEXT[lang], html.escape
    rtl = lang == "ar"
    note = ""
    if msg:
        note = (f'<p class="msg {"err" if error else "ok"}" role="{"alert" if error else "status"}">'
                f"{esc(t[msg])}</p>")
    switch = f"/login?lang={t['other_lang']}&next={quote(nxt, safe='')}"
    return f"""<!doctype html>
<html lang="{lang}" dir="{'rtl' if rtl else 'ltr'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>{esc(t['go'])} · {esc(title[lang])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=Noto+Naskh+Arabic:wght@700&display=swap">
<style>
:root{{--peri:#646EC8;--peri-ink:#4E58B8;--peri-soft:#EEF0FB;--ink:#1B1B1F;--muted:#6F6F78;--line:#E3E3E3;
--bad:#C23B3B;--bad-bg:#FBE9E9;--ok:#2E8B5E;--ok-bg:#E6F4EC;
--f-body:"IBM Plex Sans Arabic","Segoe UI",Tahoma,system-ui,sans-serif;--f-title:"Noto Naskh Arabic","IBM Plex Sans Arabic",serif}}
*{{box-sizing:border-box}}
html,body{{margin:0;min-height:100%;background:#E9E9EE}}
body{{font-family:var(--f-body);font-size:15px;line-height:1.6;color:var(--ink);display:flex;flex-direction:column;min-height:100vh}}
.band{{height:20px;background:url(/web/assets/band.png) repeat-x;background-size:auto 20px}}
main{{flex:1;display:flex;align-items:center;justify-content:center;padding:32px 16px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:16px;width:100%;max-width:420px;padding:32px 28px;box-shadow:0 8px 30px rgba(27,27,31,.06)}}
.logo{{display:block;width:150px;max-width:60%;margin:0 auto 18px}}
.prov{{text-align:center;color:#6E7BD6;font-size:13px;letter-spacing:.04em;text-transform:uppercase}}
h1{{text-align:center;font-family:var(--f-title);font-size:28px;line-height:1.3;margin:2px 0 4px}}
html[lang="en"] h1{{font-family:var(--f-body);font-weight:700;font-size:26px}}
.sub{{text-align:center;color:var(--muted);margin:0 0 22px}}
label{{display:block;font-weight:600;margin:14px 0 6px}}
input{{font:inherit;font-size:16px;width:100%;padding:12px 14px;border:1px solid #C9CBD6;border-radius:10px;background:#fff;color:var(--ink)}}
input:focus{{outline:3px solid var(--peri-soft);border-color:var(--peri)}}
button{{font:inherit;font-weight:600;font-size:16px;width:100%;margin-top:22px;padding:12px 16px;border:0;border-radius:10px;background:var(--peri);color:#fff;cursor:pointer}}
button:hover{{background:var(--peri-ink)}}
button:focus-visible,a:focus-visible{{outline:3px solid var(--peri-ink);outline-offset:2px}}
.msg{{border-radius:10px;padding:10px 14px;margin:0 0 6px}}
.msg.err{{background:var(--bad-bg);color:var(--bad)}}
.msg.ok{{background:var(--ok-bg);color:var(--ok)}}
.foot{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:20px;font-size:14px;color:var(--muted)}}
.foot a{{color:var(--peri-ink)}}
</style>
</head>
<body>
<div class="band" aria-hidden="true"></div>
<main>
  <form class="card" method="post" action="/login">
    <img class="logo" src="/web/assets/logo.png" alt="Saudi Partner">
    <div class="prov">Saudi Partner · Prototype</div>
    <h1>{esc(title[lang])}</h1>
    <p class="sub">{esc(t['sub'])}</p>
    {note}
    <input type="hidden" name="next" value="{esc(nxt)}">
    <input type="hidden" name="lang" value="{lang}">
    <label for="username">{esc(t['user'])}</label>
    <input id="username" name="username" autocomplete="username" autocapitalize="none" spellcheck="false" required value="{esc(name)}" {'' if name else 'autofocus'}>
    <label for="password">{esc(t['pass'])}</label>
    <input id="password" name="password" type="password" autocomplete="current-password" required {'autofocus' if name else ''}>
    <button type="submit">{esc(t['go'])}</button>
    <div class="foot"><span>{esc(t['help'])}</span><a href="{esc(switch)}" lang="{t['other_lang']}">{esc(t['other'])}</a></div>
  </form>
</main>
</body>
</html>"""


def install(app: FastAPI, title_ar: str, title_en: str, users_raw: str | None = None) -> bool:
    """Require a sign-in on `app` when LOGIN_USERS (or users_raw) lists users. Returns whether it is on."""
    raw = os.getenv("LOGIN_USERS", "") if users_raw is None else users_raw
    users = parse_users(raw)
    if not users:
        return False
    key = hashlib.sha256(("saudi-partner-login|" + raw).encode()).digest()
    title = {"ar": title_ar, "en": title_en}

    def html_page(status: int = 200, **kw) -> HTMLResponse:
        return HTMLResponse(page(title, **kw), status_code=status,
                            headers={"Cache-Control": "no-store", "X-Frame-Options": "DENY"})

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        if (path in OPEN_PATHS or path.startswith(OPEN_PREFIX)
                or token_user(request.cookies.get(COOKIE), key, users)):
            return await call_next(request)
        if path.startswith("/api/") or request.method != "GET":
            return JSONResponse({"detail": "Sign in first."}, status_code=401)
        target = path + ("?" + request.url.query if request.url.query else "")
        return RedirectResponse("/login?next=" + quote(target, safe=""), status_code=303)

    @app.get("/login", include_in_schema=False)
    def login_form(request: Request, next: str = "/", lang: str = "ar", bye: int = 0):
        nxt = _safe_next(next)
        if token_user(request.cookies.get(COOKIE), key, users):
            return RedirectResponse(nxt, status_code=303)
        return html_page(lang=lang, nxt=nxt, msg="bye" if bye else "")

    @app.post("/login", include_in_schema=False)
    async def login_submit(request: Request):
        form = parse_qs((await request.body()).decode("utf-8", "replace"), keep_blank_values=True)
        get = lambda k: (form.get(k) or [""])[0]
        name, password = get("username").strip().lower(), get("password")
        lang, nxt, ip = get("lang") or "ar", _safe_next(get("next")), _client(request)
        if _locked(ip):
            return html_page(429, lang=lang, nxt=nxt, msg="locked", error=True, name=name)
        expected = users.get(name)
        ok = hmac.compare_digest((expected or "\0").encode(), password.encode()) and expected is not None
        if not ok:
            _fails.setdefault(ip, []).append(time.time())
            await asyncio.sleep(FAIL_DELAY)
            return html_page(401, lang=lang, nxt=nxt, msg="bad", error=True, name=name)
        _fails.pop(ip, None)
        resp = RedirectResponse(nxt, status_code=303)
        resp.set_cookie(COOKIE, make_token(key, name, int(time.time()) + MAX_AGE), max_age=MAX_AGE,
                        httponly=True, samesite="lax", secure=_https(request), path="/")
        return resp

    @app.get("/logout", include_in_schema=False)
    def logout(lang: str = "ar"):
        resp = RedirectResponse(f"/login?bye=1&lang={'en' if lang == 'en' else 'ar'}", status_code=303)
        resp.delete_cookie(COOKIE, path="/")
        return resp

    return True
