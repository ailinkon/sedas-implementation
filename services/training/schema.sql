-- SEDAS Training Module — database schema
-- MIS5320 Part B | FR-05 (persona-based micro-lessons), FR-06 (progress tracking)
-- Design: persona-driven content selection grounded in the Theory of Planned
-- Behaviour (Part A §1.2); all user records are fictitious test identities.

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT UNIQUE NOT NULL,
    persona      TEXT NOT NULL CHECK (persona IN ('student','staff','admin')),
    risk_score   REAL DEFAULT 50.0,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lessons (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT UNIQUE NOT NULL,
    title        TEXT NOT NULL,
    persona      TEXT NOT NULL,
    difficulty   INTEGER NOT NULL,
    body         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_code  TEXT NOT NULL,
    prompt       TEXT NOT NULL,
    option_a     TEXT NOT NULL,
    option_b     TEXT NOT NULL,
    option_c     TEXT NOT NULL,
    option_d     TEXT NOT NULL,
    correct      TEXT NOT NULL CHECK (correct IN ('a','b','c','d')),
    explanation  TEXT NOT NULL,
    FOREIGN KEY (lesson_code) REFERENCES lessons(code)
);

CREATE TABLE IF NOT EXISTS attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT NOT NULL,
    lesson_code  TEXT NOT NULL,
    score_pct    REAL NOT NULL,
    answered     INTEGER NOT NULL,
    correct_cnt  INTEGER NOT NULL,
    attempted_at TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(username);