import streamlit as st
from datetime import datetime
from src.passwords import require_login
from api.courses import create_class
from api.courses import get_classes
#require Login
require_login()

courses = get_classes()

st.title("Classes")
st.write("Classes you are enrolled in.")

for course in courses:
  with st.container(border=True):
      st.subheader(f"{course["name"]}")
      st.write(f"{course["course_id"]}")
      if st.button("Go to Analytics", key=f"btn_{course["id"]}"):
        st.switch_page("pages/class.py")

if(st.button("Create New Class")):
  create_class("Test Class", 12345)