"""Persona simulator (D2): labeled simulated reading for backfilled days, and the A10 learning evaluation.

Simulated reader: cascade examination (attention decays with position), engagement drawn from the persona's
ground-truth topic interest. Ground truth is used ONLY here, never by ranking.
"""
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import numpy as np

from . import config, db, edition, ingest, learn, personas, rank

log = logging.getLogger("paper.simulate")
EXAMINE_FIRST = 0.95   # assumption: probability the first story is examined
EXAMINE_DECAY = 0.90   # assumption: examination probability multiplier per position (cascade model)


def _truth(con, persona):
    slugs = {r["id"]: r["slug"] for r in con.execute("SELECT id, slug FROM topics WHERE kind='iptc'")}
    return {tid: persona["truth"].get(slug, 0.05) for tid, slug in slugs.items()}


def _p_engage(weights, truth):
    return sum(float(w) * truth.get(int(t), 0.05) for t, w in weights.items())


def simulate_day(con, reader_id, persona, eid, day):
    truth = _truth(con, persona)
    body = json.loads(con.execute("SELECT body FROM editions WHERE id=?", (eid,)).fetchone()["body"])
    rng = rank.rng_for(day, f"sim-{reader_id}")  # deterministic across processes (hash() is salted)
    ts = datetime.now(UTC).isoformat()
    for k, s in enumerate(body["stories"]):
        if rng.random() > EXAMINE_FIRST * EXAMINE_DECAY ** k:
            continue
        db.add_event(con, reader_id, ts, day.isoformat(), "seen", eid, k, simulated=True)
        if rng.random() < _p_engage(s["topic_weights"], truth):
            act = rng.choice(["click", "dwell", "more", "save"], p=[0.5, 0.3, 0.12, 0.08])
            db.add_event(con, reader_id, ts, day.isoformat(), str(act), eid, k, {"seconds": int(rng.integers(30, 120))} if act == "dwell" else None, simulated=True)
        elif rng.random() < 0.35:
            db.add_event(con, reader_id, ts, day.isoformat(), str(rng.choice(["skip", "less"], p=[0.8, 0.2])), eid, k, simulated=True)


def demo(days: int = 7):
    """Seed personas; for each day oldest->newest: shared stages, three editions in parallel, simulated reading on backfilled days."""
    ids = personas.seed()
    today = datetime.now(config.PKT).date()
    for d in range(days - 1, -1, -1):
        day = today - timedelta(days=d)
        log.info("day %s: %s", day, ingest.run_day(day))
        kind = "live" if d == 0 else "backfilled"
        with ThreadPoolExecutor(3) as ex:
            eids = dict(zip(ids, ex.map(lambda key, day=day, kind=kind: edition.build_edition(ids[key], day, kind), ids)))
        if d == 0:
            continue  # real signals start today (D2)
        with db.tx() as con:
            for p in personas.PERSONAS:
                if eids.get(p["key"]) and not con.execute("SELECT 1 FROM events WHERE edition_id=? AND simulated=1", (eids[p["key"]],)).fetchone():
                    simulate_day(con, ids[p["key"]], p, eids[p["key"]], day)
    log.info("demo complete: %s", ids)


def _ndcg(gains_ranked, gains_ideal, k=10):
    disc = 1 / np.log2(np.arange(2, k + 2))
    ideal = float(np.sort(gains_ideal)[::-1][:k] @ disc[: min(k, len(gains_ideal))])
    got = float(np.asarray(gains_ranked[:k]) @ disc[: min(k, len(gains_ranked))])
    return got / ideal if ideal else 0.0


def evaluate(days: int = 7, k: int = 10):
    """A10: replay days with a simulated reader on ranked lists (no LLM), comparing learned ranking with baselines."""
    today = datetime.now(config.PKT).date()
    results = {}
    with db.tx() as con:
        tids, tvecs = zip(*[(r["id"], np.frombuffer(r["vec"], dtype=np.float32)) for r in con.execute("SELECT id, vec FROM topics WHERE kind='iptc' ORDER BY id")])
        tvecs = np.stack(tvecs)
        for p in personas.PERSONAS:
            truth = _truth(con, p)
            prior = {}
            for slug in p["chips"]:
                r = con.execute("SELECT id FROM topics WHERE slug=?", (slug,)).fetchone()
                n, m = config.PRIOR_STRENGTH, config.PRIOR_MEAN_CHOSEN
                prior[r["id"]] = (m * n, (1 - m) * n)
            prof = learn.Profile(prior=dict(prior))
            onboard_only = learn.Profile(prior=dict(prior))
            rng = np.random.default_rng(7)
            scores = {"learned": [], "onboarding_only": [], "recency": [], "random": []}
            for d in range(days - 1, -1, -1):
                day = (today - timedelta(days=d)).isoformat()
                rows = con.execute("SELECT id, title, domain, source_time, vec FROM items WHERE day=? AND vec IS NOT NULL", (day,)).fetchall()
                if not rows:
                    continue
                items = [{"title": r["title"], "domain": r["domain"], "t": r["source_time"]} for r in rows]
                vecs = np.stack([np.frombuffer(r["vec"], dtype=np.float32) for r in rows])
                top1 = np.argmax(vecs @ tvecs.T, axis=1)
                gain = np.array([truth[tids[j]] for j in top1])
                pool = list(set(prof.prior) | set(tids))  # learned ranker may surface any topic it has evidence for

                def ranked(pr, topics, items=items, vecs=vecs):
                    return [c["i"] for c in rank.candidates(items, vecs, list(tids), tvecs, topics, pr)]

                lists = {
                    "learned": ranked(prof, [t for t in pool if t in prof.prior or prof.evidence.get(t)] or list(prof.prior)),
                    "onboarding_only": ranked(onboard_only, list(prior)),
                    "recency": sorted(range(len(items)), key=lambda i: items[i]["t"], reverse=True)[:k],
                    "random": list(rng.permutation(len(items))[:k]),
                }
                for name, lst in lists.items():
                    scores[name].append(_ndcg(gain[lst[:k]], gain, k))
                # simulated reading of the learned list updates the learned profile (explore 2 extra topics by Thompson)
                shown = lists["learned"][:k]
                explore = sorted([t for t in tids if t not in prof.prior], key=lambda t: -rng.beta(*prof.ab(t)))[:2]
                for t in explore:
                    j = tids.index(t)
                    cand = [i for i in np.argsort(-(vecs @ tvecs[j]))[:50] if top1[i] == j]
                    if cand:
                        shown.append(int(cand[0]))
                for pos, i in enumerate(shown):
                    if rng.random() > EXAMINE_FIRST * EXAMINE_DECAY ** pos:
                        continue
                    t = tids[top1[i]]
                    y = int(rng.random() < truth[t])
                    a, b = prof.ab(t)
                    prof.alpha[t], prof.beta[t] = a + y, b + 1 - y
                    prof.evidence.setdefault(t, []).append(y)
            results[p["key"]] = {name: [round(x, 3) for x in v] for name, v in scores.items()}
    return results
