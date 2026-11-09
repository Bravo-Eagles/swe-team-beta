
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.database import get_connection, init_db
from src.passwords import hash_password

TEACHER_EMAIL = "demo.professor49@example.com"
STUDENT_EMAIL = "demo.student49@example.com"
DEMO_PASSWORD = "DemoCheckin49!"
COURSE_ID = "CS 10001"
COURSE_NAME = "Introduction to Computer Science"


def get_or_create_account(conn, email, role):
    row = conn.execute(
        "SELECT id FROM accounts WHERE email = ?", (email,)
    ).fetchone()
    if row:
        return row["id"]

    cursor = conn.execute(
        """
        INSERT INTO accounts (email, password_hash, role)
        VALUES (?, ?, ?)
        """,
        (email, hash_password(DEMO_PASSWORD), role),
    )
    return cursor.lastrowid


def get_or_create_person(conn, table, account_id, first, last):
    row = conn.execute(
        f"SELECT id FROM {table} WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    if row:
        return row["id"]

    if table == "student":
        cursor = conn.execute(
            """
            INSERT INTO student
                (first_name, last_name, account_id, active)
            VALUES (?, ?, ?, 1)
            """,
            (first, last, account_id),
        )
    else:
        cursor = conn.execute(
            """
            INSERT INTO teacher
                (first_name, last_name, account_id)
            VALUES (?, ?, ?)
            """,
            (first, last, account_id),
        )
    return cursor.lastrowid


def setup_demo():
    init_db()

    now = datetime.now(ZoneInfo("America/New_York"))
    semester = "Fall" if now.month >= 8 else "Spring"

    with get_connection() as conn:
        with conn:
            teacher_account = get_or_create_account(
                conn, TEACHER_EMAIL, "PROFESSOR"
            )
            student_account = get_or_create_account(
                conn, STUDENT_EMAIL, "STUDENT"
            )

            teacher_id = get_or_create_person(
                conn, "teacher", teacher_account, "Demo", "Professor"
            )
            student_id = get_or_create_person(
                conn, "student", student_account, "Demo", "Student"
            )

            course = conn.execute(
                """
                SELECT id FROM class
                WHERE course_id = ? AND name = ?
                """,
                (COURSE_ID, COURSE_NAME),
            ).fetchone()

            if course:
                class_id = course["id"]
            else:
                class_id = conn.execute(
                    """
                    INSERT INTO class (course_id, name)
                    VALUES (?, ?)
                    """,
                    (COURSE_ID, COURSE_NAME),
                ).lastrowid

            teaching = conn.execute(
                """
                SELECT id FROM teaching
                WHERE teacher_id = ? AND class_id = ?
                  AND semester = ? AND year = ?
                """,
                (teacher_id, class_id, semester, now.year),
            ).fetchone()

            if teaching:
                teaching_id = teaching["id"]
            else:
                teaching_id = conn.execute(
                    """
                    INSERT INTO teaching
                        (teacher_id, class_id, semester, year)
                    VALUES (?, ?, ?, ?)
                    """,
                    (teacher_id, class_id, semester, now.year),
                ).lastrowid

            conn.execute(
                """
                INSERT OR IGNORE INTO enrolled
                    (teaching_id, student_id)
                VALUES (?, ?)
                """,
                (teaching_id, student_id),
            )

            # Reuse a current demo session when possible.
            # Otherwise create a fresh session for the demonstration.
            session = conn.execute(
                """
                SELECT id FROM scheduled
                WHERE teaching_id = ? AND date = ?
                  AND start_time <= ? AND end_time > ?
                ORDER BY id DESC LIMIT 1
                """,
                (
                    teaching_id,
                    now.date().isoformat(),
                    now.strftime("%H:%M:%S"),
                    now.strftime("%H:%M:%S"),
                ),
            ).fetchone()

            if session:
                scheduled_id = session["id"]
            else:
                start = now - timedelta(minutes=5)
                end = now + timedelta(minutes=30)

                scheduled_id = conn.execute(
                    """
                    INSERT INTO scheduled
                        (teaching_id, date, start_time, end_time)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        teaching_id,
                        now.date().isoformat(),
                        start.strftime("%H:%M:%S"),
                        end.strftime("%H:%M:%S"),
                    ),
                ).lastrowid

    print("\nDEMO SETUP COMPLETE")
    print("-----------------------------")
    print("Professor:", TEACHER_EMAIL)
    print("Student:  ", STUDENT_EMAIL)
    print("Password: ", DEMO_PASSWORD)
    print("Course:   ", COURSE_ID)
    print("Session:  ", scheduled_id)
    print("-----------------------------")
    print("Run: python -m streamlit run main.py")
    print("Professor page: /professor_checkin")
    print("Use your laptop's Network URL for phone QR scanning.")
    print("Demo accounts only. Never use these passwords in production.")


if __name__ == "__main__":
    setup_demo()
