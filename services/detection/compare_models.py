"""
SEDAS - Improved Logistic Regression Phishing Email Detector

Improvements:
- Word-level TF-IDF features
- Character-level TF-IDF features
- Trigrams
- Sublinear term frequency
- Duplicate removal
- Balanced class weights
- Validation-based threshold optimisation
- Saved model and threshold

Run:
    python services/detection/compare_models.py

Required packages:
    pip install pandas scikit-learn joblib numpy
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline


# ---------------------------------------------------------
# File locations
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "phishing_email.csv"

MODEL_PATH = BASE_DIR / "improved_logistic_regression.joblib"


# ---------------------------------------------------------
# Find a column automatically
# ---------------------------------------------------------

def find_column(columns, accepted_names, column_description):
    """
    Find the first column that matches one of the accepted names.
    """

    for column in columns:
        cleaned_name = column.lower().strip()

        if cleaned_name in accepted_names:
            return column

    raise ValueError(
        f"Could not find the {column_description} column.\n"
        f"Available columns: {list(columns)}\n"
        f"Accepted names: {sorted(accepted_names)}"
    )


# ---------------------------------------------------------
# Convert labels to 0 and 1
# ---------------------------------------------------------

def normalise_labels(labels):
    """
    Convert common phishing labels to binary values.

    0 = legitimate email
    1 = phishing email
    """

    if pd.api.types.is_numeric_dtype(labels):

        unique_labels = sorted(labels.dropna().unique().tolist())

        if len(unique_labels) != 2:
            raise ValueError(
                "The dataset must contain exactly two classes. "
                f"Classes found: {unique_labels}"
            )

        if set(unique_labels) == {0, 1}:
            return labels.astype(int)

        mapping = {
            unique_labels[0]: 0,
            unique_labels[1]: 1,
        }

        print(f"Numeric label mapping: {mapping}")

        return labels.map(mapping).astype(int)

    cleaned_labels = labels.astype(str).str.lower().str.strip()

    label_mapping = {
        "0": 0,
        "legitimate": 0,
        "legit": 0,
        "safe": 0,
        "safe email": 0,
        "ham": 0,
        "normal": 0,
        "benign": 0,
        "non-phishing": 0,
        "not phishing": 0,

        "1": 1,
        "phishing": 1,
        "phish": 1,
        "phishing email": 1,
        "spam": 1,
        "malicious": 1,
        "fraud": 1,
        "fraudulent": 1,
    }

    converted_labels = cleaned_labels.map(label_mapping)

    if converted_labels.isna().any():

        unknown_labels = sorted(
            cleaned_labels[converted_labels.isna()].unique().tolist()
        )

        raise ValueError(
            "Some labels could not be converted.\n"
            f"Unknown labels: {unknown_labels}\n"
            "Add these labels to the label_mapping dictionary."
        )

    return converted_labels.astype(int)


# ---------------------------------------------------------
# Load and clean the dataset
# ---------------------------------------------------------

def load_data():
    """
    Load, clean and validate the phishing email dataset.
    """

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{DATA_PATH}\n\n"
            "Create a data folder beside this script and place "
            "phishing_email.csv inside it."
        )

    dataframe = pd.read_csv(DATA_PATH)

    print("=" * 70)
    print("SEDAS -  LOGISTIC REGRESSION")
    print("=" * 70)

    print(f"Original rows: {len(dataframe):,}")
    print(f"Columns: {list(dataframe.columns)}")

    text_column = find_column(
        dataframe.columns,
        {
            "text_combined",
            "text",
            "body",
            "email_text",
            "email",
            "message",
        },
        "email text",
    )

    label_column = find_column(
        dataframe.columns,
        {
            "label",
            "class",
            "category",
            "type",
            "target",
        },
        "label",
    )

    dataframe = dataframe[[text_column, label_column]].copy()

    dataframe.columns = ["text", "label"]

    # Remove missing values
    dataframe = dataframe.dropna(subset=["text", "label"])

    # Convert email text to strings
    dataframe["text"] = dataframe["text"].astype(str).str.strip()

    # Remove empty email messages
    dataframe = dataframe[dataframe["text"].str.len() > 0]

    # Remove duplicate emails
    rows_before_duplicates = len(dataframe)

    dataframe = dataframe.drop_duplicates(
        subset=["text"]
    ).reset_index(drop=True)

    duplicates_removed = rows_before_duplicates - len(dataframe)

    # Convert labels to 0 and 1
    dataframe["label"] = normalise_labels(dataframe["label"])

    print(f"Text column: {text_column}")
    print(f"Label column: {label_column}")
    print(f"Duplicates removed: {duplicates_removed:,}")
    print(f"Clean rows: {len(dataframe):,}")

    print("\nClass distribution:")
    print(dataframe["label"].value_counts().sort_index())

    print("\n0 = legitimate email")
    print("1 = phishing email")

    return dataframe


# ---------------------------------------------------------
# Create the improved Logistic Regression pipeline
# ---------------------------------------------------------

def create_model():
    """
    Create a pipeline combining word-level and character-level
    TF-IDF features with Logistic Regression.
    """

    features = FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    analyzer="word",

                    # Convert text to lowercase
                    lowercase=True,

                    # Normalise accented characters
                    strip_accents="unicode",

                    # Use individual words, bigrams and trigrams
                    ngram_range=(1, 3),

                    # Maximum number of word features
                    max_features=100000,

                    # Ignore terms appearing in fewer than two emails
                    min_df=2,

                    # Ignore terms appearing in more than 95% of emails
                    max_df=0.95,

                    # Apply logarithmic scaling to term frequencies
                    sublinear_tf=True,

                    # Remove common English words
                    stop_words="english",
                ),
            ),

            (
                "character_tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",

                    lowercase=True,

                    # Character combinations of length 3 to 5
                    ngram_range=(3, 5),

                    # Maximum number of character features
                    max_features=50000,

                    min_df=2,

                    max_df=1.0,

                    sublinear_tf=True,
                ),
            ),
        ]
    )

    classifier = LogisticRegression(
        # Controls regularisation strength
        C=5.0,

        # Suitable solver for binary classification
        solver="liblinear",

        # L2 regularisation
        penalty="l2",

        # Maximum optimisation iterations
        max_iter=3000,

        # Handle unequal class distribution
        class_weight="balanced",

        # Reproducible results
        random_state=42,
    )

    model = Pipeline(
        [
            ("features", features),
            ("classifier", classifier),
        ]
    )

    return model


# ---------------------------------------------------------
# Find the best classification threshold
# ---------------------------------------------------------

def find_best_threshold(model, validation_text, validation_labels):
    """
    Test thresholds from 0.10 to 0.90 and select the threshold
    with the highest validation F1 score.
    """

    probabilities = model.predict_proba(validation_text)[:, 1]

    best_threshold = 0.50
    best_f1 = 0.0

    for threshold in np.arange(0.10, 0.91, 0.01):

        predictions = (
            probabilities >= threshold
        ).astype(int)

        current_f1 = f1_score(
            validation_labels,
            predictions,
            zero_division=0,
        )

        if current_f1 > best_f1:
            best_f1 = current_f1
            best_threshold = float(threshold)

    return best_threshold, best_f1


# ---------------------------------------------------------
# Evaluate the trained model
# ---------------------------------------------------------

def evaluate_model(model, test_text, test_labels, threshold):
    """
    Evaluate the trained model using the selected threshold.
    """

    probabilities = model.predict_proba(test_text)[:, 1]

    predictions = (
        probabilities >= threshold
    ).astype(int)

    confusion = confusion_matrix(
        test_labels,
        predictions,
        labels=[0, 1],
    )

    tn, fp, fn, tp = confusion.ravel()

    accuracy = accuracy_score(
        test_labels,
        predictions,
    )

    precision = precision_score(
        test_labels,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        test_labels,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        test_labels,
        predictions,
        zero_division=0,
    )

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0.0
    )

    print("\n" + "=" * 70)
    print("FINAL TEST RESULTS")
    print("=" * 70)

    print(f"Selected threshold : {threshold:.2f}")
    print(f"Accuracy           : {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print(f"Precision          : {precision:.4f} ({precision * 100:.2f}%)")
    print(f"Recall             : {recall:.4f} ({recall * 100:.2f}%)")
    print(f"F1 score           : {f1:.4f} ({f1 * 100:.2f}%)")
    print(f"False-positive rate: {false_positive_rate:.4f}")

    print(
        f"Confusion matrix   : "
        f"TN={tn}, FP={fp}, FN={fn}, TP={tp}"
    )

    print("\nClassification report:")

    print(
        classification_report(
            test_labels,
            predictions,
            labels=[0, 1],
            target_names=[
                "Legitimate",
                "Phishing",
            ],
            zero_division=0,
        )
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": false_positive_rate,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


# ---------------------------------------------------------
# Main program
# ---------------------------------------------------------

def main():
    """
    Run the complete training and evaluation process.
    """

    dataframe = load_data()

    # First split:
    # 70% training
    # 30% temporary data
    X_train, X_temporary, y_train, y_temporary = train_test_split(
        dataframe["text"],
        dataframe["label"],
        test_size=0.30,
        random_state=42,
        stratify=dataframe["label"],
    )

    # Divide temporary data equally:
    # 15% validation
    # 15% final testing
    X_validation, X_test, y_validation, y_test = train_test_split(
        X_temporary,
        y_temporary,
        test_size=0.50,
        random_state=42,
        stratify=y_temporary,
    )

    print("\n" + "=" * 70)
    print("DATA SPLIT")
    print("=" * 70)

    print(f"Training emails  : {len(X_train):,}")
    print(f"Validation emails: {len(X_validation):,}")
    print(f"Testing emails   : {len(X_test):,}")

    model = create_model()

    print("\nTraining improved Logistic Regression model...")

    model.fit(
        X_train,
        y_train,
    )

    print("Training completed.")

    # Select the best threshold using validation data
    best_threshold, validation_f1 = find_best_threshold(
        model,
        X_validation,
        y_validation,
    )

    print("\n" + "=" * 70)
    print("THRESHOLD OPTIMISATION")
    print("=" * 70)

    print(f"Best validation threshold: {best_threshold:.2f}")
    print(f"Validation F1 score       : {validation_f1:.4f}")
    print(f"Validation F1 percentage  : {validation_f1 * 100:.2f}%")

    # Evaluate once using the untouched final test set
    results = evaluate_model(
        model,
        X_test,
        y_test,
        best_threshold,
    )

    # Save model, threshold and metadata
    model_package = {
        "model": model,
        "threshold": best_threshold,
        "label_mapping": {
            0: "legitimate",
            1: "phishing",
        },
        "metrics": results,
    }

    joblib.dump(
        model_package,
        MODEL_PATH,
    )

    print("\n" + "=" * 70)
    print("MODEL SAVED")
    print("=" * 70)

    print(f"Saved to:\n{MODEL_PATH}")

    print("\nProgram completed successfully.")


if __name__ == "__main__":
    main()