"""
SEDAS - Awareness Training Service
MIS5320 Part B | FR-05 (persona-based micro-lessons), FR-06 (progress tracking)
Runs on port 8003.

Scoring engine: score_attempt(), update_risk(), risk_band(), next_lesson_for()
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = Path(__file__).parent / "training.db"
SCHEMA = Path(__file__).parent / "schema.sql"

app = FastAPI(
    title="SEDAS Awareness Training Service",
    description="Persona-based micro-lessons, quizzes and per-user risk "
                "tracking (FR-05, FR-06).",
    version="0.1.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA.read_text())
    return conn


def now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------
# SCORING ENGINE
#
# ALPHA controls how strongly the most recent attempt influences a
# user's risk score relative to their history. At 0.4, recent behaviour
# matters substantially but a single poor attempt cannot erase a
# sustained good record.
# ---------------------------------------------------------------

ALPHA = 0.4


def score_attempt(correct_cnt: int, answered: int) -> float:
    """Percentage score for one attempt, 0.0-100.0, guarded against
    division by zero when no questions were answered."""
    if answered == 0:
        return 0.0
    return round((correct_cnt / answered) * 100, 1)


def update_risk(current_risk: float, score_pct: float) -> float:
    """Exponentially weighted moving average of risk.

    A high quiz score lowers risk; a low score raises it. The result is
    clamped to the 0-100 range and rounded to one decimal place.
    """
    new_risk = (1 - ALPHA) * current_risk + ALPHA * (100 - score_pct)
    return round(max(0.0, min(100.0, new_risk)), 1)


def risk_band(risk: float) -> str:
    """Map a numeric risk score onto a coarse band used for lesson
    selection and dashboard reporting."""
    if risk < 33:
        return "low"
    if risk < 66:
        return "medium"
    return "high"


def next_lesson_for(persona, risk, completed_codes, all_lessons):
    """Choose the next lesson for a user, or None if all are completed.

    Difficulty is inverted against risk deliberately: a high-risk user
    receives foundational material first, because reinforcing basics is
    more effective than escalating difficulty for someone who is
    struggling. A low-risk user receives advanced material to remain
    challenged.
    """
    eligible = [
        lesson for lesson in all_lessons
        if lesson["persona"] in (persona, "all")
        and lesson["code"] not in completed_codes
    ]
    if not eligible:
        return None

    band = risk_band(risk)
    target_difficulty = {"high": 1, "medium": 2, "low": 3}[band]

    preferred = [l for l in eligible if l["difficulty"] == target_difficulty]
    if preferred:
        return preferred[0]

    # Fall back to any remaining eligible lesson so the user is never
    # left without content while lessons remain unseen.
    return eligible[0]


# ---------------------------------------------------------------
# API models
# ---------------------------------------------------------------

class UserIn(BaseModel):
    username: str
    persona: Literal["student", "staff", "admin"]


class SubmissionIn(BaseModel):
    username: str
    lesson_code: str
    answers: dict          # {"1": "a", "2": "c", ...} question_id -> choice


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------

@app.post("/users")
def create_user(u: UserIn):
    conn = db()
    try:
        conn.execute("INSERT INTO users (username, persona, created_at) "
                     "VALUES (?,?,?)", (u.username, u.persona, now()))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "username already exists")
    finally:
        conn.close()
    return {"created": True, "username": u.username, "persona": u.persona}


@app.get("/lessons")
def list_lessons(persona: str | None = None):
    conn = db()
    rows = conn.execute("SELECT * FROM lessons").fetchall()
    conn.close()
    out = [dict(r) for r in rows]
    if persona:
        out = [l for l in out if l["persona"] in (persona, "all")]
    return {"count": len(out), "lessons": out}


@app.get("/lessons/{code}/quiz")
def get_quiz(code: str):
    conn = db()
    rows = conn.execute(
        "SELECT id, prompt, option_a, option_b, option_c, option_d "
        "FROM questions WHERE lesson_code = ?", (code,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(404, "no questions for that lesson")
    return {"lesson_code": code, "questions": [dict(r) for r in rows]}


@app.post("/submit")
def submit(s: SubmissionIn):
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE username = ?",
                        (s.username,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(404, "unknown user")

    qs = conn.execute("SELECT id, correct, explanation FROM questions "
                      "WHERE lesson_code = ?", (s.lesson_code,)).fetchall()
    if not qs:
        conn.close()
        raise HTTPException(404, "no questions for that lesson")

    correct_cnt, feedback = 0, []
    for q in qs:
        given = s.answers.get(str(q["id"]))
        ok = given == q["correct"]
        correct_cnt += ok
        feedback.append({"question_id": q["id"], "correct": ok,
                         "expected": q["correct"],
                         "explanation": q["explanation"]})

    score = score_attempt(correct_cnt, len(qs))
    new_risk = update_risk(user["risk_score"], score)

    conn.execute("INSERT INTO attempts (username, lesson_code, score_pct, "
                 "answered, correct_cnt, attempted_at) VALUES (?,?,?,?,?,?)",
                 (s.username, s.lesson_code, score, len(qs), correct_cnt, now()))
    conn.execute("UPDATE users SET risk_score = ? WHERE username = ?",
                 (new_risk, s.username))
    conn.commit()
    conn.close()

    return {"score_pct": score, "correct": correct_cnt, "answered": len(qs),
            "risk_score": new_risk, "risk_band": risk_band(new_risk),
            "feedback": feedback}


@app.get("/progress/{username}")
def progress(username: str):
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE username = ?",
                        (username,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(404, "unknown user")
    attempts = conn.execute(
        "SELECT lesson_code, score_pct, attempted_at FROM attempts "
        "WHERE username = ? ORDER BY id", (username,)).fetchall()
    lessons = [dict(r) for r in conn.execute("SELECT * FROM lessons").fetchall()]
    conn.close()

    completed = sorted({a["lesson_code"] for a in attempts})
    nxt = next_lesson_for(user["persona"], user["risk_score"], completed, lessons)
    return {
        "username": username,
        "persona": user["persona"],
        "risk_score": user["risk_score"],
        "risk_band": risk_band(user["risk_score"]),
        "completed_lessons": completed,
        "attempts": [dict(a) for a in attempts],
        "next_lesson": {"code": nxt["code"], "title": nxt["title"]} if nxt else None,
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "training"}
