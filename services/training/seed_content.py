"""
SEDAS - Training Content Seeder
MIS5320 Part B | FR-05 — persona-based micro-lessons (Theory of Planned Behaviour)

OWNERSHIP: starter set by A. Islam; content library extended and maintained
by Sonu (250001). Add lessons/questions to the lists below and re-run.
Run: python services/training/seed_content.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "training.db"
SCHEMA = Path(__file__).parent / "schema.sql"

LESSONS = [
    ("SE-101", "Spotting urgency and fear tactics", "all", 1,
     "Attackers manufacture urgency so you act before you think. Deadlines "
     "('within 24 hours'), threats of account suspension, and warnings about "
     "unauthorised access are designed to bypass careful judgement. "
     "Slow down: legitimate organisations do not demand instant credential "
     "entry under threat."),
    ("SE-102", "Checking links before you click", "all", 1,
     "Hover over a link to reveal its true destination. Watch for lookalike "
     "domains (apex-verify.example vs apex.edu.au), raw IP addresses, "
     "excessive subdomains, high-risk top-level domains, and URL shorteners "
     "that hide the destination entirely."),
    ("SE-201", "Credential requests and MFA fatigue", "staff", 2,
     "No legitimate IT department asks for your password by email or chat. "
     "Repeated multi-factor prompts you did not trigger are an attack in "
     "progress, not a glitch: deny them and report immediately."),
    ("SE-202", "Protecting research and student data", "staff", 2,
     "Targeted (spear) phishing uses real names, unit codes and current "
     "events to appear credible. Verify unusual data or payment requests "
     "through a second channel you look up yourself — never a number or "
     "link supplied in the message."),
    ("SE-301", "Administrative privilege and escalation", "admin", 3,
     "Privileged accounts are the highest-value target. Use separate "
     "administrative identities, apply least privilege, and treat any "
     "request to bypass process as hostile until independently verified."),
]

QUESTIONS = [
    ("SE-101", "An email says your account will be closed in 12 hours unless you verify now. What is the strongest signal this is phishing?",
     "It has a spelling mistake", "It creates artificial time pressure",
     "It was sent in the evening", "It has an attachment", "b",
     "Manufactured urgency is the core social-engineering lever: it pushes the target to act before verifying."),
    ("SE-101", "What is the safest first action on receiving such a message?",
     "Click the link to check", "Reply asking if it is genuine",
     "Verify through an official channel you look up yourself", "Forward it to colleagues", "c",
     "Independent verification breaks the attacker's control of the communication channel."),
    ("SE-102", "Which URL is most suspicious?",
     "https://apex.edu.au/library", "https://portal.apex.edu.au/login",
     "http://apex-verify-login.secure-update.xyz/account", "https://apex.edu.au/news", "c",
     "It combines no HTTPS, lookalike hyphenated wording, a high-risk TLD, and credential-lure keywords."),
    ("SE-102", "Why are URL shorteners a risk in unsolicited messages?",
     "They are slower to load", "They hide the real destination",
     "They break on mobile", "They cost money", "b",
     "The destination cannot be inspected before clicking, defeating visual verification."),
    ("SE-201", "You receive three MFA prompts you did not initiate. What should you do?",
     "Approve one to stop the prompts", "Ignore them and continue working",
     "Deny them and report to IT immediately", "Turn MFA off temporarily", "c",
     "Unsolicited prompts mean someone already has your password — this is MFA fatigue, an attack in progress."),
    ("SE-202", "A message from your unit coordinator's name asks for a student list 'urgently'. Best response?",
     "Send it — the name is familiar", "Check the sender address and confirm by a known phone number",
     "Reply to the email asking for confirmation", "Post in the group chat", "b",
     "Display names are trivially spoofed; confirmation must use a channel the attacker does not control."),
    ("SE-301", "Why should administrators use a separate privileged account?",
     "It is faster", "It limits blast radius if the daily account is compromised",
     "It is required by law", "It avoids password changes", "b",
     "Separation of duties means a compromised routine account does not hand over administrative control."),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA.read_text())
    conn.executemany(
        "INSERT OR IGNORE INTO lessons (code, title, persona, difficulty, body) "
        "VALUES (?,?,?,?,?)", LESSONS)
    for q in QUESTIONS:
        exists = conn.execute(
            "SELECT 1 FROM questions WHERE lesson_code=? AND prompt=?",
            (q[0], q[1])).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO questions (lesson_code, prompt, option_a, option_b, "
                "option_c, option_d, correct, explanation) VALUES (?,?,?,?,?,?,?,?)", q)
    conn.commit()
    n_l = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
    n_q = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    conn.close()
    print(f"Seeded. Lessons: {n_l}, Questions: {n_q}")


if __name__ == "__main__":
    main()