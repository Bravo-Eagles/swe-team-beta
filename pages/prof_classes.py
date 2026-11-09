import streamlit as st
from datetime import datetime
from src.passwords import require_login
from api.courses import create_class
from api.courses import get_classes
#require Login
require_login()
st.query_params.clear() #Clear query params, useful if prof goes back a page from a class

courses = get_classes()

st.title("Classes")
st.write("Classes you teach.")

cols = st.columns(2)

#Class Creation Modal
@st.dialog("Create a Class")
def create_class_modal():
  st.header("Create a Class")
  with st.form("class_form", clear_on_submit=True, enter_to_submit=False):
    new_class_name = st.text_input("Class Name")
    course_id = st.number_input("Course ID", min_value=0, max_value=999999, step=1)
    submitted = st.form_submit_button("Submit")

    if submitted:
      create_class(new_class_name, course_id)
      st.success("Class Created")



for index, course in enumerate(courses):

  col_target = cols[index % 2]

  with col_target:
    with st.container(border=True):
        st.subheader(f"{course["name"]}")
        st.write(f"{course["course_id"]}")
        if st.button("View Class", key=f"btn_{course["id"]}"):
          st.switch_page("pages/class.py", query_params={"courseID": f"{course["course_id"]}"})

if(st.button("Create New Class")):
  create_class_modal()