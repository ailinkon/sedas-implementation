"""
SEDAS - K-Fold Cross-Validation and Significance Testing
MIS5320 Part B | Addresses supervisor feedback item 1.1: the single-split
results in Tables 13/14/16 have no variance reporting, so the "ceiling"
finding (differences of 0.01-0.04 F1 points) currently lacks statistical
backing. This script runs 5-fold stratified CV on all five classical
models AND on the four optimisation-experiment configurations, reporting
mean +/- SD F1 for each, plus a paired significance test between the
two best-performing models.

Run: python services/detection/crossval_significance.py
Expect 30-90 minutes depending on hardware (RF and XGBoost are the
slow ones, now multiplied by 5 folds instead of 1 split).
"""

import re
import numpy as np
import pandas as pd
import scipy.sparse as sp
from pathlib import Path
from scipy import stats
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score

DATA_PATH = Path(__file__).parent / "data" / "phishing_email.csv"
N_FOLDS = 5
RANDOM_STATE = 42


def load_data():
    df = pd.read_csv(DATA_PATH)
    text_col = next(c for c in df.columns if c.lower() in
                    ("text_combined", "text", "body", "email_text", "email"))
    label_col = next(c for c in df.columns if c.lower() in
                     ("label", "class", "category", "type"))
    df = df[[text_col, label_col]].dropna()
    df.columns = ["text", "label"]
    return df.reset_index(drop=True)


def clean_text(text):
    text = str(text)
    text = re.sub(r"https?://\S+|www\.\S+", " XURLX ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def engineer_features(texts):
    feats = []
    for t in texts:
        t = str(t)
        length = len(t)
        n_urls = len(re.findall(r"https?://|www\.", t))
        n_exclaim = t.count("!")
        n_digits = sum(c.isdigit() for c in t)
        caps_ratio = (sum(c.isupper() for c in t) / length) if length else 0
        keyword_hits = sum(t.lower().count(k) for k in
                           ("verify", "urgent", "suspend", "click",
                            "password", "account", "confirm", "immediately"))
        feats.append([length, n_urls, n_exclaim, n_digits, caps_ratio, keyword_hits])
    return np.array(feats, dtype=float)


def build_tfidf():
    return TfidfVectorizer(max_features=50000, ngram_range=(1, 2), stop_words="english")


def cv_classical_models(df, skf):
    """Part A: 5-fold CV for the five classical models on plain TF-IDF,
    matching the feature configuration used in Tables 13/14."""
    models = {
        "SVC / LinearSVC": lambda: LinearSVC(class_weight="balanced"),
        "Random Forest": lambda: RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1),
        "Logistic Regression": lambda: LogisticRegression(max_iter=1000, class_weight="balanced"),
        "XGBoost": lambda: XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                                         eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE),
        "Multinomial Naive Bayes": lambda: MultinomialNB(),
    }

    fold_scores = {name: {"f1": [], "acc": [], "prec": [], "rec": []} for name in models}
    X_text = df["text"].values
    y = df["label"].values

    for fold_i, (train_idx, test_idx) in enumerate(skf.split(X_text, y), 1):
        print(f"\n--- Fold {fold_i}/{N_FOLDS} ---")
        X_train_text, X_test_text = X_text[train_idx], X_text[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        tfidf = build_tfidf()
        X_train = tfidf.fit_transform(X_train_text)
        X_test = tfidf.transform(X_test_text)

        for name, make_model in models.items():
            model = make_model()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            f1 = f1_score(y_test, y_pred)
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred)
            rec = recall_score(y_test, y_pred)
            fold_scores[name]["f1"].append(f1)
            fold_scores[name]["acc"].append(acc)
            fold_scores[name]["prec"].append(prec)
            fold_scores[name]["rec"].append(rec)
            print(f"  {name:<28} F1={f1*100:.2f}%")

    return fold_scores


