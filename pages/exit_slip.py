
import streamlit as st
from datetime import datetime
from src.passwords import require_login
#require Login
require_login()

st.title("Exit Slip")
st.write("Submit your response to today's class question.")

# Demo question
st.subheader("Today's Question")
question = "What is one thing you learned today, and what is one question you still have?"

st.info(question)

# Store responses during the current session
if "exit_slip_responses" not in st.session_state:
    st.session_state.exit_slip_responses = []

# Student response form
with st.form("exit_slip_form"):
    student_name = st.text_input("Your name")
    answer = st.text_area("Your response")

    submitted = st.form_submit_button("Submit Exit Slip")

    if submitted:
        if not student_name.strip() or not answer.strip():
            st.error("Please enter your name and response.")
        else:
            response = {
                "name": student_name.strip(),
                "question": question,
                "answer": answer.strip(),
                "submitted_at": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            st.session_state.exit_slip_responses.append(response)

            st.success("Your exit slip was submitted successfully!")

# Demo view of submitted responses
st.divider()

with st.expander("Professor View: Submitted Responses"):
    st.subheader("Exit Slip Responses")

    if st.session_state.exit_slip_responses:
        st.write(
            f"Total submissions: "
            f"{len(st.session_state.exit_slip_responses)}"
        )

        for index, response in enumerate(
            st.session_state.exit_slip_responses, start=1
        ):
            st.markdown(f"### Response {index}")
            st.write("Student:", response["name"])
            st.write("Answer:", response["answer"])
            st.caption(
                f"Submitted at: {response['submitted_at']}"
            )
    else:
        st.info("No responses have been submitted yet.")

if st.session_state.exit_slip_responses:
    for index, response in enumerate(
        st.session_state.exit_slip_responses, start=1
    ):
        with st.expander(f"Response {index}: {response['name']}"):
            st.write("**Question:**", response["question"])
            st.write("**Answer:**", response["answer"])
            st.caption(f"Submitted: {response['submitted_at']}")
else:
    st.write("No responses submitted yet.")
