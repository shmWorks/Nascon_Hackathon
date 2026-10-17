"""Spike: cleanest/cheapest way to call Jina Reader; does Dawn's feed carry full text for every item?"""
import json
import re
import time
from urllib.parse import urlsplit

import feedparser
import httpx
import trafilatura

items = json.load(open("spikes/out/bakeoff_items.json"))
toks = lambda s: set(re.findall(r"[a-z0-9]{4,}", s.lower()))
rec = lambda txt, it: round(len(toks(it["desc"]) & toks(txt or "")) / max(len(toks(it["desc"])), 1), 2)
c = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "MorningPaperBot/0.1"})

# Dawn: does the feed's content:encoded carry each article in full?
f = feedparser.parse(c.get("https://www.dawn.com/feeds/home").content)
byurl = {e.link.split("?")[0]: e for e in f.entries}
for it in [i for i in items if "dawn.com" in i["url"]]:
    e = byurl.get(it["url"].split("?")[0])
    body = trafilatura.extract(e.content[0].value) if e is not None and e.get("content") else None
    print(f"dawn-feed in_feed={e is not None} chars={len(body or '')} recall={rec(body, it)}")

modes = {
    "md-default": {"Accept": "application/json"},
    "html+trafi": {"Accept": "application/json", "X-Return-Format": "html"},
    "md-article": {"Accept": "application/json", "X-Target-Selector": "article"},
}
targets = [i for i in items if urlsplit(i["url"]).netloc in ("www.cricinfo.com", "arstechnica.com")]
for name, h in modes.items():
    for it in targets:
        t0 = time.perf_counter()
        r = c.get(f"https://r.jina.ai/{it['url']}", headers=h)
        d = r.json().get("data", {}) if r.headers.get("content-type", "").startswith("application/json") else {}
        content = d.get("content") or d.get("html") or ""
        txt = trafilatura.extract(content) if name == "html+trafi" else re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", content)
        usage = d.get("usage", {})
        print(f"{name:11} {r.status_code} raw={len(content):6} text={len(txt or ''):6} recall={rec(txt, it)} tokens={usage.get('tokens')} keys={sorted(d)[:8]} {time.perf_counter() - t0:.1f}s")
        time.sleep(3.1)  # stay under 20 RPM without key
