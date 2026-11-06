import streamlit as st
from src.passwords import require_login
from src import database as db
from datetime import date

# Page configuration
st.set_page_config(
    page_title="Class Details",
    page_icon="📚",
    layout="wide"
)

# Require login
user = require_login()


def get_student_by_account_id(account_id):
    """Retrieve the student linked to the logged-in account."""

    with db.get_connection() as conn:
        student = conn.execute(
            """
            SELECT id, first_name, last_name
            FROM student
            WHERE account_id = ?
            """,
            (account_id,)
        ).fetchone()

    return student


def get_class_details(teaching_id, student_id):
    """Retrieve class information if the student is enrolled."""

    with db.get_connection() as conn:
        course = conn.execute(
            """
            SELECT
                c.name AS class_name,
                c.course_id,
                t.semester,
                t.year
            FROM enrolled e
            JOIN teaching t ON e.teaching_id = t.id
            JOIN class c ON t.class_id = c.id
            WHERE e.student_id = ?
            AND t.id = ?
            """,
            (student_id, teaching_id)
        ).fetchone()

    return course


# Retrieve logged-in student
student = get_student_by_account_id(user["id"])

if student is None:
    st.error("No student profile is linked to your account.")
    st.stop()


# Retrieve selected class
teaching_id = st.session_state.get("selected_teaching_id")

if teaching_id is None:
    st.warning("Please select a class from your dashboard.")
    st.stop()

course = get_class_details(teaching_id, student["id"])

def get_attendance_history(teaching_id, student_id):
    """Retrieve scheduled sessions and the student's attendance records."""

    with db.get_connection() as conn:
        records = conn.execute(
            """
            SELECT
                s.date,
                s.start_time,
                s.end_time,
                a.check_in_time
            FROM scheduled s
            LEFT JOIN attendance a
                ON s.id = a.scheduled_id
                AND a.student_id = ?
            WHERE s.teaching_id = ?
            ORDER BY s.date DESC
            """,
            (student_id, teaching_id)
        ).fetchall()

    return records

if course is None:
    st.error("You are not enrolled in this class.")
    st.stop()


# Display class information
st.title(course["class_name"])
st.caption(f"{course['course_id']} | {course['semester']} {course['year']}")

if st.button("← Back to Dashboard"):
    st.switch_page("pages/student_dashboard.py")

st.divider()

st.header("Attendance Summary")

records = get_attendance_history(teaching_id, student["id"])

# Only count sessions that have already happened
completed_sessions = [
    record for record in records
    if record["date"] <= date.today().isoformat()
]

total_sessions = len(completed_sessions)

attended_sessions = sum(
    1 for record in completed_sessions
    if record["check_in_time"]
)

if total_sessions > 0:
    attendance_percentage = (
        attended_sessions / total_sessions
    ) * 100
else:
    attendance_percentage = 0

# Display attendance statistics
col1, col2, col3 = st.columns(3)

col1.metric("Sessions Held", total_sessions)
col2.metric("Sessions Attended", attended_sessions)
col3.metric("Attendance Rate", f"{attendance_percentage:.1f}%")

st.divider()

# Display individual sessions
st.header("Attendance History")

if not records:
    st.info("No scheduled class sessions found.")
else:
    for record in records:
        with st.container(border=True):
            st.write(f"**Date:** {record['date']}")
            st.write(
                f"**Time:** {record['start_time']} - {record['end_time']}"
            )

            if record["date"] > date.today().isoformat():
                st.info("Upcoming session")
            elif record["check_in_time"]:
                st.success("Attendance recorded")
            else:
                st.warning("No attendance record")