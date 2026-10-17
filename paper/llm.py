"""LLM gateway: the only module that calls a model.

Owns: input-hash cache, error-classified retry (spec.md Failure cases), model fallback, media validation.
"""
import json
import logging
import random
import re
import threading
import time

from . import cache, config

log = logging.getLogger("paper.llm")
_clients: dict[int, object] = {}
_cooling: dict[tuple[str, int], float] = {}  # (model, key index) -> monotonic time until the lane may be used again
_concurrency = threading.BoundedSemaphore(2)  # avoid per-minute bursts across parallel builds


def _retry_after(err) -> tuple[float | None, bool]:
    """(seconds, per_day) from the API's own RetryInfo / QuotaFailure details."""
    s = str(err)
    m = re.search(r"retryDelay'?:\s*'?(\d+(?:\.\d+)?)s", s)
    return (float(m[1]) if m else None), ("PerDay" in s)


class LLMUnavailable(Exception):
    """All models in the chain failed for this call; callers apply the F3 fallback."""


def client(ki: int = 0):
    """One client per configured key; each key is a separate quota lane."""
    if not config.GEMINI_API_KEYS:
        raise LLMUnavailable("No GEMINI_API_KEY / GEMINI_API_KEY1..9 is set")
    if ki not in _clients:
        from google import genai
        from google.genai import types

        # Per-request timeout: a hung request must become a classified transient error, not a stuck pipeline.
        _clients[ki] = genai.Client(api_key=config.GEMINI_API_KEYS[ki], http_options=types.HttpOptions(timeout=config.LLM_REQUEST_TIMEOUT_MS))
    return _clients[ki]


def lanes(role: str):
    """(model, key) pairs in preference order: each model is tried on every key before the next model."""
    return [(m, ki) for m in config.MODELS[role] for ki in range(len(config.GEMINI_API_KEYS))]


def classify(err: Exception) -> str:
    """Type first: only API and network errors are retryable; anything else is a programming error ("bug")."""
    import httpx

    if isinstance(err, httpx.TransportError):  # timeouts, connection resets, protocol errors
        return "transient"
    code = getattr(err, "code", None) or getattr(err, "status_code", None)
    if not isinstance(code, int):
        return "bug"
    msg = str(err).lower()
    if code in (429, 500, 502, 503, 504) or "timeout" in msg or "temporarily" in msg or "connection" in msg:
        return "transient"
    if code in (401, 403) or "api key" in msg or ("model" in msg and "not found" in msg) or code == 404:
        return "config"
    if code == 400 or "safety" in msg or "blocked" in msg:
        return "permanent"
    return "unknown"


IMAGE_MAGIC = (b"\xff\xd8\xff", b"\x89PNG", b"GIF8", b"RIFF")


def valid_image(data: bytes | None, ctype: str) -> bool:
    """Media guard: only real image bytes reach the model (spike: HTML error pages caused invented image claims)."""
    return bool(data) and ctype.startswith("image/") and data[:4].startswith(IMAGE_MAGIC) and len(data) > 1024


def generate_json(role: str, prompt: str, schema, images=()):
    """Structured generation over the role's model chain. Returns parsed JSON or raises LLMUnavailable."""
    from google.genai import types

    img_keys = [cache.key(len(b), b[:64].hex(), b[-64:].hex()) for b, _ in images]
    k = cache.key(role, prompt, img_keys, str(schema))
    hit = cache.get("llm", k)
    if hit is not None:
        return hit
    parts = [types.Part.from_bytes(data=b, mime_type=m) for b, m in images] + [prompt]
    deadline = time.monotonic() + config.LLM_CALL_BUDGET_S
    last = None
    if not config.GEMINI_API_KEYS:
        raise LLMUnavailable("No GEMINI_API_KEY / GEMINI_API_KEY1..9 is set")
    all_lanes = lanes(role)
    for li, (model, ki) in enumerate(all_lanes):
        if _cooling.get((model, ki), 0) > time.monotonic():
            continue  # this lane's quota is cooling down: skip without spending a request
        more_lanes = li < len(all_lanes) - 1
        repair = None
        for attempt in range(config.LLM_MAX_ATTEMPTS):
            if time.monotonic() > deadline:
                raise LLMUnavailable(f"time budget exhausted: {last}")
            try:
                contents = parts if repair is None else parts + [f"Your previous output was invalid: {repair}. Return valid JSON only."]
                with _concurrency:
                    r = client(ki).models.generate_content(
                        model=model, contents=contents,
                        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema, temperature=0.2),
                    )
                try:
                    out = json.loads(r.text)
                except (json.JSONDecodeError, TypeError) as e:
                    if repair is not None:
                        break  # one repair retry only, then next model
                    repair = str(e)[:200]
                    continue
                return cache.put("llm", k, out)
            except LLMUnavailable:
                raise
            except Exception as e:
                if classify(e) == "bug":
                    raise  # never retry or mask a programming error
                last = e
                kind = classify(e)
                log.warning("llm %s key#%d %s attempt %d: %s", model, ki + 1, kind, attempt + 1, str(e)[:1500] if "429" in str(e)[:40] else str(e)[:300])
                if kind == "transient":
                    delay, per_day = _retry_after(e)
                    if getattr(e, "code", None) == 429 and (per_day or more_lanes or (delay and delay > config.LLM_CALL_BUDGET_S)):
                        cool = delay or (3600 if per_day else 60)
                        _cooling[(model, ki)] = time.monotonic() + cool
                        log.warning("llm %s key#%d quota hit (%s) — cooling %.0fs, next lane", model, ki + 1, "day" if per_day else "minute", cool)
                        break
                    remaining = deadline - time.monotonic()
                    wait = delay + random.uniform(0, 1) if delay else random.uniform(0, 2 ** (attempt + 1))  # server hint, else full jitter
                    if wait >= remaining:
                        break
                    time.sleep(wait)
                    continue
                if kind == "unknown" and attempt == 0:
                    continue
                if kind == "config" and "api key" in str(e).lower():
                    for lane_model, lane_key in all_lanes:  # an invalid key disables every lane that uses it, not the whole call
                        if lane_key == ki:
                            _cooling[(lane_model, lane_key)] = time.monotonic() + 86400
                    log.error("llm key#%d rejected (configuration error) — disabled", ki + 1)
                break  # permanent / config / unknown twice: next lane
    raise LLMUnavailable(str(last))
