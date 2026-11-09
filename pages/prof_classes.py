import streamlit as st
from datetime import datetime, date
from src.passwords import require_login
from api.courses import create_class
from api.courses import get_classes, get_teaching_classes, get_teacher_id, create_section
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
SEMESTERS = ["Spring", "Summer", "Fall", "Winter"]

@st.dialog("Create a Section")
def create_class_modal():
    classes = {c["id"]: c for c in get_classes()}

    def class_label(class_id):
        if class_id is None:
            return "New class..."
        c = classes[class_id]
        return f"{c['course_id']} - {c['name']}"

    #Unpacks classes into a list
    chosen = st.selectbox("Class", options=[None, *classes], format_func=class_label)

    new_name = new_course_id = None
    if chosen is None:
        new_name = st.text_input("Class name")
        new_course_id = st.text_input("Course ID (e.g. CS101)")

    col1, col2 = st.columns(2)
    semester = col1.selectbox("Semester", SEMESTERS)
    year = col2.number_input("Year", min_value=2000, max_value=2100,
                             value=date.today().year, step=1)

    if st.button("Create section"):
        try:
            create_section(teacher_id, semester, year, class_id=chosen,
                           class_name=new_name, course_id=new_course_id)
        except ValueError as e:
            st.error(str(e))
        else:
            st.session_state["flash"] = "Section created."
            st.rerun()  # closes the dialog and refreshes the list



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