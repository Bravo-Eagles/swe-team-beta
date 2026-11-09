import streamlit as st
from api.courses import get_classes
from api.courses import get_class_roster

#Load course data from URL param
course = get_classes(class_id=st.query_params.courseID)
roster = get_class_roster(course_id=st.query_params.courseID)

if course is not None:
    st.header(f"{course["name"]}")
    st.subheader("Roster")
    if roster:
        for student in roster:
            with st.container(border=True):
                st.subheader(student["first_name"])
    else:
        st.error("No Students Enrolled")
    
else:
    st.header("Error No Class in URL, or Invalid course ID")