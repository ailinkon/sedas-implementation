"""
Feedback item 2.1: extend the C hyperparameter search to loss function and
class_weight, on top of the existing C=2.0 tuned result.

DROP-IN NOTES:
- Reuses whatever you already have from your Table 13a/16a CV script:
    X          -> the TF-IDF-ready feature matrix (or raw text, if you
                  vectorise inside the fold loop like your existing script)
    y          -> labels (1 = phishing, 0 = legitimate)
    skf        -> your existing StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
- If your existing script vectorises TF-IDF fresh inside each fold (to avoid
  train/test leakage), copy that exact vectorisation block in place of the
  "VECTORIZE HERE" comment below instead of using a pre-fit X.
- Baseline for the significance tests is your already-established best config:
  LinearSVC(C=2.0, loss='squared_hinge', class_weight=None) — i.e. "SVC tuned
  (C=2.0)" from Table 16. This script checks whether loss function or
  class_weight moves the needle beyond what C-tuning alone found.

Run this after your existing CV script (or merge the fold loop with it) and
paste the printed SUMMARY + significance blocks back for insertion into
Section 5.4 / a new Table 17a.
"""

import numpy as np
from sklearn.svm import LinearSVC
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score
from scipy import stats

# --------------------------------------------------------------------------
# 1. LOAD YOUR DATA — replace this block with your existing loader
# --------------------------------------------------------------------------
# X, y = load_your_dataset()          # <-- your existing function
# vectorizer = TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
#
# If you vectorise fresh per fold (recommended, matches your existing script):
# keep X as the raw/cleaned text list and vectorise inside the loop below.

RANDOM_STATE = 42
N_SPLITS = 5

CONFIGS = [
    {"name": "C=2.0, squared_hinge, class_weight=None (baseline)",
     "params": dict(C=2.0, loss="squared_hinge", class_weight=None)},
    {"name": "C=2.0, hinge, class_weight=None",
     "params": dict(C=2.0, loss="hinge", class_weight=None)},
    {"name": "C=2.0, squared_hinge, class_weight=balanced",
     "params": dict(C=2.0, loss="squared_hinge", class_weight="balanced")},
    {"name": "C=2.0, hinge, class_weight=balanced",
     "params": dict(C=2.0, loss="hinge", class_weight="balanced")},
]

def run_fold_scores(X, y, params):
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    fold_scores = []
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # --- VECTORIZE HERE if you fit TF-IDF fresh per fold ---
        # tfidf = TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
        # X_train = tfidf.fit_transform(X_train)
        # X_test = tfidf.transform(X_test)

        clf = LinearSVC(random_state=RANDOM_STATE, **params)
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        f1 = f1_score(y_test, preds)
        fold_scores.append(f1)
        print(f"  Fold {fold_idx}/{N_SPLITS}  F1={f1*100:.2f}%")
    return fold_scores

def main(X, y):
    print("=" * 70)
    print("2.1: Extended LinearSVC hyperparameter search (loss / class_weight)")
    print("=" * 70)

    results = {}
    for cfg in CONFIGS:
        print(f"\n--- {cfg['name']} ---")
        scores = run_fold_scores(X, y, cfg["params"])
        mean = np.mean(scores) * 100
        sd = np.std(scores, ddof=1) * 100
        results[cfg["name"]] = scores
        print(f"  Mean F1 = {mean:.3f}% +/- {sd:.3f}%")

    print("\n" + "=" * 70)
    print("SUMMARY - mean +/- standard deviation across folds")
    print("=" * 70)
    for name, scores in results.items():
        mean = np.mean(scores) * 100
        sd = np.std(scores, ddof=1) * 100
        rounded = [round(s * 100, 2) for s in scores]
        print(f"{name:50s} F1 = {mean:.3f}% +/- {sd:.3f}%   (folds: {rounded})")

    baseline_name = CONFIGS[0]["name"]
    baseline_scores = results[baseline_name]

    print("\n" + "=" * 70)
    print(f"SIGNIFICANCE TEST: each config vs baseline ({baseline_name})")
    print("=" * 70)
    for cfg in CONFIGS[1:]:
        name = cfg["name"]
        t_stat, p_val = stats.ttest_rel(results[name], baseline_scores)
        sig = "SIGNIFICANT" if p_val < 0.05 else "not significant"
        print(f"{name:50s} vs baseline: t={t_stat:+.4f}, p={p_val:.4f}  ({sig})")

    print("\nCopy the SUMMARY and significance blocks above into Section 5.4 /")
    print("a new Table 17a, alongside the existing C-sweep in Table 17.")


if __name__ == "__main__":
    # main(X, y)   # <-- uncomment once X, y are loaded above
    raise SystemExit(
        "Load X, y from your existing pipeline (same as your Table 13a/16a "
        "script), then call main(X, y)."
    )