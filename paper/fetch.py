"""Fetch gateway: the only module that makes outbound HTTP requests.

Owns caching, timeouts, the honest User-Agent, robots.txt and per-host pacing.
"""
import threading
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from . import cache, config

_client = httpx.Client(headers={"User-Agent": config.USER_AGENT}, timeout=config.FETCH_TIMEOUT_S, follow_redirects=True)
_robots: dict[str, RobotFileParser | None] = {}
_lock = threading.Lock()
_last_call: dict[str, float] = {}


def _pace(bucket: str, min_interval: float):
    with _lock:
        wait = min_interval - (time.monotonic() - _last_call.get(bucket, 0.0))
        if wait > 0:
            time.sleep(wait)
        _last_call[bucket] = time.monotonic()


def allowed(url: str) -> bool:
    host = urlsplit(url).netloc
    if host not in _robots:
        rp = RobotFileParser()
        try:
            r = _client.get(f"https://{host}/robots.txt")
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except httpx.HTTPError:
            rp = None  # unreachable robots.txt: treat as no restrictions
        _robots[host] = rp
    rp = _robots[host]
    return rp is None or rp.can_fetch(config.USER_AGENT, url)


def get(url: str, *, ns="http", headers=None, timeout=None, min_interval=0.0, respect_robots=True, binary=False):
    """Return (status, content_type, body) — cached by URL+headers; failures are cached only as 'no body'."""
    k = cache.key(url, headers)
    hit = cache.get(ns, k)
    if hit is not None:
        body = cache.get_bytes(ns + "-b", k) if binary else hit.get("body")
        return hit["status"], hit["ctype"], body
    if respect_robots and not allowed(url):
        return 999, "", None
    if min_interval:
        _pace(ns, min_interval)
    try:
        r = _client.get(url, headers=headers, timeout=timeout or config.FETCH_TIMEOUT_S)
    except httpx.HTTPError:
        return 0, "", None  # network failure: not cached, may succeed later
    ctype = r.headers.get("content-type", "")
    if binary:
        if r.status_code == 200:
            cache.put_bytes(ns + "-b", k, r.content)
        cache.put(ns, k, {"status": r.status_code, "ctype": ctype})
        return r.status_code, ctype, r.content if r.status_code == 200 else None
    body = r.text if r.status_code == 200 else None
    cache.put(ns, k, {"status": r.status_code, "ctype": ctype, "body": body})
    return r.status_code, ctype, body
