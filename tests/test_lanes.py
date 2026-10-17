"""Key/model lane failover: quota hits and bad keys move to the next lane; nothing is retried blindly."""
import pytest

from paper import config, llm


class Quota(Exception):
    code = 429


class BadKey(Exception):
    code = 400

    def __str__(self):
        return "API key not valid"


class FakeModels:
    def __init__(self, ki, behaviour, calls):
        self.ki, self.behaviour, self.calls = ki, behaviour, calls

    def generate_content(self, model, contents, config):
        self.calls.append((model, self.ki))
        outcome = self.behaviour.get((model, self.ki), "ok")
        if outcome == "day":
            raise Quota("{'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'retryDelay': '39000s'}")
        if outcome == "minute":
            raise Quota("{'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'retryDelay': '20s'}")
        if outcome == "badkey":
            raise BadKey()
        return type("R", (), {"text": '{"ok": true}'})()


@pytest.fixture
def lanes(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CACHE", tmp_path)
    monkeypatch.setattr(config, "GEMINI_API_KEYS", ["k1", "k2", "k3"])
    monkeypatch.setattr(config, "MODELS", {"synth": ["m-a", "m-b"]})
    llm._cooling.clear()
    calls, behaviour = [], {}
    monkeypatch.setattr(llm, "client", lambda ki=0: type("C", (), {"models": FakeModels(ki, behaviour, calls)})())
    return calls, behaviour


def test_daily_quota_on_first_key_fails_over_to_second_key_same_model(lanes):
    calls, behaviour = lanes
    behaviour[("m-a", 0)] = "day"
    assert llm.generate_json("synth", "p1", dict) == {"ok": True}
    assert calls == [("m-a", 0), ("m-a", 1)]
    calls.clear()
    llm.generate_json("synth", "p2", dict)  # cooled lane is skipped without spending a request
    assert calls == [("m-a", 1)]


def test_per_minute_quota_moves_on_instead_of_sleeping(lanes):
    calls, behaviour = lanes
    behaviour[("m-a", 0)] = "minute"
    llm.generate_json("synth", "p3", dict)
    assert calls == [("m-a", 0), ("m-a", 1)]


def test_invalid_key_disables_only_that_key(lanes):
    calls, behaviour = lanes
    behaviour[("m-a", 0)] = "badkey"
    llm.generate_json("synth", "p4", dict)
    calls.clear()
    llm.generate_json("synth", "p5", dict)
    assert all(ki != 0 for _, ki in calls)


def test_all_lanes_exhausted_raises_for_f3_fallback(lanes):
    calls, behaviour = lanes
    for m in ("m-a", "m-b"):
        for ki in range(3):
            behaviour[(m, ki)] = "day"
    with pytest.raises(llm.LLMUnavailable):
        llm.generate_json("synth", "p6", dict)
    assert len(calls) == 6
