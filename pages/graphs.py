#Notes. without a shared database i can't have attendance
#update in real time and have a history of student attendance. 
# left an example to show it works
# to run make sure you have streamlit and matplotlib installed.
# uv add matplotlib streamlit
# uv run streamlit run graphs.py
#  

import streamlit as st
import matplotlib.pyplot as plt


st.title("Class Attendance Dashboard")

# example until we connect to database
# creates attendance data organized by class
attendance = {
    "CS 32301": {
        "Shagai (Student)": [1, 1, 0, 1, 1],
        "Aidan (Student)": [1, 0, 1, 1, 1],
        "Giovanni (Teacher)": [1, 0, 0, 0, 1]
    },

    "CS 35101": {
        "Shagai (Student)": [1, 1, 1, 1, 1],
        "Aidan (Student)": [0, 0, 0, 0, 1],
        "Giovanni (Teacher)": [1, 1, 1, 1, 0]
    }
}

days = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# class select
course = st.selectbox( #creates dropdown menu
    "Select a class",
    list(attendance.keys()) #adds anything under "attendance" ( cs 32301 and cs 35101)
)

# Select a person enrolled in the class
person = st.selectbox(
    "Select a student or teacher",
    list(attendance[course].keys())
)

# Gets attendance for the selected person
records = attendance[course][person]

# Creates graph
fig, ax = plt.subplots() #fig is the image creating the graph and ax are the axes

ax.plot(days, records, marker="o") # x-axis is days, y-axis is records, marker places a circle at each data point

ax.set_title(person + " - " + course) #concatenation of the name and course
ax.set_xlabel("Day of the Week")
ax.set_ylabel("Attendance")

ax.set_yticks([0, 1]) #only show ticks for attendance, either present or not
ax.set_yticklabels(["Absent", "Present"])

ax.set_ylim(-0.2, 1.2) #gives more room so graph looks better
ax.grid(True, linestyle="--", alpha=0.3) #creates a dashed grid with 30% opacity. 

st.pyplot(fig)
plt.close(fig)

# Calculate attendance statistics
days_present = sum(records)
total_days = len(records) #len for length (5 days)

st.write("Days Present:", days_present)
st.write("Total Days:", total_days)
st.write(
    "Attendance Percentage:",
    round(days_present / total_days * 100, 1), #makes it a whole number and round to 1 decimal
    "%"
)
