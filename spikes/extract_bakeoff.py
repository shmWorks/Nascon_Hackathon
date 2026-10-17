"""Spike: article-extraction bake-off on real URLs from our own sources.

Oracle independent of every extractor: the publisher's own RSS description must appear in the extracted text
(token recall of the description). Also: success rate, length, boilerplate leakage, time, metadata.
"""
import asyncio
import json
import re
import statistics
import sys
import time
from html import unescape
from pathlib import Path

import feedparser
import httpx

FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.theguardian.com/environment/rss",
    "https://www.dawn.com/feeds/home",
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "https://www.space.com/feeds/all",
    "https://techcrunch.com/feed/",
    "https://feeds.arstechnica.com/arstechnica/index",
]
PER_FEED = 3
BOILER = re.compile(r"\b(cookie|subscribe|newsletter|sign up|advertisement|all rights reserved|follow us|related articles|read more)\b", re.I)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}
toks = lambda s: set(re.findall(r"[a-z0-9]{4,}", s.lower()))


def strip(h):
    return unescape(re.sub(r"<[^>]+>", " ", h or ""))


def sample():
    c = httpx.Client(headers=UA, timeout=15, follow_redirects=True)
    out = []
    for f in FEEDS:
        try:
            d = feedparser.parse(c.get(f).content)
        except httpx.HTTPError:
            continue
        for e in d.entries[:PER_FEED]:
            desc = strip(e.get("summary", ""))
            if len(toks(desc)) >= 6:
                out.append({"url": e.link, "title": e.title, "desc": desc})
    return out


def score(text, item):
    d = toks(item["desc"])
    return {
        "ok": len(text) >= 500,
        "chars": len(text),
        "recall": round(len(d & toks(text)) / len(d), 2) if d else None,
        "boiler": len(BOILER.findall(text)),
    }


def run_trafilatura(items, htmls):
    import trafilatura

    res = []
    for it, h in zip(items, htmls):
        t0 = time.perf_counter()
        txt = trafilatura.extract(h, url=it["url"], favor_precision=True) if h else None
        meta = trafilatura.extract_metadata(h) if h else None
        res.append(score(txt or "", it) | {"s": time.perf_counter() - t0, "date": bool(meta and meta.date), "img": bool(meta and meta.image)})
    return res


def run_readability(items, htmls):
    from readability import Document

    res = []
    for it, h in zip(items, htmls):
        t0 = time.perf_counter()
        txt = strip(Document(h).summary()) if h else ""
        res.append(score(re.sub(r"\s+", " ", txt), it) | {"s": time.perf_counter() - t0, "date": None, "img": None})
    return res


def run_crawl4ai(items):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.content_filter_strategy import PruningContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

    async def go():
        cfg = CrawlerRunConfig(markdown_generator=DefaultMarkdownGenerator(content_filter=PruningContentFilter()), page_timeout=20000)
        res = []
        async with AsyncWebCrawler() as cr:
            for it in items:
                t0 = time.perf_counter()
                try:
                    r = await cr.arun(it["url"], config=cfg)
                    md = r.markdown.fit_markdown if r.success and r.markdown else ""
                except Exception:
                    md = ""
                txt = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md or "")
                res.append(score(txt, it) | {"s": time.perf_counter() - t0, "date": None, "img": None})
        return res

    return asyncio.run(go())


def summarize(name, res, fetch_s=0.0):
    rec = [r["recall"] for r in res if r["recall"] is not None]
    print(
        f"{name:12} ok {sum(r['ok'] for r in res):2}/{len(res)}  recall med {statistics.median(rec):.2f} min {min(rec):.2f}"
        f"  chars med {int(statistics.median(r['chars'] for r in res)):5}  boiler/page {statistics.mean(r['boiler'] for r in res):.1f}"
        f"  s/page {statistics.mean(r['s'] for r in res) + fetch_s:.2f}"
        + (f"  date {sum(bool(r['date']) for r in res)}  img {sum(bool(r['img']) for r in res)}" if res[0]["date"] is not None else "")
    )


if __name__ == "__main__":
    which = sys.argv[1:] or ["trafilatura", "readability"]
    cache = Path("spikes/out/bakeoff_items.json")
    items = json.loads(cache.read_text()) if cache.exists() else sample()
    cache.write_text(json.dumps(items))
    c = httpx.Client(headers=UA, timeout=15, follow_redirects=True)
    t0 = time.perf_counter()
    htmls = []
    for it in items:
        try:
            r = c.get(it["url"])
            htmls.append(r.text if r.status_code == 200 else "")
        except httpx.HTTPError:
            htmls.append("")
    fetch_s = (time.perf_counter() - t0) / len(items)
    print(f"items {len(items)}  http-200 {sum(bool(h) for h in htmls)}  fetch s/page {fetch_s:.2f}")
    for w in which:
        if w == "trafilatura":
            summarize(w, run_trafilatura(items, htmls), fetch_s)
        elif w == "readability":
            summarize(w, run_readability(items, htmls), fetch_s)
        elif w == "crawl4ai":
            summarize(w, run_crawl4ai(items))
