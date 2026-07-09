"""
SEDAS - Phishing Detection Service: Baseline Model Training
MIS5320 Part B | Traceability: FR-01, NFR-01 | Refinement R-04
Trains a TF-IDF + Logistic Regression baseline on public email corpora
(Nazario, Enron, SpamAssassin et al. via Kaggle combined dataset).
"""

import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, classification_report)

DATA_PATH = Path(__file__).parent / "data" / "phishing_email.csv"
MODEL_PATH = Path(__file__).parent / "model.joblib"

def load_data():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    # Auto-detect the text and label columns
    text_col = next(c for c in df.columns if c.lower() in
                    ("text_combined", "text", "body", "email_text", "email"))
    label_col = next(c for c in df.columns if c.lower() in
                     ("label", "class", "category", "type"))
    df = df[[text_col, label_col]].dropna()
    df.columns = ["text", "label"]
    print(f"Using text column '{text_col}', label column '{label_col}'")
    print(df["label"].value_counts())
    return df

def main():
    df = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2,
        random_state=42, stratify=df["label"])
    print(f"Training on {len(X_train)}, testing on {len(X_test)} held-out emails")

    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=50000, ngram_range=(1, 2),
                                  stop_words="english")),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    print("\n===== SEDAS BASELINE MODEL EVALUATION (NFR-01) =====")
    print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
    print(f"F1 score : {f1_score(y_test, y_pred):.4f}   (Part A target: >= 0.95)")
    print(f"False positive rate: {fp / (fp + tn):.4f}   (Part A target: < 0.02)")
    print(f"Confusion matrix: TN={tn} FP={fp} FN={fn} TP={tp}")
    print("\n", classification_report(y_test, y_pred))

    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    main()