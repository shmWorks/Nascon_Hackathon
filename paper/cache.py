"""Content-addressed disk cache: identical inputs never cost a second external call."""
import hashlib
import json

from . import config


def key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


def _path(ns, k):
    p = config.CACHE / ns / k[:2]
    p.mkdir(parents=True, exist_ok=True)
    return p / k


def get(ns, k):
    p = _path(ns, k)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def put(ns, k, value):
    p = _path(ns, k)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(value), encoding="utf-8")
    tmp.replace(p)  # atomic: a crash never leaves a half-written entry
    return value


def get_bytes(ns, k):
    p = _path(ns, k)
    return p.read_bytes() if p.exists() else None


def put_bytes(ns, k, data):
    p = _path(ns, k)
    tmp = p.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(p)
    return data
