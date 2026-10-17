"""build_edition: rank -> cluster -> select -> retrieve -> synthesize -> commit -> render. Idempotent; editions are immutable."""
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

import numpy as np

from . import config, db, learn, llm, rank, render, retrieve, synth

log = logging.getLogger("paper.edition")


def _load_items(con, day):
    rows = con.execute("SELECT id,url,domain,title,description,source_time,image_url,feed_body,vec FROM items WHERE day=? AND vec IS NOT NULL", (day.isoformat(),)).fetchall()
    items = [dict(r) for r in rows]
    vecs = np.stack([np.frombuffer(r["vec"], dtype=np.float32) for r in rows]) if rows else np.zeros((0, config.EMBED_DIM), np.float32)
    for it in items:
        it.pop("vec")
    return items, vecs


def _topics(con, reader_id):
    rows = con.execute("SELECT id,label,vec FROM topics WHERE kind='iptc' OR owner=? ORDER BY id", (reader_id,)).fetchall()
    return [r["id"] for r in rows], {r["id"]: r["label"] for r in rows}, np.stack([np.frombuffer(r["vec"], dtype=np.float32) for r in rows])


def _why(prof, t, label, exploring):
    if exploring:
        return f"Exploring: a {label} story outside your usual topics, to learn whether you want more"
    ev = prof.evidence.get(t, [])
    if ev:
        return f"You engaged with {sum(ev)} of {len(ev)} {label} stories you saw"
    return f"You chose {label}"


def build_edition(reader_id: int, day: date, kind: str = "live", force: bool = False):
    with db.tx() as con:
        ex = con.execute("SELECT id, status FROM editions WHERE reader_id=? AND day=?", (reader_id, day.isoformat())).fetchone()
        if ex and not force:
            return ex["id"]
        reader = con.execute("SELECT id, name FROM readers WHERE id=?", (reader_id,)).fetchone()
        items, vecs = _load_items(con, day)
        if not items:
            log.error("no items for %s — no edition committed (F2)", day)
            return None
        tids, labels, tvecs = _topics(con, reader_id)
        prof = learn.profile(con, reader_id, day - timedelta(days=1))
    reader_topics = [t for t in prof.prior] or tids[:5]
    cands = rank.candidates(items, vecs, tids, tvecs, reader_topics, prof)
    stories = rank.select(rank.cluster(cands, items, vecs), prof, day, reader_id, tids, items, vecs, tvecs)

    members = {c["i"] for st in stories for c in st["members"]}
    with ThreadPoolExecutor(6) as ex:
        texts = dict(zip(members, ex.map(lambda i: retrieve.get_text(items[i]), members)))
    unreadable = sum(1 for t, _ in texts.values() if t is None)

    out = []
    for n, st in enumerate(stories):
        its = [items[c["i"]] for c in st["members"]]
        ktexts = {k: texts[c["i"]][0] for k, c in enumerate(st["members"]) if texts[c["i"]][0]}
        top = max(st["weights"], key=st["weights"].get)
        story = {
            "items": [{"url": it["url"], "domain": it["domain"], "title": it["title"], "source_time": it["source_time"],
                       "route": texts[c["i"]][1]} for it, c in zip(its, st["members"])],
            "image_url": next((it["image_url"] for it in its if it["image_url"]), None),
            "topic_weights": {str(t): round(w, 4) for t, w in st["weights"].items()},
            "topic": labels.get(top, ""), "why": _why(prof, top, labels.get(top, ""), st["exploring"]), "exploring": st["exploring"],
            "headline": its[0]["title"], "dek": (its[0]["description"] or "")[:280], "claims": [], "claims_total": 0, "status": "link_only",
        }
        if ktexts:
            image = retrieve.get_image(story["image_url"])
            try:
                s = synth.synthesize(its, ktexts, image, role="lead" if n == 0 else "synth")
                story.update(headline=s["headline"], dek=s["dek"], claims=s["claims"], claims_total=s["claims_total"],
                             image_note=s.get("image_note", ""), status="synthesized")
            except llm.LLMUnavailable as e:
                log.warning("synthesis unavailable (F3): %s", str(e)[:200])
                story["status"] = "summary_unavailable"
        out.append(story)

    # Presentation personalization (R2): lead = top story; sections ordered by interest strength.
    lead, rest = out[0], out[1:]
    order = sorted({s["topic"] for s in rest}, key=lambda lab: -max(prof.mean(t) for t, la in labels.items() if la == lab))
    sections = [{"topic": lab, "stories": [s for s in rest if s["topic"] == lab]} for lab in order]
    things = []
    syn = [f"{s['headline']}: {s['dek']}" for s in out if s["status"] == "synthesized"]
    if len(syn) >= 3:
        try:
            things = synth.three_things(syn)
        except llm.LLMUnavailable:
            things = []
    shown_topics = {t for st in stories for t in st["weights"]}
    empty = sorted(labels[t] for t in reader_topics if t not in shown_topics and t not in prof.muted_topics and t in labels)  # F6
    body = {"day": day.isoformat(), "kind": kind, "reader": reader["name"], "lead": lead, "sections": sections, "stories": out,
            "empty_topics": empty,
            "three_things": things, "sources_unavailable": unreadable, "generated": datetime.now(config.PKT).isoformat(timespec="minutes")}
    for k, s in enumerate(out):
        s["idx"] = k
    with db.tx() as con:
        if ex and force:
            con.execute("DELETE FROM editions WHERE id=?", (ex["id"],))
        cur = con.execute("INSERT INTO editions(reader_id,day,kind,status,body) VALUES (?,?,?,?,?)",
                          (reader_id, day.isoformat(), kind, "committed", json.dumps(body)))
        eid = cur.lastrowid
    render.pdf_for(eid)
    return eid
