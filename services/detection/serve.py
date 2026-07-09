"""
SEDAS - Phishing Detection Service: Classification API
MIS5320 Part B | Traceability: FR-01, FR-02, FR-09 | NFR-03
Exposes the trained baseline model via POST /classify with explainability.
"""

import time
import joblib
import numpy as np
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_PATH = Path(__file__).parent / "model.joblib"

app = FastAPI(
    title="SEDAS Phishing Detection Service",
    description="Classifies email text and returns a phishing risk score "
                "with the top contributing indicators (FR-01, FR-02).",
    version="0.1.0",
)

model = joblib.load(MODEL_PATH)
vectorizer = model.named_steps["tfidf"]
classifier = model.named_steps["clf"]
feature_names = np.array(vectorizer.get_feature_names_out())


class EmailIn(BaseModel):
    text: str


class ClassificationOut(BaseModel):
    label: str
    risk_score: float
    top_indicators: list[str]
    latency_ms: float


@app.post("/classify", response_model=ClassificationOut)
def classify(email: EmailIn):
    start = time.perf_counter()

    proba = model.predict_proba([email.text])[0]
    phishing_prob = float(proba[1])
    label = "phishing" if phishing_prob >= 0.5 else "legitimate"

    # Explainability (FR-02): which words pushed the score up the most
    vec = vectorizer.transform([email.text])
    contributions = vec.toarray()[0] * classifier.coef_[0]
    top_idx = np.argsort(contributions)[-5:][::-1]
    indicators = [feature_names[i] for i in top_idx if contributions[i] > 0]

    latency_ms = (time.perf_counter() - start) * 1000
    return ClassificationOut(
        label=label,
        risk_score=round(phishing_prob * 100, 2),
        top_indicators=indicators,
        latency_ms=round(latency_ms, 1),
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "detection", "model": "tfidf-lr-baseline"}