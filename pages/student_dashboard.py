
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

# Classes section
st.header("My Classes")
st.info("Your enrolled classes will appear here.")
