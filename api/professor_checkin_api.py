
from src.database import get_connection


def get_professor_sessions(account_id):
    """Return scheduled classes belonging to the logged-in professor."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                scheduled.id AS scheduled_id,
                class.name AS class_name,
                class.course_id,
                teaching.semester,
                teaching.year,
                scheduled.date,
                scheduled.start_time,
                scheduled.end_time
            FROM teacher
            JOIN teaching
                ON teaching.teacher_id = teacher.id
            JOIN class
                ON class.id = teaching.class_id
            JOIN scheduled
                ON scheduled.teaching_id = teaching.id
            WHERE teacher.account_id = ?
            ORDER BY scheduled.date DESC, scheduled.start_time DESC
            """,
            (account_id,)
        ).fetchall()

        return [dict(row) for row in rows]
