import sqlite3
from contextlib import closing
from datetime import date, datetime, time
from typing import TypedDict

from src import database as db


class AttendanceEdit(TypedDict):
    student_id: int
    attendance_status: str
    check_in_time: str | None

def create_attendance_log(scheduled_id, student_id, time):
    """Create an attendance record for an active class meeting."""

    with closing(db.get_connection()) as conn:
        with conn:
            meeting = conn.execute(
                """
                SELECT is_cancelled
                FROM scheduled
                WHERE id = ?
                """,
                (scheduled_id,),
            ).fetchone()

            if meeting is None:
                raise ValueError("The selected class meeting does not exist.")

            if meeting["is_cancelled"]:
                raise ValueError(
                    "Cannot record attendance for a canceled meeting."
                )

            cursor = conn.execute(
                """
                INSERT INTO attendance
                    (scheduled_id, student_id, check_in_time)
                VALUES (?, ?, ?)
                """,
                (scheduled_id, student_id, time),
            )



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
        SET check_in_time = ?, is_deleted = 0, attendance_status = 'Present'
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
        SET is_deleted = 1
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
    """List active scheduled meetings for a class offering, newest first."""
    query = """
        SELECT id, date, start_time, end_time
        FROM scheduled
        WHERE teaching_id = ?
        AND is_cancelled = 0
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
        CASE
            WHEN attendance.student_id IS NULL THEN 'Not recorded'
            ELSE attendance.attendance_status
        END AS attendance_status
        FROM enrolled
        JOIN student ON student.id = enrolled.student_id
        LEFT JOIN attendance
            ON attendance.student_id = student.id
            AND attendance.scheduled_id = ?
            AND attendance.is_deleted = 0
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
    teaching_id: int,
    session_date: date,
    start_time: time,
    end_time: time,
) -> int:
    """Create a future class meeting with a start and end time."""

    meeting_datetime = datetime.combine(session_date, start_time)

    if meeting_datetime <= datetime.now():
        raise ValueError("Cannot schedule a meeting in the past.")

    if end_time <= start_time:
        raise ValueError("End time must be later than start time.")

    with closing(db.get_connection()) as conn:
        with conn:
            conn.execute("BEGIN IMMEDIATE")

            teaching = conn.execute(
                "SELECT id FROM teaching WHERE id = ?", (teaching_id,)
            ).fetchone()

            if teaching is None:
                raise ValueError(
                    "The selected class offering no longer exists."
                )

            next_id = conn.execute(
                "SELECT COALESCE(MAX(id), 0) + 1 FROM scheduled"
            ).fetchone()[0]

            try:
                conn.execute(
                    """
                    INSERT INTO scheduled
                        (id, teaching_id, date, start_time, end_time)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        next_id,
                        teaching_id,
                        session_date.isoformat(),
                        start_time.isoformat(),
                        end_time.isoformat(),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    "A meeting already exists for this class "
                    "at that date and time."
                ) from exc

            return next_id


