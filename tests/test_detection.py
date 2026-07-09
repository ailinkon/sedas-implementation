"""
SEDAS - Detection Service Test Suite
MIS5320 Part B | Test IDs TD-01..TD-05 traced to FR-01, FR-02, FR-09, NFR-03
Run: pytest tests/ -v
"""

import pytest
from pathlib import Path

MODEL = Path("services/detection/model.joblib")

# Skip the whole suite if the model hasn't been trained on this machine
# (e.g. a fresh clone or CI runner - model and data are not in the repo)
pytestmark = pytest.mark.skipif(
    not MODEL.exists(), reason="model.joblib not present - run train.py first"
)

if MODEL.exists():
    from fastapi.testclient import TestClient
    from services.detection.serve import app
    client = TestClient(app)

PHISHING_TEXT = ("URGENT: Your account will be suspended. "
                 "Click here to verify your password immediately.")
LEGIT_TEXT = ("Hi team, attached are the minutes from Monday's meeting. "
              "See you Thursday.")


def test_td01_health_endpoint():
    """TD-01 (FR-09): service reports healthy."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_td02_phishing_detected():
    """TD-02 (FR-01): obvious phishing is labelled phishing with high score."""
    r = client.post("/classify", json={"text": PHISHING_TEXT})
    body = r.json()
    assert r.status_code == 200
    assert body["label"] == "phishing"
    assert body["risk_score"] > 70


def test_td03_legitimate_passed():
    """TD-03 (FR-01): normal email is labelled legitimate with low score."""
    r = client.post("/classify", json={"text": LEGIT_TEXT})
    body = r.json()
    assert body["label"] == "legitimate"
    assert body["risk_score"] < 30


def test_td04_explainability_present():
    """TD-04 (FR-02): phishing result includes contributing indicators."""
    r = client.post("/classify", json={"text": PHISHING_TEXT})
    assert len(r.json()["top_indicators"]) >= 1


def test_td05_latency_within_nfr():
    """TD-05 (NFR-03): classification completes within 2000 ms."""
    r = client.post("/classify", json={"text": PHISHING_TEXT})
    assert r.json()["latency_ms"] < 2000