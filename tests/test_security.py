"""
SEDAS - Security and Negative-Case Test Suite
MIS5320 Part B | Test IDs TS-01..TS-06 traced to NFR-05 (security)

These tests verify defensive behaviour rather than happy-path function:
that malformed input is rejected safely, that injection metacharacters
cannot corrupt stored data, that answer keys are not leaked to clients,
and that services fail with descriptive errors rather than crashing.

Run: pytest tests/ -v
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "services" / "url-verify"))
sys.path.insert(0, str(ROOT / "services" / "training"))

import serve as training_serve  # noqa: E402

# The URL verification service module is loaded separately because both
# services expose a module named 'serve'.
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "url_verify_serve", ROOT / "services" / "url-verify" / "serve.py")
url_serve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(url_serve)

url_client = TestClient(url_serve.app)
training_client = TestClient(training_serve.app)


# ---------------------------------------------------------------
# TS-01 - SQL injection resistance (NFR-05)
# ---------------------------------------------------------------

def test_ts01_sql_metacharacters_handled_safely():
    """TS-01 (NFR-05): a URL containing SQL metacharacters is stored as
    literal text via parameterised queries, and the registry chain
    remains valid afterwards - demonstrating no injection occurred."""
    malicious = "http://evil.example/'; DROP TABLE registry;--"

    response = url_client.post("/report", json={
        "url": malicious, "verdict": "malicious", "reported_by": "pytest"})
    assert response.status_code == 200
    assert response.json()["recorded"] is True

    # The registry must still exist and validate - proving the table was
    # not dropped and the chain was not corrupted.
    chain = url_client.get("/chain/validate")
    assert chain.status_code == 200
    assert chain.json()["valid"] is True

    # The URL must be retrievable exactly as submitted, not executed.
    verify = url_client.post("/verify", json={"url": malicious})
    assert verify.status_code == 200
    assert verify.json()["registry_status"] == "malicious"


# ---------------------------------------------------------------
# TS-02 - empty and malformed input (NFR-05)
# ---------------------------------------------------------------

def test_ts02_empty_input_handled_gracefully():
    """TS-02 (NFR-05): empty input returns a structured response rather
    than raising an unhandled server error."""
    response = url_client.post("/verify", json={"url": ""})
    assert response.status_code == 200
    assert "verdict" in response.json()


def test_ts02b_malformed_request_rejected_with_422():
    """TS-02 (NFR-05): a request missing a required field is rejected
    with HTTP 422 and a descriptive validation error, not a 500."""
    response = url_client.post("/verify", json={"wrong_field": "value"})
    assert response.status_code == 422
    assert "detail" in response.json()


# ---------------------------------------------------------------
# TS-03 - unknown resource handling (NFR-05)
# ---------------------------------------------------------------

def test_ts03_unknown_user_returns_404_not_500():
    """TS-03 (NFR-05): submitting for a non-existent user returns a
    404 with a clear message rather than a server error."""
    response = training_client.post("/submit", json={
        "username": "no_such_user_exists_12345",
        "lesson_code": "SE-101",
        "answers": {"1": "a"}})
    assert response.status_code == 404
    assert "detail" in response.json()


def test_ts03b_unknown_lesson_returns_404():
    """TS-03 (NFR-05): requesting a quiz for a non-existent lesson code
    returns 404 rather than an empty success response."""
    response = training_client.get("/lessons/NO-SUCH-CODE/quiz")
    assert response.status_code == 404


# ---------------------------------------------------------------
# TS-04 - answer key confidentiality (NFR-05)
# ---------------------------------------------------------------

def test_ts04_quiz_does_not_leak_correct_answers():
    """TS-04 (NFR-05): the quiz endpoint returns prompts and options
    only. Correct answers and explanations are withheld so a client
    cannot inspect them before submitting."""
    response = training_client.get("/lessons/SE-101/quiz")
    assert response.status_code == 200

    body = response.json()
    for question in body["questions"]:
        assert "correct" not in question
        assert "explanation" not in question
        # The fields a legitimate client does need must still be present
        assert "prompt" in question
        assert "option_a" in question


# ---------------------------------------------------------------
# TS-05 - service liveness (NFR-05)
# ---------------------------------------------------------------

def test_ts05_health_endpoints_respond():
    """TS-05 (NFR-05): each service exposes a health endpoint reporting
    operational status, supporting monitoring in deployment."""
    for client, service_name in ((url_client, "url-verify"),
                                 (training_client, "training")):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == service_name


# ---------------------------------------------------------------
# TS-06 - registry tamper-evidence (FR-04, NFR-05)
# ---------------------------------------------------------------

def test_ts06_chain_remains_valid_across_multiple_writes():
    """TS-06 (FR-04, NFR-05): the hash chain remains verifiable after
    successive writes, confirming each new entry correctly links to its
    predecessor rather than breaking the chain."""
    before = url_client.get("/chain/validate").json()
    assert before["valid"] is True

    for i in range(3):
        url_client.post("/report", json={
            "url": f"http://chain-test-{i}.example/path",
            "verdict": "malicious", "reported_by": "pytest"})

    after = url_client.get("/chain/validate").json()
    assert after["valid"] is True
    assert after["entries"] == before["entries"] + 3
