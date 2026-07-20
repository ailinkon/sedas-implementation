"""
SEDAS - URL Verification Test Suite
MIS5320 Part B | TU-01..TU-03 traced to FR-03, FR-04
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "url-verify"))

from fastapi.testclient import TestClient
import serve
client = TestClient(serve.app)


def test_tu01_suspicious_url_flagged():
    """TU-01 (FR-03): risky URL gets findings and elevated score."""
    r = client.post("/verify", json={"url": "http://a-b-c.suspicious.xyz/login/verify"})
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