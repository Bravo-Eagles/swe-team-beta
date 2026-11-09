#!/usr/bin/env python3
"""Tiny test dataset for the attendance tracker (SQLite).

2 teachers, 8 students, 2 classes, 4 weeks of sessions centered on today
(so there are both past sessions with attendance and future ones without).

Usage:
    python populate_small.py --db attendance.db --schema schema.sql
    python populate_small.py --db attendance.db --reset
"""
import argparse
import random
import sqlite3
from datetime import date, datetime, timedelta
import bcrypt

TEST_PASSWORD = "password123"
ATTEND_PROBABILITY = 0.85
SEMESTER, YEAR = "Fall", 2026

TEACHERS = [("Alice", None, "Nguyen"), ("Bob", "J", "Patel")]
STUDENTS = [  # first, middle, last, active
    ("Cara", None, "Lopez", 1),
    ("Dev", "K", "Shah", 1),
    ("Elena", None, "Rossi", 1),
    ("Frank", "L", "Moore", 1),
    ("Grace", None, "Kim", 1),
    ("Hector", None, "Garcia", 1),
    ("Imani", "R", "Okafor", 1),
    ("Jon", None, "Smith", 0),  # inactive, not enrolled anywhere
]
# name, course_id, teacher index, weekdays (0=Mon), start, end, enrolled student indexes
CLASSES = [
    ("Intro to Programming", "CS101", 0, (0, 2, 4), "09:30", "10:20", [0, 1, 2, 3, 4]),
    ("Calculus I", "MATH101", 1, (1, 3), "11:00", "12:15", [3, 4, 5, 6]),
]
WEEKS = 4


def hash_password(password: str) -> str:
    """Placeholder. Swap in your app's real hash function to allow logins."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="attendance.db")
    ap.add_argument("--schema")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    rng = random.Random(1)
    now = datetime.now()

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    if args.schema:
        with open(args.schema) as f:
            cur.executescript(f.read())
    if args.reset:
        for t in ["attendance", "enrolled", "scheduled", "teaching",
                  "class", "student", "teacher", "sessions", "accounts"]:
            cur.execute(f"DELETE FROM {t}")
    elif cur.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] > 0:
        raise SystemExit("accounts table already has data. Re-run with --reset to wipe it first.")

    pw = hash_password(TEST_PASSWORD)
    acc_id = 0

    def account(first, last, role):
        nonlocal acc_id
        acc_id += 1
        domain = "school.edu" if role == "TEACHER" else "students.school.edu"
        email = f"{first}.{last}@{domain}".lower()
        cur.execute("INSERT INTO accounts (id, email, password_hash, role) VALUES (?,?,?,?)",
                    (acc_id, email, pw, role))
        return acc_id, email

    emails = []
    for i, (f, m, l) in enumerate(TEACHERS, start=1):
        a, e = account(f, l, "TEACHER")
        emails.append(("teacher", e))
        cur.execute("INSERT INTO teacher (id, first_name, middle_name, last_name, account_id) VALUES (?,?,?,?,?)",
                    (i, f, m, l, a))

    for i, (f, m, l, active) in enumerate(STUDENTS, start=1):
        a, e = account(f, l, "STUDENT")
        if i == 1:
            emails.append(("student", e))
        cur.execute("INSERT INTO student (id, first_name, middle_name, last_name, account_id, active) VALUES (?,?,?,?,?,?)",
                    (i, f, m, l, a, active))

    # Monday two weeks ago, so the 4-week window straddles today
    today = date.today()
    first_monday = today - timedelta(days=today.weekday()) - timedelta(weeks=2)

    sched_id = 0
    deleted_flagged = False
    for cid, (name, course_id, t_idx, days, start, end, enrolled_idx) in enumerate(CLASSES, start=1):
        cur.execute("INSERT INTO class (id, name, course_id) VALUES (?,?,?)", (cid, name, course_id))
        # one teaching per class; ids match class ids since there's one semester
        cur.execute("INSERT INTO teaching (id, teacher_id, class_id, semester, year) VALUES (?,?,?,?,?)",
                    (cid, t_idx + 1, cid, SEMESTER, YEAR))
        for s in enrolled_idx:
            cur.execute("INSERT INTO enrolled (teaching_id, student_id) VALUES (?,?)", (cid, s + 1))

        for week in range(WEEKS):
            for wd in days:
                d = first_monday + timedelta(weeks=week, days=wd)
                sched_id += 1
                cur.execute("INSERT INTO scheduled (id, teaching_id, date, start_time, end_time) VALUES (?,?,?,?,?)",
                            (sched_id, cid, d.isoformat(), start, end))
                start_dt = datetime.fromisoformat(f"{d} {start}")
                if start_dt > now:
                    continue  # future session: no attendance yet
                for s in enrolled_idx:
                    if rng.random() > ATTEND_PROBABILITY:
                        continue  # absent
                    check_in = start_dt + timedelta(minutes=rng.randint(-5, 15))
                    deleted = 0 if deleted_flagged else 1  # flag exactly one row as soft-deleted
                    deleted_flagged = True
                    # NOTE: column is spelled "is_delted" in the schema
                    cur.execute("INSERT INTO attendance (scheduled_id, student_id, check_in_time, is_delted) VALUES (?,?,?,?)",
                                (sched_id, s + 1, check_in.isoformat(sep=" ", timespec="seconds"), deleted))

    conn.commit()

    print(f"Populated {args.db}:")
    for t in ["accounts", "teacher", "student", "class", "teaching", "scheduled", "enrolled", "attendance"]:
        print(f"  {t:<11}{cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>5}")
    print(f"\nSample logins (password '{TEST_PASSWORD}', if your hash function matches):")
    for role, e in emails:
        print(f"  {role}: {e}")
    conn.close()


if __name__ == "__main__":
    main()