def cv_optimisation_experiments(df, skf):
    """Part B: 5-fold CV for the four optimisation-experiment configurations
    from Table 16, to check whether the 0.01-0.04 point differences survive
    variance reporting."""
    X_text = df["text"].values
    y = df["label"].values
    clean_texts = np.array([clean_text(t) for t in X_text], dtype=object)

    fold_scores = {
        "SVC baseline": [],
        "SVC + engineered features": [],
        "Equal-weight ensemble": [],
        "Weighted ensemble": [],
        "SVC tuned (C=2.0)": [],
    }

    for fold_i, (train_idx, test_idx) in enumerate(skf.split(X_text, y), 1):
        print(f"\n--- Optimisation fold {fold_i}/{N_FOLDS} ---")
        y_train, y_test = y[train_idx], y[test_idx]

        # Plain TF-IDF (for baseline, ensembles, tuned)
        tfidf = build_tfidf()
        X_train_plain = tfidf.fit_transform(X_text[train_idx])
        X_test_plain = tfidf.transform(X_text[test_idx])

        # SVC baseline
        svc = LinearSVC(class_weight="balanced")
        svc.fit(X_train_plain, y_train)
        f1 = f1_score(y_test, svc.predict(X_test_plain))
        fold_scores["SVC baseline"].append(f1)
        print(f"  SVC baseline                 F1={f1*100:.2f}%")

        # SVC tuned C=2.0
        svc_tuned = LinearSVC(C=2.0, class_weight="balanced")
        svc_tuned.fit(X_train_plain, y_train)
        f1 = f1_score(y_test, svc_tuned.predict(X_test_plain))
        fold_scores["SVC tuned (C=2.0)"].append(f1)
        print(f"  SVC tuned (C=2.0)            F1={f1*100:.2f}%")

        # Equal-weight ensemble
        ensemble_eq = VotingClassifier(estimators=[
            ("svc", LinearSVC(class_weight="balanced")),
            ("rf", RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)),
            ("lr", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ], voting="hard")
        ensemble_eq.fit(X_train_plain, y_train)
        f1 = f1_score(y_test, ensemble_eq.predict(X_test_plain))
        fold_scores["Equal-weight ensemble"].append(f1)
        print(f"  Equal-weight ensemble        F1={f1*100:.2f}%")

        # Weighted ensemble
        ensemble_w = VotingClassifier(estimators=[
            ("svc", LinearSVC(C=2.0, class_weight="balanced")),
            ("rf", RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)),
            ("lr", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ], voting="hard", weights=[3, 1, 1])
        ensemble_w.fit(X_train_plain, y_train)
        f1 = f1_score(y_test, ensemble_w.predict(X_test_plain))
        fold_scores["Weighted ensemble"].append(f1)
        print(f"  Weighted ensemble            F1={f1*100:.2f}%")

        # SVC + engineered features
        eng_train = engineer_features(clean_texts[train_idx])
        eng_test = engineer_features(clean_texts[test_idx])
        scaler = StandardScaler()
        eng_train_scaled = scaler.fit_transform(eng_train)
        eng_test_scaled = scaler.transform(eng_test)
        tfidf2 = build_tfidf()
        X_train_tfidf2 = tfidf2.fit_transform(clean_texts[train_idx])
        X_test_tfidf2 = tfidf2.transform(clean_texts[test_idx])
        X_train_combined = sp.hstack([X_train_tfidf2, sp.csr_matrix(eng_train_scaled)]).tocsr()
        X_test_combined = sp.hstack([X_test_tfidf2, sp.csr_matrix(eng_test_scaled)]).tocsr()
        svc_eng = LinearSVC(class_weight="balanced")
        svc_eng.fit(X_train_combined, y_train)
        f1 = f1_score(y_test, svc_eng.predict(X_test_combined))
        fold_scores["SVC + engineered features"].append(f1)
        print(f"  SVC + engineered features    F1={f1*100:.2f}%")

    return fold_scores


def summarise(fold_scores, metric_key=None):
    print("\n" + "=" * 70)
    print("SUMMARY - mean +/- standard deviation across folds")
    print("=" * 70)
    summary = {}
    for name, scores in fold_scores.items():
        vals = scores[metric_key] if metric_key else scores
        vals = np.array(vals) * 100
        mean, sd = vals.mean(), vals.std(ddof=1)
        summary[name] = (mean, sd, vals)
        print(f"{name:<30} F1 = {mean:.3f}% +/- {sd:.3f}%   (folds: {np.round(vals, 2).tolist()})")
    return summary


def main():
    df = load_data()
    print(f"Dataset: {len(df)} emails, {N_FOLDS}-fold stratified cross-validation, seed={RANDOM_STATE}\n")
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    print("#" * 70)
    print("PART A: Five classical models (matches Tables 13/14)")
    print("#" * 70)
    classical_scores = cv_classical_models(df, skf)
    classical_summary = summarise(classical_scores, metric_key="f1")

    print("\n" + "#" * 70)
    print("SIGNIFICANCE TEST: SVC vs Random Forest (nearest competitor)")
    print("#" * 70)
    svc_folds = np.array(classical_scores["SVC / LinearSVC"]["f1"])
    rf_folds = np.array(classical_scores["Random Forest"]["f1"])
    t_stat, p_value = stats.ttest_rel(svc_folds, rf_folds)
    print(f"SVC folds: {np.round(svc_folds*100, 3).tolist()}")
    print(f"RF folds:  {np.round(rf_folds*100, 3).tolist()}")
    print(f"Paired t-test: t = {t_stat:.4f}, p = {p_value:.4f}")
    if p_value < 0.05:
        print("Result: statistically significant at alpha=0.05 - SVC's advantage is unlikely to be noise.")
    else:
        print("Result: NOT statistically significant at alpha=0.05 given only 5 folds - "
              "report this honestly rather than asserting SVC is definitively better.")

    print("\n" + "#" * 70)
    print("PART B: Four optimisation experiments (matches Table 16)")
    print("#" * 70)
    opt_scores = cv_optimisation_experiments(df, skf)
    opt_summary = summarise(opt_scores)

    print("\n" + "#" * 70)
    print("SIGNIFICANCE TEST: SVC baseline vs each optimisation attempt")
    print("#" * 70)
    baseline_folds = np.array(opt_scores["SVC baseline"])
    for name, scores in opt_scores.items():
        if name == "SVC baseline":
            continue
        other_folds = np.array(scores)
        t_stat, p_value = stats.ttest_rel(baseline_folds, other_folds)
        sig = "SIGNIFICANT" if p_value < 0.05 else "not significant"
        print(f"{name:<30} vs baseline: t={t_stat:+.4f}, p={p_value:.4f}  ({sig})")

    print("\n" + "=" * 70)
    print("Copy the SUMMARY blocks above into the report's Section 5.1/5.4 "
          "as mean +/- SD, and cite the p-values in the interpretation.")
    print("=" * 70)


if __name__ == "__main__":
    main()