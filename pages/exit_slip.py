import streamlit as st

from api.exit_slip_api import QUESTION, list_student_meetings, submit_exit_slip
from src.passwords import require_login
from src.sidebar import sidebar


user = require_login()
sidebar()

st.title("Exit Slip")
st.write("Submit your response to a class meeting's question.")

meetings = {row["id"]: row for row in list_student_meetings(user["id"])}
if not meetings:
    st.info("No class meetings are available. You must be enrolled in a scheduled class.")
    st.stop()


def meeting_label(meeting_id):
    meeting = meetings[meeting_id]
    return (f"{meeting['course_id']} - {meeting['name']} | "
            f"{meeting['date']} {meeting['start_time']}")


selected_meeting = st.selectbox("Class meeting", list(meetings), format_func=meeting_label)
st.subheader("Class Question")
st.info(QUESTION)
st.caption("Submitting again replaces your response for this meeting.")

with st.form(f"exit_slip_form_{selected_meeting}", clear_on_submit=True):
    answer = st.text_area("Your response")
    submitted = st.form_submit_button("Submit Exit Slip")

if submitted:
    try:
        submit_exit_slip(user["id"], selected_meeting, answer)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.success("Your exit slip was submitted successfully!")
