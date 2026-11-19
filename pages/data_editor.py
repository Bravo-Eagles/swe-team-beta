
from datetime import date, datetime, time

import streamlit as st

from api import attendance_api
from src.sidebar import sidebar


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def _offering_label(offering) -> str:
    return (
        f"{offering['class_name']} ({offering['course_id']}) - "
        f"{offering['semester']} {offering['year']}"
    )


def _format_time(value) -> str:
    """Display database time in 12-hour format."""
    if not value:
        return "Not set"

    return time.fromisoformat(str(value)).strftime("%I:%M %p")


def _to_24_hour(hour: int, minute: int, period: str) -> time:
    """Convert 12-hour time into a Python time object."""
    hour_24 = hour % 12

    if period == "PM":
        hour_24 += 12

    return time(hour_24, minute)


def _time_label(value: time) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def _meeting_status(session, now: datetime) -> tuple[str, int]:
    session_date = date.fromisoformat(session["date"])

    start = datetime.combine(
        session_date,
        time.fromisoformat(session["start_time"]),
    )

    if start > now:
        return "Upcoming", 0

    if session["end_time"]:
        end = datetime.combine(
            session_date,
            time.fromisoformat(session["end_time"]),
        )

        if now <= end:
            return "In progress", 1

        return "Past", 2

    return "Started (end unknown)", 2


def _attendance_defaults(student, session):
    """Get the initial attendance date and time."""
    meeting_date = date.fromisoformat(session["date"])
    stored = student["check_in_time"]

    if stored and student["attendance_status"] == "Present":
        try:
            parsed = datetime.fromisoformat(str(stored))

            # Do not initialize the calendar with an invalid
            # date before the meeting.
            if parsed.date() >= meeting_date:
                return (
                    parsed.date(),
                    parsed.time().replace(second=0, microsecond=0),
                )
        except ValueError:
            pass

    return (
        meeting_date,
        time.fromisoformat(session["start_time"]).replace(
            second=0,
            microsecond=0,
        ),
    )


def _initialize_attendance_state(students, session, scheduled_id):
    """Prepare editable attendance values for a meeting."""
    state_key = f"attendance_data_{scheduled_id}"

    if state_key not in st.session_state:
        data = {}

        for student in students:
            student_id = student["student_id"]

            check_date, check_time = _attendance_defaults(
                student, session
            )

            data[student_id] = {
                "status": student["attendance_status"],
                "date": check_date,
                "time": check_time,
            }

        st.session_state[state_key] = data

    return state_key


def _time_selectors(prefix: str, default: time) -> time:
    """Show 12-hour Hour, Minute, and AM/PM selectors."""
    hour_12 = default.hour % 12 or 12
    period = "AM" if default.hour < 12 else "PM"

    hour_col, minute_col, period_col = st.columns(3)

    with hour_col:
        hour = st.selectbox(
            "Hour",
            options=list(range(1, 13)),
            index=hour_12 - 1,
            key=f"{prefix}_hour",
        )

    with minute_col:
        minute = st.selectbox(
            "Minute",
            options=list(range(60)),
            index=default.minute,
            format_func=lambda value: f"{value:02d}",
            key=f"{prefix}_minute",
        )

    with period_col:
        selected_period = st.selectbox(
            "AM / PM",
            options=["AM", "PM"],
            index=0 if period == "AM" else 1,
            key=f"{prefix}_period",
        )

    return _to_24_hour(hour, minute, selected_period)


# --------------------------------------------------
# PAGE
# --------------------------------------------------

sidebar()

st.title("Meeting and Student Editor", anchor = False)
st.write("Review and update student attendance for a class meeting.")


# --------------------------------------------------
# SELECT CLASS
# --------------------------------------------------

offerings = attendance_api.list_class_offerings()

if not offerings:
    st.info(
        "No class offerings are available yet. "
        "Set up classes, teaching assignments, and "
        "student enrollments first."
    )
    st.stop()

offerings_by_id = {
    offering["teaching_id"]: offering
    for offering in offerings
}

teaching_id = st.selectbox(
    "Class",
    options=list(offerings_by_id),
    format_func=lambda offering_id: _offering_label(
        offerings_by_id[offering_id]
    ),
)


# --------------------------------------------------
# ADD CLASS MEETING
# --------------------------------------------------

with st.expander("Add a class meeting"):

    with st.form("add_class_meeting"):

        meeting_date = st.date_input(
            "Date",
            value=date.today(),
            min_value=date.today(),
        )

        st.write("**Start time**")

        meeting_start_time = _time_selectors(
            "add_start",
            time(0, 0),
        )

        st.write("**End time**")

        meeting_end_time = _time_selectors(
            "add_end",
            time(0, 0),
        )

        add_meeting = st.form_submit_button("Add meeting")

    if add_meeting:

        if meeting_end_time <= meeting_start_time:
            st.error(
                "End time must be later than start time."
            )

        else:
            try:
                attendance_api.create_scheduled_session(
                    teaching_id,
                    meeting_date,
                    meeting_start_time,
                    meeting_end_time,
                )

            except ValueError as exc:
                st.error(str(exc))

            else:
                st.success(
                    "Class meeting added successfully!"
                )
                st.rerun()


# --------------------------------------------------
# CLASS MEETING TABLE
# --------------------------------------------------

sessions = attendance_api.list_scheduled_sessions(teaching_id)

if not sessions:
    st.info(
        "This class has no scheduled meetings yet. "
        "Add one above to enter attendance."
    )
    st.stop()

sessions_by_id = {
    session["id"]: session
    for session in sessions
}

