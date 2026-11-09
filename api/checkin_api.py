
from contextlib import closing
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.database import get_connection


# Kent State / Ohio local time
CLASS_TIMEZONE = ZoneInfo("America/New_York")


def get_checkin_details(account_id, scheduled_id):
    """Verify the student is enrolled in the scheduled class."""

    with closing(get_connection()) as conn:
        row = conn.execute(
            """
            SELECT
                student.id AS student_id,
                scheduled.id AS scheduled_id,
                class.name AS class_name,
                class.course_id,
                scheduled.date,
                scheduled.start_time,
                scheduled.end_time
            FROM student
            JOIN enrolled
                ON enrolled.student_id = student.id
            JOIN teaching
                ON teaching.id = enrolled.teaching_id
            JOIN scheduled
                ON scheduled.teaching_id = teaching.id
            JOIN class
                ON class.id = teaching.class_id
            WHERE student.account_id = ?
              AND scheduled.id = ?
              AND student.active = 1
            """,
            (account_id, scheduled_id),
        ).fetchone()

        return dict(row) if row else None


def submit_checkin(account_id, scheduled_id, question, answer):
    """Validate the class time and save exit slip and attendance."""

    question = question.strip()
    answer = answer.strip()

    if not question or not answer:
        raise ValueError("Question and answer are required.")

    with closing(get_connection()) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")

            row = conn.execute(
                """
                SELECT
                    student.id AS student_id,
                    scheduled.date,
                    scheduled.start_time,
                    scheduled.end_time
                FROM student
                JOIN enrolled
                    ON enrolled.student_id = student.id
                JOIN scheduled
                    ON scheduled.teaching_id = enrolled.teaching_id
                WHERE student.account_id = ?
                  AND scheduled.id = ?
                  AND student.active = 1
                """,
                (account_id, scheduled_id),
            ).fetchone()

            if row is None:
                raise ValueError(
                    "You are not enrolled in this scheduled class."
                )

            student_id = row["student_id"]

            # Prevent duplicate exit slip submissions.
            existing = conn.execute(
                """
                SELECT id FROM exit_slip
                WHERE scheduled_id = ? AND student_id = ?
                """,
                (scheduled_id, student_id),
            ).fetchone()

            if existing:
                raise ValueError(
                    "You have already submitted this exit slip."
                )

            # Check scheduled class time in Ohio timezone.
            now_local = datetime.now(CLASS_TIMEZONE)

            class_start = datetime.fromisoformat(
                f"{row['date']}T{row['start_time']}"
            ).replace(tzinfo=CLASS_TIMEZONE)

            class_end = datetime.fromisoformat(
                f"{row['date']}T{row['end_time']}"
            ).replace(tzinfo=CLASS_TIMEZONE)

            # Allow check-in during class and for 15 minutes afterward.
            checkin_deadline = class_end + timedelta(minutes=15)

            if not (class_start <= now_local <= checkin_deadline):
                raise ValueError(
                    "Check-in is closed. You can only submit "
                    "during your scheduled class or within "
                    "15 minutes after it ends."
                )

            # Save the exit slip and attendance together.
            now = now_local.isoformat()

            conn.execute(
                """
                INSERT INTO exit_slip
                    (scheduled_id, student_id, question,
                     answer, submitted_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (scheduled_id, student_id, question, answer, now),
            )

            conn.execute(
                """
                INSERT INTO attendance
                    (scheduled_id, student_id, check_in_time, is_deleted)
                VALUES (?, ?, ?, 0)
                ON CONFLICT(scheduled_id, student_id)
                DO UPDATE SET
                    check_in_time = excluded.check_in_time,
                    is_deleted = 0
                """,
                (scheduled_id, student_id, now),
            )

    return True
