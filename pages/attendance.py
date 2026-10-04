import streamlit as st #brings streamlit library into program to use its tools, as st gives streamlit a shorter name "st"
from datetime import datetime # imports the datetime class from pythons datetime module
                              #use datetime later to record when the student submitted attendance, datatime might produce a value representing 2026-10-03 21:12:35
st.title("KSU Attendance Tracker")     # creates large title at the top of streamlit webpage
st.header("Student Check-In")          # creates a smaller heading underneath the title

name = st.text_input("Name")             # st.text_input("Name") creates a textbox on the webpage, and whatever the student types is returned by text_input and stored in name
student_id = st.text_input("Student ID") #streamlit creates a textbox to contain your student id, and stores your input in student_id

course = st.selectbox(                   #creates a dropdown menu on streamlit so students can select the course they are in
    "Select your class",                                
    ["CS 32301", "CS35101"]              #whatever the student selects gets stored in course
)

answer = st.text_area(                   #text_area recieves user input and provides a larger box for longer responses.
    "What is one thing you learned in class today?"
)

if st.button("Submit Attendance"):  #streamlit creates button that returns either true or false, when student clicks the button, it becomes true and code below runs

    if name == "" or student_id == "" or answer == "":    #if name, or student_id or answer contains an empty string, it executes an error message on the webpage stating please complete all fields
        st.error("Please complete all fields.")

    else:
        submission_time = datetime.now()               # get current date and time and store it in submission_time

        st.success("Attendance submitted successfully!")  #gives student a success message on the webpage

        st.write("Name:", name)                            #display the data
        st.write("Student ID:", student_id)
        st.write("Course:", course)
        st.write("Answer:", answer)
        st.write("Submitted:", submission_time)