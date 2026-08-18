"""
Feedback item 2.2: qualitative look at the 70 SVC false negatives.

Goes further than "sample 10-15 and eyeball them" — it pairs the manual
reading with measurable signals (length, trigger-word presence, punctuation)
so the qualitative claim in the report is backed by numbers, not just
anecdote. That's the difference between "we looked at a few and noticed X"
and "we looked at all 70, and X is true for N of them, versus Y% in the
correctly-caught phishing emails" — the second is what a marker checking
for evidence over plausible narrative wants to see.

DROP-IN NOTES:
- This targets the ORIGINAL single 80/20 split (65,988 train / 16,498 test,
  seed=42, stratified) — the one that produced the locked confusion matrix
  in your report (70 FN / 75 FP / 7844 TN / 8509 TP for SVC). NOT the 5-fold
  CV folds from crossval_significance.py.
- Replace the LOAD SECTION below with however train.py / serve.py already
  loads the raw dataframe (needs the actual email TEXT column, not just
  TF-IDF vectors, since we need to read the missed emails).
- If model.joblib is already the fitted SVC pipeline (vectorizer + classifier
  together), the "load model" line is a one-liner. If model.joblib is just
  the classifier and the vectorizer is separate/refit in train.py, load both
  the same way train.py does before calling .transform() on the test split.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
TEST_SIZE = 0.20  # matches 65,988 / 16,498 split

# --------------------------------------------------------------------------
# 1. LOAD SECTION — replace with your existing loader
# --------------------------------------------------------------------------
# df = load_your_dataset()            # needs columns: text (raw email body), label (1=phishing, 0=legit)
# model = joblib.load("model.joblib") # or joblib.load(...) for vectorizer + classifier separately
# vectorizer = ...                    # if separate from model.joblib

# Recreate the exact split used for Table 13/14 (same seed/proportions)
# X_train_text, X_test_text, y_train, y_test = train_test_split(
#     df["text"], df["label"], test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=df["label"]
# )
# X_test_vec = vectorizer.transform(X_test_text)
# preds = model.predict(X_test_vec)

TRIGGER_WORDS = ["verify", "urgent", "password", "account", "click", "confirm",
                  "suspend", "immediately", "security", "update"]

def analyse_false_negatives(X_test_text, y_test, preds):
    y_test = np.asarray(y_test)
    preds = np.asarray(preds)
    X_test_text = np.asarray(X_test_text)

    fn_mask = (y_test == 1) & (preds == 0)
    tp_mask = (y_test == 1) & (preds == 1)
    fn_idx = np.where(fn_mask)[0]
    tp_idx = np.where(tp_mask)[0]

    print("=" * 70)
    print(f"False negatives found: {len(fn_idx)}  (report states 70 — confirm this matches)")
    print(f"True positives (correctly caught phishing): {len(tp_idx)}")
    print("=" * 70)

    def stats_for(indices, label):
        texts = [X_test_text[i] for i in indices]
        lengths = [len(t.split()) for t in texts]
        trigger_hits = [sum(1 for w in TRIGGER_WORDS if w in t.lower()) for t in texts]
        exclaim_counts = [t.count("!") for t in texts]
        url_like = [t.lower().count("http") + t.lower().count("www.") for t in texts]
        print(f"\n--- {label} (n={len(indices)}) ---")
        print(f"  Mean word count:            {np.mean(lengths):.1f}  (median {np.median(lengths):.0f})")
        print(f"  Mean trigger-word hits:     {np.mean(trigger_hits):.2f}")
        print(f"  Emails with 0 trigger words: {sum(1 for h in trigger_hits if h == 0)} / {len(indices)} "
              f"({100*sum(1 for h in trigger_hits if h == 0)/len(indices):.0f}%)")
        print(f"  Mean exclamation marks:     {np.mean(exclaim_counts):.2f}")
        print(f"  Mean URL-like mentions:     {np.mean(url_like):.2f}")
        return dict(lengths=lengths, trigger_hits=trigger_hits, exclaim=exclaim_counts, url=url_like)

    fn_stats = stats_for(fn_idx, "FALSE NEGATIVES (missed phishing)")
    tp_stats = stats_for(tp_idx, "TRUE POSITIVES (correctly caught phishing)")

    print("\n" + "=" * 70)
    print("COMPARISON — false negatives vs correctly-caught phishing")
    print("=" * 70)
    print(f"Word count:      FN {np.mean(fn_stats['lengths']):.1f} vs TP {np.mean(tp_stats['lengths']):.1f}")
    print(f"Trigger words:   FN {np.mean(fn_stats['trigger_hits']):.2f} vs TP {np.mean(tp_stats['trigger_hits']):.2f}")
    print(f"Exclamations:    FN {np.mean(fn_stats['exclaim']):.2f} vs TP {np.mean(tp_stats['exclaim']):.2f}")
    print(f"URL mentions:    FN {np.mean(fn_stats['url']):.2f} vs TP {np.mean(tp_stats['url']):.2f}")

    print("\n" + "=" * 70)
    print(f"ALL {len(fn_idx)} FALSE NEGATIVES — short preview (first 120 chars)")
    print("=" * 70)
    for rank, i in enumerate(fn_idx, start=1):
        preview = X_test_text[i][:120].replace("\n", " ")
        print(f"[{rank:2d}] {preview}...")

    print("\n" + "=" * 70)
    print("SEEDED SAMPLE OF 15 — full text, for close qualitative reading")
    print("=" * 70)
    rng = np.random.RandomState(RANDOM_STATE)
    sample_idx = rng.choice(fn_idx, size=min(15, len(fn_idx)), replace=False)
    for n, i in enumerate(sorted(sample_idx), start=1):
        print(f"\n----- Sample {n} (test-set index {i}) -----")
        print(X_test_text[i])

    print("\nCopy the COMPARISON block and a few representative samples into")
    print("Section 5.2/5.3 as evidence for the qualitative false-negative discussion.")


if __name__ == "__main__":
    # analyse_false_negatives(X_test_text, y_test, preds)   # <-- uncomment once loaded above
    raise SystemExit(
        "Load df/model/vectorizer as in train.py, recreate the test split, "
        "get preds, then call analyse_false_negatives(X_test_text, y_test, preds)."
    )