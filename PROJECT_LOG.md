# SEDAS Part B — Project Log
MIS5320 Applied IS Project – Part B

## Entry 1 — 9 July 2026
**Meeting/attendees:**
**Decisions made (with justification):**
- Created dedicated Part B repository for a clean implementation history; Part A design artefacts remain in the original repository.
- Repository set to private during the assessment period (academic integrity); to be made public after grade release.
**Work completed:** Repository structure established (microservice layout per Implementation Project Plan Section 4).
**Ethics/security/privacy notes:** No secrets committed; .env.example pattern adopted.
**Tools/AI/code sources used (with reflection):** Claude used for planning documents and repo structure guidance; structure reviewed and created manually by the team.
**Problems & resolutions:**
**Next steps:** CI workflow, dataset acquisition for detection service.

## Entry 2 — 9 July 2026
**Work completed:** Baseline phishing detection model trained (FR-01, NFR-01).
Dataset: Kaggle combined phishing corpus (Nazario, Enron, SpamAssassin, CEAS, Ling, Nigerian), 82,486 emails, 80/20 stratified split.
Pipeline: TF-IDF (50k features, 1-2 grams) + Logistic Regression (balanced class weights).
**Results on 16,498 held-out emails:** Accuracy 0.9859, Precision 0.9867, Recall 0.9862, F1 0.9865 (target >=0.95: MET), FP rate 0.0144 (target <0.02: MET). Confusion: TN=7805 FP=114 FN=118 TP=8461.
**Reflection:** Results are on public research corpora; live institutional traffic would likely show lower performance (domain shift). DistilBERT comparison planned per Implementation Plan.
**Tools/AI/code sources:** scikit-learn, pandas; training script scaffolded with Claude, reviewed and executed by the team.
**Next steps:** Wrap model in FastAPI /classify endpoint with explainability.

## Entry 3 — 9 July 2026
**Work completed:** /classify REST API implemented (FastAPI) exposing the baseline model with explainability — returns label, risk score 0-100, top contributing indicators, and latency (FR-01, FR-02, FR-09). Auto-generated OpenAPI documentation at /docs. /health endpoint added for service monitoring.
**Testing:** Manual functional test — phishing sample scored ~9X/100 with indicators (urgent, click, verify); legitimate sample scored 0.85/100. Measured latency ~11 ms vs NFR-03 target < 2,000 ms (target met by >100x on CPU hardware). Evidence screenshots in docs/evidence/.
**Tools/AI/code sources:** FastAPI, uvicorn, joblib; API scaffolded with Claude, reviewed and tested by the team.
**Next steps:** pytest unit tests for the endpoint; URL verification service.

## Entry 4 — 9 July 2026
**Team formation:** Following Dr Chandana's Week 1 email, group formation initiated. Huzaifa Iqbal (240220) confirmed as team member; recruitment of 1–2 further members in progress. Project confirmed as SEDAS (implementation of A. Islam's Part A design) per unit requirement. Consultation slot: Thursdays 11:30.
**Next steps:** Confirm final team to Dr Chandana; assign modules per RACI; Week 1 LOG submission Sunday.

## Entry 5 — 9 July 2026
**Work completed:** Automated test suite created (TD-01..TD-05) covering health, phishing detection, legitimate pass-through, explainability, and latency — all 5 passing (4.3s). Tests traced to FR-01, FR-02, FR-09, NFR-03. GitHub Actions CI pipeline added: pytest runs on every push/PR. Suite auto-skips on machines without the trained model (model and dataset are intentionally excluded from the repo); CI validates imports and harness.
**Tools/AI/code sources:** pytest, FastAPI TestClient; suite scaffolded with Claude, executed and verified by the team.
**Next steps:** Onboard team members to repo; Week 1 LOG submission; URL verification service (Sprint 1).


## Entry 6 — 16 July 2026
**Consultation:** Supervisor consultation held (Minutes #1 in docs/minutes/). Key directives: recent-paper benchmark on a shared dataset; Week 3 = combined Wk2+3 log + two minutes; Week 4 preliminary results; Week 5 individual walk-throughs; Week 6 final results; work split across members; supervisor to be added to GitHub for random checks.
**Work completed:** Benchmark identified — the dataset's own source paper (Al-Subaiey et al. 2024, CEE 120:109625; TF-IDF+SVM, F1 0.99 on the identical 82.5k corpus). SVM replication implemented and run: F1 0.9916, FP rate 0.0095 (TN=7844 FP=75 FN=70 TP=8509) — matches the published benchmark, validating the pipeline. Benchmark justification document prepared, incl. Part A parameter linkage.
**Tools/AI/code sources:** scikit-learn LinearSVC; comparison script scaffolded with Claude, executed and verified by the team; benchmark paper verified via web search.
**Next steps:** Team meeting #1 (module allocation → Minutes #2); URL verification service; teammate onboarding commits.


## Entry 7 — 20 July 2026
**Work completed:** URL Verification Service implemented (FR-03, FR-04, refinement R-01): heuristic risk analysis (HTTPS, IP-literal, hyphens, subdomain depth, high-risk TLDs, shorteners, credential-lure keywords), SHA-256 hash-chained append-only registry (SQLite), /verify, /report, /chain/validate and /health endpoints on port 8002. Functional demo: suspicious URL scored 75/100 with 4 findings (~1.4–9.3 ms); after malicious report, verdict flipped to blocked with chain proof; /chain/validate returned valid=true. Tests TU-01..TU-03 added (model-free — CI now executes real assertions). registry.db excluded from version control.
**Design note:** Append-only ledger semantics — reports are never overwritten; latest verdict governs lookup; chain validation recomputes every hash to prove tamper-evidence, preserving the Part A blockchain design intent without Ethereum (R-01 justification).
**Tools/AI/code sources:** FastAPI, hashlib, sqlite3; service scaffolded with Claude, executed, demonstrated and verified by the team.
**Next steps:** Team meeting #1 + Minutes #2; frontend demo page; combined Wk2+3 log.