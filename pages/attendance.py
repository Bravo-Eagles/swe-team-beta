import streamlit as st            # as st gives streamlit a shorter name "st"
from datetime import datetime     #datetime class from pythons datetime module
                                
st.title("KSU Attendance Tracker")     # creates large title at the top of webpage
st.header("Student Check-In")          # creates a smaller heading underneath the title

name = st.text_input("Name")             #creates a textbox on the webpage for input name
student_id = st.text_input("Student ID") #creates a textbox to contain your student id

course = st.selectbox(                   #creates a dropdown menu to select the course 
    "Select your class",                                
    ["CS 32301", "CS35101"]              #whatever the student selects gets stored in course
)

answer = st.text_area(                   #text_area makes a larger box for longer responses.
    "What is one thing you learned in class today?"
)

if st.button("Submit Attendance"):      #creates button called submit attendance

    if name == "" or student_id == "" or answer == "":   
        st.error("Please complete all fields.")

    else:
        submission_time = datetime.now()  # get current date and time 

        st.success("Attendance submitted successfully!")  #gives student a success message

        st.write("Name:", name)                            #display the data
        st.write("Student ID:", student_id)
        st.write("Course:", course)
        st.write("Answer:", answer)
        st.write("Submitted:", submission_time)