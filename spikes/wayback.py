"""Spike: can the Wayback Machine return a high-volume feed as it looked on each past morning?"""
from datetime import date, timedelta

import feedparser
import httpx

c = httpx.Client(headers={"User-Agent": "Mozilla/5.0 (morning-paper spike)"}, timeout=30, follow_redirects=True)
for feed in ["https://feeds.bbci.co.uk/news/world/rss.xml", "https://techcrunch.com/feed/", "https://www.dawn.com/feeds/home"]:
    for back in (6, 3):
        d = date.today() - timedelta(days=back)
        ts = d.strftime("%Y%m%d") + "060000"
        try:
            r = c.get(f"https://web.archive.org/web/{ts}id_/{feed}")
            f = feedparser.parse(r.content)
            snap = str(r.url).split("/web/")[1][:14] if "/web/" in str(r.url) else "?"
            dates = sorted(e.get("published", "")[5:16] for e in f.entries)[-1:] if f.entries else []
            print(f"{feed[8:40]:32} want {d} snap {snap} status {r.status_code} items {len(f.entries)} newest {dates}")
        except httpx.HTTPError as e:
            print(feed, back, "FAIL", type(e).__name__)
