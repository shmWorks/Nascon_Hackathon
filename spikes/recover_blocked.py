"""Spike: recover article text for pages blocked to direct fetch, via legitimate alternate routes."""
import json
import re
import time
from urllib.parse import quote, urlsplit

import feedparser
import httpx
import trafilatura

UA = {"User-Agent": "MorningPaperBot/0.1 (+https://github.com/shmWorks/Nascon_Hackathon)"}
c = httpx.Client(headers=UA, timeout=20, follow_redirects=True)
items = json.load(open("spikes/out/bakeoff_items.json"))
blocked = [it for it in items if urlsplit(it["url"]).netloc in ("www.dawn.com", "www.cricinfo.com", "arstechnica.com")]
toks = lambda s: set(re.findall(r"[a-z0-9]{4,}", s.lower()))

# Route 1: full text inside the feed itself (content:encoded / long description)
for name, feed in [("dawn", "https://www.dawn.com/feeds/home"), ("cricinfo", "https://www.espncricinfo.com/rss/content/story/feeds/0.xml"), ("ars", "https://feeds.arstechnica.com/arstechnica/index")]:
    f = feedparser.parse(c.get(feed).content)
    e = f.entries[0]
    body = (e.get("content") or [{}])[0].get("value", "") or e.get("summary", "")
    print(f"feed-fulltext {name:9} content_field={bool(e.get('content'))} chars={len(re.sub('<[^>]+>', '', body))}")


def judge(txt, it):
    d = toks(it["desc"])
    return len(txt or ""), round(len(d & toks(txt or "")) / max(len(d), 1), 2)


def try_route(label, url_fn):
    ok = 0
    for it in blocked:
        t0 = time.perf_counter()
        try:
            r = c.get(url_fn(it["url"]))
            txt = (r.text if label == "jina" else trafilatura.extract(r.text)) if r.status_code == 200 else None
            n, rec = judge(txt, it)
            ok += n >= 500
            print(f"  {label:8} {r.status_code} chars={n:5} recall={rec} {time.perf_counter() - t0:.1f}s {it['url'][8:60]}")
        except httpx.HTTPError as e:
            print(f"  {label:8} ERR {type(e).__name__} {it['url'][8:60]}")
    print(f"{label}: {ok}/{len(blocked)} recovered")


try_route("wayback", lambda u: f"https://web.archive.org/web/2026id_/{u}")
try_route("amp", lambda u: u.split("?")[0].rstrip("/") + ("/amp" if "dawn.com" in u else "?amp=1"))
try_route("jina", lambda u: f"https://r.jina.ai/{u}")
