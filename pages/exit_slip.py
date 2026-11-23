import streamlit as st
from datetime import datetime
from src.passwords import require_login
from src.sidebar import sidebar
from src.style import setup_page

setup_page("Exit Slip", gradient=False)
require_login()
sidebar()

st.title("Exit Slip")
st.write("Submit your response to today's class question.")

st.subheader("Today's Question")
question = "What is one thing you learned today, and what is one question you still have?"
st.info(question)

# Store responses during the current session
if "exit_slip_responses" not in st.session_state:
    st.session_state.exit_slip_responses = []

with st.form("exit_slip_form"):
    student_name = st.text_input("Your name")
    answer = st.text_area("Your response", height=150)
    submitted = st.form_submit_button("Submit Exit Slip", type="primary")

# Messages sit outside the form so they don't render inside the card
if submitted:
    if not student_name.strip() or not answer.strip():
        st.error("Please enter your name and response.")
    else:
        st.session_state.exit_slip_responses.append(
            {
                "name": student_name.strip(),
                "question": question,
                "answer": answer.strip(),
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        st.success("Your exit slip was submitted successfully!")

st.divider()

with st.expander("Professor View: Submitted Responses"):
    responses = st.session_state.exit_slip_responses

    if responses:
        st.write(f"Total submissions: {len(responses)}")

        for index, response in enumerate(responses, start=1):
            with st.container(border=True, key=f"card_response_{index}"):
                st.markdown(f"**Response {index}: {response['name']}**")
                st.write("**Question:**", response["question"])
                st.write("**Answer:**", response["answer"])
                st.caption(f"Submitted: {response['submitted_at']}")
    else:
        st.info("No responses have been submitted yet.")