"""Shared per-day stages: ingest (GDELT GKG + RSS catalog) -> allowlist -> embed. Idempotent."""
import csv
import io
import json
import logging
import re
import zipfile
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import feedparser

from . import config, db, embed, fetch

log = logging.getLogger("paper.ingest")
csv.field_size_limit(10**8)
FEEDS = json.loads((Path(__file__).parent / "data" / "feeds.json").read_text(encoding="utf-8"))
GKG_MIN_DOMAIN_COUNT = 3  # a domain qualifies from GKG when it publishes >=3 items in the day's sample


def window(day: date):
    """Edition day D covers source time in [D-1 06:00, D 06:00) PKT (D4); returned in UTC."""
    end = datetime.combine(day, time(config.EDITION_CUTOFF_HOUR), config.PKT)
    return (end - timedelta(days=1)).astimezone(UTC), end.astimezone(UTC)


def domain(url):
    return urlsplit(url).netloc.lower().removeprefix("www.")


def canonical(url):
    p = urlsplit(url.strip())
    return urlunsplit((p.scheme, p.netloc.lower(), p.path, p.query, ""))


def strip_html(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _gkg(day):
    start, end = window(day)
    out, t = [], start
    while t < end:
        stamp = t.strftime("%Y%m%d%H%M%S")
        status, _, body = fetch.get(f"https://data.gdeltproject.org/gdeltv2/{stamp}.gkg.csv.zip", ns="gkg", binary=True, timeout=60, respect_robots=False)
        if status != 200 or not body:
            log.warning("gkg %s missing (%s) — skipped (F1)", stamp, status)
            t += timedelta(hours=config.GKG_STEP_HOURS)
            continue
        z = zipfile.ZipFile(io.BytesIO(body))
        for x in csv.reader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8", "replace")), delimiter="\t"):
            if len(x) < 27:
                continue
            m = re.search(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", x[26])
            if not m or not x[4].startswith("http"):
                continue
            ts = datetime.strptime(x[1], "%Y%m%d%H%M%S").replace(tzinfo=UTC)
            out.append({"url": canonical(x[4]), "title": unescape(m[1]).strip(), "description": "", "source_time": ts,
                        "image_url": x[18] or None, "feed_body": None, "origin": "gkg"})
        t += timedelta(hours=config.GKG_STEP_HOURS)
    return out


def _rss(day):
    start, end = window(day)
    out, failed = [], 0
    for url in FEEDS:
        status, _, body = fetch.get(url, ns="feed", tag=day.isoformat())
        if status != 200 or not body:
            failed += 1
            continue
        for e in feedparser.parse(body).entries:
            if not e.get("published_parsed") or not e.get("link"):
                continue  # an item without a source time cannot be placed in an edition day
            ts = datetime(*e.published_parsed[:6], tzinfo=UTC)
            if not (start <= ts < end):
                continue
            media = (e.get("media_content") or e.get("media_thumbnail") or [{}])[0].get("url")
            body_html = (e.get("content") or [{}])[0].get("value")
            out.append({"url": canonical(e.link), "title": strip_html(e.get("title")), "description": strip_html(e.get("summary"))[:600],
                        "source_time": ts, "image_url": media, "feed_body": body_html, "origin": "rss"})
    return out, failed


def run_day(day: date) -> dict:
    gkg = _gkg(day)
    rss, feeds_failed = _rss(day)
    trusted = {domain(u) for u in FEEDS}
    counts = Counter(domain(i["url"]) for i in gkg)
    trusted |= {d for d, n in counts.items() if n >= GKG_MIN_DOMAIN_COUNT}
    keep = [i for i in rss + gkg if domain(i["url"]) in trusted and len(re.findall(r"[A-Za-z]{4,}", i["title"])) >= 4]
    with db.tx() as con:
        for i in keep:
            con.execute(
                "INSERT INTO items(url,domain,title,description,source_time,day,image_url,feed_body,origin) VALUES (?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(url) DO NOTHING",
                (i["url"], domain(i["url"]), i["title"], i["description"], i["source_time"].isoformat(), day.isoformat(),
                 i["image_url"], i["feed_body"], i["origin"]),
            )
        todo = con.execute("SELECT id, title, description FROM items WHERE day=? AND vec IS NULL", (day.isoformat(),)).fetchall()
    embedded = 0
    if todo:
        vecs = embed.embed([f"{r['title']}. {r['description'][:300]}" for r in todo])
        with db.tx() as con:
            for r, v in zip(todo, vecs):
                con.execute("UPDATE items SET vec=? WHERE id=?", (v.tobytes(), r["id"]))
        embedded = len(todo)
    return {"day": day.isoformat(), "gkg_rows": len(gkg), "rss_items": len(rss), "feeds_failed": feeds_failed,
            "kept": len(keep), "embedded": embedded, "trusted_domains": len(trusted)}
