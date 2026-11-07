import streamlit as st
from api.courses import get_classes

#Load course data from URL param
course = get_classes(class_id=st.query_params.courseID)

if course is not None:
    st.header(f"{course["name"]}")
    
else:
    st.header("Error No Class in URL, or Invalid course ID")
