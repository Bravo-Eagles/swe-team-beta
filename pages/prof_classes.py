import streamlit as st
from datetime import datetime
from src.passwords import require_login
from api.courses import create_class
from api.courses import get_classes, get_teaching_classes, get_teacher_id
from src.sidebar import sidebar

#require Login
user = require_login()
sidebar()
st.query_params.clear() #Clear query params, useful if prof goes back a page from a class
teacher_id = get_teacher_id(user["id"])

if teacher_id is None:
    st.error("This account is not a teacher.")
    st.stop()


sections = get_teaching_classes(teacher_id)

st.title("Classes")
st.write("Classes you teach.")

cols = st.columns(2)

#Class Creation Modal
@st.dialog("Create a Class")
def create_class_modal():
    with st.form("class_form", clear_on_submit=True, enter_to_submit=False):
        new_class_name = st.text_input("Class Name")
        course_id = st.text_input("Course ID (e.g. CS101)")
        submitted = st.form_submit_button("Submit")

    if submitted:
        if not new_class_name.strip() or not course_id.strip():
            st.error("Both fields are required.")
        elif create_class(new_class_name.strip(), course_id.strip()) is None:
            st.error("Could not create the class. That Course ID may already exist.")
        else:
            st.success("Class created.")



for index, section in enumerate(sections):

  col_target = cols[index % 2]

  with col_target:
    with st.container(border=True):
        st.subheader(f"{section["name"]}")
        st.write(f"{section["course_id"]}")
        st.caption(f"{section['semester']} {section['year']}")
        if st.button("View Class", key=f"btn_{section["teaching_id"]}"):
          st.switch_page("pages/class.py", query_params={"teachingID": f"{section["teaching_id"]}"})

if(st.button("Create New Class")):
  create_class_modal()