"""
Feedback item 2.3: check whether the engineered-feature "no improvement"
result (SVC + engineered features = 99.16% F1, identical to baseline to two
decimal places) is a genuine redundancy finding or a scaling artefact.

This produces the evidence needed to state the "redundancy" explanation
with actual numbers instead of plausible reasoning alone — either:
  (a) the six engineered features get near-zero coefficients AND their raw
      values are on a comparable scale to TF-IDF -> genuinely redundant, or
  (b) the six engineered features are numerically dominated (raw values much
      larger/smaller than TF-IDF's ~0-1 range, no scaler applied) -> the
      "no improvement" result is a scaling artefact, not redundancy, and
      the report's explanation needs a caveat or a rerun with scaling fixed.

DROP-IN NOTES:
- Targets the "SVC + engineered features" model from Table 16 (contribution_experiment.py
  or contribution_experiment_v2.py, based on your file names — use whichever
  produced the 99.16% engineered-features row).
- ENGINEERED_FEATURE_NAMES below must match the six columns in your pipeline,
  in the same order they were added to the feature matrix. Fix the list if
  your actual names/order differ.
- Assumes the engineered features were combined with the TF-IDF matrix via
  scipy.sparse.hstack (dense engineered columns appended after the TF-IDF
  columns) — the most common pattern for this. If your pipeline is a
  ColumnTransformer or something else, the "LOCATE ENGINEERED COLUMNS"
  section needs adjusting, but the diagnostic logic (coefficient percentile
  + raw value range) stays the same.
"""

import numpy as np
import joblib

# --------------------------------------------------------------------------
# 1. LOAD SECTION — replace with your existing loader for this specific model
# --------------------------------------------------------------------------
# model = joblib.load("model_engineered_features.joblib")  # the fitted SVC + engineered-features pipeline
# vectorizer = ...       # the TF-IDF vectorizer used for this run
# X_engineered = ...     # the raw (un-scaled) engineered feature matrix, shape (n_samples, 6),
#                         # i.e. the values BEFORE any hstack/scaling was applied

ENGINEERED_FEATURE_NAMES = [
    "url_count",
    "capital_ratio",
    "exclamation_count",
    "phishing_keyword_count",
    # fix these two to match your actual pipeline if the names differ:
    "html_removed_flag",
    "url_normalised_flag",
]

def diagnose(model, vectorizer, X_engineered):
    # LinearSVC stores coefficients in model.coef_[0] for binary classification
    coefs = np.asarray(model.coef_).ravel()
    n_features_total = len(coefs)
    n_engineered = len(ENGINEERED_FEATURE_NAMES)
    n_tfidf = n_features_total - n_engineered

    print("=" * 70)
    print(f"Total features in fitted model: {n_features_total}")
    print(f"  TF-IDF columns (assumed):     {n_tfidf}")
    print(f"  Engineered columns (assumed): {n_engineered}  (last {n_engineered} columns)")
    print("=" * 70)
    if n_tfidf != vectorizer.vocabulary_.__len__() if hasattr(vectorizer, "vocabulary_") else True:
        pass  # sanity check only; remove if vectorizer isn't available here

    # --- LOCATE ENGINEERED COLUMNS ---
    # Assumes engineered features are the LAST n_engineered columns after hstack.
    # If they were prepended instead, use coefs[:n_engineered].
    tfidf_coefs = coefs[:n_tfidf]
    engineered_coefs = coefs[n_tfidf:]

    abs_tfidf = np.abs(tfidf_coefs)
    print("\n--- TF-IDF coefficient magnitude distribution (for percentile comparison) ---")
    for pct in [50, 75, 90, 95, 99]:
        print(f"  {pct}th percentile |coef|: {np.percentile(abs_tfidf, pct):.6f}")
    print(f"  Max |coef|:               {abs_tfidf.max():.6f}")

    print("\n" + "=" * 70)
    print("ENGINEERED FEATURE DIAGNOSTIC")
    print("=" * 70)
    print(f"{'Feature':28s} {'Coefficient':>14s} {'|coef| pctile':>15s} {'Raw min':>10s} {'Raw max':>10s} {'Raw mean':>10s} {'Raw std':>10s}")
    for i, name in enumerate(ENGINEERED_FEATURE_NAMES):
        coef = engineered_coefs[i]
        pctile = (abs_tfidf < abs(coef)).mean() * 100
        raw_col = X_engineered[:, i]
        print(f"{name:28s} {coef:14.6f} {pctile:14.1f}% {raw_col.min():10.3f} {raw_col.max():10.3f} "
              f"{raw_col.mean():10.3f} {raw_col.std():10.3f}")

    print("\n" + "=" * 70)
    print("INTERPRETATION GUIDE")
    print("=" * 70)
    print("- If engineered coefficients sit BELOW the 50th percentile of TF-IDF |coef|")
    print("  AND their raw value range is comparable to TF-IDF's (roughly 0-1 after")
    print("  normalisation), that supports genuine redundancy: the model 'saw' these")
    print("  signals and gave them a fair chance, but didn't need them.")
    print("- If engineered raw values are on a much larger scale (e.g. url_count up to")
    print("  10-50, exclamation_count up to 20+) while TF-IDF values sit in 0-1, AND no")
    print("  StandardScaler/MinMaxScaler was applied before hstack, that's evidence of a")
    print("  scaling mismatch — LinearSVC's L2-regularised objective penalises large-scale")
    print("  features more heavily per unit weight, which can suppress their coefficients")
    print("  regardless of true signal value. In that case, the 'redundancy' explanation")
    print("  in Section 5.4 needs a caveat, or a quick rerun with the engineered columns")
    print("  scaled to match TF-IDF's range before concluding redundancy.")
    print("\nCopy the ENGINEERED FEATURE DIAGNOSTIC table and whichever interpretation")
    print("applies into Section 5.4's engineered-feature paragraph as supporting evidence.")


if __name__ == "__main__":
    # diagnose(model, vectorizer, X_engineered)   # <-- uncomment once loaded above
    raise SystemExit(
        "Load the engineered-features model, vectorizer, and the raw (un-scaled) "
        "engineered feature matrix as in contribution_experiment.py, then call "
        "diagnose(model, vectorizer, X_engineered)."
    )
