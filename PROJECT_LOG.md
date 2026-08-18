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


## Entry 9 — Continued
**Supervisor directive:** Run ALL methods used in benchmark paper [41], not just one, then explore methods beyond it (e.g. XGBoost). Web frontend explicitly does not count toward marks — real ML execution and explanation is the priority. Every team member must be able to run and explain the model execution, not just the theory.
**Work completed:** Replicated all three of [41]'s models on the identical dataset: SVC/LinearSVC (F1 99.16%, paper 99.0%, +0.16), Random Forest (F1 98.71%, paper 98.0%, +0.71), Multinomial NB (F1 97.47%, paper 98.0%, -0.53). SEDAS Logistic Regression baseline (not in paper): F1 98.65%.
**Analysis:** SVC is the strongest model for both the paper and SEDAS, consistent with paper's own conclusion. MNB underperforms on recall (95.93% vs ~98-99% for others, 349 false negatives) - independence assumption between features likely too strong for this text data. RF and SVC both exceed the paper, suggesting our TF-IDF configuration (50k features, 1-2 grams, balanced class weights) is at least as effective as the original.
**Next steps:** XGBoost comparison (method beyond the paper); team teach-in session so all members can run and explain compare_models.py; Minutes #3 for this consultation.


## Entry 10 — Continued
**Work completed:** Added XGBoost (200 estimators, max_depth 6) as the "beyond the paper" method per supervisor directive. Full 5-model comparison complete on identical 82,486-email corpus: SVC F1 99.16% (paper 99.0%, +0.16), Random Forest F1 98.71% (paper 98.0%, +0.71), Logistic Regression F1 98.65% (not in paper), XGBoost F1 97.56% (not in paper), Multinomial NB F1 97.47% (paper 98.0%, -0.53).
**Analysis:** XGBoost did not outperform the linear/paper methods. Its false-positive count (324) is markedly higher than SVC (75) or Random Forest (103) despite comparable recall — likely overfitting on the high-dimensional sparse TF-IDF feature space (50,000 mostly-zero features) without hyperparameter tuning, whereas linear methods (SVC, Logistic Regression) handle sparse text features more naturally. This is a legitimate negative result: exploring beyond the benchmark does not guarantee improvement, and the paper's choice of SVM as best model is corroborated rather than beaten.
**Tools/AI/code sources:** xgboost, scikit-learn; comparison script extended with Claude, executed and verified by the team.
**Next steps:** Team teach-in on full 5-model comparison; Minutes #3 finalisation; combined Week 2+3 log submission.



## Entry 11 — 30 July 2026
**Work completed:** Team teach-in session delivered covering the full five-model comparison (compare_models.py): the dataset, TF-IDF vectorisation, the train/test split methodology, the confusion matrix, and each of the five models' results, using plain-language analogies (train/test split as "study vs exam", confusion matrix as "marking the exam"). Each member ran the comparison script independently on their own machine and explained the dataset, the metrics, and the result to the rest of the team unprompted.
**Decisions made (with justification):** Individual understanding treated as a team priority following the Thu 23 July consultation's explicit warning that shared marks fall if any member cannot run and explain the execution, regardless of code quality.
**Tools/AI/code sources used (with reflection):** Walkthrough materials drafted with Claude; delivered live by Ashraful; independently verified by each member running the script themselves.
**Problems & resolutions:** None — all four members successfully ran the script and could explain the dataset, split methodology and results.
**Next steps:** Minutes #3 finalisation; combined Week 2+3 log and minutes submission; prepare for next Thursday consultation.

