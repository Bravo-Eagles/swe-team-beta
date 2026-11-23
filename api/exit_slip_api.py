"""Persist exit slips and limit access to enrolled students and class teachers."""

from contextlib import closing
from datetime import datetime, timezone

from src import database as db


QUESTION = "What is one thing you learned today, and what is one question you still have?"


def list_student_meetings(account_id):
    with closing(db.get_connection()) as conn:
        return conn.execute(
            """SELECT sc.id, sc.date, sc.start_time, c.name, c.course_id
               FROM scheduled sc
               JOIN teaching t ON t.id = sc.teaching_id
               JOIN class c ON c.id = t.class_id
               JOIN enrolled e ON e.teaching_id = t.id
               JOIN student s ON s.id = e.student_id
               WHERE s.account_id = ?
               ORDER BY sc.date DESC, sc.start_time DESC, sc.id DESC""",
            (account_id,),
        ).fetchall()


def submit_exit_slip(account_id, scheduled_id, answer):
    answer = answer.strip()
    if not answer:
        raise ValueError("Please enter a response.")
    with closing(db.get_connection()) as conn, conn:
        student = conn.execute(
            """SELECT s.id FROM student s
               JOIN enrolled e ON e.student_id = s.id
               JOIN scheduled sc ON sc.teaching_id = e.teaching_id
               WHERE s.account_id = ? AND sc.id = ?""",
            (account_id, scheduled_id),
        ).fetchone()
        if student is None:
            raise ValueError("You are not enrolled in this class meeting.")
        conn.execute(
            """INSERT INTO exit_slip
                   (scheduled_id, student_id, question, answer, submitted_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (scheduled_id, student_id) DO UPDATE SET
                   question = excluded.question, answer = excluded.answer,
                   submitted_at = excluded.submitted_at""",
            (scheduled_id, student["id"], QUESTION, answer,
             datetime.now(timezone.utc).isoformat()),
        )


def list_teacher_responses(account_id, scheduled_id):
    """Authorize the meeting before returning any student response data."""
    with closing(db.get_connection()) as conn:
        allowed = conn.execute(
            """SELECT sc.id FROM scheduled sc
               JOIN teaching t ON t.id = sc.teaching_id
               JOIN teacher te ON te.id = t.teacher_id
               WHERE sc.id = ? AND te.account_id = ?""",
            (scheduled_id, account_id),
        ).fetchone()
        if allowed is None:
            raise ValueError("You do not teach this class meeting.")
        return conn.execute(
            """SELECT id, question, answer, submitted_at FROM exit_slip
               WHERE scheduled_id = ? ORDER BY id""",
            (scheduled_id,),
        ).fetchall()
