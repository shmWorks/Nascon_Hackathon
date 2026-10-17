"""Topics are labeled vectors: IPTC-based nodes and readers' free-text interests, one mechanism for both."""
import json
import re
from pathlib import Path

import numpy as np

from . import db, embed

DATA = Path(__file__).parent / "data"


def _text(label, desc):
    return f"{label}: {desc}"


def load_iptc():
    rows = json.loads((DATA / "topics.json").read_text(encoding="utf-8"))
    vecs = embed.embed([_text(label, desc) for _, label, desc in rows])
    with db.tx() as con:
        for (slug, label, desc), v in zip(rows, vecs):
            con.execute(
                "INSERT INTO topics(slug,label,description,kind,vec) VALUES (?,?,?,?,?) "
                "ON CONFLICT(slug) DO UPDATE SET label=excluded.label, description=excluded.description, vec=excluded.vec",
                (slug, label, desc, "iptc", v.astype(np.float32).tobytes()),
            )
    return len(rows)


def add_custom(con, reader_id: int, phrase: str) -> int:
    """A reader's free-text interest becomes its own topic vector (only the phrase goes to the model: D5)."""
    phrase = phrase.strip()[:120]
    slug = f"u{reader_id}-" + re.sub(r"[^a-z0-9]+", "-", phrase.lower()).strip("-")[:60]
    v = embed.embed([phrase])[0]
    con.execute(
        "INSERT INTO topics(slug,label,description,kind,owner,vec) VALUES (?,?,?,?,?,?) ON CONFLICT(slug) DO NOTHING",
        (slug, phrase, phrase, "custom", reader_id, v.astype(np.float32).tobytes()),
    )
    return con.execute("SELECT id FROM topics WHERE slug=?", (slug,)).fetchone()["id"]


def vectors(con, ids):
    rows = con.execute(f"SELECT id, label, vec FROM topics WHERE id IN ({','.join('?' * len(ids))})", list(ids)).fetchall()
    return [r["id"] for r in rows], [r["label"] for r in rows], np.stack([np.frombuffer(r["vec"], dtype=np.float32) for r in rows])


def catalog(con):
    return con.execute("SELECT id, slug, label FROM topics WHERE kind='iptc' ORDER BY id").fetchall()
