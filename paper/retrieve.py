"""Generic retrieval chain; acceptance is route-agnostic (validated against the item's source-of-record title).

Routes, cheapest first, each an independent failure domain: feed body -> direct fetch -> Jina Reader -> Wayback.
No per-site rules. Spike evidence: docs/state.md (principled retrieval chain).
"""
import json
import re

import trafilatura

from . import cache, config, fetch

STOP = {"this", "that", "with", "from", "have", "will", "what", "when", "where", "which", "their", "about", "after", "over", "into", "more", "than", "been", "were", "they", "them", "your", "said", "says", "news", "live", "update", "latest"}


def _words(s):
    return re.findall(r"[A-Za-z][A-Za-z'-]+", s or "")


def _content(s):
    return {w.lower() for w in _words(s) if len(w) >= 4 and w.lower() not in STOP}


def validate(text: str, title: str) -> bool:
    t = _content(title)
    recall = len(t & _content(text)) / len(t) if t else 0.0
    return len(_words(text)) >= config.RETRIEVE_MIN_WORDS and recall >= config.RETRIEVE_MIN_TITLE_RECALL


def _clean_md(md):
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md or "")
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)


def _direct(item):
    status, ctype, body = fetch.get(item["url"], ns="page")
    return trafilatura.extract(body, url=item["url"]) if status == 200 and body and "html" in ctype else None


def _jina(item):
    status, _, body = fetch.get(f"https://r.jina.ai/{item['url']}", ns="jina", headers={"Accept": "application/json"},
                                timeout=30, min_interval=config.JINA_MIN_INTERVAL_S, respect_robots=False)
    if status != 200 or not body:
        return None
    try:
        return _clean_md(json.loads(body).get("data", {}).get("content"))
    except json.JSONDecodeError:
        return None


def _wayback(item):
    status, _, body = fetch.get(f"https://web.archive.org/web/2026id_/{item['url']}", ns="wayback", timeout=30, respect_robots=False)
    return trafilatura.extract(body, url=item["url"]) if status == 200 and body else None


ROUTES = [("direct", _direct), ("jina", _jina), ("wayback", _wayback)]


def get_text(item) -> tuple[str | None, str]:
    """Return (text, route) or (None, 'unreadable'). Cached per URL."""
    k = cache.key("text", item["url"])
    hit = cache.get("text", k)
    if hit is not None:
        return hit["text"], hit["route"]
    result = (None, "unreadable")
    if item.get("feed_body"):
        txt = trafilatura.extract(item["feed_body"]) or ""
        if validate(txt, item["title"]):
            result = (txt, "feed")
    if result[0] is None:
        for name, fn in ROUTES:
            txt = fn(item) or ""
            if validate(txt, item["title"]):
                result = (txt, name)
                break
    cache.put("text", k, {"text": result[0], "route": result[1]})
    return result


def get_image(url: str | None):
    """Image bytes for synthesis only if they pass the media guard."""
    if not url:
        return None
    status, ctype, body = fetch.get(url, ns="img", binary=True, respect_robots=False)
    from .llm import valid_image

    return (body, ctype.split(";")[0]) if status == 200 and valid_image(body, ctype) else None
