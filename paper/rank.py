"""Per-reader rank -> cluster -> select. Every rule is relative (ranks, percentiles); no absolute cosine thresholds."""
import hashlib
import re
from collections import defaultdict

import numpy as np

from . import config
from .learn import Profile

STOP = {"this", "that", "with", "from", "have", "will", "what", "when", "where", "which", "their", "about", "after", "over", "into", "more", "than", "been", "were", "they", "them", "your", "says", "said", "news"}


def words(s):
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", s or "") if w.lower() not in STOP}


def rng_for(day, reader_id):
    return np.random.default_rng(int(hashlib.sha256(f"{day}:{reader_id}".encode()).hexdigest()[:12], 16))


def candidates(items, item_vecs, all_topic_ids, all_topic_vecs, reader_topics, prof: Profile):
    """Items attached to reader topics: t in the item's top-K topics AND item in the day's top-N for t."""
    sims = item_vecs @ all_topic_vecs.T  # items x all topics
    topk = np.argsort(-sims, axis=1)[:, : config.TOPIC_TOP_K]
    col = {t: j for j, t in enumerate(all_topic_ids)}
    attached = defaultdict(dict)  # item idx -> {topic: sim}
    for t in reader_topics:
        if t in prof.muted_topics or t not in col:
            continue
        j = col[t]
        eligible = np.where((topk == j).any(axis=1))[0]
        best = eligible[np.argsort(-sims[eligible, j])][: config.CANDIDATES_PER_TOPIC]
        for rank_pos, i in enumerate(best):  # relevance = rank within the topic, in (0, 1]; model-scale independent
            attached[int(i)][t] = (float(sims[i, j]), 1.0 - rank_pos / max(1, len(best)))
    out = []
    for i, tsims in attached.items():
        it = items[i]
        if it["domain"] in prof.muted_sources:
            continue
        total = sum(max(s, 1e-6) for s, _ in tsims.values())
        w = {t: max(s, 1e-6) / total for t, (s, _) in tsims.items()}
        score = prof.source_factor(it["domain"]) * sum(w[t] * prof.mean(t) * r for t, (_, r) in tsims.items())
        out.append({"i": i, "score": score, "weights": w})
    out.sort(key=lambda c: -c["score"])
    return out[: config.CANDIDATES_PER_READER]


def cluster(cands, items, item_vecs):
    """Union-find over pairs that are both semantically extreme (top percentile) and lexically overlapping."""
    if len(cands) < 2:
        return [[c] for c in cands]
    idx = [c["i"] for c in cands]
    v = item_vecs[idx]
    s = v @ v.T
    iu = np.triu_indices(len(idx), 1)
    cut = np.percentile(s[iu], config.CLUSTER_PERCENTILE)
    parent = list(range(len(idx)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    toks = [words(items[i]["title"]) for i in idx]
    for a, b in zip(*iu):
        if s[a, b] >= cut:
            j = len(toks[a] & toks[b]) / max(1, len(toks[a] | toks[b]))
            if j >= config.CLUSTER_MIN_JACCARD:
                parent[find(a)] = find(b)
    groups = defaultdict(list)
    for k, c in enumerate(cands):
        groups[find(k)].append(c)
    stories = []
    for g in groups.values():
        g.sort(key=lambda c: -c["score"])
        seen_dom, members = set(), []
        for c in g:  # one item per publisher per story
            d = items[c["i"]]["domain"]
            if d not in seen_dom:
                members.append(c)
                seen_dom.add(d)
        stories.append({"members": members[:4], "score": g[0]["score"], "weights": g[0]["weights"]})
    stories.sort(key=lambda st: -st["score"])
    return stories


def select(stories, prof: Profile, day, reader_id, all_topic_ids, items, item_vecs, all_topic_vecs):
    chosen, per_topic = [], defaultdict(int)
    main_slots = config.EDITION_SIZE - config.EXPLORE_SLOTS
    for st in stories:
        top = max(st["weights"], key=st["weights"].get)
        if per_topic[top] >= config.MAX_PER_TOPIC:
            continue
        chosen.append({**st, "exploring": False})
        per_topic[top] += 1
        if len(chosen) >= main_slots:
            break
    # Exploring slots: Thompson draw over topics the reader has not chosen; best item of the winning topic.
    rng = rng_for(day, reader_id)
    used = {c["i"] for st in chosen for c in st["members"]}
    others = [t for t in all_topic_ids if t not in prof.prior and t not in prof.muted_topics]
    draws = sorted(others, key=lambda t: -rng.beta(*prof.ab(t)))
    col = {t: j for j, t in enumerate(all_topic_ids)}
    for t in draws[: config.EXPLORE_SLOTS]:
        sims = item_vecs @ all_topic_vecs[col[t]]
        for i in np.argsort(-sims)[:50]:
            i = int(i)
            in_topk = col[t] in np.argsort(-(item_vecs[i] @ all_topic_vecs.T))[: config.TOPIC_TOP_K]  # same relative rule as candidates
            if in_topk and i not in used and items[i]["domain"] not in prof.muted_sources:
                chosen.append({"members": [{"i": i, "score": 0.0, "weights": {t: 1.0}}], "score": 0.0, "weights": {t: 1.0}, "exploring": True})
                used.add(i)
                break
    return chosen
