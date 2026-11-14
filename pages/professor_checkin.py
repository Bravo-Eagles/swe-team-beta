
import io
import qrcode
import streamlit as st
from src.sidebar import sidebar

from src.passwords import require_login
from api.professor_checkin_api import get_professor_sessions

sidebar()

st.title("Professor Check-In")
st.write("Select a scheduled class to generate its check-in QR code.")

user = require_login()
sessions = get_professor_sessions(user["id"])

if not sessions:
    st.write("Logged-in account:", user["email"])
    st.write("Account ID:", user["id"])
    st.warning("No scheduled classes were found for your professor account.")
    st.stop()

options = {
    (
        f"{s['course_id']} - {s['class_name']} | "
        f"{s['date']} | {s['start_time']}"
    ): s
    for s in sessions
}

selected_label = st.selectbox(
    "Select a scheduled class",
    list(options.keys())
)

selected = options[selected_label]

st.write("Course:", selected["course_id"])
st.write("Class:", selected["class_name"])
st.write("Date:", selected["date"])
st.write("Time:", selected["start_time"], "-", selected["end_time"])

base_url = st.text_input(
    "App URL accessible to students",
    value="http://localhost:8501",
    help="Use your computer's network address or deployed app URL for phone scanning."
)

if st.button("Generate QR Code"):
    base_url = base_url.strip().rstrip("/")

    if not (
        base_url.startswith("http://")
        or base_url.startswith("https://")
    ):
        st.error("Enter a valid URL starting with http:// or https://.")
        st.stop()

    checkin_url = (
        f"{base_url}/check_in"
        f"?scheduled_id={selected['scheduled_id']}"
    )

    qr = qrcode.make(checkin_url)
    image_buffer = io.BytesIO()
    qr.save(image_buffer, format="PNG")

    st.image(image_buffer.getvalue(), width=250)
    st.code(checkin_url)
    st.success("QR code generated successfully!")
