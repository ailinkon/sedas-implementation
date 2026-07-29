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


## Entry 8 — 20 July 2026
**Work completed:** Frontend live demo page implemented (frontend/demo.html): email analysis and URL verification cards calling both services, with verdict badges, risk scores, indicator/finding chips, registry proof display and latency readout. CORS middleware added to both services (permissive for local demo; origin restriction listed for Week 6 security hardening). End-to-end demo verified: phishing 98.07/100 (10.8 ms), legitimate 0.85/100 (7 ms), reported URL returned BLOCKED 75/100 with chain proof (1.4 ms). Evidence in docs/evidence/.
**Tools/AI/code sources:** Vanilla HTML/CSS/JS (no framework — deliberate for demo reliability; React dashboard to follow); page scaffolded with Claude, tested and verified by the team.
**Next steps:** Training module skeleton (Dominic); awareness content drafting (Sonu); CORS restriction + security review items (Huzaifa); dashboard charts.


## Entry 9 — [today's date]
**Supervisor directive:** Run ALL methods used in benchmark paper [41], not just one, then explore methods beyond it (e.g. XGBoost). Web frontend explicitly does not count toward marks — real ML execution and explanation is the priority. Every team member must be able to run and explain the model execution, not just the theory.
**Work completed:** Replicated all three of [41]'s models on the identical dataset: SVC/LinearSVC (F1 99.16%, paper 99.0%, +0.16), Random Forest (F1 98.71%, paper 98.0%, +0.71), Multinomial NB (F1 97.47%, paper 98.0%, -0.53). SEDAS Logistic Regression baseline (not in paper): F1 98.65%.
**Analysis:** SVC is the strongest model for both the paper and SEDAS, consistent with paper's own conclusion. MNB underperforms on recall (95.93% vs ~98-99% for others, 349 false negatives) - independence assumption between features likely too strong for this text data. RF and SVC both exceed the paper, suggesting our TF-IDF configuration (50k features, 1-2 grams, balanced class weights) is at least as effective as the original.
**Next steps:** XGBoost comparison (method beyond the paper); team teach-in session so all members can run and explain compare_models.py; Minutes #3 for this consultation.


## Entry 10 — [today's date]
**Work completed:** Added XGBoost (200 estimators, max_depth 6) as the "beyond the paper" method per supervisor directive. Full 5-model comparison complete on identical 82,486-email corpus: SVC F1 99.16% (paper 99.0%, +0.16), Random Forest F1 98.71% (paper 98.0%, +0.71), Logistic Regression F1 98.65% (not in paper), XGBoost F1 97.56% (not in paper), Multinomial NB F1 97.47% (paper 98.0%, -0.53).
**Analysis:** XGBoost did not outperform the linear/paper methods. Its false-positive count (324) is markedly higher than SVC (75) or Random Forest (103) despite comparable recall — likely overfitting on the high-dimensional sparse TF-IDF feature space (50,000 mostly-zero features) without hyperparameter tuning, whereas linear methods (SVC, Logistic Regression) handle sparse text features more naturally. This is a legitimate negative result: exploring beyond the benchmark does not guarantee improvement, and the paper's choice of SVM as best model is corroborated rather than beaten.
**Tools/AI/code sources:** xgboost, scikit-learn; comparison script extended with Claude, executed and verified by the team.
**Next steps:** Team teach-in on full 5-model comparison; Minutes #3 finalisation; combined Week 2+3 log submission.