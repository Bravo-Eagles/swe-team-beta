import sqlite3
from contextlib import closing
from datetime import date, datetime, time
from typing import TypedDict

from src import database as db


class AttendanceEdit(TypedDict):
    student_id: int
    present: bool
    check_in_time: str | None


def create_attendance_log(scheduled_id, student_id, time):
    """Create an attendance record and return its database row ID.

    Args:
        scheduled_id: ID of the scheduled class meeting.
        student_id: ID of the student being checked in.
        time: Check-in date and time to store.

    Returns:
        int | None: The inserted row ID.
    """
    query = "INSERT INTO attendance (scheduled_id, student_id, check_in_time) VALUES (?, ?, ?);"
    with closing(db.get_connection()) as conn:
        with conn:
            cursor = conn.execute(query, (scheduled_id, student_id, time))
            return cursor.lastrowid


def update_attendance_log(check_in_time, student_id, scheduled_id):
    """Update a student's check-in time and restore their attendance record.

    Args:
        check_in_time: Updated check-in date and time.
        student_id: ID of the student being updated.
        scheduled_id: ID of the scheduled class meeting.

    Returns:
        int: Number of attendance rows updated.
    """
    query = """
        UPDATE attendance
        SET check_in_time = ?, is_delted = 0
        WHERE student_id = ? AND scheduled_id = ?
    """
    with closing(db.get_connection()) as conn:
        with conn:
            cursor = conn.execute(query, (check_in_time, student_id, scheduled_id))
            return cursor.rowcount


def select_attendance_log(student_id=None, scheduled_id=None):
    """Return attendance records matching the optional student and meeting IDs.

    Args:
        student_id: Optional student ID to filter by.
        scheduled_id: Optional scheduled meeting ID to filter by.

    Returns:
        list[sqlite3.Row]: Matching attendance records.
    """
    query = "SELECT * FROM attendance WHERE 1=1"
    params = []

    if student_id is not None:
        query += " AND student_id = ?"
        params.append(student_id)

    if scheduled_id is not None:
        query += " AND scheduled_id = ?"
        params.append(scheduled_id)

    with closing(db.get_connection()) as conn:
        return conn.execute(query, params).fetchall()


def delete_attendance_log(student_id, scheduled_id):
    """Soft-delete a student's attendance record for a scheduled meeting.

    Args:
        student_id: ID of the student whose record should be deleted.
        scheduled_id: ID of the scheduled class meeting.

    Returns:
        int: Number of attendance rows marked deleted.
    """
    query = """
        UPDATE attendance
        SET is_delted = 1
        WHERE scheduled_id = ? AND student_id = ?
    """
    with closing(db.get_connection()) as conn:
        with conn:
            cursor = conn.execute(query, (scheduled_id, student_id))
            return cursor.rowcount


def list_class_offerings() -> list[sqlite3.Row]:
    """Return class offerings with their course, term, and year details.

    Returns:
        list[sqlite3.Row]: Class offerings ordered by class and term.
    """
    query = """
        SELECT
            teaching.id AS teaching_id,
            class.name AS class_name,
            class.course_id,
            teaching.semester,
            teaching.year
        FROM teaching
        JOIN class ON class.id = teaching.class_id
        ORDER BY class.name, class.course_id, teaching.year DESC, teaching.semester
    """
    with closing(db.get_connection()) as conn:
        return conn.execute(query).fetchall()


def list_scheduled_sessions(teaching_id: int) -> list[sqlite3.Row]:
    """List scheduled meetings for a class offering, newest first.

    Args:
        teaching_id: ID of the class offering.

    Returns:
        list[sqlite3.Row]: Scheduled meetings for the offering.
    """
    query = """
        SELECT id, date, start_time, end_time
        FROM scheduled
        WHERE teaching_id = ?
        ORDER BY date DESC, start_time DESC
    """
    with closing(db.get_connection()) as conn:
        return conn.execute(query, (teaching_id,)).fetchall()


