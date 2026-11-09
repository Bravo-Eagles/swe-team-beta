import streamlit as st
from src.passwords import require_login
from api.courses import get_classes
from api.courses import get_class_roster, get_teacher_id, get_teaching_section
from api.attendance_api import create_scheduled_session, list_scheduled_sessions, list_students_for_session
from datetime import date, time
from src.sidebar import sidebar

#Require Login
user = require_login()
sidebar()

#Ensure user is a teacher
teacher_id = get_teacher_id(user["id"])
if teacher_id is None:
    st.error("This account is not a teacher.")
    st.stop()

# Read and validate the section from the URL
raw_id = st.query_params.get("teachingID")
section = None
if raw_id and raw_id.isdigit():
    teaching_id = int(raw_id)
    section = get_teaching_section(teaching_id, teacher_id)

if section is None:
    st.error("No class in URL, or you don't teach this section.")
    st.stop()



# Header
st.header(section["name"])
st.caption(f"{section['course_id']} · {section['semester']} {section['year']}")

# Roster
roster = get_class_roster(teaching_id)
with st.expander("Roster", expanded=True):
    if roster:
        for student in roster:
            st.write(f"{student['first_name']} {student['last_name']}")
    else:
        st.info("No students enrolled.")

#Get Attendance Information from all scheduled groups of the class
scheduled_sessions = list_scheduled_sessions(teaching_id)
with st.expander("Scheduled Sessions"):
    if scheduled_sessions:
        session_options = {session["id"]: session for session in scheduled_sessions}
        #Format Function for session labels
        def section_labels(session_id):
            s = session_options[session_id]
            end = f" - {s['end_time']}" if s["end_time"] else ""
            return f"{s['date']}  {s['start_time']}{end}"

        selected_session = st.selectbox("Select a Session", list(session_options), format_func=section_labels)
        try:
            students = list_students_for_session(teaching_id, selected_session)
        except ValueError as e:
            st.error(str(e))
        else:
            present = sum(r["is_present"] for r in students)
            st.metric("Present", f"{present} / {len(students)}")
            st.dataframe(
                [
                    {
                        "Student": f"{r['first_name']} {r['last_name']}",
                        "Status": "Present" if r["is_present"] else "Absent",
                        "Check-in": r["check_in_time"] or "",
                    }
                    for r in students
                ],
                hide_index=True,
            )
            
                

# Add a meeting
with st.expander("Add a class meeting"):
    with st.form("add_class_meeting"):
        meeting_date = st.date_input("Date", value=date.today())
        meeting_start = st.time_input("Start time", value=time(8, 0))
        add_meeting = st.form_submit_button("Add meeting")

    if add_meeting:
        if create_scheduled_session(teaching_id, meeting_date, meeting_start):
            st.success("Class meeting added.")
        else:
            st.error("Could not add the meeting.")