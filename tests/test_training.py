"""
SEDAS - Awareness Training Service Test Suite
MIS5320 Part B | Test IDs TT-01..TT-06 traced to FR-05, FR-06

Verifies the scoring engine: attempt scoring, EWMA risk update,
risk banding, and persona-aware adaptive lesson selection.
These tests are model-free and therefore execute in CI.

Run: pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "training"))

import serve  # noqa: E402


# ---------------------------------------------------------------
# Fixtures - a representative lesson set for selection tests
# ---------------------------------------------------------------

LESSONS = [
    {"code": "SE-101", "title": "Urgency tactics", "persona": "all",
     "difficulty": 1, "body": ""},
    {"code": "SE-102", "title": "Checking links", "persona": "all",
     "difficulty": 1, "body": ""},
    {"code": "SE-201", "title": "MFA fatigue", "persona": "staff",
     "difficulty": 2, "body": ""},
    {"code": "SE-202", "title": "Protecting data", "persona": "staff",
     "difficulty": 2, "body": ""},
    {"code": "SE-301", "title": "Privilege escalation", "persona": "admin",
     "difficulty": 3, "body": ""},
]


# ---------------------------------------------------------------
# TT-01 - attempt scoring (FR-06)
# ---------------------------------------------------------------

def test_tt01_score_calculation():
    """TT-01 (FR-06): percentage score computed correctly, including the
    divide-by-zero guard when no questions were answered."""
    assert serve.score_attempt(3, 4) == 75.0
    assert serve.score_attempt(4, 4) == 100.0
    assert serve.score_attempt(0, 4) == 0.0
    assert serve.score_attempt(0, 0) == 0.0      # guard: no division error
    assert serve.score_attempt(1, 3) == 33.3     # rounded to 1 decimal


# ---------------------------------------------------------------
# TT-02 / TT-03 - EWMA risk update (FR-06)
# ---------------------------------------------------------------

def test_tt02_risk_decreases_on_good_score():
    """TT-02 (FR-06): a high quiz score lowers the user's risk score."""
    new_risk = serve.update_risk(50.0, 100.0)
    assert new_risk < 50.0
    # EWMA with ALPHA=0.4: 0.6*50 + 0.4*(100-100) = 30.0
    assert new_risk == 30.0


def test_tt03_risk_increases_on_poor_score():
    """TT-03 (FR-06): a low quiz score raises risk, and the result stays
    within the valid 0-100 range."""
    new_risk = serve.update_risk(50.0, 0.0)
    assert new_risk > 50.0
    # EWMA with ALPHA=0.4: 0.6*50 + 0.4*(100-0) = 70.0
    assert new_risk == 70.0
    # Boundary conditions must remain clamped
    assert 0.0 <= serve.update_risk(0.0, 100.0) <= 100.0
    assert 0.0 <= serve.update_risk(100.0, 0.0) <= 100.0


# ---------------------------------------------------------------
# TT-04 - risk banding (FR-06)
# ---------------------------------------------------------------

def test_tt04_risk_bands():
    """TT-04 (FR-06): numeric risk maps to the correct band, including
    at the threshold boundaries."""
    assert serve.risk_band(0) == "low"
    assert serve.risk_band(32.9) == "low"
    assert serve.risk_band(33) == "medium"
    assert serve.risk_band(65.9) == "medium"
    assert serve.risk_band(66) == "high"
    assert serve.risk_band(100) == "high"


# ---------------------------------------------------------------
# TT-05 - adaptive lesson selection (FR-05)
# ---------------------------------------------------------------

def test_tt05_next_lesson_respects_persona_and_risk():
    """TT-05 (FR-05): lesson selection filters by persona and serves
    foundational (difficulty 1) content to a high-risk user."""
    lesson = serve.next_lesson_for("student", 80, [], LESSONS)
    assert lesson is not None
    assert lesson["persona"] in ("student", "all")
    assert lesson["difficulty"] == 1       # high risk -> easiest first

    # A staff user at medium risk should receive difficulty 2 content
    lesson = serve.next_lesson_for("staff", 50, [], LESSONS)
    assert lesson["difficulty"] == 2
    assert lesson["persona"] in ("staff", "all")


def test_tt05b_completed_lessons_excluded():
    """TT-05 (FR-05): lessons already completed are not served again,
    and None is returned once no eligible lessons remain."""
    lesson = serve.next_lesson_for("student", 80, ["SE-101"], LESSONS)
    assert lesson["code"] != "SE-101"

    # A student has access only to the two 'all' lessons
    lesson = serve.next_lesson_for("student", 80, ["SE-101", "SE-102"], LESSONS)
    assert lesson is None


# ---------------------------------------------------------------
# TT-06 - fallback behaviour (FR-05)
# ---------------------------------------------------------------

def test_tt06_falls_back_when_target_difficulty_unavailable():
    """TT-06 (FR-05): where no lesson matches the target difficulty, the
    selector falls back to any remaining eligible lesson rather than
    leaving the user with no content."""
    # A low-risk student targets difficulty 3, but only difficulty 1
    # lessons exist for the 'all' persona - a lesson must still be returned.
    lesson = serve.next_lesson_for("student", 10, [], LESSONS)
    assert lesson is not None
    assert lesson["persona"] in ("student", "all")
