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