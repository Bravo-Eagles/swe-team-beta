
import streamlit as st

from src.sidebar import sidebar
from src.passwords import require_login
from api.checkin_api import get_checkin_details, submit_checkin

from src.passwords import current_user

from src.nfc import verify_tap
from api.nfc_api import record_tap, find_nfc_scheduled_id
sidebar()

st.title("Student Check-In")

# Factory key (all zeros) for testing. Replace with our own secret key before real use.
FACTORY_KEY = bytes(16)

picc_data = st.query_params.get("picc_data")
cmac = st.query_params.get("cmac")

if picc_data and cmac:
    try:
        uid, counter = verify_tap(picc_data, cmac, FACTORY_KEY)
    except ValueError:
        st.error("This check-in link isn't valid. Please tap the tag again.")
        st.stop()

    if not record_tap(uid, counter):
        st.error("This check-in link was already used. Please tap the tag again.")
        st.stop()

    # Link accepted: remember the tag for this browser session, and remove
    # the link from the address bar so reruns don't check it again.
    st.session_state["nfc_uid"] = uid
    st.query_params.clear()

raw_id = st.query_params.get("scheduled_id")

if current_user() is None:
    if raw_id:
        st.session_state["pending_checkin_id"] = str(raw_id)
    st.switch_page("./pages/login.py")

user = require_login()

# NFC check-in: work out the class from the tag's professor.
if not raw_id and "nfc_uid" in st.session_state:
    found = find_nfc_scheduled_id(st.session_state["nfc_uid"], user["id"])
    if found is None:
        st.error("You don't have a class with this professor right now.")
        st.stop()
    raw_id = found

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
            st.session_state.pop("nfc_uid", None)
            
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Check-in failed. Please try again.")