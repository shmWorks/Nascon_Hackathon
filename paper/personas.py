"""Demo personas: seeded through the same onboarding function the web form uses. `truth` is simulator-only ground truth."""
from argon2 import PasswordHasher

from . import db, topics

PERSONAS = [
    {"key": "ayesha", "name": "Ayesha", "email": "ayesha@demo.paper", "chips": ["ai", "startups", "tech-industry", "pakistan"],
     "free": ["AI product launches and LLM tools"],
     "truth": {"ai": 0.85, "startups": 0.7, "tech-industry": 0.55, "pakistan": 0.35, "cybersecurity": 0.6, "markets": 0.2}},
    {"key": "bilal", "name": "Bilal", "email": "bilal@demo.paper", "chips": ["cricket", "space", "astronomy"],
     "free": ["Pakistan cricket team"],
     "truth": {"cricket": 0.9, "space": 0.75, "astronomy": 0.6, "football": 0.3, "biology-medicine": 0.25, "pakistan": 0.5}},
    {"key": "sara", "name": "Sara", "email": "sara@demo.paper", "chips": ["climate", "markets", "energy", "economy"],
     "free": ["climate finance and carbon markets"],
     "truth": {"climate": 0.85, "markets": 0.7, "energy": 0.65, "economy": 0.45, "environment": 0.55, "politics": 0.2}},
]
DEMO_PASSWORD = "morningpaper"  # demo accounts only; shown on the login page for evaluators

ph = PasswordHasher()


def onboard(con, reader_id: int, chips: list[str], free: list[str]):
    """Shared by the web form and the seeder. Records onboarding as events (A1)."""
    n = 0
    for slug in chips:
        r = con.execute("SELECT id FROM topics WHERE slug=?", (slug,)).fetchone()
        if r:
            con.execute("INSERT OR IGNORE INTO reader_topics(reader_id, topic_id, mode) VALUES (?,?,'chosen')", (reader_id, r["id"]))
            n += 1
    for phrase in [f for f in free if f.strip()]:
        tid = topics.add_custom(con, reader_id, phrase)
        con.execute("INSERT OR IGNORE INTO reader_topics(reader_id, topic_id, mode) VALUES (?,?,'chosen')", (reader_id, tid))
        n += 1
    return n


def create_reader(con, email, name, password, persona=None):
    cur = con.execute("INSERT INTO readers(email, name, pw_hash, persona) VALUES (?,?,?,?)", (email.lower().strip(), name.strip(), ph.hash(password), persona))
    return cur.lastrowid


def seed():
    ids = {}
    with db.tx() as con:
        for p in PERSONAS:
            r = con.execute("SELECT id FROM readers WHERE email=?", (p["email"],)).fetchone()
            rid = r["id"] if r else create_reader(con, p["email"], p["name"], DEMO_PASSWORD, p["key"])
            onboard(con, rid, p["chips"], p["free"])
            ids[p["key"]] = rid
    return ids
