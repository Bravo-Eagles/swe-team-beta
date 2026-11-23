import streamlit as st
from src.passwords import require_login
from api.auth_api import get_user_role


def sidebar():
    user = require_login()
    role = get_user_role(user["id"])

    st.sidebar.title("CheckIn")

    st.sidebar.page_link("main.py", label="Home")

    if role == "STUDENT":
        st.sidebar.page_link(
            "pages/student_dashboard.py",
            label="Student Dashboard"
        )
        st.sidebar.page_link(
            "pages/check_in.py",
            label="Student Check In"
        )
        st.sidebar.page_link(
            "pages/exit_slip.py",
            label="Exit Slip"
        )

    elif role == "TEACHER":
        st.sidebar.page_link(
            "pages/prof_classes.py",
            label="Professor Dashboard"
        )
        st.sidebar.page_link(
            "pages/professor_checkin.py",
            label="Professor Check In"
        )

    else:
        st.sidebar.warning("Your account has no recognized role.")