def list_students_for_session(
    teaching_id: int, scheduled_id: int
) -> list[sqlite3.Row]:
    """Return an offering's enrolled students and attendance for a meeting.

    Args:
        teaching_id: ID of the class offering.
        scheduled_id: ID of a meeting belonging to that offering.

    Returns:
        list[sqlite3.Row]: Enrolled students with present status and check-in time.

    Raises:
        ValueError: If the meeting does not exist or belongs to another offering.
    """
    query = """
        SELECT
            student.id AS student_id,
            student.first_name,
            student.last_name,
            attendance.check_in_time,
            CASE WHEN attendance.student_id IS NULL THEN 0 ELSE 1 END AS is_present
        FROM enrolled
        JOIN student ON student.id = enrolled.student_id
        LEFT JOIN attendance
            ON attendance.student_id = student.id
            AND attendance.scheduled_id = ?
            AND attendance.is_delted = 0
        WHERE enrolled.teaching_id = ?
        ORDER BY student.last_name, student.first_name, student.id
    """
    with closing(db.get_connection()) as conn:
        session = conn.execute(
            "SELECT teaching_id FROM scheduled WHERE id = ?", (scheduled_id,)
        ).fetchone()
        if session is None:
            raise ValueError("The selected class meeting no longer exists.")
        if session["teaching_id"] != teaching_id:
            raise ValueError("The selected class meeting does not belong to this class.")
        return conn.execute(query, (scheduled_id, teaching_id)).fetchall()


def create_scheduled_session(
    teaching_id: int, session_date: date, start_time: time
) -> int:
    """Add a scheduled meeting to an existing class offering.

    Args:
        teaching_id: ID of the class offering.
        session_date: Date of the meeting.
        start_time: Meeting start time.

    Returns:
        int: ID assigned to the new meeting.

    Raises:
        ValueError: If the class offering does not exist.
    """
    with closing(db.get_connection()) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            teaching = conn.execute(
                "SELECT id FROM teaching WHERE id = ?", (teaching_id,)
            ).fetchone()
            if teaching is None:
                raise ValueError("The selected class offering no longer exists.")

            next_id = conn.execute(
                "SELECT COALESCE(MAX(id), 0) + 1 FROM scheduled"
            ).fetchone()[0]
            conn.execute(
                """
                INSERT INTO scheduled (id, teaching_id, date, start_time)
                VALUES (?, ?, ?, ?)
                """,
                (next_id, teaching_id, session_date.isoformat(), start_time.isoformat()),
            )
            return next_id


def save_attendance_records(
    scheduled_id: int, records: list[AttendanceEdit]
) -> None:
    """Save present or absent statuses for enrolled students in one meeting.

    Present records are inserted or restored with their check-in time; absent
    records are soft-deleted so their history remains in the database.

    Args:
        scheduled_id: ID of the scheduled class meeting.
        records: Student IDs, attendance statuses, and check-in times to save.

    Raises:
        ValueError: If the meeting is missing, a student is not enrolled, a
            student is repeated, or an attendance value is invalid.
    """
    normalized_records: list[tuple[int, bool, str | None]] = []
    seen_student_ids: set[int] = set()

    for record in records:
        student_id = int(record["student_id"])
        if student_id in seen_student_ids:
            raise ValueError("A student can only appear once in an attendance update.")
        seen_student_ids.add(student_id)

        present = record["present"]
        if not isinstance(present, bool):
            raise ValueError("Attendance status must be present or absent.")

        raw_check_in_time = record["check_in_time"]
        check_in_time = (
            "" if raw_check_in_time is None else str(raw_check_in_time).strip()
        )
        if present:
            if not check_in_time:
                raise ValueError("Enter a check-in time for each student marked present.")
            try:
                parsed_check_in = datetime.fromisoformat(check_in_time)
            except ValueError as exc:
                raise ValueError(
                    "Check-in times must use YYYY-MM-DD HH:MM format."
                ) from exc
            check_in_time = parsed_check_in.isoformat(sep=" ")
        else:
            check_in_time = None

        normalized_records.append((student_id, present, check_in_time))

    with closing(db.get_connection()) as conn:
        with conn:
            session = conn.execute(
                "SELECT teaching_id FROM scheduled WHERE id = ?", (scheduled_id,)
            ).fetchone()
            if session is None:
                raise ValueError("The selected class meeting no longer exists.")

            enrolled_student_ids = {
                row["student_id"]
                for row in conn.execute(
                    "SELECT student_id FROM enrolled WHERE teaching_id = ?",
                    (session["teaching_id"],),
                )
            }
            if not seen_student_ids.issubset(enrolled_student_ids):
                raise ValueError(
                    "Attendance can only be edited for students enrolled in this class."
                )

            for student_id, present, check_in_time in normalized_records:
                if present:
                    conn.execute(
                        """
                        INSERT INTO attendance
                            (scheduled_id, student_id, check_in_time, is_delted)
                        VALUES (?, ?, ?, 0)
                        ON CONFLICT (scheduled_id, student_id) DO UPDATE SET
                            check_in_time = excluded.check_in_time,
                            is_delted = 0
                        """,
                        (scheduled_id, student_id, check_in_time),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE attendance
                        SET is_delted = 1
                        WHERE scheduled_id = ? AND student_id = ?
                        """,
                        (scheduled_id, student_id),
                    )
