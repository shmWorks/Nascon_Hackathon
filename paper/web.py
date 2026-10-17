"""Web app: auth, onboarding, edition reading, archive, PDF download, event capture, learned-profile view."""
import json
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import BackgroundTasks, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from . import config, db, learn, personas, render, topics

app = FastAPI(title="Morning Paper")
ph = PasswordHasher()
env = render.env
SESSION_DAYS = 14
EVENT_TYPES = {"seen", "click", "dwell", "skip", "more", "less", "save"}
_login_attempts: dict[str, deque] = defaultdict(deque)
_building: set[int] = set()
_build_lock = threading.Lock()

db.init()


@app.middleware("http")
async def origin_check(request: Request, call_next):
    """CSRF defense (D6): state-changing requests must come from this origin; cookie is SameSite=Lax."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin") or request.headers.get("referer")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            return JSONResponse({"error": "cross-origin request rejected"}, status_code=403)
    return await call_next(request)


def page(name, request, **ctx):
    return HTMLResponse(env.get_template(name).render(request=request, **ctx))


def current_reader(request: Request):
    sid = request.cookies.get("sid")
    if not sid:
        return None
    with db.tx() as con:
        return con.execute(
            "SELECT r.* FROM sessions s JOIN readers r ON r.id=s.reader_id WHERE s.token=? AND s.expires>?",
            (sid, datetime.now(UTC).isoformat()),
        ).fetchone()


def start_session(reader_id):
    token = secrets.token_urlsafe(32)
    with db.tx() as con:
        con.execute("INSERT INTO sessions(token, reader_id, expires) VALUES (?,?,?)",
                    (token, reader_id, (datetime.now(UTC) + timedelta(days=SESSION_DAYS)).isoformat()))
    r = RedirectResponse("/", status_code=303)
    r.set_cookie("sid", token, httponly=True, samesite="lax", max_age=SESSION_DAYS * 86400)
    return r


def latest_day():
    with db.tx() as con:
        r = con.execute("SELECT MAX(day) d FROM items WHERE vec IS NOT NULL").fetchone()
    return date.fromisoformat(r["d"]) if r and r["d"] else datetime.now(config.PKT).date()


def _build_async(reader_id):
    from . import edition

    with _build_lock:
        if reader_id in _building:
            return
        _building.add(reader_id)
    try:
        edition.build_edition(reader_id, latest_day(), "live")
    finally:
        _building.discard(reader_id)


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    r = current_reader(request)
    if not r:
        return page("landing.html", request, personas=personas.PERSONAS, demo_password=personas.DEMO_PASSWORD)
    with db.tx() as con:
        has_topics = con.execute("SELECT 1 FROM reader_topics WHERE reader_id=?", (r["id"],)).fetchone()
        e = con.execute("SELECT id FROM editions WHERE reader_id=? ORDER BY day DESC LIMIT 1", (r["id"],)).fetchone()
    if not has_topics:
        return RedirectResponse("/onboarding", status_code=303)
    if not e:
        return page("preparing.html", request, reader=r)
    return HTMLResponse(render.edition_html(e["id"], print_mode=False))


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return page("auth.html", request, mode="login", error=None)


@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    ip = request.client.host if request.client else "?"
    q = _login_attempts[ip]
    now = time.monotonic()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 10:
        return page("auth.html", request, mode="login", error="Too many attempts. Wait a minute and try again.")
    q.append(now)
    with db.tx() as con:
        r = con.execute("SELECT * FROM readers WHERE email=?", (email.lower().strip(),)).fetchone()
    try:
        if not r:
            raise VerifyMismatchError
        ph.verify(r["pw_hash"], password)
    except VerifyMismatchError:
        return page("auth.html", request, mode="login", error="Email or password is incorrect.")
    return start_session(r["id"])


@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return page("auth.html", request, mode="signup", error=None)


@app.post("/signup")
def signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if len(password) < 8 or "@" not in email or not name.strip():
        return page("auth.html", request, mode="signup", error="Use your name, a valid email and a password of at least 8 characters.")
    with db.tx() as con:
        if con.execute("SELECT 1 FROM readers WHERE email=?", (email.lower().strip(),)).fetchone():
            return page("auth.html", request, mode="signup", error="An account with this email already exists. Sign in instead.")
        rid = personas.create_reader(con, email, name, password)
    resp = start_session(rid)
    resp.headers["location"] = "/onboarding"
    return resp


@app.get("/onboarding", response_class=HTMLResponse)
def onboarding_form(request: Request):
    r = current_reader(request)
    if not r:
        return RedirectResponse("/login", status_code=303)
    with db.tx() as con:
        cat = topics.catalog(con)
    return page("onboarding.html", request, reader=r, catalog=cat, error=None)


@app.post("/onboarding")
async def onboarding(request: Request, background: BackgroundTasks):
    r = current_reader(request)
    if not r:
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    chips = form.getlist("topic")
    free = [s.strip() for s in (form.get("free") or "").split(",") if s.strip()][:5]
    if not chips and not free:  # F5
        with db.tx() as con:
            cat = topics.catalog(con)
        return page("onboarding.html", request, reader=r, catalog=cat, error="Pick at least one topic or describe an interest, so your paper has something to follow.")
    with db.tx() as con:
        personas.onboard(con, r["id"], chips, free)
        db.add_event(con, r["id"], datetime.now(UTC).isoformat(), latest_day().isoformat(), "onboarding", payload={"topics": chips, "free": free})
    background.add_task(_build_async, r["id"])
    return RedirectResponse("/", status_code=303)


@app.get("/edition/{eid}", response_class=HTMLResponse)
def edition_view(eid: int, request: Request):
    r = current_reader(request)
    if not r:
        return RedirectResponse("/login", status_code=303)
    with db.tx() as con:
        e = con.execute("SELECT id FROM editions WHERE id=? AND reader_id=?", (eid, r["id"])).fetchone()
    if not e:
        return HTMLResponse("Not found", status_code=404)
    return HTMLResponse(render.edition_html(eid, print_mode=False))


@app.get("/editions/{eid}.pdf")
def edition_pdf(eid: int, request: Request):
    r = current_reader(request)
    if not r:
        return RedirectResponse("/login", status_code=303)
    with db.tx() as con:
        e = con.execute("SELECT day, pdf_path FROM editions WHERE id=? AND reader_id=?", (eid, r["id"])).fetchone()
    if not e or not e["pdf_path"] or not (config.EDITIONS / e["pdf_path"]).exists():
        return HTMLResponse("PDF not available for this edition.", status_code=404)
    return FileResponse(config.EDITIONS / e["pdf_path"], media_type="application/pdf", filename=f"morning-paper-{e['day']}.pdf")


@app.get("/editions/{eid}/render")
def retry_pdf(eid: int, request: Request):
    r = current_reader(request)
    if r:
        with db.tx() as con:
            ok = con.execute("SELECT 1 FROM editions WHERE id=? AND reader_id=?", (eid, r["id"])).fetchone()
        if ok:
            render.pdf_for(eid)  # F4 retry
    return RedirectResponse(f"/edition/{eid}", status_code=303)


@app.post("/events")
async def events(request: Request):
    r = current_reader(request)
    if not r:
        return JSONResponse({"error": "not signed in"}, status_code=401)
    try:
        ev = json.loads(await request.body())
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)
    if ev.get("type") not in EVENT_TYPES:
        return JSONResponse({"error": "unknown event type"}, status_code=400)
    with db.tx() as con:
        e = con.execute("SELECT day FROM editions WHERE id=? AND reader_id=?", (ev.get("edition_id"), r["id"])).fetchone()
        if not e:
            return JSONResponse({"error": "edition not found"}, status_code=404)
        db.add_event(con, r["id"], datetime.now(UTC).isoformat(), e["day"], ev["type"], ev["edition_id"], int(ev.get("story_idx", -1)), ev.get("payload"))
    return {"ok": True}


@app.get("/archive", response_class=HTMLResponse)
def archive(request: Request):
    r = current_reader(request)
    if not r:
        return RedirectResponse("/login", status_code=303)
    with db.tx() as con:
        eds = con.execute("SELECT id, day, kind, pdf_path, body FROM editions WHERE reader_id=? ORDER BY day DESC", (r["id"],)).fetchall()
    rows = [{"id": e["id"], "day": e["day"], "kind": e["kind"], "pdf": bool(e["pdf_path"]), "lead": json.loads(e["body"])["lead"]["headline"]} for e in eds]
    return page("archive.html", request, reader=r, editions=rows)


@app.get("/profile", response_class=HTMLResponse)
def profile_view(request: Request):
    r = current_reader(request)
    if not r:
        return RedirectResponse("/login", status_code=303)
    with db.tx() as con:
        prof = learn.profile(con, r["id"], latest_day())
        labels = {t["id"]: t["label"] for t in con.execute("SELECT id, label FROM topics")}
        n_events = con.execute("SELECT COUNT(*) n, SUM(simulated) s FROM events WHERE reader_id=?", (r["id"],)).fetchone()
    rows = []
    for t in set(prof.prior) | set(prof.alpha):
        a, b = prof.ab(t)
        ev = prof.evidence.get(t, [])
        a0, b0 = prof.prior.get(t, prof._other())
        rows.append({"label": labels.get(t, "?"), "now": a / (a + b), "start": a0 / (a0 + b0), "seen": len(ev), "engaged": sum(ev), "chosen": t in prof.prior})
    rows.sort(key=lambda x: -x["now"])
    return page("profile.html", request, reader=r, rows=rows, n_events=n_events["n"], n_sim=n_events["s"] or 0)


@app.get("/logout")
def logout(request: Request):
    sid = request.cookies.get("sid")
    if sid:
        with db.tx() as con:
            con.execute("DELETE FROM sessions WHERE token=?", (sid,))
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("sid")
    return resp
