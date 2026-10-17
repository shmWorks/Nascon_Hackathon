"""Spike: can each source return items for a specific past day, with the fields we need?"""
import json
import re
import sys
import time
from datetime import date, timedelta
from urllib.parse import quote

import feedparser
import httpx

UA = {"User-Agent": "Mozilla/5.0 (morning-paper spike)"}
day = date.today() - timedelta(days=3)
nxt = day + timedelta(days=1)
client = httpx.Client(headers=UA, timeout=20, follow_redirects=True)


def gdelt(query):
    d0, d1 = day.strftime("%Y%m%d000000"), nxt.strftime("%Y%m%d000000")
    url = (
        "http://api.gdeltproject.org/api/v2/doc/doc?query="
        + quote(query)
        + f"&mode=artlist&format=json&maxrecords=50&startdatetime={d0}&enddatetime={d1}&sourcelang=english"
    )
    for attempt in range(3):
        r = client.get(url)
        if r.status_code == 429 or "limit requests" in r.text[:200].lower():
            time.sleep(6)
            continue
        break
    print("GDELT status", r.status_code, "len", len(r.text))
    try:
        arts = r.json().get("articles", [])
    except json.JSONDecodeError:
        print("GDELT non-JSON:", r.text[:200])
        return []
    print("GDELT count", len(arts), "keys", sorted(arts[0].keys()) if arts else None)
    for a in arts[:3]:
        print("  ", a.get("seendate"), a.get("domain"), "| img:", bool(a.get("socialimage")), "|", a.get("title", "")[:80])
    with_img = sum(1 for a in arts if a.get("socialimage"))
    print(f"GDELT with socialimage: {with_img}/{len(arts)}")
    return arts


def gnews(query):
    q = quote(f"{query} after:{day.isoformat()} before:{nxt.isoformat()}")
    f = feedparser.parse(client.get(f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en").content)
    print("GNews count", len(f.entries))
    dates = sorted({e.get("published", "")[:16] for e in f.entries})
    print("  date range:", dates[:1], "...", dates[-1:])
    for e in f.entries[:3]:
        print("  ", e.get("published"), "|", e.get("source", {}).get("title"), "|", e.title[:70])
    return f.entries


def rss(url):
    f = feedparser.parse(client.get(url).content)
    imgs = sum(1 for e in f.entries if e.get("media_content") or e.get("media_thumbnail") or any(l.get("type", "").startswith("image") for l in e.get("links", [])))
    dates = sorted(e.get("published_parsed") for e in f.entries if e.get("published_parsed"))
    span = (time.strftime("%Y-%m-%d", dates[0]), time.strftime("%Y-%m-%d", dates[-1])) if dates else None
    print(f"RSS {url[:50]} count {len(f.entries)} with_image {imgs} date_span {span}")


def og_image(url):
    try:
        html = client.get(url).text
    except httpx.HTTPError as e:
        print("og fetch fail", type(e).__name__)
        return
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', html)
    print("og:image", bool(m), url[:60])


print("target day", day)
arts = gdelt(sys.argv[1] if len(sys.argv) > 1 else "artificial intelligence")
gn = gnews("cricket")
for u in ["https://feeds.bbci.co.uk/news/technology/rss.xml", "https://www.theverge.com/rss/index.xml", "https://www.sciencedaily.com/rss/space_time.xml"]:
    rss(u)
for a in arts[:3]:
    og_image(a["url"])
