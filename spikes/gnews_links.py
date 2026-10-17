"""Spike: do Google News RSS links resolve to publisher URLs (needed for og:image, text, click-through)?"""
import re
from urllib.parse import quote

import feedparser
import httpx

c = httpx.Client(headers={"User-Agent": "Mozilla/5.0"}, timeout=15, follow_redirects=True)
f = feedparser.parse(c.get("https://news.google.com/rss/search?q=" + quote("space science after:2026-10-14 before:2026-10-15") + "&hl=en-US&gl=US&ceid=US:en").content)
print("entries", len(f.entries))
e = f.entries[0]
print("keys", sorted(e.keys()))
print("link", e.link[:90])
print("source", e.get("source"))
print("summary html", e.get("summary", "")[:200])
r = c.get(e.link)
print("GET ->", r.status_code, str(r.url)[:90], "len", len(r.text))
print("og:image in landing", bool(re.search(r'og:image', r.text)))
m = re.search(r'data-n-a-sg="([^"]+)"', r.text)
print("has decode signature attr", bool(m))