def save_attendance_records(
    scheduled_id: int, records: list[AttendanceEdit]
) -> None:
    """Save Present, Absent, or Not recorded for enrolled students."""
    normalized_records: list[tuple[int, str, str | None]] = []
    seen_student_ids: set[int] = set()

    for record in records:
        student_id = int(record["student_id"])

        if student_id in seen_student_ids:
            raise ValueError(
                "A student can only appear once in an attendance update."
            )
        seen_student_ids.add(student_id)

        status = record["attendance_status"]

        if status not in ("Present", "Absent", "Not recorded"):
            raise ValueError("Invalid attendance status.")

        raw_check_in_time = record["check_in_time"]
        check_in_time = (
            "" if raw_check_in_time is None else str(raw_check_in_time).strip()
        )

        if status == "Present":
            if not check_in_time:
                raise ValueError(
                    "Enter a check-in time for each student marked present."
                )
            try:
                parsed_check_in = datetime.fromisoformat(check_in_time)
            except ValueError as exc:
                raise ValueError(
                    "Check-in times must use YYYY-MM-DD HH:MM format."
                ) from exc

            check_in_time = parsed_check_in.isoformat(sep=" ")
        else:
            check_in_time = None

        normalized_records.append(
            (student_id, status, check_in_time)
        )

    with closing(db.get_connection()) as conn:
        with conn:
            session = conn.execute(
                """SELECT teaching_id, is_cancelled
                   FROM scheduled
                   WHERE id = ?
                """,
                (scheduled_id,),
            ).fetchone()

            if session is None:
                raise ValueError(
                    "The selected class meeting no longer exists."
                )
            if session["is_cancelled"]:
                raise ValueError(
                    "Attendance cannot be edited for a canceled meeting."
                )
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

            for student_id, status, check_in_time in normalized_records:

                if status == "Not recorded":
                    conn.execute(
                        """
                        UPDATE attendance
                        SET is_deleted = 1
                        WHERE scheduled_id = ? AND student_id = ?
                        """,
                        (scheduled_id, student_id),
                    )

                else:
                    # Absent needs a stored row too.
                    # Use the meeting start as a placeholder when absent.
                    if status == "Absent":
                        meeting = conn.execute(
                            """
                            SELECT date, start_time
                            FROM scheduled
                            WHERE id = ?
                            """,
                            (scheduled_id,),
                        ).fetchone()

                        check_in_time = (
                            f"{meeting['date']} {meeting['start_time']}"
                        )

                    conn.execute(
                        """
                        INSERT INTO attendance
                            (scheduled_id, student_id, check_in_time,
                             is_deleted, attendance_status)
                        VALUES (?, ?, ?, 0, ?)
                        ON CONFLICT (scheduled_id, student_id)
                        DO UPDATE SET
                            check_in_time = excluded.check_in_time,
                            is_deleted = 0,
                            attendance_status = excluded.attendance_status
                        """,
                        (
                            scheduled_id,
                            student_id,
                            check_in_time,
                            status,
                        ),
                    )


def update_scheduled_session(
    scheduled_id: int,
    session_date: date,
    start_time: time,
    end_time: time,
) -> None:
    """Update the date, start time, and end time of a future meeting."""

    new_datetime = datetime.combine(session_date, start_time)

    if new_datetime <= datetime.now():
        raise ValueError("Cannot move a meeting to a past date or time.")

    if end_time <= start_time:
        raise ValueError("End time must be later than start time.")

    with closing(db.get_connection()) as conn:
        with conn:
            meeting = conn.execute(
                """
                SELECT date, start_time, is_cancelled
                FROM scheduled
                WHERE id = ?
                """,
                (scheduled_id,),
            ).fetchone()

            if meeting is None:
                raise ValueError(
                    "The selected class meeting no longer exists."
                )

            if meeting["is_cancelled"]:
                raise ValueError(
                    "Canceled meetings cannot be rescheduled."
                )

            original_datetime = datetime.combine(
                date.fromisoformat(meeting["date"]),
                time.fromisoformat(meeting["start_time"]),
            )

            if original_datetime <= datetime.now():
                raise ValueError(
                    "Meetings that have already started cannot be rescheduled."
                )

            try:
                conn.execute(
                    """
                    UPDATE scheduled
                    SET date = ?, start_time = ?, end_time = ?
                    WHERE id = ?
                    """,
                    (
                        session_date.isoformat(),
                        start_time.isoformat(),
                        end_time.isoformat(),
                        scheduled_id,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    "Another meeting already exists at that date and time."
                ) from exc


def cancel_scheduled_session(scheduled_id: int) -> None:
    """Cancel a future class meeting without deleting its records."""

    with closing(db.get_connection()) as conn:
        with conn:
            meeting = conn.execute(
                """
                SELECT date, start_time, is_cancelled
                FROM scheduled
                WHERE id = ?
                """,
                (scheduled_id,),
            ).fetchone()

            if meeting is None:
                raise ValueError("The selected class meeting does not exist.")

            if meeting["is_cancelled"]:
                raise ValueError("This meeting is already canceled.")

            meeting_datetime = datetime.combine(
                date.fromisoformat(meeting["date"]),
                time.fromisoformat(meeting["start_time"]),
            )

            if meeting_datetime <= datetime.now():
                raise ValueError("Past meetings cannot be canceled.")

            conn.execute(
                """
                UPDATE scheduled
                SET is_cancelled = 1
                WHERE id = ?
                """,
                (scheduled_id,),
            )
