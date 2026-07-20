"""
SEDAS - Awareness Training Service
MIS5320 Part B | FR-05 (persona-based micro-lessons), FR-06 (progress tracking)
Runs on port 8003.

OWNERSHIP NOTE:
  Scaffold (schema, seeding, endpoints, persistence): A. Islam
  score_attempt() + next_lesson_for() scoring engine: D. Kipchirchir  <-- see TODO
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
# SCORING ENGINE — owner: Dominic Kipchirchir
#
# SPEC (implement below, replacing the TODO):
#
# score_attempt(correct_cnt, answered) -> float
#   Return the percentage score for one quiz attempt, 0.0-100.0,
#   rounded to 1 decimal place. If answered == 0, return 0.0
#   (guard against division by zero).
#
# update_risk(current_risk, score_pct) -> float
#   Recalculate a user's risk score after an attempt, using an
#   exponentially weighted moving average so recent behaviour counts
#   more than old behaviour:
#       new_risk = (1 - ALPHA) * current_risk + ALPHA * (100 - score_pct)
#   with ALPHA = 0.4. Clamp the result to 0.0-100.0 and round to 1dp.
#   Rationale: a high quiz score should LOWER risk, and one bad attempt
#   should not erase a long good history.
#
# risk_band(risk) -> str
#   "low" if risk < 33, "medium" if risk < 66, otherwise "high".
#
# next_lesson_for(persona, risk, completed_codes, all_lessons) -> dict | None
#   Choose the next lesson: filter all_lessons to those matching the
#   user's persona (or persona 'all') and NOT already in completed_codes;
#   target difficulty 1 for "low" risk users... wait, higher risk needs
#   easier reinforcement first: difficulty 1 for "high" risk,
#   2 for "medium", 3 for "low". If nothing matches that difficulty,
#   fall back to any remaining eligible lesson. Return the lesson dict
#   or None if all are completed.
# ---------------------------------------------------------------

ALPHA = 0.4


def score_attempt(correct_cnt: int, answered: int) -> float:
    raise NotImplementedError("TODO(dominic): implement per spec above")


def update_risk(current_risk: float, score_pct: float) -> float:
    raise NotImplementedError("TODO(dominic): implement per spec above")


def risk_band(risk: float) -> str:
    raise NotImplementedError("TODO(dominic): implement per spec above")


def next_lesson_for(persona, risk, completed_codes, all_lessons):
    raise NotImplementedError("TODO(dominic): implement per spec above")


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