"""The app must start from a clean checkout: every packaged data file exists, parses and is consistent.

Regression: `.gitignore` once ignored `paper/data/` (unanchored `data/`), so a clean deploy crashed at import.
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

DATA = Path(__file__).resolve().parent.parent / "paper" / "data"


def test_packaged_data_files_exist_and_are_consistent():
    topics = json.loads((DATA / "topics.json").read_text(encoding="utf-8"))
    feeds = json.loads((DATA / "feeds.json").read_text(encoding="utf-8"))
    groups = json.loads((DATA / "topic_groups.json").read_text(encoding="utf-8"))
    slugs = {t[0] for t in topics}
    grouped = [s for _, ss in groups for s in ss]
    assert topics and feeds and groups
    assert set(grouped) <= slugs, "topic_groups.json names a topic missing from topics.json"
    assert len(grouped) == len(set(grouped)), "a topic appears in two groups"


def test_app_imports_and_serves_from_clean_state():
    from paper import web

    c = TestClient(web.app)
    assert c.get("/healthz").json() == {"ok": True}
    assert c.get("/").status_code == 200
    assert c.get("/login").status_code == 200
