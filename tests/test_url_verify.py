"""
SEDAS - URL Verification Test Suite
MIS5320 Part B | Test IDs TU-01..TU-03 traced to FR-03, FR-04

Note: the URL verification module is loaded explicitly by file path
rather than by module name, because both the URL verification and
training services expose a module named 'serve'. Importing by name
causes whichever service was imported first to be returned for both.
"""

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location(
    "url_verify_serve", ROOT / "services" / "url-verify" / "serve.py")
url_serve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(url_serve)

client = TestClient(url_serve.app)


def test_tu01_suspicious_url_flagged():
    """TU-01 (FR-03): risky URL gets findings and elevated score."""
    r = client.post("/verify",
                    json={"url": "http://a-b-c.suspicious.xyz/login/verify"})
    body = r.json()
    assert r.status_code == 200
    assert body["heuristic_risk_score"] >= 50
    assert len(body["findings"]) >= 2


def test_tu02_report_then_blocked():
    """TU-02 (FR-03/FR-04): reported-malicious URL returns blocked with proof."""
    url = "http://test-malicious-entry.example.xyz/account"
    client.post("/report", json={"url": url, "verdict": "malicious",
                                 "reported_by": "pytest"})
    r = client.post("/verify", json={"url": url})
    body = r.json()
    assert body["verdict"] == "blocked"
    assert body["registry_proof"] is not None


def test_tu03_chain_validates():
    """TU-03 (FR-04): full hash chain recomputes cleanly."""
    r = client.get("/chain/validate")
    assert r.json()["valid"] is True