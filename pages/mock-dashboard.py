import streamlit as st
import pandas as pd

st.title("Attendance Dashboard")

st.header("Attendance Overview")

# Fake data for testing
total_students = 25
present_students = 20
absent_students = 5

# Display basic attendance numbers
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Students", total_students)

with col2:
    st.metric("Present", present_students)

with col3:
    st.metric("Absent", absent_students)

st.header("Weekly Attendance")

# Fake attendance data
attendance_data = {
    "Day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "Present": [27, 24, 26, 28, 23],
}

df = pd.DataFrame(attendance_data)

# Display the data
st.dataframe(df)

# Create a graph
st.bar_chart(df.set_index("Day"))