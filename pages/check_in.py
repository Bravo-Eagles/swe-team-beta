
import streamlit as st

from src.passwords import require_login
from api.checkin_api import get_checkin_details, submit_checkin

from src.passwords import current_user

st.title("Student Check-In")

raw_id = st.query_params.get("scheduled_id")

if current_user() is None:
    if raw_id:
        st.session_state["pending_checkin_id"] = str(raw_id)
    st.switch_page("./pages/login.py")

user = require_login()
if not raw_id:
    st.warning("Please scan your class QR code to check in.")
    st.stop()

try:
    scheduled_id = int(raw_id)
    if scheduled_id <= 0:
        raise ValueError()
except (ValueError, TypeError):
    st.error("Invalid class check-in link.")
    st.stop()

# Verify the logged-in student is enrolled
details = get_checkin_details(user["id"], scheduled_id)

if details is None:
    st.error("You are not enrolled in this scheduled class.")
    st.stop()

st.subheader(details["class_name"])
st.write("Course:", details["course_id"])
st.write("Date:", details["date"])
st.write("Start time:", details["start_time"])

question = (
    "What is one thing you learned today, "
    "and what is one question you still have?"
)

st.subheader("Exit Slip")
st.info(question)

with st.form("student_checkin_form"):
    answer = st.text_area("Your response")
    submitted = st.form_submit_button("Submit and Check In")

if submitted:
    if not answer.strip():
        st.error("Please enter your response.")
    else:
        try:
            submit_checkin(
                user["id"],
                scheduled_id,
                question,
                answer,
            )
            st.success(
                "Exit slip submitted! "
                "You have been marked present."
            )
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Check-in failed. Please try again.")
