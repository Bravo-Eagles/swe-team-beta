import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from api.nfc_api import (
    TAP_ACCEPTED,
    TAP_ALREADY_USED,
    TAP_TOO_OLD,
    TAP_UNKNOWN_TAG,
    record_tap,
)
from src import database
from src.nfc import verify_tap
from tests.nfc_test_helpers import FACTORY_KEY, TEST_UID, make_tap


class VerifyTapTests(unittest.TestCase):
    def test_real_tag_link(self):
        self.assertEqual(
            verify_tap("5E5C236A25FA38D76D74724DC7C9893A", "B76B3E5157143117", FACTORY_KEY),
            ("0461205abd2390", 1),
        )

    def test_generated_link(self):
        picc, cmac = make_tap(7)
        self.assertEqual(verify_tap(picc, cmac, FACTORY_KEY), (TEST_UID, 7))

    def test_tampered_signature(self):
        picc, cmac = make_tap(7)
        bad = cmac[:-1] + ("0" if cmac[-1] != "0" else "1")
        with self.assertRaises(ValueError):
            verify_tap(picc, bad, FACTORY_KEY)

    def test_wrong_key(self):
        picc, cmac = make_tap(7)
        with self.assertRaises(ValueError):
            verify_tap(picc, cmac, bytes([1] * 16))

    def test_bad_input(self):
        for picc, cmac in [("ABCD", "B76B3E5157143117"), ("zz" * 16, "00" * 8), ("", "")]:
            with self.assertRaises(ValueError):
                verify_tap(picc, cmac, FACTORY_KEY)


class RecordTapTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(database, "DB_PATH", Path(self.temp_dir.name) / "test.db")
        self.db_patch.start()
        database.init_db()
        conn = database.get_connection()
        with conn:
            conn.execute("INSERT INTO accounts (id, email, password_hash, role) VALUES (1, 't@x.com', 'x', 'PROFESSOR')")
            conn.execute("INSERT INTO teacher (id, first_name, last_name, account_id) VALUES (1, 'T', 'T', 1)")
            conn.execute("INSERT INTO nfc_tag (uid, teacher_id) VALUES (?, 1)", (TEST_UID,))
        conn.close()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_new_tap_accepted(self):
        self.assertEqual(record_tap(TEST_UID, 1), TAP_ACCEPTED)

    def test_same_tap_twice(self):
        record_tap(TEST_UID, 5)
        self.assertEqual(record_tap(TEST_UID, 5), TAP_ALREADY_USED)

    def test_out_of_order(self):
        self.assertEqual(record_tap(TEST_UID, 11), TAP_ACCEPTED)
        self.assertEqual(record_tap(TEST_UID, 10), TAP_ACCEPTED)
        self.assertEqual(record_tap(TEST_UID, 10), TAP_ALREADY_USED)

    def test_too_old(self):
        record_tap(TEST_UID, 30)
        self.assertEqual(record_tap(TEST_UID, 20), TAP_TOO_OLD)
        self.assertEqual(record_tap(TEST_UID, 21), TAP_ACCEPTED)

    def test_unknown_tag(self):
        self.assertEqual(record_tap("ffffffffffffff", 1), TAP_UNKNOWN_TAG)


if __name__ == "__main__":
    unittest.main()