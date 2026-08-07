"""
SEDAS - DistilBERT Preliminary Comparison
MIS5320 Part B | Preliminary results per supervisor directive:
transformer-based approach as the escalation beyond classical TF-IDF +
linear methods, which have plateaued near the benchmark paper's own
ceiling (~99.15-99.17% F1) after preprocessing and ensemble experiments.

NOTE: This is a PRELIMINARY run on a stratified subsample of the full
82,486-email dataset, due to CPU-only training time constraints. Full-
dataset fine-tuning is documented as future work.

Run: python services/detection/distilbert_preliminary.py
"""

import pandas as pd
import torch
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix)
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

DATA_PATH = Path(__file__).parent / "data" / "phishing_email.csv"

# Preliminary run settings - deliberately small for CPU feasibility.
# Increase these later (with more time/GPU access) for final results.
SAMPLE_SIZE = 6000
MAX_LENGTH = 128
BATCH_SIZE = 8
EPOCHS = 2
LEARNING_RATE = 2e-5

OUR_SVC_F1 = 99.16
PAPER_SVC_F1 = 99.0


def load_sample():
    df = pd.read_csv(DATA_PATH)
    text_col = next(c for c in df.columns if c.lower() in
                    ("text_combined", "text", "body", "email_text", "email"))
    label_col = next(c for c in df.columns if c.lower() in
                     ("label", "class", "category", "type"))
    df = df[[text_col, label_col]].dropna()
    df.columns = ["text", "label"]
    df_sample, _ = train_test_split(
        df, train_size=SAMPLE_SIZE, random_state=42, stratify=df["label"])
    return df_sample.reset_index(drop=True)


class EmailDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.encodings = tokenizer(list(texts), truncation=True,
                                   padding=True, max_length=MAX_LENGTH)
        self.labels = list(labels)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(int(self.labels[idx]))
        return item


def main():
    print(f"PRELIMINARY RUN - stratified subsample of {SAMPLE_SIZE} emails")
    print("(full-dataset fine-tuning deferred to future work)\n")
    print(f"Reference - paper [41] SVC: {PAPER_SVC_F1}%")
    print(f"Reference - our tuned SVC (full dataset): {OUR_SVC_F1}%\n")

    df = load_sample()
    print(f"Sample: {len(df)} emails "
          f"({(df['label']==1).sum()} phishing / {(df['label']==0).sum()} legitimate)")

    train_texts, test_texts, train_labels, test_labels = train_test_split(
        df["text"], df["label"], test_size=0.2,
        random_state=42, stratify=df["label"])
    print(f"Train: {len(train_texts)} | Test: {len(test_texts)}\n")

    print("Loading DistilBERT (first run downloads ~260MB, cached after)...")
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    model = DistilBertForSequenceClassification.from_pretrained(
        "distilbert-base-uncased", num_labels=2)

    train_ds = EmailDataset(train_texts, train_labels, tokenizer)
    test_ds = EmailDataset(test_texts, test_labels, tokenizer)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}\n")
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    print("=" * 60)
    print(f"TRAINING - {EPOCHS} epoch(s), batch size {BATCH_SIZE}")
    print("=" * 60)
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        for i, batch in enumerate(train_loader):
            optimizer.zero_grad()
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            if (i + 1) % 50 == 0:
                print(f"  epoch {epoch+1} batch {i+1}/{len(train_loader)} "
                      f"avg loss: {total_loss/(i+1):.4f}")
        print(f"Epoch {epoch+1} complete. Average loss: {total_loss/len(train_loader):.4f}")

    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for batch in test_loader:
            labels = batch.pop("labels").to(device)
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            preds = torch.argmax(outputs.logits, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    tn, fp, fn, tp = confusion_matrix(all_labels, all_preds).ravel()
    acc = accuracy_score(all_labels, all_preds) * 100
    prec = precision_score(all_labels, all_preds) * 100
    rec = recall_score(all_labels, all_preds) * 100
    f1 = f1_score(all_labels, all_preds) * 100

    print(f"\n--- DistilBERT (preliminary, {SAMPLE_SIZE}-email subsample) ---")
    print(f"Accuracy : {acc:.2f}%")
    print(f"Precision: {prec:.2f}%")
    print(f"Recall   : {rec:.2f}%")
    print(f"F1 score : {f1:.2f}%")
    print(f"FP rate  : {fp / (fp + tn):.4f}")
    print(f"Confusion: TN={tn} FP={fp} FN={fn} TP={tp}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Paper [41] SVC (full dataset)':<50} F1={PAPER_SVC_F1:.2f}%")
    print(f"{'Our tuned SVC (full dataset)':<50} F1={OUR_SVC_F1:.2f}%")
    print(f"{'DistilBERT (PRELIMINARY, ' + str(SAMPLE_SIZE) + '-sample)':<50} F1={f1:.2f}%")
    print("\nNOTE: trained on a small subsample due to CPU time constraints.")
    print("Comparison to full-dataset classical results is indicative only.")
    print("Full-dataset fine-tuning is documented as future work.")


if __name__ == "__main__":
    main()
