"""One Jinja template renders both the web edition and the PDF (A5 by construction)."""
import base64
import io
import json
import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import config, db

log = logging.getLogger("paper.render")
env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=select_autoescape())
env.filters["longdate"] = lambda d: date.fromisoformat(d).strftime("%A, %d %B %Y")


PRINT_IMAGE_PX = 900  # A4 column width at print resolution; larger source images only bloat the PDF


def _print_image(url):
    """Downscaled JPEG data URI for print, or None (image omitted) if it cannot be fetched or decoded."""
    from PIL import Image

    from . import fetch

    status, ctype, data = fetch.get(url, ns="img", binary=True, respect_robots=False)
    if status != 200 or not data or not ctype.startswith("image/"):
        return None
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((PRINT_IMAGE_PX, PRINT_IMAGE_PX))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=72, optimize=True)
    except Exception:  # noqa: BLE001 — any undecodable image is simply left out of print
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def edition_html(eid: int, print_mode: bool, printing: bool = False) -> str:
    with db.tx() as con:
        e = con.execute("SELECT * FROM editions WHERE id=?", (eid,)).fetchone()
    body = json.loads(e["body"])
    if print_mode:
        for s in body["stories"]:
            s["image_url"] = _print_image(s["image_url"]) if s.get("image_url") else None
        body["lead"] = body["stories"][body["lead"]["idx"]]
        for sec in body["sections"]:
            sec["stories"] = [body["stories"][s["idx"]] for s in sec["stories"]]
    return env.get_template("edition.html").render(e=body, eid=eid, print_mode=print_mode, pdf=bool(e["pdf_path"]), printing=printing)


def pdf_for(eid: int) -> str | None:
    """Render and store the PDF once at commit. On failure the web edition stays available (F4)."""
    path = config.EDITIONS / f"edition-{eid}.pdf"
    try:
        from playwright.sync_api import sync_playwright

        html = edition_html(eid, print_mode=True)
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page()
            page.set_content(html, wait_until="networkidle", timeout=45000)
            page.pdf(path=str(path), format="A4", print_background=True, margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"})
            b.close()
    except Exception as e:  # noqa: BLE001 — PDF failure must never take the edition down (F4)
        log.error("PDF render failed for edition %s: %s", eid, str(e)[:300])
        return None
    with db.tx() as con:
        con.execute("UPDATE editions SET pdf_path=? WHERE id=?", (path.name, eid))
    return path.name
