import gc
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from api.exit_slip_api import list_student_meetings, list_teacher_responses, submit_exit_slip
from src import database


class ExitSlipTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict("os.environ", {"AI_API_KEY": "test-key"})
        env.start()
        self.addCleanup(env.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.object(database, "DB_PATH", Path(self.temp.name) / "test.db")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(gc.collect)
        database.init_db()
        with closing(database.get_connection()) as conn, conn:
            conn.executescript("""
                INSERT INTO accounts (id, email, password_hash) VALUES
                    (1, 'teacher@test', 'x'), (2, 'student@test', 'x'),
                    (3, 'other@test', 'x');
                INSERT INTO teacher (id, first_name, last_name, account_id) VALUES
                    (10, 'T', 'One', 1), (11, 'T', 'Two', 3);
                INSERT INTO student (id, first_name, last_name, account_id, active)
                    VALUES (20, 'S', 'One', 2, 1);
                INSERT INTO class (id, name, course_id) VALUES (30, 'Computing', 'CS1');
                INSERT INTO teaching (id, teacher_id, class_id, semester, year)
                    VALUES (40, 10, 30, 'Fall', 2026), (41, 11, 30, 'Fall', 2026);
                INSERT INTO scheduled (id, teaching_id, date, start_time) VALUES
                    (50, 40, '2026-11-17', '08:00'), (51, 41, '2026-11-17', '09:00');
                INSERT INTO enrolled (teaching_id, student_id) VALUES (40, 20);
            """)

    def test_persists_submission_and_replaces_repeat(self):
        submit_exit_slip(2, 50, "I learned recursion")
        self.assertEqual(list_teacher_responses(1, 50)[0]["answer"], "I learned recursion")
        submit_exit_slip(2, 50, "Updated answer")
        rows = list_teacher_responses(1, 50)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["answer"], "Updated answer")

    def test_rejects_blank_and_unenrolled_submissions(self):
        for account, meeting, answer in [(2, 50, "  "), (2, 51, "answer"), (1, 50, "answer")]:
            with self.assertRaises(ValueError):
                submit_exit_slip(account, meeting, answer)
        self.assertEqual(list_teacher_responses(1, 50), [])

    def test_only_assigned_teacher_can_read_responses(self):
        submit_exit_slip(2, 50, "Private response")
        for account in [2, 3, 999]:
            with self.assertRaises(ValueError):
                list_teacher_responses(account, 50)
        self.assertEqual(list_teacher_responses(3, 51), [])

    def test_student_only_sees_enrolled_meetings(self):
        self.assertEqual([r["id"] for r in list_student_meetings(2)], [50])
        self.assertEqual(list_student_meetings(1), [])

    def test_summary_requires_click_and_survives_reruns(self):
        from streamlit.testing.v1 import AppTest

        submit_exit_slip(2, 50, "I learned recursion")
        with patch("src.passwords.require_login", return_value={"id": 1}), \
             patch("src.sidebar.sidebar"), \
             patch("src.ai_summary.AIRequest") as factory:
            factory.return_value.send.return_value.json.return_value = {"output_text": "Recursion summary"}
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "pages/class.py"), default_timeout=15)
            app.query_params["teachingID"] = "40"
            app.run()
            self.assertEqual(list(app.exception), [])
            factory.assert_not_called()
            app.button(key="generate_summary_50").click().run()
            self.assertEqual(list(app.exception), [])
            factory.assert_called_once()
            app.run()
            factory.assert_called_once()
            self.assertIn("Recursion summary", [m.value for m in app.markdown])
            submit_exit_slip(2, 50, "Now I have another question")
            app.run()
            factory.assert_called_once()
            self.assertTrue(any("Responses have changed" in info.value for info in app.info))

    def test_empty_meeting_disables_summary(self):
        from streamlit.testing.v1 import AppTest

        with patch("src.passwords.require_login", return_value={"id": 1}), \
             patch("src.sidebar.sidebar"), patch("src.ai_summary.AIRequest") as factory:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "pages/class.py"), default_timeout=15)
            app.query_params["teachingID"] = "40"
            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertTrue(app.button(key="generate_summary_50").disabled)
            factory.assert_not_called()

    def test_student_submission_does_not_request_ai(self):
        from streamlit.testing.v1 import AppTest

        with patch("src.passwords.require_login", return_value={"id": 2}), \
             patch("src.sidebar.sidebar"), patch("src.ai_summary.AIRequest") as factory:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "pages/exit_slip.py"), default_timeout=15)
            app.run()
            app.text_area[0].input("I learned about functions")
            app.button[0].click().run()
            self.assertEqual(list(app.exception), [])
            self.assertTrue(app.success)
            self.assertEqual(list_teacher_responses(1, 50)[0]["answer"], "I learned about functions")
            factory.assert_not_called()

    def test_failed_summary_can_be_retried(self):
        from requests import Timeout
        from streamlit.testing.v1 import AppTest

        submit_exit_slip(2, 50, "Response")
        with patch("src.passwords.require_login", return_value={"id": 1}), \
             patch("src.sidebar.sidebar"), patch("src.ai_summary.AIRequest") as factory:
            factory.return_value.send.side_effect = Timeout()
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "pages/class.py"), default_timeout=15)
            app.query_params["teachingID"] = "40"
            app.run()
            app.button(key="generate_summary_50").click().run()
            self.assertEqual(list(app.exception), [])
            self.assertTrue(any("could not complete" in error.value for error in app.error))
            factory.return_value.send.side_effect = None
            factory.return_value.send.return_value.json.return_value = {"output_text": "Retried summary"}
            app.button(key="generate_summary_50").click().run()
            self.assertEqual(list(app.exception), [])
            self.assertIn("Retried summary", [m.value for m in app.markdown])
