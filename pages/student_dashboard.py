
import streamlit as st
from src.passwords import require_login
from src import database as db

# Page configuration
st.set_page_config(
    page_title="Student Dashboard",
    page_icon="🎓",
    layout="wide"
)

# Require login
user = require_login()


def get_student_by_account_id(account_id):
    """Retrieve a student using their linked account ID."""

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



# Retrieve the logged-in student's information
student = get_student_by_account_id(user["id"])

if student is None:
    st.warning("No student profile is linked to your account.")
    st.stop()


# Dashboard display
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
                f"Semester: {course['semester']} {course['year']}"
            )

            if st.button(
                "View Class",
                key=f"view_class_{course['teaching_id']}"
            ):
                st.session_state["selected_teaching_id"] = course["teaching_id"]
                st.switch_page("pages/class_attendance.py")

