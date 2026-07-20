"""
SEDAS - Model Comparison vs Published Benchmark
MIS5320 Part B | Benchmark: Al-Subaiey et al. (2024), CEE 120:109625
Same dataset (82.5k combined corpus), same TF-IDF features.
Compares: LR (our baseline) vs LinearSVC (benchmark replication).
Run: python services/detection/compare_models.py
"""

import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix)

DATA_PATH = Path(__file__).parent / "data" / "phishing_email.csv"

def load_data():
    df = pd.read_csv(DATA_PATH)
    text_col = next(c for c in df.columns if c.lower() in
                    ("text_combined", "text", "body", "email_text", "email"))
    label_col = next(c for c in df.columns if c.lower() in
                     ("label", "class", "category", "type"))
    df = df[[text_col, label_col]].dropna()
    df.columns = ["text", "label"]
    return df

def evaluate(name, model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    print(f"\n--- {name} ---")
    print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
    print(f"F1 score : {f1_score(y_test, y_pred):.4f}")
    print(f"FP rate  : {fp / (fp + tn):.4f}")
    print(f"Confusion: TN={tn} FP={fp} FN={fn} TP={tp}")

def main():
    df = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2,
        random_state=42, stratify=df["label"])
    print(f"Dataset: {len(df)} emails | train {len(X_train)} / test {len(X_test)}")
    print("Benchmark to beat/match: Al-Subaiey et al. (2024) TF-IDF+SVM, F1 = 0.99")

    tfidf = lambda: TfidfVectorizer(max_features=50000, ngram_range=(1, 2),
                                    stop_words="english")

    evaluate("Logistic Regression (SEDAS baseline)",
             Pipeline([("tfidf", tfidf()),
                       ("clf", LogisticRegression(max_iter=1000,
                                                  class_weight="balanced"))]),
             X_train, X_test, y_train, y_test)

    evaluate("LinearSVC (benchmark replication)",
             Pipeline([("tfidf", tfidf()),
                       ("clf", LinearSVC(class_weight="balanced"))]),
             X_train, X_test, y_train, y_test)

if __name__ == "__main__":
    main()