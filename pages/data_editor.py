from datetime import date, datetime, time

import streamlit as st

from api import attendance_api


def _offering_label(offering) -> str:
    return (
        f"{offering['class_name']} ({offering['course_id']}) - "
        f"{offering['semester']} {offering['year']}"
    )


def _session_label(session) -> str:
    return f"{session['date']} at {session['start_time']}"


def _check_in_time_label(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


st.title("Attendance Data Editor")
st.write("Review and update student attendance for a class meeting.")

offerings = attendance_api.list_class_offerings()
if not offerings:
    st.info(
        "No class offerings are available yet. Set up classes, teaching assignments, "
        "and student enrollments before editing attendance."
    )
    st.stop()

offerings_by_id = {offering["teaching_id"]: offering for offering in offerings}
teaching_id = st.selectbox(
    "Class",
    options=list(offerings_by_id),
    format_func=lambda offering_id: _offering_label(offerings_by_id[offering_id]),
)

with st.expander("Add a class meeting"):
    with st.form("add_class_meeting"):
        meeting_date = st.date_input("Date", value=date.today())
        meeting_start_time = st.time_input(
            "Start time", value=time(hour=8, minute=0)
        )
        add_meeting = st.form_submit_button("Add meeting")

    if add_meeting:
        attendance_api.create_scheduled_session(
            teaching_id, meeting_date, meeting_start_time
        )
        st.success("Class meeting added.")
        st.rerun()

sessions = attendance_api.list_scheduled_sessions(teaching_id)
if not sessions:
    st.info("This class has no scheduled meetings yet. Add one above to enter attendance.")
    st.stop()

sessions_by_id = {session["id"]: session for session in sessions}
scheduled_id = st.selectbox(
    "Class meeting",
    options=list(sessions_by_id),
    format_func=lambda session_id: _session_label(sessions_by_id[session_id]),
)

students = attendance_api.list_students_for_session(teaching_id, scheduled_id)
if not students:
    st.info("There are no students enrolled in this class offering.")
    st.stop()

selected_session = sessions_by_id[scheduled_id]
editor_rows = []
for student in students:
    check_in_time = student["check_in_time"]
    if check_in_time is None:
        check_in_time = f"{selected_session['date']} {selected_session['start_time']}"

    editor_rows.append(
        {
            "student_id": student["student_id"],
            "student": f"{student['first_name']} {student['last_name']}",
            "attendance": "Present" if student["is_present"] else "Absent",
            "check_in_time": _check_in_time_label(str(check_in_time)),
        }
    )

st.caption(f"{len(editor_rows)} enrolled student(s)")
with st.form("attendance_editor"):
    edited_rows = st.data_editor(
        editor_rows,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        disabled=["student_id", "student"],
        column_config={
            "student_id": None,
            "student": st.column_config.TextColumn("Student", disabled=True),
            "attendance": st.column_config.SelectboxColumn(
                "Attendance",
                options=["Present", "Absent"],
                required=True,
            ),
            "check_in_time": st.column_config.TextColumn(
                "Check-in time",
                help="Use YYYY-MM-DD HH:MM. The time is ignored when the student is absent.",
            ),
        },
    )
    save_attendance = st.form_submit_button("Save attendance", type="primary")

if save_attendance:
    records = []
    for row in edited_rows.to_dict(orient="records"):
        attendance_status = row["attendance"]
        if attendance_status not in ("Present", "Absent"):
            st.error("Choose Present or Absent for every student.")
            st.stop()
        check_in_time = row["check_in_time"]
        records.append(
            {
                "student_id": int(row["student_id"]),
                "present": attendance_status == "Present",
                "check_in_time": "" if check_in_time is None else str(check_in_time),
            }
        )

    try:
        attendance_api.save_attendance_records(scheduled_id, records)
    except ValueError as exc:
        st.error(str(exc))
    else:
        st.success("Attendance saved.")
        st.rerun()
