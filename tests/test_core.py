"""Behavior at public seams: citation verification, retrieval acceptance, learning fold, ranking relativity."""
import json

import numpy as np

from paper import learn, rank, retrieve, synth

TEXT = "The Pakistan team won the third Test in Karachi by five wickets after a record chase on the final day."


def test_verify_keeps_quote_present_in_cited_item():
    c = {"text": "Pakistan won.", "item_ids": [0], "quote": "won the third Test in Karachi by five wickets"}
    assert synth.verify([c], {0: TEXT}) == [c]


def test_verify_drops_fabricated_quote():
    c = {"text": "Pakistan lost.", "item_ids": [0], "quote": "lost the third Test in Karachi by an innings"}
    assert synth.verify([c], {0: TEXT}) == []


def test_verify_drops_quote_cited_to_wrong_item():
    c = {"text": "x", "item_ids": [1], "quote": "won the third Test in Karachi by five wickets"}
    assert synth.verify([c], {0: TEXT, 1: "Unrelated text about markets and bonds today."}) == []


def test_retrieval_accepts_body_matching_title():
    body = (TEXT + " ") * 20
    assert retrieve.validate(body, "Pakistan win third Test in Karachi by five wickets")


def test_retrieval_rejects_other_article_and_challenge_page():
    other = "Oil prices fell sharply as investors weighed supply data from producers. " * 20
    assert not retrieve.validate(other, "Pakistan win third Test in Karachi by five wickets")
    assert not retrieve.validate("Just a moment... Checking your browser", "Pakistan win third Test in Karachi")


def _profile_with(events):
    """Build a profile from an in-memory edition and events using the real fold."""
    import sqlite3

    from paper import db

    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(db.SCHEMA)
    con.execute("INSERT INTO readers(id,email,name,pw_hash) VALUES (1,'a@b.c','A','x')")
    con.execute("INSERT INTO reader_topics(reader_id,topic_id,mode) VALUES (1,10,'chosen'),(1,20,'chosen')")
    stories = [{"topic_weights": {"10": 1.0}, "items": [{"domain": "a.com"}]}, {"topic_weights": {"20": 1.0}, "items": [{"domain": "b.com"}]}]
    con.execute("INSERT INTO editions(id,reader_id,day,kind,status,body) VALUES (1,1,'2026-10-10','backfilled','committed',?)", (json.dumps({"stories": stories}),))
    for typ, idx in events:
        con.execute("INSERT INTO events(reader_id,ts,day,type,edition_id,story_idx) VALUES (1,'t','2026-10-10',?,1,?)", (typ, idx))
    from datetime import date

    return learn.profile(con, 1, date(2026, 10, 11))


def test_engagement_raises_topic_and_skip_lowers_it():
    base = _profile_with([])
    p = _profile_with([("seen", 0), ("click", 0), ("seen", 1), ("skip", 1)])
    assert p.mean(10) > base.mean(10)
    assert p.mean(20) < base.mean(20)


def test_unseen_story_teaches_nothing():
    base = _profile_with([])
    assert _profile_with([]).mean(10) == base.mean(10)
    p = _profile_with([("seen", 0)])  # seen without action = not engaged
    assert p.mean(10) < base.mean(10)
    assert p.mean(20) == base.mean(20)  # story 1 never seen: no credit either way


def test_candidates_rule_is_scale_invariant():
    rng = np.random.default_rng(0)
    items = [{"title": f"t{i}", "domain": "x.com"} for i in range(40)]
    v = rng.normal(size=(40, 8)).astype(np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    tv = rng.normal(size=(5, 8)).astype(np.float32)
    tv /= np.linalg.norm(tv, axis=1, keepdims=True)
    prof = learn.Profile(prior={0: (1.2, 2.8), 1: (1.2, 2.8)})
    a = [c["i"] for c in rank.candidates(items, v, [0, 1, 2, 3, 4], tv, [0, 1], prof)]
    b = [c["i"] for c in rank.candidates(items, v, [0, 1, 2, 3, 4], tv * 3.0, [0, 1], prof)]  # rescaled similarity
    assert a == b
