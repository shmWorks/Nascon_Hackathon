"""Profile = deterministic fold of the event log into Beta posteriors per topic and per source (state.md: learning).

One binary outcome per seen story impression. Engaged (1): click-through, save, "more like this", or in-app
dwell >= tau. Not engaged (0): seen with none of those, skip, or "less like this". Credit goes to the story's
topics with the same weights ranking used (stored in the edition at commit), so ranking and learning cannot drift.
"""
import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from . import config

POSITIVE = {"click", "save", "more"}
NEGATIVE = {"skip", "less"}
MIN_DWELL_S = 15.0  # floor for tau; tau = max(floor, reader's median dwell)


@dataclass
class Profile:
    prior: dict[int, tuple[float, float]]
    alpha: dict[int, float] = field(default_factory=dict)
    beta: dict[int, float] = field(default_factory=dict)
    src_a: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    src_n: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    muted_topics: set = field(default_factory=set)
    muted_sources: set = field(default_factory=set)
    evidence: dict[int, list] = field(default_factory=lambda: defaultdict(list))

    def mean(self, t):
        a0, b0 = self.prior.get(t, self._other())
        return self.alpha.get(t, a0) / (self.alpha.get(t, a0) + self.beta.get(t, b0))

    def ab(self, t):
        a0, b0 = self.prior.get(t, self._other())
        return self.alpha.get(t, a0), self.beta.get(t, b0)

    @staticmethod
    def _other():
        return config.PRIOR_MEAN_OTHER * config.PRIOR_STRENGTH, (1 - config.PRIOR_MEAN_OTHER) * config.PRIOR_STRENGTH

    def source_factor(self, domain):
        n = self.src_n.get(domain, 0.0)
        tot_a, tot_n = sum(self.src_a.values()), sum(self.src_n.values())
        if n == 0 or tot_n == 0:
            return 1.0
        g = (tot_a + 1) / (tot_n + 2)
        s = (self.src_a[domain] + g * config.PRIOR_STRENGTH) / (n + config.PRIOR_STRENGTH)
        lo, hi = config.SOURCE_FACTOR_CLIP
        return min(hi, max(lo, s / g))


def profile(con, reader_id: int, as_of: date) -> Profile:
    n = config.PRIOR_STRENGTH
    prior = {}
    for r in con.execute("SELECT topic_id, mode FROM reader_topics WHERE reader_id=?", (reader_id,)):
        m = config.PRIOR_MEAN_CHOSEN if r["mode"] in ("chosen", "follow") else config.PRIOR_MEAN_OTHER
        prior[r["topic_id"]] = (m * n, (1 - m) * n)
    p = Profile(prior=prior)
    for r in con.execute("SELECT topic_id FROM reader_topics WHERE reader_id=? AND mode='mute'", (reader_id,)):
        p.muted_topics.add(r["topic_id"])
    rows = con.execute(
        "SELECT e.day, e.type, e.edition_id, e.story_idx, e.payload, ed.body FROM events e "
        "LEFT JOIN editions ed ON ed.id = e.edition_id WHERE e.reader_id=? AND e.day<=? ORDER BY e.day, e.id",
        (reader_id, as_of.isoformat()),
    ).fetchall()
    dwells = [json.loads(r["payload"]).get("seconds", 0) for r in rows if r["type"] == "dwell"]
    tau = max(MIN_DWELL_S, statistics.median(dwells)) if dwells else MIN_DWELL_S
    outcomes: dict[tuple, dict] = {}
    for r in rows:
        if r["type"] == "mute_source":
            p.muted_sources.add(json.loads(r["payload"]).get("domain"))
            continue
        if r["edition_id"] is None or r["story_idx"] is None:
            continue
        o = outcomes.setdefault((r["day"], r["edition_id"], r["story_idx"]), {"seen": False, "y": None, "body": r["body"]})
        if r["type"] == "seen":
            o["seen"] = True
        elif r["type"] in POSITIVE or (r["type"] == "dwell" and json.loads(r["payload"]).get("seconds", 0) >= tau):
            o["y"], o["seen"] = 1, True
        elif r["type"] in NEGATIVE and o["y"] != 1:
            o["y"], o["seen"] = 0, True
    gamma = 2 ** (-1 / config.DECAY_HALF_LIFE_DAYS)
    last_day = None
    for (day, _, idx), o in sorted(outcomes.items()):
        if not o["seen"] or not o["body"]:
            continue
        d = date.fromisoformat(day)
        if last_day and d > last_day:  # decay toward the prior between days
            k = gamma ** (d - last_day).days
            for t in list(p.alpha):
                a0, b0 = p.prior.get(t, p._other())
                p.alpha[t] = a0 + k * (p.alpha[t] - a0)
                p.beta[t] = b0 + k * (p.beta[t] - b0)
        last_day = d
        story = json.loads(o["body"])["stories"][idx]
        y = o["y"] or 0
        for t, w in story["topic_weights"].items():
            t = int(t)
            a, b = p.ab(t)
            p.alpha[t], p.beta[t] = a + w * y, b + w * (1 - y)
            p.evidence[t].append(y)
        dom = story["items"][0]["domain"]
        p.src_a[dom] += y
        p.src_n[dom] += 1
    return p
