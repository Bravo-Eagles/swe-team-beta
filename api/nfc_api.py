"""
src/nfc.py checks that a tap's link is genuine. This file checks that
it's new, by remembering the last tap counter seen for each tag.
"""

from src.database import get_connection

def record_tap(uid: str, counter: int) -> bool:
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