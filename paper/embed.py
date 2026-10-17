"""Local embeddings (model2vec static model): no quota, no network after first download, deterministic.

One embedding space for items, IPTC topics and readers' free-text interests. Interest phrases never leave the
machine. All downstream rules are relative (ranks, percentiles), never absolute cosine thresholds, so swapping
the model does not silently break them.
"""
import functools

import numpy as np

from . import config


@functools.lru_cache(maxsize=1)
def _model():
    from model2vec import StaticModel

    return StaticModel.from_pretrained(config.EMBED_MODEL)


def embed(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, config.EMBED_DIM), dtype=np.float32)
    v = _model().encode(list(texts)).astype(np.float32)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)
