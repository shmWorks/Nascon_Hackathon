"""Spike: how many days back does each candidate publisher feed reach, and does it carry images?"""
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import feedparser
import httpx

FEEDS = {
    "bbc-world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "bbc-tech": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "bbc-science": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "bbc-business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "bbc-cricket": "https://feeds.bbci.co.uk/sport/cricket/rss.xml",
    "guardian-tech": "https://www.theguardian.com/technology/rss",
    "guardian-environment": "https://www.theguardian.com/environment/rss",
    "guardian-business": "https://www.theguardian.com/business/rss",
    "guardian-science": "https://www.theguardian.com/science/rss",
    "guardian-cricket": "https://www.theguardian.com/sport/cricket/rss",
    "aljazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "dawn": "https://www.dawn.com/feeds/home",
    "techcrunch": "https://techcrunch.com/feed/",
    "techcrunch-ai": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "arstechnica": "https://feeds.arstechnica.com/arstechnica/index",
    "nasa": "https://www.nasa.gov/news-release/feed/",
    "space-com": "https://www.space.com/feeds/all",
    "sciencedaily-space": "https://www.sciencedaily.com/rss/space_time.xml",
    "espncricinfo": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "carbonbrief": "https://www.carbonbrief.org/feed/",
    "hn-frontpage": "https://hnrss.org/frontpage?count=100",
}
now = datetime.now(timezone.utc)
c = httpx.Client(headers={"User-Agent": "Mozilla/5.0 (morning-paper spike)"}, timeout=15, follow_redirects=True)


def probe(item):
    name, url = item
    try:
        f = feedparser.parse(c.get(url).content)
    except Exception as e:
        return f"{name:22} FAIL {type(e).__name__}"
    ts = [datetime(*e.published_parsed[:6], tzinfo=timezone.utc) for e in f.entries if e.get("published_parsed")]
    img = sum(1 for e in f.entries if e.get("media_content") or e.get("media_thumbnail") or any(l.get("type", "").startswith("image") for l in e.get("links", [])))
    days = (now - min(ts)).days if ts else None
    per_day = round(len(ts) / max(days, 1), 1) if ts else 0
    return f"{name:22} n={len(f.entries):3} back={days} d  ~{per_day}/day  img={img}/{len(f.entries)}"


t0 = time.perf_counter()
with ThreadPoolExecutor(8) as ex:
    for line in ex.map(probe, FEEDS.items()):
        print(line)
print(f"{time.perf_counter() - t0:.1f}s")
