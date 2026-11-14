
import streamlit as st
from src.passwords import require_login
from src import database as db
from datetime import date
from src.sidebar import sidebar

# Page configuration
st.set_page_config(
    page_title="Student Dashboard",
    page_icon="🎓",
    layout="wide"
)

# Require login
user = require_login()
sidebar()

# Retrieve student information
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


# Retrieve enrolled classes
def get_enrolled_classes(student_id):
    """Retrieve all classes a student is enrolled in."""

    with db.get_connection() as conn:
        classes = conn.execute(
            """
            SELECT
                c.id AS class_id,
                c.name AS class_name,
                c.course_id,
                t.id AS teaching_id,
                t.semester,
                t.year
            FROM enrolled e
            JOIN teaching t ON e.teaching_id = t.id
            JOIN class c ON t.class_id = c.id
            WHERE e.student_id = ?
            ORDER BY t.year DESC, t.semester
            """,
            (student_id,)
        ).fetchall()

    return classes


# Retrieve individual class information
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


# Retrieve attendance history
def get_attendance_history(teaching_id, student_id):
    """Retrieve scheduled sessions and attendance records."""

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


# Retrieve logged-in student
student = get_student_by_account_id(user["id"])

if student is None:
    st.warning("No student profile is linked to your account.")
    st.stop()


# Track which screen is displayed
if "show_class_details" not in st.session_state:
    st.session_state["show_class_details"] = False


# Display individual class details
if st.session_state["show_class_details"]:

    teaching_id = st.session_state.get("selected_teaching_id")

    if teaching_id is None:
        st.warning("Please select a class.")
        st.session_state["show_class_details"] = False
        st.rerun()

    course = get_class_details(teaching_id, student["id"])

    if course is None:
        st.error("You are not enrolled in this class.")
        st.session_state["show_class_details"] = False
        st.stop()

    st.title(course["class_name"])
    st.caption(
        f"{course['course_id']} | "
        f"{course['semester']} {course['year']}"
    )

    if st.button("← Back to Dashboard"):
        st.session_state["show_class_details"] = False
        st.rerun()

    st.divider()

    st.header("Attendance Summary")

    records = get_attendance_history(teaching_id, student["id"])

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

    col1, col2, col3 = st.columns(3)

    col1.metric("Sessions Held", total_sessions)
    col2.metric("Sessions Attended", attended_sessions)
    col3.metric("Attendance Rate", f"{attendance_percentage:.1f}%")

    st.divider()

    st.header("Attendance History")

    if not records:
        st.info("No scheduled class sessions found.")
    else:
        for record in records:
            with st.container(border=True):
                st.write(f"**Date:** {record['date']}")
                st.write(
                    f"**Time:** {record['start_time']} - "
                    f"{record['end_time']}"
                )

                if record["date"] > date.today().isoformat():
                    st.info("Upcoming session")
                elif record["check_in_time"]:
                    st.success("Attendance recorded")
                else:
                    st.warning("No attendance record")


# Display student dashboard
else:

    st.title("Student Dashboard")
    st.subheader(f"Welcome, {student['first_name']}!")
    st.caption(user["email"])

    st.divider()

    st.header("My Classes")

    classes = get_enrolled_classes(student["id"])

    if not classes:
        st.info("You are not currently enrolled in any classes.")

    else:
        for course in classes:
            with st.container(border=True):
                st.subheader(course["class_name"])
                st.write(f"Course ID: {course['course_id']}")
                st.write(
                    f"Semester: {course['semester']} "
                    f"{course['year']}"
                )

                if st.button(
                    "View Class",
                    key=f"view_class_{course['teaching_id']}"
                ):
                    st.session_state["selected_teaching_id"] = (
                        course["teaching_id"]
                    )
                    st.session_state["show_class_details"] = True
                    st.rerun()
