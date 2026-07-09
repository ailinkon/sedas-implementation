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