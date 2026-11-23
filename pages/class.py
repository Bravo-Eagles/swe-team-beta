import streamlit as st
from src.passwords import require_role
from api.courses import get_classes
from api.courses import get_class_roster, get_teacher_id, get_teaching_section, search_addable_students, add_students_to_section
from api.attendance_api import create_scheduled_session, list_scheduled_sessions, list_students_for_session
from datetime import date, time
from src.sidebar import sidebar
from api.exit_slip_api import list_teacher_responses
from src.ai_summary import summarize_responses
from requests import RequestException
from src.style import setup_page

# Require teacher permissions
user = require_role(["TEACHER"])
sidebar()

setup_page("Class Overview", gradient=False)

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

#Add Students to the class
with st.expander("Add students"):
    search = st.text_input("Search by name", key="add_student_search")
    candidates = search_addable_students(teaching_id, search)
    by_id = {s["id"]: s for s in candidates}

    def stu_label(student):
        return f"{by_id[student]['first_name']} {by_id[student]['last_name']}"

    picked = st.multiselect(
        "Students to add",
        options=list(by_id),
        format_func=stu_label,
        key="add_student_pick",
    )
    if len(candidates) == 25:
        st.caption("Showing the first 25 matches. Type more to narrow the search.")

    if st.button("Add selected", disabled=not picked):
        count = add_students_to_section(teaching_id, picked)
        st.session_state.pop("add_student_pick", None)
        st.session_state.pop("add_student_search", None)
        st.session_state["flash"] = f"Added {count} student{'s' if count != 1 else ''}."
        st.rerun()

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
            present = sum(r["check_in_time"] is not None for r in students)
            st.metric("Present", f"{present} / {len(students)}")
            st.dataframe(
                [
                    {
                        "Student": f"{r['first_name']} {r['last_name']}",
                        "Status": "Present" if r["check_in_time"] else "Absent",
                        "Check-in": r["check_in_time"] or "",
                    }
                    for r in students
                ],
                hide_index=True,
            )

        st.subheader("Exit Slip Responses")
        responses = list_teacher_responses(user["id"], selected_session)
        st.write(f"Total submissions: {len(responses)}")
        if st.toggle("Show submitted responses", key=f"show_resp_{selected_session}"):
            for index, response in enumerate(responses, start=1):
                st.markdown(f"**Response {index}**")
                st.write("Question:", response["question"])
                st.write("Answer:", response["answer"])

        st.subheader("AI Summary")
        st.caption("Generate a summary when you need it. Responses are sent to the configured AI service only when you click the button.")
        summary_key = f"exit_slip_summary_{user['id']}_{selected_session}"
        snapshot = tuple((r["id"], r["question"], r["answer"], r["submitted_at"]) for r in responses)
        saved_summary = st.session_state.get(summary_key)
        if st.button("Generate AI summary", disabled=not responses, key=f"generate_summary_{selected_session}"):
            try:
                with st.spinner("Summarizing student responses..."):
                    summary = summarize_responses(responses)
            except RequestException:
                st.error("The AI service could not complete the request. Please try again.")
            except (ValueError, KeyError, IndexError, TypeError):
                st.error("Could not generate a summary. Check the server's AI configuration and try again.")
            else:
                saved_summary = {"text": summary, "snapshot": snapshot}
                st.session_state[summary_key] = saved_summary
        if saved_summary:
            if saved_summary["snapshot"] != snapshot:
                st.info("Responses have changed. Generate a new summary to include the latest submissions.")
            st.markdown(saved_summary["text"])
            st.caption("AI-generated from the submissions available when requested. Review against the original responses.")
        elif not responses:
            st.info("No responses have been submitted yet.")
            
                

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
