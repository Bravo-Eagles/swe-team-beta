"""Database functions for NFC tags.

src/nfc.py checks that a tap's link is genuine. This file checks that
it hasn't been used, by remembering every accepted tap for each tag.
"""

from datetime import datetime

from api.checkin_api import CLASS_TIMEZONE
from src.database import get_connection

# How far behind the newest tap a link can be and still be accepted. Allows
# taps that arrive slightly out of order, but rejects saved, old links.
MAX_TAPS_BEHIND = 10

# Possible results of record_tap
TAP_ACCEPTED = "accepted"
TAP_ALREADY_USED = "already_used"
TAP_TOO_OLD = "too_old"
TAP_UNKNOWN_TAG = "unknown_tag"


def record_tap(uid: str, counter: int) -> str:
    """Record a tap if its link hasn't been used and isn't too old.

    Returns TAP_ACCEPTED if the tap is accepted and saved. Otherwise returns
    TAP_ALREADY_USED, TAP_TOO_OLD, or TAP_UNKNOWN_TAG, saying why not.
    """
    conn = get_connection()
    try:
        with conn:
            row = conn.execute(
                "SELECT last_counter FROM nfc_tag WHERE uid = ?", (uid,)
            ).fetchone()
            if row is None:
                return TAP_UNKNOWN_TAG

            if counter <= row["last_counter"] - MAX_TAPS_BEHIND:
                return TAP_TOO_OLD

            # The primary key on (uid, counter) makes the database refuse a
            # tap that was already used, even if two arrive at the same moment.
            cursor = conn.execute(
                "INSERT OR IGNORE INTO nfc_tap (uid, counter) VALUES (?, ?)",
                (uid, counter),
            )
            if cursor.rowcount == 0:
                return TAP_ALREADY_USED

            conn.execute(
                "UPDATE nfc_tag SET last_counter = MAX(last_counter, ?) WHERE uid = ?",
                (counter, uid),
            )
        return TAP_ACCEPTED
    finally:
        conn.close()


def find_nfc_scheduled_id(uid: str, account_id: int):
    """Find the class meeting a student is checking into with an NFC tag.

    Looks for a class taught by the tag's teacher, that the student is
    enrolled in, scheduled for today and already started. Returns its
    scheduled_id, or None if there isn't one.
    """
    now = datetime.now(CLASS_TIMEZONE)
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT scheduled.id
            FROM nfc_tag
            JOIN teaching ON teaching.teacher_id = nfc_tag.teacher_id
            JOIN enrolled ON enrolled.teaching_id = teaching.id
            JOIN student ON student.id = enrolled.student_id
            JOIN scheduled ON scheduled.teaching_id = teaching.id
            WHERE nfc_tag.uid = ?
              AND student.account_id = ?
              AND student.active = 1
              AND scheduled.date = ?
              AND scheduled.start_time <= ?
            ORDER BY scheduled.start_time DESC
            LIMIT 1
            """,
            (uid, account_id, now.date().isoformat(), now.strftime("%H:%M:%S")),
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()