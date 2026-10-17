"""LLM gateway: the only module that calls a model.

Owns: input-hash cache, error-classified retry (spec.md Failure cases), model fallback, media validation.
"""
import json
import logging
import random
import time

from . import cache, config

log = logging.getLogger("paper.llm")
_client = None


class LLMUnavailable(Exception):
    """All models in the chain failed for this call; callers apply the F3 fallback."""


def client():
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise LLMUnavailable("GEMINI_API_KEY is not set")
        from google import genai

        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def classify(err: Exception) -> str:
    code = getattr(err, "code", None) or getattr(err, "status_code", None)
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
    for model in config.MODELS[role]:
        repair = None
        for attempt in range(config.LLM_MAX_ATTEMPTS):
            if time.monotonic() > deadline:
                raise LLMUnavailable(f"time budget exhausted: {last}")
            try:
                contents = parts if repair is None else parts + [f"Your previous output was invalid: {repair}. Return valid JSON only."]
                r = client().models.generate_content(
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
                last = e
                kind = classify(e)
                log.warning("llm %s %s attempt %d: %s", model, kind, attempt + 1, str(e)[:300])
                if kind == "transient":
                    time.sleep(min(30, random.uniform(0, 2 ** (attempt + 1))))  # full jitter
                    continue
                if kind == "unknown" and attempt == 0:
                    continue
                if kind == "config" and "api key" in str(e).lower():
                    raise LLMUnavailable(f"configuration error: {e}") from e
                break  # permanent / config(model) / unknown twice: next model
    raise LLMUnavailable(str(last))