## Entry 12 — continued
**Consultation:** Supervisor consultation held Thu 30 July (Minutes #4). Directive: replicating the paper's methods and achieving similar or marginally better results does not by itself constitute a contribution — described as "ground level", even after adding XGBoost. Directed to explore techniques beyond the paper (preprocessing/feature engineering, hybrid/combination methods) and to prepare a backup plan should results not be significant. Confirmed the dataset's full feature set is already used by the paper, so no unused data exists to exploit — any contribution must come from technique, not data.
**Work completed:** Implemented two contribution experiments per the directive. Experiment 1: text cleaning (URL normalisation, HTML stripping) plus six hand-crafted signal features (length, URL count, exclamation count, digit count, capital-letter ratio, keyword count) combined with TF-IDF via sparse hstack. Result: F1 99.16% — unchanged from baseline. Experiment 2: equal-weight voting ensemble of SVC, Random Forest and Logistic Regression. Result: F1 99.13% — a slight decline.
**Analysis:** Engineered features added no signal because TF-IDF already weights the same terms directly; the features were redundant rather than complementary. The equal-weight ensemble declined because Random Forest and Logistic Regression, both individually weaker than SVC, can jointly outvote SVC whenever they agree with each other, including cases where SVC was correct — a vote-dilution effect.
**Tools/AI/code sources:** scikit-learn VotingClassifier, scipy.sparse; contribution_experiment.py scaffolded with Claude, executed and verified by the team.
**Next steps:** Weighted ensemble and SVC hyperparameter tuning as the next two contribution attempts; prepare a genuine backup plan (transformer-based approach) in case none of the four strategies succeed.

## Entry 13 — continued
**Work completed:** Two further contribution experiments completed. Experiment 3: weighted voting ensemble giving SVC three votes against one each for Random Forest and Logistic Regression. Result: F1 99.17%. Experiment 4: SVC hyperparameter search across seven values of the regularisation parameter C (0.1 to 10.0). Best result: C=2.0, F1 99.17%; default C=1.0 gave 99.155%.
**Analysis:** The weighted ensemble's result is numerically identical to the tuned SVC's result down to the full confusion matrix, which is explained rather than coincidental: with weights 3:1:1, the two weaker models' combined two votes can never outnumber SVC's three, so the ensemble mathematically reduces to SVC acting alone. All four contribution experiments now converge within a 0.04-point F1 band (99.13%–99.17%), which is interpreted as a practical performance ceiling for TF-IDF combined with linear classifiers on this dataset, rather than four independent failures.
**Tools/AI/code sources:** scikit-learn LinearSVC, VotingClassifier with explicit weights; contribution_experiment_v2.py scaffolded with Claude, executed and verified by the team.
**Next steps:** Begin the transformer-based (DistilBERT) experiment as the backup/escalation approach discussed with the supervisor; prepare for Thu 6 August consultation.

## Entry 14 — 06 August 2026
**Consultation:** Supervisor consultation held Thu 6 August (Minutes #5). Directives: the final report must follow the base paper's [41] own section sequence, not the generic unit template, because SEDAS has an exact-matching benchmark paper; Part A literature tables must be carried into the Part B report; approximately 15 additional recent papers required, targeting 50–60 references in total; the Discussion section must explain clearly why the results are significant, described as the most important element of the report; at least 60% of the report to be completed and brought to the next class. Team was unable to immediately evidence the base paper's Q1 journal ranking when questioned.
**Work completed:** Journal ranking confirmed and evidenced (Computers and Electrical Engineering, Elsevier, Q1, ISSN 0045-7906). Sixteen new references sourced ([42]–[57]) covering deep learning detection, transformer-based detection, explainable AI, security awareness training, and blockchain-based URL verification (including a directly comparable paper, MLPhishChain, contrasting an Ethereum-based approach with SEDAS's hash-chain design). Literature review draft prepared integrating the new references with the Part A material. Final report restructured to follow [41]'s section sequence.
**Tools/AI/code sources:** Literature search conducted with Claude (web search); references and draft integration reviewed by the team; Scimago ranking record retrieved and verified independently.
**Next steps:** Complete the DistilBERT experiment; continue report drafting toward the 60% target; prepare journal-ranking evidence to have on screen at future consultations.

## Entry 15 — continued
**Work completed:** DistilBERT preliminary experiment completed as the "beyond the paper" transformer approach. Constrained to a stratified subsample (6,000 of 82,486 emails, 7.3%) due to CPU-only training hardware: 4,800 train / 1,200 test, max sequence length 128, batch size 8, 2 epochs, learning rate 2e-5. Result: Accuracy 97.92%, Precision 97.77%, Recall 98.24%, F1 98.00%, FP rate 0.0243, confusion TN=562 FP=14 FN=11 TP=613. Training loss declined steadily in epoch 1 (0.5951→0.1868) and rose slightly in epoch 2 (0.0329→0.0412).
**Analysis:** The epoch-2 loss rise is consistent with early overfitting on the reduced training sample, expected given the small subsample size, and is direct evidence the experiment needs the full dataset for a conclusive result. The headline result must be read against the sampling constraint: DistilBERT reached within 1.16 F1 points of the best classical model (SVC, 99.16%) using approximately 7% of the training data used by the classical models — read correctly, this favours the transformer's data efficiency rather than representing a straightforward loss. Comparison to the full-dataset classical results is explicitly treated as indicative, not definitive.
**Tools/AI/code sources:** PyTorch, Hugging Face Transformers (distilbert-base-uncased); distilbert_preliminary.py scaffolded with Claude, executed and verified by the team.
**Next steps:** Complete the training module scoring engine (previously raising NotImplementedError); expand the test suite; continue report drafting.

## Entry 16 — continued
**Work completed:** Awareness training service scoring engine implemented (FR-05, FR-06), closing the previously incomplete fourth system component. Four functions implemented: score_attempt (percentage score with divide-by-zero guard), update_risk (exponentially weighted moving average, ALPHA=0.4, clamped 0–100), risk_band (low <33, medium <66, high ≥66), and next_lesson_for (persona filtering, completed-lesson exclusion, difficulty targeting inverted against risk band, with fallback to any remaining eligible lesson). Full end-to-end flow verified manually via /docs: user registration, quiz retrieval (confirmed correct answers withheld from the response), submission with per-question feedback, and progress retrieval showing updated risk score, band, and a correctly persona/difficulty-matched next lesson recommendation.
**Design note:** Difficulty is deliberately inverted against risk — a high-risk user receives foundational (difficulty 1) content rather than advanced content, on the basis that reinforcing fundamentals is more effective than escalating difficulty for a struggling learner.
**Tools/AI/code sources:** FastAPI, sqlite3; scoring engine implementation drafted with Claude against a written specification, executed, tested and verified end-to-end by the team.
**Next steps:** Write TT-series tests for the scoring engine; write TS-series security/negative-case tests; all four system components now functional.

## Entry 17 — 13 August 2026
**Work completed:** Test suite expanded from 8 to 23 tests. Added TT-01..TT-06 (training scoring engine: attempt scoring including divide-by-zero guard, EWMA risk increase/decrease and boundary clamping, risk band thresholds, persona-aware adaptive selection, completed-lesson exclusion, fallback behaviour) and TS-01..TS-06 (security/negative cases: SQL metacharacter injection resistance with registry and chain-integrity verification, empty and malformed input handling, unknown-user and unknown-lesson 404 handling, quiz answer-key confidentiality, service health checks, chain integrity across multiple successive writes). All 23 tests passing.
**Problems & resolutions:** Expanding the suite exposed a defect: both the URL verification and training services define a module named `serve`; Python's module cache returned whichever loaded first for both, causing the URL verification tests to silently execute against the wrong service and fail with HTTP 404. Diagnosed by observing the security suite (which loads modules explicitly by file path) exercised the same endpoints successfully. Resolved by applying the same explicit `importlib` file-path loading to the URL verification test module. Retained as a documented example of testing revealing and correcting a genuine defect rather than merely confirming existing behaviour.
**Tools/AI/code sources:** pytest, FastAPI TestClient, importlib; test suites scaffolded with Claude, executed, debugged and verified by the team.
**Next steps:** OWASP Top 10 security assessment; Technical/Programmer Manual; User Guide; architecture and data model diagrams.

## Entry 18 — continued
**Work completed:** OWASP Top 10 (2021) security assessment conducted across all three services via manual source review, cross-referenced against the automated test suite. Ten categories assessed: 3 High (A01 Broken Access Control, A07 Authentication Failures, A09 Logging & Monitoring Failures — all traced to the single documented decision not to implement production authentication at MVP scope), 5 Medium (A02 Cryptographic Failures, A04 Insecure Design, A05 Security Misconfiguration, A06 Vulnerable Components, A08 Software/Data Integrity), 1 Resolved (A03 Injection — verified directly by test TS-01 rather than claimed by review alone), 1 Not Applicable (A10 SSRF — the URL verification service performs string-pattern heuristic analysis only and never issues an outbound request to a submitted URL). Prioritised remediation roadmap produced, separating low-effort pre-submission fixes from properly-scoped future work.
**Tools/AI/code sources:** Manual code review methodology; assessment document drafted with Claude against the actual codebase, reviewed and verified by Huzaifa.
**Next steps:** Architecture, data model and ML pipeline diagrams; Technical/Programmer Manual; User Guide; final report drafting.

## Entry 19 — continued
**Work completed:** System architecture, data model (training schema and URL registry, including the tamper-evidence hash formula) and ML pipeline diagrams produced. Technical/Programmer Manual completed covering system overview, architecture, technology stack, data model, core modules, security controls (mapped to verifying tests), and deployment instructions verified against a clean-clone setup sequence. User Guide completed for a non-technical audience covering email checking, URL verification, awareness training, everyday good practice, troubleshooting and a glossary. Consolidated Project Log (Weeks 1–7) assembled from individual entries. Results figures generated (model comparison, metric breakdowns, confusion matrices, false-positive/negative breakdown, performance-ceiling chart, precision-recall positioning, six-method comparison including DistilBERT, training-loss curve).
**Ethics/security/privacy notes:** Known limitations (no authentication/RBAC, permissive CORS, no rate limiting) documented explicitly in both the Technical Manual and the OWASP assessment rather than omitted.
**Tools/AI/code sources:** matplotlib for figures; manual (Technical Manual, User Guide, architecture diagrams) drafted with Claude from the actual implemented system, reviewed and verified by the team.
**Next steps:** Final report analytical writing, divided across all four members by section; reference list verification (three entries flagged for journal/quartile confirmation); prepare draft for Thu 13 August consultation feedback.

## Entry 20 — 17 August 2026
**Work completed:** Detailed written supervisor feedback received on the submitted draft report, following the Thu 13 August consultation. Highest-priority item: single-split results for both the benchmark comparison and the four optimisation experiments carried no variance reporting, so small numerical differences (0.01–0.04 F1 points) could not be distinguished from split-specific noise. Implemented 5-fold stratified cross-validation across all five classical models and all four optimisation-experiment configurations, with paired significance testing (α=0.05) against the SVC baseline.
**Results:** Five-model CV means: SVC 99.233% (±0.086%), Logistic Regression 98.724% (±0.091%), Random Forest 98.705% (±0.077%), XGBoost 97.588% (±0.074%), Multinomial NB 97.495% (±0.129%). Paired t-test SVC vs Random Forest: t=16.60, p=0.0001 (significant). Optimisation experiments vs baseline: engineered features p=0.1217, equal-weight ensemble p=0.0008 (significant decline), weighted ensemble p=0.3139, tuned SVC p=0.3139 — three of four not significant, strengthening rather than weakening the ceiling finding. Weighted ensemble and tuned SVC produced identical F1 on every individual fold, confirming the 3:1:1 vote-mathematics explanation with direct evidence rather than a single-split coincidence.
**Further corrections applied:** conclusion's Q1-tier overclaim corrected; DistilBERT caveat consolidated into one consistent statement in two locations; Table 14c added making XGBoost/Logistic Regression precision and recall traceable before first use in the discussion; Section 5.8 limitations wording corrected to distinguish significance testing against the external paper (still not possible, as [41] publishes no fold-level data) from significance testing across SEDAS's own experiments (now completed); a duplicate, informally worded draft summary section identified and removed.
**Problems & resolutions:** Cross-validation script initially failed with a 1.28 TiB memory allocation error. Cause: constructing a NumPy array from variable-length email text without specifying dtype=object causes NumPy to infer a fixed-width type sized to the single longest string in the corpus and pad every row to that width. Resolved by specifying dtype=object explicitly. Report corrections applied via direct, targeted editing of the existing document structure to preserve all embedded figures and custom table formatting rather than regenerating the document from extracted text.
**Tools/AI/code sources:** scikit-learn StratifiedKFold, scipy.stats (paired t-test); crossval_significance.py scaffolded with Claude, executed and verified by the team; document corrections applied with Claude directly to the report file, reviewed by Ashraful.
**Next steps:** Address remaining feedback items (extended hyperparameter search; qualitative inspection of SVC false negatives; engineered-feature weight scaling check); complete remaining analytical report sections; final reference list verification; viva preparation ahead of Week 8.