import streamlit as st

def sidebar():
    # Sidebar navigation
    st.sidebar.page_link('main.py', label='Home')
    st.sidebar.page_link('pages/AITest.py', label='AI Test Page')
    st.sidebar.page_link('pages/import.py', label='Data Import')
    st.sidebar.page_link('pages/prof_classes.py', label='Professor Dashboard')
    st.sidebar.page_link('pages/student_dashboard.py', label='Student Dashboard')
    st.sidebar.page_link('pages/exit_slip.py', label='Exit Slip')
