import streamlit as st
from datetime import datetime
from src.passwords import require_login
from api.courses import create_class
from api.courses import get_classes
#require Login
require_login()

courses = get_classes()

st.title("Classes")
st.write("Classes you teach.")

cols = st.columns(2)

for index, course in enumerate(courses):

  col_target = cols[index % 2]

  with col_target:
    with st.container(border=True):
        st.subheader(f"{course["name"]}")
        st.write(f"{course["course_id"]}")
        if st.button("View Class", key=f"btn_{course["id"]}"):
          st.switch_page("pages/class.py", query_params={"courseID": f"{course["course_id"]}"})

if(st.button("Create New Class")):
  create_class("Test Class", 12345)