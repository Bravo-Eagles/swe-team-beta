import tempfile
import unittest
from contextlib import closing
from datetime import date, time
from pathlib import Path
from unittest.mock import patch

from api import attendance_api
from src import database


class AttendanceApiTests(unittest.TestCase):
    def setUp(self):
        """Create an isolated SQLite database with a class and enrolled students."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "attendance.db"
        self.db_path_patch = patch.object(database, "DB_PATH", self.db_path)
        self.db_path_patch.start()
        database.init_db()

        with closing(database.get_connection()) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO teacher (id, first_name, last_name, email, password_hash)
                    VALUES (10, 'Alex', 'Teacher', 'alex@example.com', 'hash')
                    """
                )
                conn.execute(
                    """
                    INSERT INTO student
                        (id, first_name, last_name, email, password_hash, active)
                    VALUES
                        (20, 'Casey', 'Student', 'casey@example.com', 'hash', 1),
                        (21, 'Jordan', 'Student', 'jordan@example.com', 'hash', 1)
                    """
                )
                conn.execute(
                    "INSERT INTO class (id, name, course_id) VALUES (30, 'CS 101', 'CS101')"
                )
                conn.execute(
                    """
                    INSERT INTO teaching
                        (id, teacher_id, class_id, semester, year)
                    VALUES (40, 10, 30, 'Fall', 2026)
                    """
                )
                conn.execute(
                    """
                    INSERT INTO scheduled (id, teaching_id, date, start_time)
                    VALUES (50, 40, '2026-10-01', '08:00:00')
                    """
                )
                conn.execute(
                    "INSERT INTO enrolled (teaching_id, student_id) VALUES (40, 20)"
                )

    def tearDown(self):
        """Restore the database path and remove the temporary database."""
        self.db_path_patch.stop()
        self.temp_dir.cleanup()

    def test_lists_class_roster_and_saves_presence_and_absence(self):
        """List the roster and save, remove, and restore an attendance record."""
        offerings = attendance_api.list_class_offerings()
        self.assertEqual(len(offerings), 1)
        self.assertEqual(offerings[0]["teaching_id"], 40)

        students = attendance_api.list_students_for_session(40, 50)
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["is_present"], 0)

        attendance_api.save_attendance_records(
            50,
            [
                {
                    "student_id": 20,
                    "present": True,
                    "check_in_time": "2026-10-01 08:04",
                }
            ],
        )
        students = attendance_api.list_students_for_session(40, 50)
        self.assertEqual(students[0]["is_present"], 1)

        attendance_api.save_attendance_records(
            50,
            [{"student_id": 20, "present": False, "check_in_time": ""}],
        )
        students = attendance_api.list_students_for_session(40, 50)
        self.assertEqual(students[0]["is_present"], 0)
        attendance_row = attendance_api.select_attendance_log(20, 50)[0]
        self.assertEqual(attendance_row["is_deleted"], 1)

        attendance_api.save_attendance_records(
            50,
            [
                {
                    "student_id": 20,
                    "present": True,
                    "check_in_time": "2026-10-01 08:10",
                }
            ],
        )
        attendance_row = attendance_api.select_attendance_log(20, 50)[0]
        self.assertEqual(attendance_row["is_deleted"], 0)

    def test_rejects_students_not_enrolled_in_the_class(self):
        """Reject attendance updates for students outside the class roster."""
        with self.assertRaisesRegex(ValueError, "enrolled in this class"):
            attendance_api.save_attendance_records(
                50,
                [
                    {
                        "student_id": 21,
                        "present": True,
                        "check_in_time": "2026-10-01 08:00",
                    }
                ],
            )

    def test_rejects_a_meeting_from_another_class(self):
        """Reject roster lookups when the meeting belongs to another offering."""
        with self.assertRaisesRegex(ValueError, "does not belong to this class"):
            attendance_api.list_students_for_session(41, 50)

    def test_creates_a_scheduled_meeting(self):
        """Create a meeting and confirm it appears in the offering's schedule."""
        meeting_id = attendance_api.create_scheduled_session(
            40,
            date(2026, 10, 2),
            time(9, 30),
        )
        sessions = attendance_api.list_scheduled_sessions(40)
        self.assertIn(meeting_id, [session["id"] for session in sessions])


if __name__ == "__main__":
    unittest.main()
