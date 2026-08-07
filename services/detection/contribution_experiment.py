"""
SEDAS - Contribution Experiment: Feature Engineering + Hybrid Ensemble
MIS5320 Part B | Following supervisor directive: replication alone is not
a contribution. This script tests two genuine extensions beyond the
benchmark paper [41]: (1) text cleaning + engineered features added
alongside TF-IDF, and (2) a hybrid voting ensemble of the strongest
models - neither technique is described in the paper's methodology.
Run: python services/detection/contribution_experiment.py
"""

import re
import numpy as np
import pandas as pd
import scipy.sparse as sp
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix)

DATA_PATH = Path(__file__).parent / "data" / "phishing_email.csv"

BENCHMARK_SVC_F1 = 99.0       # paper [41]'s best reported result
OUR_BASELINE_SVC_F1 = 99.16   # our direct replication, already achieved


def load_data():
    df = pd.read_csv(DATA_PATH)
    text_col = next(c for c in df.columns if c.lower() in
                    ("text_combined", "text", "body", "email_text", "email"))
    label_col = next(c for c in df.columns if c.lower() in
                     ("label", "class", "category", "type"))
    df = df[[text_col, label_col]].dropna()
    df.columns = ["text", "label"]
    return df


def clean_text(text):
    """Normalise URLs and strip HTML noise before vectorisation -
    a preprocessing step not described in the paper's methodology."""
    text = str(text)
    text = re.sub(r"https?://\S+|www\.\S+", " XURLX ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def engineer_features(texts):
    """Hand-crafted signal features alongside TF-IDF - our own addition,
    not present in the paper's described methodology."""
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


def evaluate(name, y_test, y_pred, ref_f1=None):
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
    if ref_f1 is not None:
        print(f"vs reference ({ref_f1}%): {f1 - ref_f1:+.2f} points")
    return f1


def main():
    df = load_data()
    print(f"Dataset: {len(df)} emails")
    print(f"Reference - paper [41] best (SVC): {BENCHMARK_SVC_F1}%")
    print(f"Reference - our direct SVC replication: {OUR_BASELINE_SVC_F1}%\n")

    df["clean_text"] = df["text"].apply(clean_text)

    X_train_txt, X_test_txt, y_train, y_test = train_test_split(
        df["clean_text"], df["label"], test_size=0.2,
        random_state=42, stratify=df["label"])

    tfidf = TfidfVectorizer(max_features=50000, ngram_range=(1, 2),
                            stop_words="english")
    X_train_tfidf = tfidf.fit_transform(X_train_txt)
    X_test_tfidf = tfidf.transform(X_test_txt)

    eng_train = engineer_features(X_train_txt)
    eng_test = engineer_features(X_test_txt)
    scaler = StandardScaler()
    eng_train_scaled = scaler.fit_transform(eng_train)
    eng_test_scaled = scaler.transform(eng_test)

    X_train_combined = sp.hstack([X_train_tfidf, sp.csr_matrix(eng_train_scaled)]).tocsr()
    X_test_combined = sp.hstack([X_test_tfidf, sp.csr_matrix(eng_test_scaled)]).tocsr()

    print("=" * 60)
    print("EXPERIMENT 1: Cleaned text + engineered features")
    print("(tests whether preprocessing + hand-crafted signals")
    print(" improve on plain TF-IDF - not done in the paper)")
    print("=" * 60)

    svc = LinearSVC(class_weight="balanced")
    svc.fit(X_train_combined, y_train)
    f1_svc_enhanced = evaluate("SVC + engineered features", y_test,
                               svc.predict(X_test_combined),
                               ref_f1=OUR_BASELINE_SVC_F1)

    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train_combined, y_train)
    f1_rf_enhanced = evaluate("Random Forest + engineered features", y_test,
                              rf.predict(X_test_combined))

    lr = LogisticRegression(max_iter=1000, class_weight="balanced")
    lr.fit(X_train_combined, y_train)
    f1_lr_enhanced = evaluate("Logistic Regression + engineered features",
                              y_test, lr.predict(X_test_combined))

    print("\n" + "=" * 60)
    print("EXPERIMENT 2: Hybrid voting ensemble")
    print("(combines SVC, Random Forest and Logistic Regression -")
    print(" a method the paper did not use)")
    print("=" * 60)

    ensemble = VotingClassifier(estimators=[
        ("svc", LinearSVC(class_weight="balanced")),
        ("rf", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)),
        ("lr", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ], voting="hard")

    ensemble.fit(X_train_combined, y_train)
    f1_ensemble = evaluate("Hybrid Voting Ensemble (SVC+RF+LR)", y_test,
                           ensemble.predict(X_test_combined),
                           ref_f1=OUR_BASELINE_SVC_F1)

    print("\n" + "=" * 60)
    print("SUMMARY - contribution experiments vs reference points")
    print("=" * 60)
    print(f"{'Paper [41] best (SVC, reference)':<45} F1={BENCHMARK_SVC_F1:.2f}%")
    print(f"{'Our direct SVC replication (reference)':<45} F1={OUR_BASELINE_SVC_F1:.2f}%")
    print(f"{'SVC + engineered features':<45} F1={f1_svc_enhanced:.2f}%")
    print(f"{'Random Forest + engineered features':<45} F1={f1_rf_enhanced:.2f}%")
    print(f"{'Logistic Regression + engineered features':<45} F1={f1_lr_enhanced:.2f}%")
    print(f"{'Hybrid Voting Ensemble (SVC+RF+LR)':<45} F1={f1_ensemble:.2f}%")


if __name__ == "__main__":
    main()
