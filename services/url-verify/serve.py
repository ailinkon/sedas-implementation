"""
SEDAS - URL Verification Service
MIS5320 Part B | Traceability: FR-03, FR-04 | Refinement R-01
Tamper-evident, hash-chained URL registry (blockchain-concept PoC)
plus heuristic URL risk analysis. Runs on port 8002.
"""

import hashlib
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from pydantic import BaseModel

DB_PATH = Path(__file__).parent / "registry.db"

app = FastAPI(
    title="SEDAS URL Verification Service",
    description="Verifies URLs against a tamper-evident hash-chained "
                "registry and heuristic risk analysis (FR-03, FR-04, R-01).",
    version="0.1.0",
)

# ---------- Hash-chain registry (FR-04) ----------

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        verdict TEXT NOT NULL,
        reported_by TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        prev_hash TEXT NOT NULL,
        entry_hash TEXT NOT NULL)""")
    return conn

def compute_hash(url, verdict, reported_by, timestamp, prev_hash):
    payload = json.dumps([url, verdict, reported_by, timestamp, prev_hash])
    return hashlib.sha256(payload.encode()).hexdigest()

def last_hash(conn):
    row = conn.execute(
        "SELECT entry_hash FROM registry ORDER BY id DESC LIMIT 1").fetchone()
    return row[0] if row else "GENESIS"

def add_entry(url, verdict, reported_by):
    conn = db()
    ts = datetime.now(timezone.utc).isoformat()
    prev = last_hash(conn)
    h = compute_hash(url, verdict, reported_by, ts, prev)
    conn.execute(
        "INSERT INTO registry (url, verdict, reported_by, timestamp, "
        "prev_hash, entry_hash) VALUES (?,?,?,?,?,?)",
        (url, verdict, reported_by, ts, prev, h))
    conn.commit()
    conn.close()
    return h

# ---------- Heuristic risk analysis (FR-03) ----------

SUSPICIOUS_TLDS = {".zip", ".xyz", ".top", ".click", ".loan", ".work",
                   ".gq", ".tk", ".ml", ".cf", ".ga"}
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
                  "is.gd", "buff.ly", "rebrand.ly"}
KEYWORD_FLAGS = ("login", "verify", "secure", "account", "update",
                 "confirm", "password", "banking", "suspend")

def analyse_url(url: str):
    findings = []
    score = 0
    parsed = urlparse(url if "://" in url else "http://" + url)
    host = (parsed.hostname or "").lower()

    if parsed.scheme == "http":
        findings.append("No HTTPS (unencrypted)"); score += 15
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host or ""):
        findings.append("Raw IP address instead of domain"); score += 30
    if "@" in url:
        findings.append("'@' symbol can hide the real destination"); score += 25
    if host.count("-") >= 2:
        findings.append("Multiple hyphens in domain"); score += 10
    if host.count(".") >= 4:
        findings.append("Excessive subdomain depth"); score += 15
    if any(host.endswith(t) for t in SUSPICIOUS_TLDS):
        findings.append("High-risk top-level domain"); score += 20
    if host in URL_SHORTENERS:
        findings.append("URL shortener obscures destination"); score += 20
    if len(url) > 90:
        findings.append("Unusually long URL"); score += 10
    kw = [k for k in KEYWORD_FLAGS if k in url.lower()]
    if kw:
        findings.append(f"Credential-lure keywords: {', '.join(kw)}")
        score += 10 * min(len(kw), 3)
    return min(score, 100), findings

# ---------- API models ----------

class URLIn(BaseModel):
    url: str

class ReportIn(BaseModel):
    url: str
    verdict: str          # "malicious" or "safe"
    reported_by: str = "analyst"

# ---------- Endpoints ----------

@app.post("/verify")
def verify(item: URLIn):
    start = time.perf_counter()
    conn = db()
    row = conn.execute(
        "SELECT verdict, timestamp, entry_hash FROM registry "
        "WHERE url = ? ORDER BY id DESC LIMIT 1", (item.url,)).fetchone()
    conn.close()

    risk_score, findings = analyse_url(item.url)
    registry_status = row[0] if row else "unknown"
    if registry_status == "malicious":
        verdict = "blocked"
    elif registry_status == "safe" and risk_score < 50:
        verdict = "trusted"
    elif risk_score >= 50:
        verdict = "suspicious"
    else:
        verdict = "low_risk"

    return {
        "url": item.url,
        "verdict": verdict,
        "registry_status": registry_status,
        "registry_proof": row[2] if row else None,
        "heuristic_risk_score": risk_score,
        "findings": findings,
        "latency_ms": round((time.perf_counter() - start) * 1000, 1),
    }

@app.post("/report")
def report(item: ReportIn):
    h = add_entry(item.url, item.verdict, item.reported_by)
    return {"recorded": True, "entry_hash": h}

@app.get("/chain/validate")
def validate_chain():
    """Walks the whole chain recomputing hashes — proves tamper-evidence (FR-04)."""
    conn = db()
    rows = conn.execute(
        "SELECT url, verdict, reported_by, timestamp, prev_hash, entry_hash "
        "FROM registry ORDER BY id").fetchall()
    conn.close()
    prev = "GENESIS"
    for i, (url, verdict, rep, ts, prev_hash, entry_hash) in enumerate(rows, 1):
        if prev_hash != prev or compute_hash(url, verdict, rep, ts, prev_hash) != entry_hash:
            return {"valid": False, "broken_at_entry": i, "entries": len(rows)}
        prev = entry_hash
    return {"valid": True, "entries": len(rows)}

@app.get("/health")
def health():
    return {"status": "ok", "service": "url-verify"}