"""
SEDAS - Model Comparison vs Published Benchmark
MIS5320 Part B | Benchmark: Al-Subaiey et al. (2024), CEE 120:109625
Same dataset (82.5k combined corpus), same TF-IDF features.
Replicates ALL THREE of the paper's models (SVC, Random Forest, Multinomial NB)
plus our own extensions (Logistic Regression, XGBoost).
Run: python services/detection/compare_models.py
"""

import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix)

DATA_PATH = Path(__file__).parent / "data" / "phishing_email.csv"

# Published benchmark numbers from Al-Subaiey et al. (2024), Table 2,
# "proposed"/merged-corpus rows (their exact 82,486-email dataset).
BENCHMARK = {
    "SVC (linear kernel)":  {"acc": 99.1, "prec": 99.0, "rec": 99.0, "f1": 99.0},
    "Random Forest":        {"acc": 98.4, "prec": 98.0, "rec": 99.0, "f1": 98.0},
    "Multinomial NB":       {"acc": 97.8, "prec": 97.0, "rec": 99.0, "f1": 98.0},
}


def load_data():
    df = pd.read_csv(DATA_PATH)
    text_col = next(c for c in df.columns if c.lower() in
                    ("text_combined", "text", "body", "email_text", "email"))
    label_col = next(c for c in df.columns if c.lower() in
                     ("label", "class", "category", "type"))
    df = df[[text_col, label_col]].dropna()
    df.columns = ["text", "label"]
    return df


def evaluate(name, model, X_train, X_test, y_train, y_test, bench_key=None):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    acc = accuracy_score(y_test, y_pred) * 100
    prec = precision_score(y_test, y_pred) * 100
    rec = recall_score(y_test, y_pred) * 100
    f1 = f1_score(y_test, y_pred) * 100
    print(f"\n--- {name} ---")
    print(f"Accuracy : {acc:.2f}%")
    print(f"Precision: {prec:.2f}%")
    print(f"Recall   : {rec:.2f}%")
    print(f"F1 score : {f1:.2f}%")
    print(f"FP rate  : {fp / (fp + tn):.4f}")
    print(f"Confusion: TN={tn} FP={fp} FN={fn} TP={tp}")
    if bench_key and bench_key in BENCHMARK:
        b = BENCHMARK[bench_key]
        print(f"Paper [41] reported : Acc {b['acc']}% / Prec {b['prec']}% / "
              f"Rec {b['rec']}% / F1 {b['f1']}%")
        print(f"Delta vs paper (F1) : {f1 - b['f1']:+.2f} points")
    return {"name": name, "acc": acc, "prec": prec, "rec": rec, "f1": f1}


def main():
    df = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2,
        random_state=42, stratify=df["label"])
    print(f"Dataset: {len(df)} emails | train {len(X_train)} / test {len(X_test)}")
    print("Replicating all three models from Al-Subaiey et al. (2024), Table 2\n")

    tfidf = lambda: TfidfVectorizer(max_features=50000, ngram_range=(1, 2),
                                    stop_words="english")
    results = []

    # ---- The paper's three models, in their order ----
    results.append(evaluate(
        "1. SVC / LinearSVC (paper's best model)",
        Pipeline([("tfidf", tfidf()), ("clf", LinearSVC(class_weight="balanced"))]),
        X_train, X_test, y_train, y_test, bench_key="SVC (linear kernel)"))

    results.append(evaluate(
        "2. Random Forest (100 trees, matching paper config)",
        Pipeline([("tfidf", tfidf()),
                 ("clf", RandomForestClassifier(n_estimators=100, random_state=42,
                                                n_jobs=-1))]),
        X_train, X_test, y_train, y_test, bench_key="Random Forest"))

    results.append(evaluate(
        "3. Multinomial Naive Bayes",
        Pipeline([("tfidf", tfidf()), ("clf", MultinomialNB())]),
        X_train, X_test, y_train, y_test, bench_key="Multinomial NB"))

    # ---- Our own extensions (not in the paper) ----
    results.append(evaluate(
        "4. Logistic Regression (SEDAS baseline - not in paper)",
        Pipeline([("tfidf", tfidf()),
                 ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))]),
        X_train, X_test, y_train, y_test))

    results.append(evaluate(
        "5. XGBoost (method NOT used in the paper - our extension)",
        Pipeline([("tfidf", tfidf()),
                 ("clf", XGBClassifier(n_estimators=200, max_depth=6,
                                       learning_rate=0.1, eval_metric="logloss",
                                       n_jobs=-1, random_state=42))]),
        X_train, X_test, y_train, y_test))

    print("\n" + "=" * 60)
    print("SUMMARY - all models, best F1 first")
    print("=" * 60)
    for r in sorted(results, key=lambda r: -r["f1"]):
        print(f"{r['name']:<50} F1={r['f1']:.2f}%")


if __name__ == "__main__":
    main()