now = datetime.now()
meeting_rows = []

for session in sessions:
    status, priority = _meeting_status(session, now)

    meeting_rows.append(
        {
            "id": session["id"],
            "Date": session["date"],
            "Start Time": _format_time(session["start_time"]),
            "End Time": _format_time(session["end_time"]),
            "Status": status,
            "_priority": priority,
        }
    )


def _meeting_sort_key(row):
    meeting_date = date.fromisoformat(row["Date"])

    if row["_priority"] == 0:
        return (0, meeting_date.toordinal())

    if row["_priority"] == 1:
        return (1, meeting_date.toordinal())

    return (2, -meeting_date.toordinal())


meeting_rows.sort(key=_meeting_sort_key)

st.subheader("Class Meeting Records")

st.caption(
    "Select a meeting to view its attendance records."
)

selection = st.dataframe(
    [
        {
            "Date": row["Date"],
            "Start Time": row["Start Time"],
            "End Time": row["End Time"],
            "Status": row["Status"],
        }
        for row in meeting_rows
    ],
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    key=f"meeting_table_{teaching_id}",
)

selected_indices = selection.selection.rows

if not selected_indices:
    st.info(
        "Select a class meeting above to view its attendance."
    )
    st.stop()

selected_row = meeting_rows[selected_indices[0]]

scheduled_id = selected_row["id"]
selected_session = sessions_by_id[scheduled_id]
meeting_status = selected_row["Status"]


# --------------------------------------------------
# EDIT OR CANCEL UPCOMING MEETING
# --------------------------------------------------

if meeting_status == "Upcoming":

    with st.expander("Edit existing class meeting"):

        with st.form(f"edit_class_meeting_{scheduled_id}"):

            new_date = st.date_input(
                "Meeting Date",
                value=date.fromisoformat(
                    selected_session["date"]
                ),
                min_value=date.today(),
            )

            st.write("**Meeting Start Time**")

            new_start_time = _time_selectors(
                f"edit_start_{scheduled_id}",
                time.fromisoformat(
                    selected_session["start_time"]
                ),
            )

            st.write("**Meeting End Time**")

            existing_end = (
                time.fromisoformat(selected_session["end_time"])
                if selected_session["end_time"]
                else time(9, 15)
            )

            new_end_time = _time_selectors(
                f"edit_end_{scheduled_id}",
                existing_end,
            )

            save_meeting = st.form_submit_button(
                "Save meeting changes"
            )

        if save_meeting:
            try:
                attendance_api.update_scheduled_session(
                    scheduled_id,
                    new_date,
                    new_start_time,
                    new_end_time,
                )

            except ValueError as exc:
                st.error(str(exc))

            else:
                st.success("Class meeting updated!")
                st.rerun()

    
    if st.button(
        "Delete Selected Meeting",
        key=f"delete_meeting_{scheduled_id}",
        type="secondary",
    ):
        try:
            attendance_api.cancel_scheduled_session(scheduled_id)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.success("Meeting removed successfully!")
            st.rerun()

elif meeting_status == "In progress":

    st.info(
        "This meeting is currently in progress. "
        "Its date and time cannot be changed."
    )

# No blue message for past meetings.


# --------------------------------------------------
# STUDENT ATTENDANCE EDITOR
# --------------------------------------------------

students = attendance_api.list_students_for_session(
    teaching_id,
    scheduled_id,
)

st.subheader("Attendance Record")

st.markdown(
    f"{selected_session['date']} · "
    f"{_format_time(selected_session['start_time'])}–"
    f"{_format_time(selected_session['end_time'])}"
)

if not students:
    st.info(
        "There are no students enrolled in this class offering."
    )
    st.stop()

state_key = _initialize_attendance_state(
    students,
    selected_session,
    scheduled_id,
)

attendance_data = st.session_state[state_key]

meeting_date = date.fromisoformat(
    selected_session["date"]
)

for student in students:

    student_id = student["student_id"]
    student_data = attendance_data[student_id]

    student_name = (
        f"{student['first_name']} "
        f"{student['last_name']}"
    )

    with st.container(border=True):

        st.markdown(f"**{student_name}**")

        attendance_options = ["Present", "Absent"]
        current_status = student_data["status"]

        student_data["status"] = st.selectbox(
            "Student Attendance",
            label_visibility="collapsed",
            options=attendance_options,
            index=(
                attendance_options.index(current_status)
                if current_status in attendance_options
                else None
            ),
            placeholder="Not recorded",
            key=f"status_{scheduled_id}_{student_id}",
        )


# --------------------------------------------------
# SAVE ATTENDANCE
# --------------------------------------------------

st.caption(
    f"{len(students)} enrolled student(s)"
)

if st.button(
    "Save Attendance",
    type="primary",
    width="stretch",
    
):


    records = []

    for student in students:

        student_id = student["student_id"]
        student_data = attendance_data[student_id]

        check_in_datetime = datetime.combine(
            student_data["date"],
            student_data["time"],
        )

        records.append(
            {
                "student_id": int(student_id),
                "attendance_status": student_data["status"] or "Not recorded",
                "check_in_time": check_in_datetime.isoformat(
                    sep=" ",
                    timespec="minutes",
                ),
            }
        )

    try:
        attendance_api.save_attendance_records(
            scheduled_id,
            records,
        )

    except ValueError as exc:
        st.error(str(exc))

    else:
        # Reload saved attendance from the database.
        del st.session_state[state_key]

        st.toast("Attendance updated successfully!", icon="✅")

        st.rerun()
