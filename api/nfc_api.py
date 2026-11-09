"""Database functions for NFC tags.

src/nfc.py checks that a tap's link is genuine. This file checks that
it's new, by remembering the last tap counter seen for each tag.
"""

from datetime import datetime

from api.checkin_api import CLASS_TIMEZONE
from src.database import get_connection


def record_tap(uid: str, counter: int) -> bool:
    """Save a tap's counter if it's newer than the last one seen for this tag.

    Returns True if the tap is new (accepted), False if the counter isn't
    higher (a reused or old link) or the tag isn't registered.
    """
    conn = get_connection()
    try:
        with conn:
            # Check and update in one statement, so the same link opened
            # twice at once can't be accepted twice.
            cursor = conn.execute(
                "UPDATE nfc_tag SET last_counter = ? "
                "WHERE uid = ? AND last_counter < ?",
                (counter, uid, counter),
            )
        # 1 row updated = new tap; 0 = reused link or unknown tag.
        return cursor.rowcount == 1
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