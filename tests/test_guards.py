"""Guards must reject what they exist to reject (falsify-first)."""
from paper import llm


class _E(Exception):
    def __init__(self, code, msg=""):
        super().__init__(msg)
        self.code = code


def test_media_guard_rejects_html_error_page():
    assert not llm.valid_image(b"<html>403 Forbidden</html>" * 100, "text/html")


def test_media_guard_rejects_non_image_bytes_declared_as_image():
    assert not llm.valid_image(b"<html>403</html>" * 100, "image/jpeg")


def test_media_guard_accepts_jpeg():
    assert llm.valid_image(b"\xff\xd8\xff\xe0" + b"0" * 2000, "image/jpeg")


def test_error_classes():
    assert llm.classify(_E(429)) == "transient"
    assert llm.classify(_E(503)) == "transient"
    assert llm.classify(_E(400)) == "permanent"
    assert llm.classify(_E(401)) == "config"
    assert llm.classify(_E(418, "weird")) == "unknown"


def test_programming_errors_are_not_retryable():
    assert llm.classify(AttributeError("no attribute LLM_REQUEST_TIMEOUT_MS")) == "bug"


def test_network_timeouts_are_transient():
    import httpx

    assert llm.classify(httpx.ConnectTimeout("")) == "transient"
    assert llm.classify(httpx.ReadTimeout("")) == "transient"


def test_quota_hints_distinguish_daily_from_per_minute():
    daily = _E(429, "{'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'retryDelay': '39368s'}")
    minute = _E(429, "{'quotaId': 'GenerateRequestsPerMinutePerProjectPerModel-FreeTier', 'retryDelay': '23s'}")
    assert llm._retry_after(daily) == (39368.0, True)
    assert llm._retry_after(minute) == (23.0, False)
