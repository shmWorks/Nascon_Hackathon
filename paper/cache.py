"""Content-addressed disk cache: identical inputs never cost a second external call.

Writes are atomic and concurrency-safe: each writer uses a unique temp file; if another writer already stored the
same key, its content is equivalent by construction (same input hash), so losing the race is success.
"""
import hashlib
import json
import os
import threading
import uuid

from . import config


def key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


def _path(ns, k):
    p = config.CACHE / ns / k[:2]
    p.mkdir(parents=True, exist_ok=True)
    return p / k


def _atomic_write(p, data: bytes):
    tmp = p.with_name(f"{p.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_bytes(data)
    try:
        tmp.replace(p)
    except PermissionError:  # Windows: target held open by a concurrent writer of the same key
        tmp.unlink(missing_ok=True)
        if not p.exists():
            raise


def get(ns, k):
    p = _path(ns, k)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def put(ns, k, value):
    _atomic_write(_path(ns, k), json.dumps(value).encode("utf-8"))
    return value


def get_bytes(ns, k):
    p = _path(ns, k)
    return p.read_bytes() if p.exists() else None


def put_bytes(ns, k, data):
    _atomic_write(_path(ns, k), data)
    return data
