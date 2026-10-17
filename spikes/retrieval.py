"""Principled retrieval chain + validation on a random cross-site sample.

Design (no per-site rules):
- Routes are generic strategies, each applicable to any URL, ordered by cost: publisher-supplied text
  (feed body) -> direct fetch -> Jina Reader -> Wayback copy. Each has an independent failure domain.
- Acceptance is route-agnostic: a candidate text is accepted only if it validates against the item's
  source-of-record metadata (title from the feed/GKG record), never because a route "usually works".
- Every knob is a named config value with a stated meaning, calibrated below; none is site-specific.

Validation:
- Positives: real item URL -> retrieved text, judged against its own title.
- Negatives generated without hand labels: (a) swap test — text of item A judged against title of item B
  must be rejected; (b) error/challenge bodies must be rejected.
"""
import csv
import io
import json
import random
import re
import statistics
import sys
import threading
import time
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import httpx
import trafilatura

CFG = {
    "timeout_s": 8,
    "min_words": 120,          # below this a page is a stub/teaser/error, not an article body
    "min_title_recall": 0.5,   # share of title content-words that must occur in the body
    "jina_min_interval_s": 3.1,  # 20 RPM keyless limit (jina.ai/reader)
}
UA = {"User-Agent": "MorningPaperBot/0.1 (+https://github.com/shmWorks/Nascon_Hackathon)"}
STOP = set("this that with from have will what when where which their about after over into more than been were they them your said says news live update latest".split())
words = lambda s: re.findall(r"[A-Za-z][A-Za-z'-]+", s or "")
content_tokens = lambda s: {w.lower() for w in words(s) if len(w) >= 4 and w.lower() not in STOP}


def validate(text, title):
    """Route-agnostic acceptance: is this text the body of the article with this title?"""
    n = len(words(text))
    t = content_tokens(title)
    recall = len(t & content_tokens(text)) / len(t) if t else 0.0
    return (n >= CFG["min_words"] and recall >= CFG["min_title_recall"]), {"words": n, "title_recall": round(recall, 2)}


def clean_md(md):
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md or "")          # images
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)           # links -> anchor text


client = httpx.Client(headers=UA, timeout=CFG["timeout_s"], follow_redirects=True)
_last_jina = [0.0]
_jina_lock = threading.Lock()


def route_direct(item):
    r = client.get(item["url"])
    return trafilatura.extract(r.text, url=item["url"]) if r.status_code == 200 and "html" in r.headers.get("content-type", "") else None


def route_jina(item):
    with _jina_lock:  # serialize to respect the keyless 20 RPM limit across threads
        wait = CFG["jina_min_interval_s"] - (time.monotonic() - _last_jina[0])
        if wait > 0:
            time.sleep(wait)
        _last_jina[0] = time.monotonic()
    r = client.get(f"https://r.jina.ai/{item['url']}", headers={"Accept": "application/json"}, timeout=30)
    return clean_md(r.json().get("data", {}).get("content")) if r.status_code == 200 else None


def route_wayback(item):
    r = client.get(f"https://web.archive.org/web/2026id_/{item['url']}", timeout=30)
    return trafilatura.extract(r.text, url=item["url"]) if r.status_code == 200 else None


ROUTES = [("direct", route_direct), ("jina", route_jina), ("wayback", route_wayback)]


def retrieve(item):
    trace = []
    if item.get("feed_body"):
        txt = trafilatura.extract(item["feed_body"]) or ""
        ok, m = validate(txt, item["title"])
        trace.append(("feed", ok, m))
        if ok:
            return txt, trace
    for name, fn in ROUTES:
        try:
            txt = fn(item) or ""
        except (httpx.HTTPError, ValueError) as e:
            trace.append((name, False, {"error": type(e).__name__}))
            continue
        ok, m = validate(txt, item["title"])
        trace.append((name, ok, m))
        if ok:
            return txt, trace
    return None, trace


def gkg_sample(stamps, n, seed=7):
    csv.field_size_limit(10**8)
    rows = []
    for s in stamps:
        z = zipfile.ZipFile(io.BytesIO(httpx.get(f"https://data.gdeltproject.org/gdeltv2/{s}.gkg.csv.zip", timeout=60).content))
        for x in csv.reader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8", "replace")), delimiter="\t"):
            m = re.search(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", x[26]) if len(x) > 26 else None
            if m and len(content_tokens(m[1])) >= 3:
                rows.append({"url": x[4], "domain": x[3], "title": m[1]})
    by_domain = {}
    for r in rows:
        by_domain.setdefault(r["domain"], r)  # one URL per domain -> breadth across sites
    pool = list(by_domain.values())
    random.Random(seed).shuffle(pool)
    return pool[:n]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    items = gkg_sample(["20261013060000", "20261013180000"], n)
    print(f"sample {len(items)} items from {len({i['domain'] for i in items})} distinct domains")
    t0 = time.perf_counter()
    with ThreadPoolExecutor(4) as ex:  # distinct hosts; Jina pacing is enforced inside route_jina
        results = list(ex.map(retrieve, items))
    by_route, fails = Counter(), Counter()
    for (txt, trace) in results:
        winner = next((r for r, ok, _ in trace if ok), "none")
        by_route[winner] += 1
        for r, ok, m in trace:
            if not ok:
                fails[(r, "error" if "error" in m else ("short" if m.get("words", 0) < CFG["min_words"] else "title"))] += 1
    print("accepted by route:", dict(by_route), f"| coverage {sum(v for k, v in by_route.items() if k != 'none')}/{len(items)} | {time.perf_counter() - t0:.0f}s")
    print("rejections by (route, reason):", dict(fails))
    # Negatives 1: swap test — accepted text of item i judged against title of item i+1
    acc = [(it, txt) for it, (txt, _) in zip(items, results) if txt]
    swaps = [validate(acc[i][1], acc[(i + 1) % len(acc)][0]["title"]) for i in range(len(acc))]
    fp = sum(ok for ok, _ in swaps)
    print(f"swap-test false accepts {fp}/{len(swaps)}; swapped title_recall median {statistics.median(m['title_recall'] for _, m in swaps):.2f}")
    pos = [validate(txt, it["title"])[1]["title_recall"] for it, txt in acc]
    print(f"accepted title_recall min {min(pos):.2f} median {statistics.median(pos):.2f}")
    # Negatives 2: error/challenge bodies
    for label, body in [("cloudflare-403", client.get("https://www.dawn.com/news/2037799").text), ("http-404", client.get("https://www.bbc.co.uk/news/this-page-does-not-exist-xyz").text)]:
        txt = trafilatura.extract(body) or ""
        print(f"negative {label}: accepted={validate(txt, items[0]['title'])[0]} words={len(words(txt))}")
    json.dump([{"url": it["url"], "trace": tr} for it, (_, tr) in zip(items, results)], open("spikes/out/retrieval_trace.json", "w"), default=str)
