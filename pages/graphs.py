
# uv run streamlit run graphs.py
#  

import streamlit as st
import matplotlib.pyplot as plt
from src.passwords import require_login
from src import database as db
from src.sidebar import sidebar
from datetime import date


# Page configuration
st.set_page_config(
    page_title="Attendance Graphs",
    page_icon="📊",
    layout="wide"
)

# Require login
user = require_login()
sidebar()

# Days of the week
days = [
    "Sunday", "Monday", "Tuesday",
    "Wednesday", "Thursday", "Friday",
    "Saturday"
]


# Retrieve account role
def get_account_role(account_id):
    """Retrieve the role linked to the logged-in account."""

    with db.get_connection() as conn:
        account = conn.execute(
            """
            SELECT role
            FROM accounts
            WHERE id = ?
            """,
            (account_id,)
        ).fetchone()

    if account is None or not account["role"]:
        return None

    return account["role"].upper()


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


# Retrieve teacher information
def get_teacher_by_account_id(account_id):
    """Retrieve the teacher linked to the logged-in account."""

    with db.get_connection() as conn:
        teacher = conn.execute(
            """
            SELECT id, first_name, last_name
            FROM teacher
            WHERE account_id = ?
            """,
            (account_id,)
        ).fetchone()

    return teacher


# Retrieve enrolled classes
def get_enrolled_classes(student_id):
    """Retrieve all classes a student is enrolled in."""

    with db.get_connection() as conn:
        classes = conn.execute(
            """
            SELECT
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


# Retrieve attendance by course
def get_attendance_by_course(student_id):
    """Count student check-ins for each enrolled course."""

    with db.get_connection() as conn:
        records = conn.execute(
            """
            SELECT
                c.course_id,
                t.semester,
                t.year,
                COUNT(a.student_id) AS total
            FROM enrolled e
            JOIN teaching t ON e.teaching_id = t.id
            JOIN class c ON t.class_id = c.id
            LEFT JOIN scheduled s
                ON s.teaching_id = t.id
                AND s.date < ?
            LEFT JOIN attendance a
                ON a.scheduled_id = s.id
                AND a.student_id = e.student_id
                AND a.is_deleted = 0
            WHERE e.student_id = ?
            GROUP BY t.id
            ORDER BY t.year, t.semester
            """,
            (date.today().isoformat(), student_id)
        ).fetchall()

    return records


# Retrieve weekly attendance
def get_weekly_attendance(student_id, teaching_id):
    """Count student check-ins grouped by week."""

    with db.get_connection() as conn:
        records = conn.execute(
            """
            SELECT
                strftime('%Y-%W', s.date) AS week,
                COUNT(a.student_id) AS total
            FROM scheduled s
            LEFT JOIN attendance a
                ON a.scheduled_id = s.id
                AND a.student_id = ?
                AND a.is_deleted = 0
            WHERE s.teaching_id = ?
                AND s.date < ?
            GROUP BY strftime('%Y-%W', s.date)
            ORDER BY week
            """,
            (
                student_id,
                teaching_id,
                date.today().isoformat()
            )
        ).fetchall()

    return records


# Retrieve student attendance percentage
def get_student_attendance(student_id, teaching_id):
    """Calculate attendance for a selected class."""

    with db.get_connection() as conn:
        records = conn.execute(
            """
            SELECT
                COUNT(s.id) AS total_sessions,
                COUNT(a.student_id) AS attended
            FROM scheduled s
            LEFT JOIN attendance a
                ON a.scheduled_id = s.id
                AND a.student_id = ?
                AND a.is_deleted = 0
            WHERE s.teaching_id = ?
                AND s.date < ?
            """,
            (
                student_id,
                teaching_id,
                date.today().isoformat()
            )
        ).fetchone()

    return records


# Retrieve historical absences by weekday
def get_absences_by_day(student_id, teaching_id):
    """Calculate absence rates for each weekday."""

    with db.get_connection() as conn:
        records = conn.execute(
            """
            SELECT
                strftime('%w', s.date) AS weekday,
                COUNT(s.id) AS total_sessions,
                COUNT(a.student_id) AS attended
            FROM scheduled s
            LEFT JOIN attendance a
                ON a.scheduled_id = s.id
                AND a.student_id = ?
                AND a.is_deleted = 0
            WHERE s.teaching_id = ?
                AND s.date < ?
            GROUP BY strftime('%w', s.date)
            ORDER BY weekday
            """,
            (
                student_id,
                teaching_id,
                date.today().isoformat()
            )
        ).fetchall()

    return records


# Retrieve attendance across a teacher's students
def get_all_student_weekday_attendance(teacher_id):
    """Calculate weekday attendance for a teacher's students."""

    with db.get_connection() as conn:
        records = conn.execute(
            """
            SELECT
                strftime('%w', s.date) AS weekday,
                COUNT(*) AS expected,
                COUNT(a.student_id) AS attended
            FROM scheduled s
            JOIN teaching t
                ON s.teaching_id = t.id
            JOIN enrolled e
                ON e.teaching_id = t.id
            JOIN student stu
                ON stu.id = e.student_id
            LEFT JOIN attendance a
                ON a.scheduled_id = s.id
                AND a.student_id = stu.id
                AND a.is_deleted = 0
            WHERE t.teacher_id = ?
                AND s.date < ?
            GROUP BY strftime('%w', s.date)
            ORDER BY weekday
            """,
            (teacher_id, date.today().isoformat())
        ).fetchall()

    return records


# Retrieve logged-in account role
role = get_account_role(user["id"])

if role is None:
    st.warning("No account role was found.")
    st.stop()


# Display teacher attendance graphs
if role == "TEACHER":

    teacher = get_teacher_by_account_id(user["id"])

    if teacher is None:
        st.warning("No teacher profile is linked to your account.")
        st.stop()

    st.title("Teacher Attendance Analytics")
    st.subheader(f"Welcome, {teacher['first_name']}!")
    st.caption(user["email"])

    st.divider()

    # Teacher Graph 1: Student Attendance by Weekday
    st.header("Student Attendance by Weekday")

    st.write(
        "This graph compares attendance rates for students "
        "enrolled in your classes."
    )

    all_student_data = get_all_student_weekday_attendance(
        teacher["id"]
    )

    labels = []
    rates = []

    expected_total = 0
    attended_total = 0

    for row in all_student_data:
        expected = row["expected"]
        attended = row["attended"]

        if expected > 0:
            attendance_rate = (attended / expected) * 100

            labels.append(days[int(row["weekday"])])
            rates.append(attendance_rate)

            expected_total += expected
            attended_total += attended

    if rates:

        fig, ax = plt.subplots()
        ax.bar(labels, rates)
        ax.set_xlabel("Day of the Week")
        ax.set_ylabel("Attendance Rate (%)")
        ax.set_ylim(0, 100)
        ax.set_title("Student Attendance by Weekday")
        plt.xticks(rotation=30)
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

        lowest_index = rates.index(min(rates))

        st.write(
            f"**Lowest Attendance Day:** "
            f"{labels[lowest_index]} "
            f"({rates[lowest_index]:.1f}%)"
        )

        overall_rate = (
            attended_total / expected_total
        ) * 100

        st.caption(
            f"Overall student attendance rate: "
            f"{overall_rate:.1f}%"
        )

    else:
        st.info("No historical student attendance data found.")


# Display student attendance graphs
elif role == "STUDENT":

    student = get_student_by_account_id(user["id"])

    if student is None:
        st.warning("No student profile is linked to your account.")
        st.stop()

    st.title("Attendance Graphs")
    st.subheader(f"Welcome, {student['first_name']}!")
    st.caption(user["email"])

    st.divider()

    classes = get_enrolled_classes(student["id"])

    if not classes:
        st.info("You are not currently enrolled in any classes.")
        st.stop()

    # Select class
    course_options = {
        (
            f"{course['course_id']} - "
            f"{course['semester']} {course['year']}"
        ): course["teaching_id"]
        for course in classes
    }

    selected_course = st.selectbox(
        "Select a class",
        list(course_options.keys())
    )

    teaching_id = course_options[selected_course]

    # Student Graph 1: Attendance by Course
    st.header("Attendance by Course")

    course_data = get_attendance_by_course(student["id"])

    if course_data:
        names = [
            f"{row['course_id']} "
            f"({row['semester']} {row['year']})"
            for row in course_data
        ]

        totals = [row["total"] for row in course_data]

        fig, ax = plt.subplots()
        ax.bar(names, totals)
        ax.set_xlabel("Course")
        ax.set_ylabel("Check-ins")
        ax.set_title("Attendance by Course")
        plt.xticks(rotation=30)
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

    else:
        st.info("No course attendance found.")

    # Student Graph 2: Weekly Attendance Trend
    st.header("Weekly Attendance Trend")

    weekly_data = get_weekly_attendance(
        student["id"], teaching_id
    )

    if weekly_data:
        weeks = [row["week"] for row in weekly_data]
        totals = [row["total"] for row in weekly_data]

        fig, ax = plt.subplots()
        ax.plot(weeks, totals, marker="o")
        ax.set_xlabel("Week")
        ax.set_ylabel("Check-ins")
        ax.set_title("Weekly Attendance")
        plt.xticks(rotation=45)
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

    else:
        st.info("No weekly attendance records found.")

    # Student Graph 3: Attendance Percentage
    st.header("Attendance Percentage")

    attendance = get_student_attendance(
        student["id"], teaching_id
    )

    total = attendance["total_sessions"]
    attended = attendance["attended"]

    if total > 0:
        percentage = (attended / total) * 100

        st.write(
            f"Attendance rate for this class: "
            f"**{percentage:.1f}%**"
        )

        fig, ax = plt.subplots()
        ax.bar(
            ["Attended", "Missed"],
            [attended, total - attended]
        )
        ax.set_ylabel("Number of Sessions")
        ax.set_title("Attendance Summary")
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

    else:
        st.info("No completed sessions found.")

    # Student Graph 4: Absences by Weekday
    st.header("Absences by Weekday")

    absence_data = get_absences_by_day(
        student["id"], teaching_id
    )

    if absence_data:
        labels = []
        rates = []

        for row in absence_data:
            total_sessions = row["total_sessions"]
            attended = row["attended"]

            if total_sessions > 0:
                absence_rate = (
                    (total_sessions - attended) / total_sessions
                ) * 100

                labels.append(days[int(row["weekday"])])
                rates.append(absence_rate)

        if rates:
            fig, ax = plt.subplots()
            ax.bar(labels, rates)
            ax.set_xlabel("Day of the Week")
            ax.set_ylabel("Absence Rate (%)")
            ax.set_ylim(0, 100)
            ax.set_title("Absences by Weekday")
            plt.xticks(rotation=30)
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

    else:
        st.info("No historical attendance records found.")


# Unknown account role
else:
    st.warning("Your account role does not have access to this page.")
